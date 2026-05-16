"""
suggestion_engine.py
────────────────────
موتور پیشنهاد سرباز برای پست نگهبانی.

منطق کلی:
  1. سربازان فعال و واجد شرایط (health_type) را پیدا کن
  2. کسانی که امروز در مرخصی هستند را حذف کن
  3. کسانی که امروز قبلاً ۲ پاس داشته‌اند را حذف کن
  4. بر اساس امتیاز (guard_score) مرتب کن
  5. دو لیست برگردان: preferred (≥۱ روز از پست قبلی) و not_recommended (<۱ روز)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from django.db.models import Count, Q

from .models import PostAssignment, PostType, ShiftConfig, Soldier


# ─────────────────────────────────────────
#  Data classes
# ─────────────────────────────────────────

@dataclass
class SoldierSuggestion:
    """اطلاعات یک سرباز پیشنهادی همراه با امتیاز و توضیح"""
    soldier: Soldier
    score: int                          # عدد بزرگ‌تر = اولویت بیشتر
    last_post_days_ago: Optional[int]   # None اگر هیچ پستی نداشته
    under_24h: bool = False             # آیا کمتر از ۱ روز از پست قبلی گذشته
    returned_from_leave: bool = False   # آیا مرخصی برگشته (bonus گرفته)
    already_assigned_today: int = 0     # چند پاس امروز گرفته

    @property
    def score_label(self) -> str:
        """توضیح کوتاه امتیاز برای نمایش در UI"""
        if self.last_post_days_ago is None:
            return "هیچ پستی نداشته"
        if self.under_24h:
            return "کمتر از ۲۴ ساعت پیش"
        if self.returned_from_leave:
            return f"مرخصی برگشته — {self.last_post_days_ago} روز پیش"
        if self.last_post_days_ago == 1:
            return "دیروز"
        return f"{self.last_post_days_ago} روز پیش"


@dataclass
class SuggestionResult:
    """نتیجه پیشنهاد برای یک پست/پاس"""
    post_type: PostType
    shift: Optional[ShiftConfig]
    target_date: date
    preferred: List[SoldierSuggestion] = field(default_factory=list)
    not_recommended: List[SoldierSuggestion] = field(default_factory=list)
    already_assigned: List[Soldier] = field(default_factory=list)  # قبلاً در همین پست/پاس

    @property
    def all_suggestions(self) -> List[SoldierSuggestion]:
        return self.preferred + self.not_recommended


# ─────────────────────────────────────────
#  موتور اصلی
# ─────────────────────────────────────────

def suggest_soldiers(
    post_type: PostType,
    target_date: date,
    shift: Optional[ShiftConfig] = None,
) -> SuggestionResult:
    """
    پیشنهاد سرباز برای یک پست در یک پاس مشخص.

    پارامترها:
        post_type   — نوع پست (PostType)
        target_date — تاریخ برنامه
        shift       — پاس (ShiftConfig) — برای پست‌های بدون پاس None

    خروجی:
        SuggestionResult با دو لیست preferred و not_recommended
    """
    result = SuggestionResult(
        post_type=post_type,
        shift=shift,
        target_date=target_date,
    )

    # ── ۱. سربازان فعال با health_type مجاز ──
    allowed_types = post_type.allowed_health_types or []
    if not allowed_types:
        return result  # پست بدون محدودیت تعریف‌نشده → لیست خالی

    candidates = Soldier.objects.filter(
        is_active=True,
        health_type__in=allowed_types,
    ).select_related("role")

    # ── ۲. حذف سربازان در مرخصی ──
    on_leave_ids = _soldiers_on_leave(target_date)
    candidates = candidates.exclude(pk__in=on_leave_ids)

    # ── ۳. تعداد پاس‌های امروز برای هر سرباز ──
    today_shift_counts = _today_shift_counts(target_date)

    # ── ۴. سربازانی که قبلاً در همین پست/پاس انتخاب شده‌اند ──
    already_ids = _already_assigned_ids(post_type, shift, target_date)
    result.already_assigned = list(
        Soldier.objects.filter(pk__in=already_ids)
    )

    # ── ۵. محاسبه امتیاز و دسته‌بندی ──
    preferred = []
    not_recommended = []

    for soldier in candidates:
        already_today = today_shift_counts.get(soldier.pk, 0)

        # اگر ۲ پاس شیفت‌دار امروز داشته → کاملاً حذف
        if already_today >= 2:
            continue

        # اگر قبلاً در همین پست/پاس هست → از لیست پیشنهاد نمایش نده
        if soldier.pk in already_ids:
            continue

        score, meta = _compute_score(soldier, target_date)

        suggestion = SoldierSuggestion(
            soldier=soldier,
            score=score,
            last_post_days_ago=meta["days_ago"],
            under_24h=meta["under_24h"],
            returned_from_leave=meta["returned_from_leave"],
            already_assigned_today=already_today,
        )

        if meta["under_24h"]:
            not_recommended.append(suggestion)
        else:
            preferred.append(suggestion)

    # مرتب‌سازی نزولی (امتیاز بیشتر = اول)
    result.preferred = sorted(preferred, key=lambda s: s.score, reverse=True)
    result.not_recommended = sorted(not_recommended, key=lambda s: s.score, reverse=True)

    return result


def suggest_full_day(target_date: date) -> dict:
    """
    پیشنهاد کامل برای همه پست‌های یک روز.

    خروجی:
        {
            post_type_id: {
                shift_id_or_None: SuggestionResult,
                ...
            },
            ...
        }
    """
    from .models import ShiftConfig, PostType

    active_posts = PostType.objects.filter(is_active=True).order_by("order")
    active_shifts = list(ShiftConfig.objects.filter(is_active=True).order_by("order"))

    result = {}
    for post in active_posts:
        result[post.pk] = {}
        if post.is_shift_based:
            shifts_to_use = active_shifts[: post.shift_count]
            for shift in shifts_to_use:
                result[post.pk][shift.pk] = suggest_soldiers(post, target_date, shift)
        else:
            result[post.pk][None] = suggest_soldiers(post, target_date, shift=None)

    return result


def auto_assign_day(target_date: date) -> list[PostAssignment]:
    """
    تخصیص خودکار سربازان به همه پست‌های یک روز.
    فقط پست‌های خالی را پر می‌کند (تخصیص موجود را حذف نمی‌کند).

    خروجی: لیست PostAssignment‌های جدید ایجادشده
    """
    from .models import DailySchedule

    schedule, _ = DailySchedule.objects.get_or_create(date=target_date)

    if schedule.is_finalized:
        return []

    suggestions = suggest_full_day(target_date)
    created = []

    # ردیابی سربازانی که در این رَند انتخاب شدند تا تکراری نشوند
    assigned_in_round: dict[int, int] = {}  # soldier_id → تعداد پاس امروز

    for post_id, shifts_map in suggestions.items():
        from .models import PostType
        post = PostType.objects.get(pk=post_id)

        for shift_id, suggestion_result in shifts_map.items():
            shift = suggestion_result.shift

            # چند نفر در این پست/پاس نیاز داریم؟
            needed = post.soldiers_per_shift
            # چند نفر قبلاً هستند؟
            existing_count = len(suggestion_result.already_assigned)
            remaining = needed - existing_count

            if remaining <= 0:
                continue

            # انتخاب از preferred، بعد not_recommended
            pool = suggestion_result.preferred + suggestion_result.not_recommended
            assigned_count = 0

            for sugg in pool:
                if assigned_count >= remaining:
                    break

                sid = sugg.soldier.pk
                # در این رَند بیش از ۲ پاس نگیرد
                round_count = assigned_in_round.get(sid, 0)
                if round_count >= 2:
                    continue

                try:
                    pa = PostAssignment(
                        schedule=schedule,
                        post_type=post,
                        shift=shift,
                        soldier=sugg.soldier,
                        is_override=False,
                    )
                    pa.full_clean()
                    pa.save()
                    created.append(pa)
                    assigned_in_round[sid] = round_count + 1
                    assigned_count += 1
                except Exception:
                    # validation خطا داد → سرباز بعدی
                    continue

    return created


# ─────────────────────────────────────────
#  توابع کمکی داخلی
# ─────────────────────────────────────────

def _soldiers_on_leave(target_date: date) -> set[int]:
    """ID سربازانی که در تاریخ داده‌شده در مرخصی هستند"""
    from .models import Leave
    return set(
        Leave.objects.filter(
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).values_list("soldier_id", flat=True)
    )


def _today_shift_counts(target_date: date) -> dict[int, int]:
    """تعداد پاس‌های شیفت‌دار هر سرباز در تاریخ داده‌شده"""
    rows = (
        PostAssignment.objects.filter(
            schedule__date=target_date,
            post_type__is_shift_based=True,
        )
        .values("soldier_id")
        .annotate(cnt=Count("id"))
    )
    return {r["soldier_id"]: r["cnt"] for r in rows}


def _already_assigned_ids(
    post_type: PostType,
    shift: Optional[ShiftConfig],
    target_date: date,
) -> set[int]:
    """ID سربازانی که قبلاً در همین پست/پاس/تاریخ انتخاب شده‌اند"""
    qs = PostAssignment.objects.filter(
        schedule__date=target_date,
        post_type=post_type,
    )
    if shift is not None:
        qs = qs.filter(shift=shift)
    else:
        qs = qs.filter(shift__isnull=True)
    return set(qs.values_list("soldier_id", flat=True))


def _compute_score(soldier: Soldier, reference_date: date) -> tuple[int, dict]:
    """
    محاسبه امتیاز سرباز برای پیشنهاد.

    خروجی: (score, meta_dict)
    meta_dict: {days_ago, under_24h, returned_from_leave}
    """
    last = soldier.last_post_assignment()
    meta = {
        "days_ago": None,
        "under_24h": False,
        "returned_from_leave": False,
    }

    if last is None:
        return 999, meta  # هیچ پستی نداشته → بالاترین اولویت

    last_date = last.schedule.date
    days_ago = (reference_date - last_date).days
    meta["days_ago"] = days_ago

    if days_ago < 1:
        meta["under_24h"] = True

    # bonus مرخصی: اگر بعد از آخرین پست مرخصی رفته و برگشته
    from .models import Leave
    returned = Leave.objects.filter(
        soldier=soldier,
        end_date__gt=last_date,
        end_date__lt=reference_date,
    ).exists()
    if returned:
        meta["returned_from_leave"] = True
        days_ago += 2  # bonus ۲ روز

    return days_ago, meta