from datetime import date, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST

from core.models import (
    DailySchedule,
    PostAssignment,
    PostType,
    ShiftConfig,
    Soldier,
    Leave,
)


def schedule_view(request):
    """
    نمایش تقویم ۳ روزه
    """

    date_str = request.GET.get("date")

    try:
        reference_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        reference_date = date.today()

    dates = [
        reference_date - timedelta(days=1),
        reference_date,
        reference_date + timedelta(days=1),
    ]

    schedules = []
    for d in dates:
        schedule, _ = DailySchedule.objects.get_or_create(date=d)
        schedules.append(schedule)

    post_types = PostType.objects.all().order_by("name")
    shifts = ShiftConfig.objects.all().order_by("start_time")

    assignments = PostAssignment.objects.filter(
        schedule__in=schedules
    ).select_related("soldier", "post_type", "shift", "schedule")

    matrix = {}

    for schedule in schedules:
        matrix[schedule.id] = {}

        for post in post_types:
            matrix[schedule.id][post.id] = {}

            for shift in shifts:
                matrix[schedule.id][post.id][shift.id] = []

    for a in assignments:
        if a.shift_id:
            matrix[a.schedule_id][a.post_type_id][a.shift_id].append(a)

    context = {
        "reference_date": reference_date,
        "dates": dates,
        "schedules": schedules,
        "post_types": post_types,
        "shifts": shifts,
        "matrix": matrix,
    }

    return render(request, "core/schedule/view.html", context)


def generate_schedule(request, schedule_id):
    """
    تولید خودکار برنامه
    """

    schedule = get_object_or_404(DailySchedule, id=schedule_id)

    if schedule.is_finalized:
        messages.error(request, "برنامه نهایی شده است.")
        return redirect("core:schedule_view")

    PostAssignment.objects.filter(
        schedule=schedule,
        is_override=False
    ).delete()

    post_types = PostType.objects.all()
    shifts = ShiftConfig.objects.all()

    active_soldiers = Soldier.objects.filter(status="active")

    leave_ids = Leave.objects.filter(
        start_date__lte=schedule.date,
        end_date__gte=schedule.date
    ).values_list("soldier_id", flat=True)

    available_soldiers = list(active_soldiers.exclude(id__in=leave_ids))

    if not available_soldiers:
        messages.warning(request, "هیچ سرباز در دسترسی وجود ندارد.")
        return redirect("core:schedule_view")

    idx = 0

    for post in post_types:
        for shift in shifts:

            if PostAssignment.objects.filter(
                schedule=schedule,
                post_type=post,
                shift=shift,
                is_override=True
            ).exists():
                continue

            soldier = available_soldiers[idx % len(available_soldiers)]
            idx += 1

            PostAssignment.objects.create(
                schedule=schedule,
                post_type=post,
                shift=shift,
                soldier=soldier,
                is_override=False,
            )

    messages.success(request, "برنامه با موفقیت تولید شد.")
    return redirect("core:schedule_view")


@require_POST
def assign_soldier_to_post(request):
    """
    اختصاص دستی سرباز به پست
    """

    schedule_id = request.POST.get("schedule_id")
    post_id = request.POST.get("post_id")
    shift_id = request.POST.get("shift_id")
    soldier_id = request.POST.get("soldier_id")

    schedule = get_object_or_404(DailySchedule, id=schedule_id)
    post = get_object_or_404(PostType, id=post_id)
    shift = get_object_or_404(ShiftConfig, id=shift_id)
    soldier = get_object_or_404(Soldier, id=soldier_id)

    PostAssignment.objects.create(
        schedule=schedule,
        post_type=post,
        shift=shift,
        soldier=soldier,
        is_override=True,
        override_reason="اختصاص دستی",
    )

    messages.success(request, "سرباز با موفقیت اختصاص داده شد.")
    return redirect("core:schedule_view")


@require_POST
def override_assignment(request, assignment_id):
    """
    تغییر دستی پست
    """

    assignment = get_object_or_404(PostAssignment, id=assignment_id)

    soldier_id = request.POST.get("soldier_id")
    reason = request.POST.get("reason", "")

    soldier = get_object_or_404(Soldier, id=soldier_id)

    assignment.soldier = soldier
    assignment.is_override = True
    assignment.override_reason = reason
    assignment.save()

    messages.success(request, "اختصاص با موفقیت تغییر یافت.")
    return redirect("core:schedule_view")
