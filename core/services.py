from django.db.models import Count, Max
from django.utils import timezone
from datetime import timedelta

from .models import (
    Soldier,
    Leave,
    SoldierTemporaryStatus,
    PostAssignment,
)


def get_guard_score(soldier, reference_date):
    """
    امتیاز کمتر = اولویت بیشتر برای نگهبانی
    """

    total_assignments = PostAssignment.objects.filter(
        soldier=soldier,
        schedule__date__lt=reference_date
    ).count()

    last_assignment = PostAssignment.objects.filter(
        soldier=soldier,
        schedule__date__lt=reference_date
    ).aggregate(last_date=Max('schedule__date'))['last_date']

    days_since_last = 999
    if last_assignment:
        days_since_last = (reference_date - last_assignment).days

    # فرمول ساده:
    # تعداد نگهبانی بیشتر → امتیاز بالاتر (بدتر)
    # فاصله بیشتر از آخرین نگهبانی → امتیاز کمتر (بهتر)
    score = total_assignments - (days_since_last * 0.1)

    return round(score, 2)


def is_soldier_available(soldier, date):
    """
    بررسی اینکه سرباز در آن تاریخ در دسترس است یا خیر
    """

    # مرخصی
    if Leave.objects.filter(
        soldier=soldier,
        start_date__lte=date,
        end_date__gte=date
    ).exists():
        return False

    # وضعیت موقت
    if SoldierTemporaryStatus.objects.filter(
        soldier=soldier,
        date=date
    ).exists():
        return False

    return True


def suggest_soldiers_for_post(post_type, shift, date, count):
    """
    پیشنهاد سربازان برای یک پست مشخص
    """

    soldiers = Soldier.objects.filter(is_active=True)

    # فیلتر نقش‌های مجاز
    if post_type.allowed_roles.exists():
        soldiers = soldiers.filter(role__in=post_type.allowed_roles.all())

    # حذف افراد غیرقابل دسترس
    available = [
        s for s in soldiers
        if is_soldier_available(s, date)
    ]

    # محاسبه امتیاز
    scored = []
    for soldier in available:
        score = get_guard_score(soldier, date)
        scored.append((soldier, score))

    # مرتب‌سازی بر اساس امتیاز (کمتر = اولویت بیشتر)
    scored.sort(key=lambda x: x[1])

    return [s[0] for s in scored[:count]]
