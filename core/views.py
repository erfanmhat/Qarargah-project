from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta
import json
import logging
from core.models import Soldier, Leave, LeaveType, ServiceLocation, ServiceStatus
from jdatetime import datetime as jdatetime

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

    # محاسبه آماری که نیاز به service_end_date دارن، در پایتون انجام می‌دیم
    # Optimized: Load all soldiers once with prefetch_related to reduce queries
    soldiers = list(Soldier.objects.select_related('service_status').prefetch_related('reductions').all())
    total_soldiers = len(soldiers)
    
    on_leave_today = Leave.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        is_approved=True
    ).count()

    # محاسبه سربازانی که تا ۹۰ روز آینده خدمت‌شون تموم می‌شه
    ending_soon = 0
    for soldier in soldiers:
        try:
            end_date = soldier.service_end_date()
            if end_date and today <= end_date <= ninety_days_later:
                ending_soon += 1
        except Exception as e:
            logger.warning(f'Error calculating service_end_date for soldier {soldier.id}: {e}')
            continue

    # Chart data: Leave type distribution
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

    # Chart data: Service ending in next 6 months
    six_months_later = today + timedelta(days=180)
    ending_chart_data = {
        'labels': [],
        'data': []
    }
    
    # Group by month
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
        
        # Count soldiers ending in this month
        # Use prefetched soldiers list to avoid multiple queries
        count = 0
        for soldier in soldiers:
            try:
                end_date = soldier.service_end_date()
                if end_date and month_start <= end_date < month_end:
                    count += 1
            except:
                continue
        
        # Convert to Jalali month name
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
        'on_leave_today': on_leave_today,
        'ending_soon': ending_soon,
    }

    context = {
        'stats': stats,
        'leave_chart_data': json.dumps(leave_chart_data),
        'ending_chart_data': json.dumps(ending_chart_data),
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def panel_soldiers(request):
    soldiers = Soldier.objects.select_related('service_status', 'current_location').all()
    
    # Pagination
    paginator = Paginator(soldiers, 25)  # Show 25 soldiers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/soldiers_list.html', {
        'soldiers': page_obj,
        'page_obj': page_obj,
    })


@login_required
def panel_leaves(request):
    leaves = Leave.objects.select_related('soldier').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(leaves, 25)  # Show 25 leaves per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/leaves_list.html', {
        'leaves': page_obj,
        'page_obj': page_obj,
    })


@login_required
def panel_search(request):
    soldiers = Soldier.objects.select_related('service_status', 'current_location', 'health_status').all()
    
    # Search filters
    query = request.GET.get('q', '').strip()
    dispatch_type = request.GET.get('dispatch_type', '')
    service_status_id = request.GET.get('service_status', '')
    
    if query:
        soldiers = soldiers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(national_code__icontains=query) |
            Q(dossier_code__icontains=query) |
            Q(phone_personal__icontains=query)
        )
    
    if dispatch_type:
        soldiers = soldiers.filter(dispatch_type=dispatch_type)
    
    if service_status_id:
        soldiers = soldiers.filter(service_status_id=service_status_id)
    
    # Pagination
    paginator = Paginator(soldiers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    from core.models import DispatchType
    
    context = {
        'soldiers': page_obj,
        'page_obj': page_obj,
        'query': query,
        'dispatch_types': DispatchType.choices,
        'service_statuses': ServiceStatus.objects.all(),
        'selected_dispatch_type': dispatch_type,
        'selected_service_status': service_status_id,
    }
    
    return render(request, 'dashboard/soldier_search.html', context)


def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)


@login_required
def panel_soldier_detail(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    leaves = soldier.leaves.all().order_by('-start_date')
    reductions = soldier.reductions.all()
    
    context = {
        'soldier': soldier,
        'leaves': leaves,
        'reductions': reductions,
    }
    
    return render(request, 'dashboard/soldier_detail.html', context)


@login_required
def panel_soldier_delete(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    
    if request.method == 'POST':
        soldier_name = soldier.full_name()
        soldier_id = soldier.id
        soldier.delete()
        logger.info(f'Soldier {soldier_id} ({soldier_name}) deleted by user {request.user.username}')
        messages.success(request, f'سرباز "{soldier_name}" با موفقیت حذف شد.')
        return redirect('panel_soldiers')
    
    return render(request, 'dashboard/soldier_confirm_delete.html', {'soldier': soldier})


@login_required
def panel_leave_delete(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    
    if request.method == 'POST':
        soldier_name = leave.soldier.full_name()
        leave_id = leave.id
        leave.delete()
        logger.info(f'Leave {leave_id} for soldier {soldier_name} deleted by user {request.user.username}')
        messages.success(request, f'مرخصی سرباز "{soldier_name}" با موفقیت حذف شد.')
        return redirect('panel_leaves')
    
    return render(request, 'dashboard/leave_confirm_delete.html', {'leave': leave})


@login_required
def health_check(request):
    """Health check endpoint for monitoring"""
    from django.db import connection
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)


@login_required
def export_soldiers_excel(request):
    """Export soldiers to Excel"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from django.http import HttpResponse
        
        soldiers = Soldier.objects.select_related('service_status', 'current_location', 'health_status').all()
        
        wb = Workbook()
        ws = wb.active
        ws.title = "سربازان"
        
        # Headers
        headers = ['نام', 'نام خانوادگی', 'کد ملی', 'کد پرونده', 'نوع اعزام', 
                  'تاریخ شروع خدمت', 'پایان خدمت', 'وضعیت خدمت', 'محل خدمت']
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Data
        for soldier in soldiers:
            end_date = soldier.service_end_date()
            ws.append([
                soldier.first_name,
                soldier.last_name,
                soldier.national_code,
                soldier.dossier_code or '',
                soldier.get_dispatch_type_display(),
                soldier.service_start_date.strftime('%Y/%m/%d') if soldier.service_start_date else '',
                end_date.strftime('%Y/%m/%d') if end_date else '',
                soldier.service_status.title if soldier.service_status else '',
                soldier.current_location.name if soldier.current_location else ''
            ])
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="soldiers.xlsx"'
        wb.save(response)
        logger.info(f'Soldiers exported to Excel by user {request.user.username}')
        return response
    except ImportError:
        messages.error(request, 'برای استفاده از این قابلیت، openpyxl را نصب کنید: pip install openpyxl')
        return redirect('panel_soldiers')
    except Exception as e:
        logger.error(f'Error exporting soldiers: {e}')
        messages.error(request, 'خطا در خروجی گرفتن اطلاعات')
        return redirect('panel_soldiers')


@login_required
def export_leaves_excel(request):
    """Export leaves to Excel"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from django.http import HttpResponse
        
        leaves = Leave.objects.select_related('soldier').order_by('-start_date')
        
        wb = Workbook()
        ws = wb.active
        ws.title = "مرخصی‌ها"
        
        # Headers
        headers = ['نام سرباز', 'کد ملی', 'نوع مرخصی', 'تاریخ رفت', 
                  'تاریخ برگشت', 'مدت (روز)', 'وضعیت تأیید']
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Data
        for leave in leaves:
            ws.append([
                leave.soldier.full_name(),
                leave.soldier.national_code,
                leave.get_leave_type_display(),
                leave.start_date.strftime('%Y/%m/%d'),
                leave.end_date.strftime('%Y/%m/%d'),
                leave.days,
                'تأیید شده' if leave.is_approved else 'در انتظار تأیید'
            ])
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="leaves.xlsx"'
        wb.save(response)
        logger.info(f'Leaves exported to Excel by user {request.user.username}')
        return response
    except ImportError:
        messages.error(request, 'برای استفاده از این قابلیت، openpyxl را نصب کنید: pip install openpyxl')
        return redirect('panel_leaves')
    except Exception as e:
        logger.error(f'Error exporting leaves: {e}')
        messages.error(request, 'خطا در خروجی گرفتن اطلاعات')
        return redirect('panel_leaves')


@login_required
def panel_reports(request):
    """Reports page"""
    from django.db.models import Count, Sum
    from datetime import datetime
    
    # Monthly leave statistics
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    
    # Get last 6 months
    monthly_leaves = []
    for i in range(6):
        month_start = current_month_start
        if month_start.month == 1:
            month_start = month_start.replace(year=month_start.year - 1, month=12)
        else:
            month_start = month_start.replace(month=month_start.month - 1)
        
        month_end = current_month_start
        if i == 0:
            month_end = today
        
        leaves_in_month = Leave.objects.filter(
            start_date__gte=month_start,
            start_date__lt=month_end
        )
        
        monthly_leaves.append({
            'month': month_start.strftime('%Y/%m'),
            'total': leaves_in_month.count(),
            'approved': leaves_in_month.filter(is_approved=True).count(),
            'total_days': leaves_in_month.aggregate(Sum('days'))['days__sum'] or 0,
        })
        
        current_month_start = month_start
    
    monthly_leaves.reverse()
    
    # Service completion forecast
    six_months_later = today + timedelta(days=180)
    ending_forecast = []
    current_month = today.replace(day=1)
    
    for i in range(6):
        if current_month.month == 12:
            month_end = current_month.replace(year=current_month.year + 1, month=1)
        else:
            month_end = current_month.replace(month=current_month.month + 1)
        
        if i == 5:
            month_end = six_months_later
        
        count = 0
        soldiers = Soldier.objects.select_related('service_status').prefetch_related('reductions').all()
        for soldier in soldiers:
            try:
                end_date = soldier.service_end_date()
                if end_date and current_month <= end_date < month_end:
                    count += 1
            except:
                continue
        
        try:
            jd = jdatetime.fromgregorian(date=current_month)
            month_label = jd.strftime('%Y/%m')
        except:
            month_label = current_month.strftime('%Y/%m')
        
        ending_forecast.append({
            'month': month_label,
            'count': count
        })
        
        current_month = month_end
    
    # Soldier distribution by location
    location_dist = ServiceLocation.objects.annotate(
        soldier_count=Count('soldier')
    ).filter(soldier_count__gt=0).order_by('-soldier_count')[:10]
    
    # Soldier distribution by status
    status_dist = ServiceStatus.objects.annotate(
        soldier_count=Count('soldier')
    ).order_by('-soldier_count')
    
    context = {
        'monthly_leaves': monthly_leaves,
        'ending_forecast': ending_forecast,
        'location_dist': location_dist,
        'status_dist': status_dist,
    }
    
    return render(request, 'dashboard/reports.html', context)
