from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from core.models import Soldier, Leave, ServiceLocation, HealthStatus, ServiceStatus
from core.utils.utils import parse_date_input
import logging

logger = logging.getLogger('core')


@login_required
def panel_soldiers(request):
    show_completed = request.GET.get('show_completed') == '1'
    sort_key = request.GET.get('sort', '-start_date')
    page_size_raw = request.GET.get('page_size')

    try:
        page_size = int(page_size_raw)
        page_size = max(5, min(page_size, 10000))
    except (TypeError, ValueError):
        page_size = 250

    sort_map = {
        'name': 'full_name',
        '-name': '-full_name',
        'national_code': 'national_code',
        '-national_code': '-national_code',
        'start_date': 'service_start_date',
        '-start_date': '-service_start_date',
        'dossier': 'dossier_code',
        '-dossier': '-dossier_code',
        'status': 'service_status__title',
        '-status': '-service_status__title',
        'location': 'current_location__name',
        '-location': '-current_location__name',
        'created': '-created_at',
        '-created': '-created_at',
    }
    order_fields = sort_map.get(sort_key, ('-service_start_date',))
    if isinstance(order_fields, str):
        order_fields = (order_fields,)

    soldiers = Soldier.objects.select_related('service_status', 'current_location')
    if not show_completed:
        soldiers = soldiers.filter(Q(service_status__isnull=True) | Q(service_status__is_active_service=True) | Q(
            service_status__is_active_service__isnull=True))
    soldiers = soldiers.order_by(*order_fields)

    paginator = Paginator(soldiers, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    for key in ('page', 'start_from_display', 'start_to_display'):
        if key in query_params:
            query_params.pop(key)
    if 'page_size' not in query_params:
        query_params['page_size'] = page_size
    base_querystring = query_params.urlencode()

    return render(request, 'dashboard/soldiers_list.html', {
        'soldiers': page_obj,
        'page_obj': page_obj,
        'show_completed': show_completed,
        'page_size': page_size,
        'sort': sort_key if sort_key in sort_map else '-start_date',
        'base_querystring': base_querystring,
    })


@login_required
def panel_leaves(request):
    leaves = Leave.objects.select_related('soldier').order_by('-created_at')

    paginator = Paginator(leaves, 250)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard/leaves_list.html', {
        'leaves': page_obj,
        'page_obj': page_obj,
    })


@login_required
def panel_search(request):
    soldiers = Soldier.objects.select_related('service_status', 'current_location', 'health_status').all()

    query = request.GET.get('q', '').strip()
    dispatch_type = request.GET.get('dispatch_type', '')
    service_status_id = request.GET.get('service_status', '')
    location_id = request.GET.get('location', '')
    health_status_id = request.GET.get('health_status', '')
    start_from_raw = request.GET.get('start_from', '')
    start_to_raw = request.GET.get('start_to', '')
    show_completed = request.GET.get('show_completed') == '1'
    page_size_raw = request.GET.get('page_size')

    try:
        page_size = int(page_size_raw)
        page_size = max(5, min(page_size, 10000))
    except (TypeError, ValueError):
        page_size = 250

    start_from_date, start_from_display = parse_date_input(start_from_raw)
    start_to_date, start_to_display = parse_date_input(start_to_raw)

    if not show_completed:
        soldiers = soldiers.filter(Q(service_status__isnull=True) | Q(service_status__is_active_service=True) | Q(
            service_status__is_active_service__isnull=True))

    if query:
        soldiers = soldiers.filter(
            Q(full_name__icontains=query) |
            Q(national_code__icontains=query) |
            Q(dossier_code__icontains=query) |
            Q(phone_personal__icontains=query) |
            Q(phone_parent__icontains=query) |
            Q(phone_home__icontains=query) |
            Q(phone_work__icontains=query) |
            Q(home_address__icontains=query)
        )

    if dispatch_type:
        soldiers = soldiers.filter(dispatch_type=dispatch_type)

    if service_status_id:
        soldiers = soldiers.filter(service_status_id=service_status_id)

    if location_id:
        soldiers = soldiers.filter(current_location_id=location_id)

    if health_status_id:
        soldiers = soldiers.filter(health_status_id=health_status_id)

    if start_from_date:
        soldiers = soldiers.filter(service_start_date__gte=start_from_date)
    if start_to_date:
        soldiers = soldiers.filter(service_start_date__lte=start_to_date)

    paginator = Paginator(soldiers, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    if 'page_size' not in query_params:
        query_params['page_size'] = page_size
    base_querystring = query_params.urlencode()

    from core.models import DispatchType

    context = {
        'soldiers': page_obj,
        'page_obj': page_obj,
        'query': query,
        'dispatch_types': DispatchType.choices,
        'service_statuses': ServiceStatus.objects.all(),
        'locations': ServiceLocation.objects.all(),
        'health_statuses': HealthStatus.objects.all(),
        'selected_dispatch_type': dispatch_type,
        'selected_service_status': service_status_id,
        'selected_location': location_id,
        'selected_health_status': health_status_id,
        'start_from_display': start_from_display or start_from_raw,
        'start_to_display': start_to_display or start_to_raw,
        'start_from_value': (start_from_date.isoformat() if start_from_date else start_from_raw),
        'start_to_value': (start_to_date.isoformat() if start_to_date else start_to_raw),
        'show_completed': show_completed,
        'base_querystring': base_querystring,
        'page_size': page_size,
    }

    return render(request, 'dashboard/soldier_search.html', context)


@login_required
def panel_soldier_delete(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)

    if request.method == 'POST':
        soldier_name = soldier.full_name
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
        soldier_name = leave.soldier.full_name
        leave_id = leave.id
        leave.delete()
        logger.info(f'Leave {leave_id} for soldier {soldier_name} deleted by user {request.user.username}')
        messages.success(request, f'مرخصی سرباز "{soldier_name}" با موفقیت حذف شد.')
        return redirect('panel_leaves')

    return render(request, 'dashboard/leave_confirm_delete.html', {'leave': leave})
