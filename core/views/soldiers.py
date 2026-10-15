from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

from ..models import Soldier
from ..forms import SoldierForm, SoldierSearchForm
from ..services import get_guard_score


def soldier_list(request):
    soldiers = Soldier.objects.all()
    form = SoldierSearchForm(request.GET or None)

    if form.is_valid():
        search = form.cleaned_data.get("search")

        if search:
            soldiers = soldiers.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(national_code__icontains=search)
            )

    context = {
        "form": form,
        "soldiers": soldiers,
    }

    return render(request, "core/soldiers/list.html", context)


def soldier_detail(request, pk):
    soldier = get_object_or_404(Soldier, pk=pk)

    assignments = soldier.postassignment_set.select_related(
        "post_type", "shift"
    ).order_by("-created_at")

    leaves = soldier.leave_set.all().order_by("-start_date")

    last_assignment = assignments.first()

    guard_score = get_guard_score(soldier, timezone.now().date())

    current_leave = leaves.filter(
        start_date__lte=datetime.now(),
        end_date__gte=datetime.now()
    ).first()

    context = {
        "soldier": soldier,
        "assignments": assignments,
        "leaves": leaves,
        "last_assignment": last_assignment,
        "guard_score": guard_score,
        "current_leave": current_leave,
        "is_on_leave": current_leave is not None,
    }

    return render(request, "core/soldiers/detail.html", context)


def soldier_create(request):
    if request.method == "POST":
        form = SoldierForm(request.POST)

        if form.is_valid():
            soldier = form.save()
            messages.success(request, "سرباز با موفقیت ثبت شد.")
            return redirect("core:soldier_detail", pk=soldier.pk)
    else:
        form = SoldierForm()

    return render(request, "core/soldiers/form.html", {"form": form})


def soldier_update(request, pk):
    soldier = get_object_or_404(Soldier, pk=pk)

    if request.method == "POST":
        form = SoldierForm(request.POST, instance=soldier)

        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات سرباز بروزرسانی شد.")
            return redirect("core:soldier_detail", pk=soldier.pk)
    else:
        form = SoldierForm(instance=soldier)

    context = {
        "form": form,
        "soldier": soldier,
    }

    return render(request, "core/soldiers/form.html", context)


def soldier_delete(request, pk):
    soldier = get_object_or_404(Soldier, pk=pk)

    if request.method == "POST":
        soldier.delete()
        messages.success(request, "سرباز حذف شد.")
        return redirect("core:soldier_list")

    return render(
        request,
        "core/soldiers/delete.html",
        {"soldier": soldier},
    )
