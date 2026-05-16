import json
from datetime import date, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import (
    DailySchedule,
    PostAssignment,
    PostType,
    ShiftConfig,
    Soldier,
)
from ..suggestion_engine import suggest_soldiers, auto_assign_day


# ─────────────────────────────────────────
#  نمایش برنامه ۳ روزه
# ─────────────────────────────────────────

def schedule_index(request):
    """نمایش برنامه امروز، فردا و پس‌فردا"""
    today = timezone.now().date()
    dates = [today, today + timedelta(days=1), today + timedelta(days=2)]

    days_data = []
    for d in dates:
        schedule = DailySchedule.objects.filter(date=d).first()
        days_data.append(_build_day_context(d, schedule))

    context = {
        "days_data": days_data,
        "today": today,
    }
    return render(request, "core/schedule/index.html", context)


def schedule_day(request, year, month, day):
    """نمایش برنامه یک روز مشخص"""
    target_date = date(year, month, day)
    schedule = DailySchedule.objects.filter(date=target_date).first()
    day_data = _build_day_context(target_date, schedule)

    context = {
        "day_data": day_data,
        "target_date": target_date,
        "today": timezone.now().date(),
    }
    return render(request, "core/schedule/day.html", context)


# ─────────────────────────────────────────
#  تولید خودکار پیشنهاد
# ─────────────────────────────────────────

@require_POST
def schedule_generate(request, year, month, day):
    """تولید خودکار برنامه یک روز (پست‌های خالی را پر می‌کند)"""
    target_date = date(year, month, day)

    schedule = DailySchedule.objects.filter(date=target_date).first()
    if schedule and schedule.is_finalized:
        messages.warning(request, "این برنامه نهایی شده و قابل تغییر نیست.")
        return redirect("core:schedule_day", year=year, month=month, day=day)

    created = auto_assign_day(target_date)
    messages.success(request, f"برنامه پیشنهادی ایجاد شد. {len(created)} تخصیص جدید.")
    return redirect("core:schedule_day", year=year, month=month, day=day)


# ─────────────────────────────────────────
#  Modal پیشنهاد سرباز (AJAX)
# ─────────────────────────────────────────

def suggest_for_post(request):
    """
    AJAX — پیشنهاد سربازان برای یک پست/پاس.
    پارامترهای GET: post_type_id, shift_id (اختیاری), date (YYYY-MM-DD)
    """
    try:
        post_type = get_object_or_404(PostType, pk=request.GET["post_type_id"])
        target_date = date.fromisoformat(request.GET["date"])
        shift_id = request.GET.get("shift_id")
        shift = get_object_or_404(ShiftConfig, pk=shift_id) if shift_id else None
    except (KeyError, ValueError):
        return JsonResponse({"error": "پارامترهای ناقص"}, status=400)

    result = suggest_soldiers(post_type, target_date, shift)

    def serialize_suggestion(s):
        return {
            "id": s.soldier.pk,
            "name": s.soldier.full_name,
            "health_type": s.soldier.health_type,
            "health_label": s.soldier.get_health_type_display(),
            "role": s.soldier.role.title if s.soldier.role else "",
            "score": s.score,
            "score_label": s.score_label,
            "under_24h": s.under_24h,
            "returned_from_leave": s.returned_from_leave,
        }

    return JsonResponse({
        "post_name": post_type.name,
        "shift_name": str(shift) if shift else "—",
        "preferred": [serialize_suggestion(s) for s in result.preferred],
        "not_recommended": [serialize_suggestion(s) for s in result.not_recommended],
        "already_assigned": [
            {"id": s.pk, "name": s.full_name} for s in result.already_assigned
        ],
    })


# ─────────────────────────────────────────
#  تخصیص / حذف یک سرباز (AJAX)
# ─────────────────────────────────────────

@require_POST
def assign_soldier(request):
    """
    AJAX POST — تخصیص یک سرباز به پست/پاس.
    Body JSON: {soldier_id, post_type_id, shift_id (nullable), date}
    """
    try:
        body = json.loads(request.body)
        soldier = get_object_or_404(Soldier, pk=body["soldier_id"])
        post_type = get_object_or_404(PostType, pk=body["post_type_id"])
        target_date = date.fromisoformat(body["date"])
        shift_id = body.get("shift_id")
        shift = get_object_or_404(ShiftConfig, pk=shift_id) if shift_id else None
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "پارامترهای ناقص"}, status=400)

    schedule, _ = DailySchedule.objects.get_or_create(date=target_date)

    if schedule.is_finalized:
        return JsonResponse({"ok": False, "error": "برنامه نهایی شده است."})

    # حذف تخصیص قبلی در همین جایگاه اگر وجود دارد
    PostAssignment.objects.filter(
        schedule=schedule,
        post_type=post_type,
        shift=shift,
        soldier=soldier,
    ).delete()

    try:
        pa = PostAssignment(
            schedule=schedule,
            post_type=post_type,
            shift=shift,
            soldier=soldier,
            is_override=True,
        )
        pa.full_clean()
        pa.save()
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})

    return JsonResponse({
        "ok": True,
        "assignment_id": pa.pk,
        "soldier_name": soldier.full_name,
    })


@require_POST
def remove_assignment(request, pk):
    """AJAX POST — حذف یک تخصیص پست"""
    pa = get_object_or_404(PostAssignment, pk=pk)

    if pa.schedule.is_finalized:
        return JsonResponse({"ok": False, "error": "برنامه نهایی شده است."})

    pa.delete()
    return JsonResponse({"ok": True})


# ─────────────────────────────────────────
#  نهایی کردن برنامه
# ─────────────────────────────────────────

@require_POST
def schedule_finalize(request, year, month, day):
    """نهایی کردن برنامه یک روز"""
    target_date = date(year, month, day)
    schedule, _ = DailySchedule.objects.get_or_create(date=target_date)
    schedule.is_finalized = True
    schedule.save()
    messages.success(request, f"برنامه {target_date} نهایی و قفل شد.")
    return redirect("core:schedule_day", year=year, month=month, day=day)


@require_POST
def schedule_unfinalize(request, year, month, day):
    """باز کردن قفل برنامه نهایی‌شده"""
    target_date = date(year, month, day)
    schedule = get_object_or_404(DailySchedule, date=target_date)
    schedule.is_finalized = False
    schedule.save()
    messages.success(request, "قفل برنامه باز شد.")
    return redirect("core:schedule_day", year=year, month=month, day=day)


# ─────────────────────────────────────────
#  تابع کمکی: ساختار یک روز
# ─────────────────────────────────────────

def _build_day_context(target_date: date, schedule: DailySchedule) -> dict:
    """
    ساختار داده برای نمایش گرید یک روز در template.

    خروجی:
    {
        date, schedule, is_finalized,
        posts: [
            {
                post_type,
                shifts: [
                    {
                        shift (یا None),
                        assignments: [PostAssignment, ...],
                        needed: int,
                        empty_slots: int,
                    },
                    ...
                ]
            },
            ...
        ]
    }
    """
    from django.db.models import Prefetch

    active_posts = PostType.objects.filter(is_active=True).order_by("order")
    active_shifts = list(ShiftConfig.objects.filter(is_active=True).order_by("order"))

    # همه تخصیص‌های این روز را یک‌بار بخوان
    if schedule:
        all_assignments = list(
            PostAssignment.objects.filter(schedule=schedule)
            .select_related("post_type", "shift", "soldier")
        )
    else:
        all_assignments = []

    # ایندکس سریع
    assignment_map: dict[tuple, list] = {}
    for pa in all_assignments:
        key = (pa.post_type_id, pa.shift_id)
        assignment_map.setdefault(key, []).append(pa)

    posts_data = []
    for post in active_posts:
        shifts_data = []
        if post.is_shift_based:
            shifts_to_show = active_shifts[: post.shift_count]
            for shift in shifts_to_show:
                assigned = assignment_map.get((post.pk, shift.pk), [])
                shifts_data.append({
                    "shift": shift,
                    "assignments": assigned,
                    "needed": post.soldiers_per_shift,
                    "empty_slots": max(post.soldiers_per_shift - len(assigned), 0),
                })
        else:
            assigned = assignment_map.get((post.pk, None), [])
            shifts_data.append({
                "shift": None,
                "assignments": assigned,
                "needed": post.soldiers_per_shift,
                "empty_slots": max(post.soldiers_per_shift - len(assigned), 0),
            })

        posts_data.append({
            "post_type": post,
            "shifts": shifts_data,
        })

    return {
        "date": target_date,
        "schedule": schedule,
        "is_finalized": schedule.is_finalized if schedule else False,
        "posts": posts_data,
    }