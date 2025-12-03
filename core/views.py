from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import json
from core.models import Soldier, Leave, LeaveType, ServiceStatus, ServiceLocation, Expertise
from django.shortcuts import render


@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()

    all_soldiers = Soldier.objects.all()
    ending_soon_count = 0
    for soldier in all_soldiers:
        try:
            end_date = soldier.service_end_date()
            if today <= end_date <= today + timedelta(days=90):
                ending_soon_count += 1
        except:
            pass

    stats = {
        'total_soldiers': Soldier.objects.count(),
        'on_leave_today': Leave.objects.filter(
            start_date__lte=today, end_date__gte=today, is_approved=True
        ).count(),
        'ending_soon': ending_soon_count,
        'medical_leaves': Leave.objects.filter(leave_type=LeaveType.MEDICAL, is_approved=True).count(),
        'reward_leaves': Leave.objects.filter(leave_type=LeaveType.REWARD, is_approved=True).count(),
        'entitlement_leaves': Leave.objects.filter(leave_type=LeaveType.ENTITLEMENT, is_approved=True).count(),
    }

    leave_data = Leave.objects.filter(is_approved=True) \
        .values('leave_type') \
        .annotate(count=Count('id'))

    leave_labels = []
    leave_values = []
    leave_colors = []
    for item in leave_data:
        if item['leave_type'] == LeaveType.MEDICAL:
            leave_labels.append('استعلاجی')
            leave_colors.append('#e91e63')
        elif item['leave_type'] == LeaveType.REWARD:
            leave_labels.append('تشویقی')
            leave_colors.append('#4caf50')
        else:
            leave_labels.append('استحقاقی')
            leave_colors.append('#2196f3')
        leave_values.append(item['count'])

    months = []
    counts = []
    for i in range(6):
        start = today + timedelta(days=30 * i)
        end = start + timedelta(days=30)
        count = 0
        for soldier in all_soldiers:
            try:
                end_date = soldier.service_end_date()
                if start <= end_date < end:
                    count += 1
            except:
                pass
        months.append(start.strftime('%Y/%m'))
        counts.append(count)

    context = {
        'title': 'داشبورد مدیریت',
        'stats': stats,
        'leave_chart_data': json.dumps({
            'labels': leave_labels or ['بدون داده'],
            'data': leave_values or [0],
            'colors': leave_colors or ['#666'],
        }),
        'ending_chart_data': json.dumps({
            'labels': months,
            'data': counts,
        }),
    }
    return render(request, 'admin/dashboard.html', context)


def soldier_search_view(request):
    soldiers = Soldier.objects.select_related('health_status', 'service_status', 'current_location').prefetch_related(
        'expertises').all()

    context = {
        'soldiers': soldiers,
        'service_statuses': ServiceStatus.objects.all(),
        'locations': ServiceLocation.objects.all(),
        'expertises': Expertise.objects.all(),
        'title': 'جستجو و فیلتر سربازان'
    }
    return render(request, 'admin/soldier_search.html', context)
