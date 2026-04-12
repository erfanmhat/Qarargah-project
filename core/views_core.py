import json
import logging
from collections import defaultdict
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.shortcuts import render, redirect
from django.utils import timezone
from jdatetime import datetime as jdatetime

from core.forms import SettingsForm
from core.models import Soldier, Leave, LeaveType, ServiceLocation, ServiceStatus, SystemSetting
from core.utils.utils import jalali_ym, prev_month_start

logger = logging.getLogger('core')


def panel_login(request):
    if request.user.is_authenticated:
        return redirect('panel_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'لطفاً نام کاربری و رمز عبور را وارد کنید.')
            return render(request, 'dashboard/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            logger.info(f'User {username} logged in successfully')
            return redirect('panel_dashboard')
        else:
            logger.warning(f'Failed login attempt for username: {username}')
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است یا دسترسی ندارید.')

    return render(request, 'dashboard/login.html')


@login_required
def panel_logout(request):
    username = request.user.username
    logout(request)
    logger.info(f'User {username} logged out')
    return redirect('panel_login')


@login_required
def panel_dashboard(request):
    today = timezone.now().date()
    ninety_days_later = today + timedelta(days=90)

    soldiers = list(Soldier.objects.select_related('service_status').prefetch_related('reductions').all())
    total_soldiers = len(soldiers)

    ending_soon = 0
    for soldier in soldiers:
        try:
            end_date = soldier.service_end_date()
            if end_date and today <= end_date <= ninety_days_later:
                ending_soon += 1
        except Exception as e:
            logger.warning(f'Error calculating service_end_date for soldier {soldier.id}: {e}')
            continue

    leave_stats = Leave.objects.values('leave_type').annotate(
        total_days=Count('days')
    ).order_by('leave_type')

    leave_chart_data = {
        'labels': [],
        'data': [],
        'colors': ['#dc2626', '#16a34a', '#3b82f6']
    }

    for stat in leave_stats:
        leave_type = stat['leave_type']
        leave_chart_data['labels'].append(dict(LeaveType.choices).get(leave_type, leave_type))
        leave_chart_data['data'].append(stat['total_days'])

    six_months_later = today + timedelta(days=180)
    ending_chart_data = {
        'labels': [],
        'data': []
    }

    current_month = today
    month_labels = []
    month_counts = []

    for i in range(6):
        month_start = current_month.replace(day=1)
        if i < 5:
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
        else:
            month_end = six_months_later

        count = 0
        for soldier in soldiers:
            try:
                end_date = soldier.service_end_date()
                if end_date and month_start <= end_date < month_end:
                    count += 1
            except:
                continue

        try:
            jd = jdatetime.fromgregorian(date=month_start)
            month_labels.append(jd.strftime('%Y/%m'))
        except:
            month_labels.append(month_start.strftime('%Y/%m'))

        month_counts.append(count)
        current_month = month_end

    ending_chart_data['labels'] = month_labels
    ending_chart_data['data'] = month_counts

    stats = {
        'total_soldiers': total_soldiers,
        'ending_soon': ending_soon,
    }

    context = {
        'stats': stats,
        'leave_chart_data': json.dumps(leave_chart_data),
        'ending_chart_data': json.dumps(ending_chart_data),
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def panel_reports(request):
    today = timezone.localdate()
    show_completed = request.GET.get('show_completed') == '1'
    # پارامتر جدید برای کنترل حالت نمایش همه سربازان
    show_all_soldiers_forecast = request.GET.get('all_soldiers') == '1'

    # ==================== Monthly leaves (last 6 months) - بدون تغییر ====================
    monthly_leaves = []
    cursor = today.replace(day=1)
    for _ in range(6):
        month_start = cursor
        next_month_start = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        leaves_in_month = Leave.objects.filter(start_date__gte=month_start, start_date__lt=next_month_start)
        monthly_leaves.append({
            "month": jalali_ym(month_start),
            "total": leaves_in_month.count(),
            "total_days": leaves_in_month.aggregate(total_days=Sum("days"))["total_days"] or 0,
        })
        cursor = prev_month_start(cursor)
    monthly_leaves.reverse()

    # ==================== Service ending forecast (هوشمند و بهینه شده) ====================

    # کوئری پایه برای سربازان
    soldiers_qs = Soldier.objects.select_related(
        "service_status", "military_rank_ref"
    ).order_by('dossier_code')

    if not show_completed:
        soldiers_qs = soldiers_qs.filter(
            Q(service_status__isnull=True) | Q(service_status__is_active_service=True)
        )

    # ✅ الگوریتم بهینه: یک حلقه به جای حلقه‌های تودرتو
    # از defaultdict برای گروه‌بندی آسان‌تر استفاده می‌کنیم
    forecast_groups = defaultdict(lambda: {"month": "", "date_obj": None, "count": 0, "soldiers": []})

    six_months_later = today + timedelta(days=180)

    for soldier in soldiers_qs:
        try:
            end_date = soldier.service_end_date()
        except Exception:
            continue

        if not end_date:
            continue

        # اگر در حالت پیش‌فرض (۶ ماهه) هستیم، سربازان خارج از بازه را نادیده بگیر
        if not show_all_soldiers_forecast and not (today <= end_date < six_months_later):
            continue

        month_key = jalali_ym(end_date)

        # اولین باری که ماهی را می‌بینیم، اطلاعات اصلی آن را ثبت کن
        if not forecast_groups[month_key]["month"]:
            forecast_groups[month_key]["month"] = month_key
            forecast_groups[month_key]["date_obj"] = end_date.replace(day=1)

        forecast_groups[month_key]["count"] += 1
        forecast_groups[month_key]["soldiers"].append(soldier)

    # تبدیل دیکشنری به لیست و مرتب‌سازی بر اساس تاریخ برای نمایش منظم
    ending_forecast = sorted(forecast_groups.values(), key=lambda item: item["date_obj"])

    # ==================== Distributions - بدون تغییر ====================
    location_dist = ServiceLocation.objects.annotate(
        soldier_count=Count("soldier")
    ).filter(soldier_count__gt=0).order_by("-soldier_count")[:10]

    status_dist = ServiceStatus.objects.annotate(
        soldier_count=Count("soldier")
    ).filter(soldier_count__gt=0).order_by("-soldier_count")

    extra_type_dist = Soldier.objects.filter(
        extra_service_type__isnull=False
    ).values('extra_service_type__title').annotate(count=Count('id')).order_by('-count')

    rank_dist = Soldier.objects.filter(
        military_rank_ref__isnull=False
    ).values(
        'military_rank_ref__title', 'military_rank_ref__code'
    ).annotate(count=Count('id')).order_by('military_rank_ref__code')

    context = {
        "monthly_leaves": monthly_leaves,
        "ending_forecast": ending_forecast,
        "location_dist": location_dist,
        "status_dist": status_dist,
        "extra_type_dist": extra_type_dist,
        "rank_dist": rank_dist,
        "show_completed": show_completed,
        # ارسال متغیر جدید به تمپلیت برای کنترل دکمه‌ها و عناوین
        "show_all_soldiers_forecast": show_all_soldiers_forecast,
    }
    return render(request, "dashboard/reports.html", context)


@login_required
def panel_settings(request):
    """System settings page"""

    def _get_bool(key, default=True):
        val = SystemSetting.get_value(key, 'true' if default else 'false')
        return str(val).lower() == 'true'

    initial = {
        'base_service_months': int(SystemSetting.get_value('BASE_SERVICE_MONTHS', '21') or 21),
        'enable_leave_entitlement': _get_bool('ENABLE_LEAVE_ENTITLEMENT', True),
        'enable_leave_medical': _get_bool('ENABLE_LEAVE_MEDICAL', True),
        'enable_leave_reward': _get_bool('ENABLE_LEAVE_REWARD', True),
    }

    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            SystemSetting.objects.update_or_create(key='BASE_SERVICE_MONTHS',
                                                   defaults={'value': str(form.cleaned_data['base_service_months'])})
            SystemSetting.objects.update_or_create(key='ENABLE_LEAVE_ENTITLEMENT', defaults={
                'value': str(form.cleaned_data['enable_leave_entitlement'])})
            SystemSetting.objects.update_or_create(key='ENABLE_LEAVE_MEDICAL',
                                                   defaults={'value': str(form.cleaned_data['enable_leave_medical'])})
            SystemSetting.objects.update_or_create(key='ENABLE_LEAVE_REWARD',
                                                   defaults={'value': str(form.cleaned_data['enable_leave_reward'])})
            messages.success(request, 'تنظیمات با موفقیت ذخیره شد.')
            return redirect('panel_settings')
    else:
        form = SettingsForm(initial=initial)

    return render(request, 'dashboard/settings.html', {'form': form})


@login_required
def calculate_jalali_diff(request):
    """calculate_jalali_diff page"""
    return render(request, 'dashboard/calculate_jalali_diff.html')
