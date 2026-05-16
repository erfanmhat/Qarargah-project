from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..forms import SoldierFilterForm, SoldierForm
from ..models import HealthType, PostAssignment, Soldier


def soldier_list(request):
    """لیست سربازان با فیلتر وضعیت سلامت و جستجو"""
    form = SoldierFilterForm(request.GET)
    soldiers = Soldier.objects.select_related("role").order_by("full_name")

    today = timezone.now().date()

    if form.is_valid():
        health = form.cleaned_data.get("health_type")
        status = form.cleaned_data.get("status")
        search = form.cleaned_data.get("search")

        if health:
            soldiers = soldiers.filter(health_type=health)

        if status == "active":
            soldiers = soldiers.filter(is_active=True)
        elif status == "on_leave":
            soldiers = soldiers.filter(
                is_active=True,
                leaves__start_date__lte=today,
                leaves__end_date__gte=today,
            ).distinct()

        if search:
            soldiers = soldiers.filter(
                full_name__icontains=search
            ) | soldiers.filter(national_code__icontains=search)

    # آمار سریع
    total = Soldier.objects.filter(is_active=True).count()
    healthy_count = Soldier.objects.filter(is_active=True, health_type=HealthType.HEALTHY).count()
    psych_count = Soldier.objects.filter(is_active=True, health_type=HealthType.PSYCH_EXEMPT).count()
    other_count = Soldier.objects.filter(is_active=True, health_type=HealthType.OTHER_EXEMPT).count()

    # وضعیت مرخصی هر سرباز
    on_leave_today = set(
        Soldier.objects.filter(
            leaves__start_date__lte=today,
            leaves__end_date__gte=today,
        ).values_list("pk", flat=True)
    )

    context = {
        "soldiers": soldiers,
        "form": form,
        "today": today,
        "on_leave_today": on_leave_today,
        "stats": {
            "total": total,
            "healthy": healthy_count,
            "psych": psych_count,
            "other": other_count,
        },
    }
    return render(request, "core/soldiers/list.html", context)


def soldier_add(request):
    """افزودن سرباز جدید"""
    if request.method == "POST":
        form = SoldierForm(request.POST)
        if form.is_valid():
            soldier = form.save()
            messages.success(request, f"سرباز «{soldier.full_name}» با موفقیت اضافه شد.")
            return redirect("core:soldier_list")
    else:
        form = SoldierForm()

    return render(request, "core/soldiers/form.html", {
        "form": form,
        "action": "add",
        "title": "افزودن سرباز",
    })


def soldier_edit(request, pk):
    """ویرایش سرباز"""
    soldier = get_object_or_404(Soldier, pk=pk)

    if request.method == "POST":
        form = SoldierForm(request.POST, instance=soldier)
        if form.is_valid():
            form.save()
            messages.success(request, f"اطلاعات «{soldier.full_name}» بروزرسانی شد.")
            return redirect("core:soldier_list")
    else:
        form = SoldierForm(instance=soldier)

    return render(request, "core/soldiers/form.html", {
        "form": form,
        "soldier": soldier,
        "action": "edit",
        "title": f"ویرایش — {soldier.full_name}",
    })


@require_POST
def soldier_delete(request, pk):
    """حذف سرباز"""
    soldier = get_object_or_404(Soldier, pk=pk)
    name = soldier.full_name
    soldier.delete()
    messages.success(request, f"سرباز «{name}» حذف شد.")
    return redirect("core:soldier_list")


def soldier_profile(request, pk):
    """پروفایل سرباز: تاریخچه نگهبانی و مرخصی‌ها"""
    soldier = get_object_or_404(Soldier.objects.select_related("role"), pk=pk)
    today = timezone.now().date()

    assignments = (
        PostAssignment.objects
        .filter(soldier=soldier)
        .select_related("schedule", "post_type", "shift")
        .order_by("-schedule__date")[:30]
    )

    leaves = soldier.leaves.order_by("-start_date")

    context = {
        "soldier": soldier,
        "assignments": assignments,
        "leaves": leaves,
        "is_on_leave": soldier.is_on_leave(today),
        "guard_score": soldier.guard_score(today),
        "today": today,
    }
    return render(request, "core/soldiers/profile.html", context)