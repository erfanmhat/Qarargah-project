from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Soldier, Leave
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta


def panel_login(request):
    if request.user.is_authenticated:
        return redirect('panel_dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('panel_dashboard')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است یا دسترسی ندارید.')

    return render(request, 'dashboard/login.html')


@login_required
def panel_logout(request):
    logout(request)
    return redirect('panel_login')


@login_required
def panel_dashboard(request):
    today = timezone.now().date()
    ninety_days_later = today + timedelta(days=90)

    # محاسبه آماری که نیاز به service_end_date دارن، در پایتون انجام می‌دیم
    total_soldiers = Soldier.objects.count()
    on_leave_today = Leave.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        is_approved=True
    ).count()

    # محاسبه سربازانی که تا ۹۰ روز آینده خدمت‌شون تموم می‌شه
    ending_soon = 0
    for soldier in Soldier.objects.all():
        try:
            end_date = soldier.service_end_date()
            if end_date and today <= end_date <= ninety_days_later:
                ending_soon += 1
        except:
            continue

    stats = {
        'total_soldiers': total_soldiers,
        'on_leave_today': on_leave_today,
        'ending_soon': ending_soon,
    }

    return render(request, 'dashboard/dashboard.html', {'stats': stats})


@login_required
def panel_soldiers(request):
    soldiers = Soldier.objects.select_related('service_status', 'current_location').all()
    return render(request, 'dashboard/soldiers_list.html', {'soldiers': soldiers})


@login_required
def panel_leaves(request):
    leaves = Leave.objects.select_related('soldier').order_by('-created_at')
    return render(request, 'dashboard/leaves_list.html', {'leaves': leaves})


@login_required
def panel_search(request):
    return render(request, 'dashboard/soldier_search.html')
