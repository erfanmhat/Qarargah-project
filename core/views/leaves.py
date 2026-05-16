from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..forms import LeaveForm
from ..models import Leave, Soldier


def leave_list(request):
    """لیست مرخصی‌های فعال (امروز یا آینده) + تاریخچه"""
    today = timezone.now().date()
    tab = request.GET.get("tab", "active")

    if tab == "history":
        leaves = Leave.objects.filter(end_date__lt=today)
    else:
        leaves = Leave.objects.filter(end_date__gte=today)

    leaves = leaves.select_related("soldier").order_by("-start_date")

    context = {
        "leaves": leaves,
        "today": today,
        "tab": tab,
    }
    return render(request, "core/leaves/list.html", context)


def leave_add(request, soldier_pk):
    """ثبت مرخصی برای سرباز مشخص"""
    soldier = get_object_or_404(Soldier, pk=soldier_pk)

    if request.method == "POST":
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.soldier = soldier
            try:
                leave.save()
                messages.success(
                    request,
                    f"مرخصی {leave.get_leave_type_display()} برای «{soldier.full_name}» ثبت شد."
                )
                return redirect("core:soldier_profile", pk=soldier.pk)
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = LeaveForm()

    return render(request, "core/leaves/form.html", {
        "form": form,
        "soldier": soldier,
    })


@require_POST
def leave_delete(request, pk):
    """حذف مرخصی"""
    leave = get_object_or_404(Leave, pk=pk)
    soldier_pk = leave.soldier.pk
    leave.delete()
    messages.success(request, "مرخصی حذف شد.")
    return redirect("core:soldier_profile", pk=soldier_pk)