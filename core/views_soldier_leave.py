import logging

import jdatetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from core.forms_document import build_document_input_form
from core.models import Soldier, Leave, ServiceLocation, HealthStatus, ServiceStatus, DocumentTemplate, DispatchType, \
    ExtraServiceType, MilitaryRankRef
from core.utils.doc_generator import build_docx

logger = logging.getLogger('core')


@login_required
def panel_soldiers(request):
    """لیست تمامی سربازها با امکان مرتب‌سازی (بدون صفحه‌بندی)."""

    sort_key = request.GET.get('sort', 'dossier')

    # باگ برطرف شده: در کد قبلی، هم 'created' و هم '-created' مقدار '-created_at' را برمی‌گرداندند!
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
        'created': 'created_at',  # این خط اصلاح شد
        '-created': '-created_at',
    }

    # دریافت فیلدهای مرتب‌سازی و تبدیل آن به تاپل
    order_fields = sort_map.get(sort_key, ('dossier_code',))
    if isinstance(order_fields, str):
        order_fields = (order_fields,)

    # واکشی تمام سربازها به همراه روابط (برای جلوگیری از N+1 query) و اعمال مرتب‌سازی
    soldiers = Soldier.objects.select_related(
        'service_status', 'current_location'
    ).order_by(*order_fields)

    # حفظ پارامترهای URL برای لینک‌های هدر جدول (مرتب‌سازی)
    query_params = request.GET.copy()
    # کلیدهای غیرضروری که نباید در لینک مرتب‌سازی تکرار شوند حذف می‌شوند
    # کلید page و page_size چون دیگر صفحه‌بندی نداریم حذف شدند
    for key in ('start_from_display', 'start_to_display'):
        if key in query_params:
            query_params.pop(key)

    base_querystring = query_params.urlencode()

    return render(request, 'dashboard/soldiers_list.html', {
        'soldiers': soldiers,  # کل لیست پاس داده می‌شود
        'sort': sort_key if sort_key in sort_map else 'dossier',
        'base_querystring': base_querystring,
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# فراموش نکنید مدل Leave فراخوانی شده باشد

@login_required
def panel_leaves(request):
    # دریافت کوئری پایه با select_related برای سرعت بیشتر
    leaves = Leave.objects.select_related('soldier').order_by('-created_at')

    # --- امکان فیلتر با سرباز خاص از طریق پارامتر URL ---
    # مثال: /panel/leaves/?soldier=15
    soldier_id = request.GET.get('soldier')
    selected_soldier = None

    if soldier_id and soldier_id.isdigit():
        leaves = leaves.filter(soldier__id=soldier_id)
        # برای نمایش نام سرباز فیلتر شده در بالای صفحه
        if leaves.exists():
            selected_soldier = leaves.first().soldier

    # گرفتن آمار تعداد کل مرخصی‌های لیست فعلی
    total_leaves = leaves.count()

    return render(request, 'dashboard/leaves_list.html', {
        'leaves': leaves,
        'total_leaves': total_leaves,
        'selected_soldier': selected_soldier,
    })


@login_required
def panel_search(request):
    # دریافت لیست کامل با Select Related برای سرعت بالا (بدون صفحه‌بندی)
    soldiers = Soldier.objects.select_related(
        'service_status', 'current_location', 'health_status',
        'military_rank_ref', 'extra_service_type'
    ).all()

    # --- ۱. دریافت پارامترها ---
    query = request.GET.get('q', '').strip()
    dispatch_type = request.GET.get('dispatch_type', '')
    service_status_id = request.GET.get('service_status', '')
    location_id = request.GET.get('location', '')
    health_status_id = request.GET.get('health_status', '')

    # پارامترهای جدید که در ویوی قبلی جا افتاده بودند!
    rank_ref_id = request.GET.get('rank_ref', '')
    extra_type_id = request.GET.get('extra_type', '')
    extra_from = request.GET.get('extra_from', '')
    extra_to = request.GET.get('extra_to', '')

    start_from_raw = request.GET.get('start_from', '')
    start_to_raw = request.GET.get('start_to', '')
    show_completed = request.GET.get('show_completed') == '1'

    # --- ۲. اعمال فیلترها ---

    # فیلتر پایان خدمت
    if not show_completed:
        soldiers = soldiers.filter(
            Q(service_status__isnull=True) |
            Q(service_status__is_active_service=True)
        )

    # جستجوی متنی همه‌جانبه
    if query:
        soldiers = soldiers.filter(
            Q(full_name__icontains=query) |
            Q(national_code__icontains=query) |
            Q(dossier_code__icontains=query) |
            Q(father_name__icontains=query) |
            Q(direct_commander_name__icontains=query)
        )

    # فیلترهای Select
    if dispatch_type:
        soldiers = soldiers.filter(dispatch_type=dispatch_type)
    if service_status_id:
        soldiers = soldiers.filter(service_status_id=service_status_id)
    if location_id:
        soldiers = soldiers.filter(current_location_id=location_id)
    if health_status_id:
        soldiers = soldiers.filter(health_status_id=health_status_id)
    if rank_ref_id:
        soldiers = soldiers.filter(military_rank_ref_id=rank_ref_id)
    if extra_type_id:
        soldiers = soldiers.filter(extra_service_type_id=extra_type_id)

    # فیلتر بازه عددی اضافه خدمت
    if extra_from and extra_from.isdigit():
        soldiers = soldiers.filter(extra_service_days__gte=int(extra_from))
    if extra_to and extra_to.isdigit():
        soldiers = soldiers.filter(extra_service_days__lte=int(extra_to))

    # فیلتر بازه تاریخ (تبدیل امن جلالی به میلادی)
    def parse_jalali_to_gregorian(j_str):
        try:
            j_str = j_str.replace('-', '/').replace(' ', '')
            y, m, d = map(int, j_str.split('/'))
            return jdatetime.date(y, m, d).togregorian()
        except:
            return None

    if start_from_raw:
        g_start = parse_jalali_to_gregorian(start_from_raw)
        if g_start: soldiers = soldiers.filter(service_start_date__gte=g_start)

    if start_to_raw:
        g_end = parse_jalali_to_gregorian(start_to_raw)
        if g_end: soldiers = soldiers.filter(service_start_date__lte=g_end)

    # --- ۳. ارسال به تمپلیت ---
    context = {
        'soldiers': soldiers,
        'results_count': soldiers.count(),  # شمارشگر نتایج

        # برای حفظ مقادیر سرچ شده در فرم
        'query': query,
        'selected_dispatch_type': dispatch_type,
        'selected_service_status': service_status_id,
        'selected_location': location_id,
        'selected_health_status': health_status_id,
        'selected_rank_ref': rank_ref_id,
        'selected_extra_type': extra_type_id,
        'extra_from': extra_from,
        'extra_to': extra_to,
        'start_from': start_from_raw,
        'start_to': start_to_raw,
        'show_completed': show_completed,

        # دیتای دراپ‌داون‌ها (مطمئن شوید مدل‌های MilitaryRank و ExtraServiceType ایمپورت شده‌اند)
        'dispatch_types': DispatchType.choices,
        'service_statuses': ServiceStatus.objects.all(),
        'locations': ServiceLocation.objects.all(),
        'health_statuses': HealthStatus.objects.all(),
        'rank_refs': MilitaryRankRef.objects.all(),
        'extra_types': ExtraServiceType.objects.all(),
    }

    return render(request, 'dashboard/soldier_search.html', context)


@login_required
def panel_soldier_delete(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)

    if request.method == 'POST':
        soldier_name = soldier.full_name
        soldier_pk = soldier.id
        soldier.delete()
        logger.info(f'Soldier {soldier_pk} ({soldier_name}) deleted by user {request.user.username}')
        messages.success(request, f'سرباز "{soldier_name}" با موفقیت حذف شد.')
        return redirect('panel_soldiers')

    return render(request, 'dashboard/soldier_confirm_delete.html', {'soldier': soldier})


@login_required
def panel_leave_delete(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)

    if request.method == 'POST':
        soldier_name = leave.soldier.full_name
        leave_pk = leave.id
        leave.delete()
        logger.info(f'Leave {leave_pk} for soldier {soldier_name} deleted by user {request.user.username}')
        messages.success(request, f'مرخصی سرباز "{soldier_name}" با موفقیت حذف شد.')
        return redirect('panel_leaves')

    return render(request, 'dashboard/leave_confirm_delete.html', {'leave': leave})


@login_required
def panel_soldier_detail(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    leaves = soldier.leaves.all().order_by('-start_date')
    reductions = soldier.reductions.all()
    balances = soldier.leave_balances()
    document_templates = DocumentTemplate.objects.filter(is_active=True).order_by("order", "id")

    context = {
        'soldier': soldier,
        'leaves': leaves,
        'reductions': reductions,
        'leave_balances': balances,
        'document_templates': document_templates,
    }

    return render(request, 'dashboard/soldier_detail.html', context)


@login_required
def soldier_documents_list(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    templates = DocumentTemplate.objects.filter(is_active=True).order_by("order", "id")
    return render(request, "dashboard/soldier_documents_list.html", {
        "soldier": soldier,
        "templates": templates
    })


@login_required
def generate_document(request, soldier_id, template_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    template_obj = get_object_or_404(DocumentTemplate, id=template_id, is_active=True)

    # اگر این فرم ورودی دستی ندارد:
    if template_obj.inputs.count() == 0:
        input_data = {}
        content = build_docx(template_obj, soldier, input_data)

        filename = f"{template_obj.title}_{soldier.national_code}.docx"
        response = HttpResponse(content,
                                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # اگر ورودی دستی دارد:
    if request.method == "POST":
        form = build_document_input_form(template_obj, request.POST)
        if form.is_valid():
            input_data = form.cleaned_data
            content = build_docx(template_obj, soldier, input_data)

            filename = f"{template_obj.title}_{soldier.national_code}.docx"
            response = HttpResponse(content,
                                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
    else:
        form = build_document_input_form(template_obj)

    return render(request, "dashboard/document_fill_form.html", {
        "soldier": soldier,
        "template_obj": template_obj,
        "form": form
    })


@login_required
def document_templates_help(request):
    return render(request, "dashboard/document_templates_help.html")
