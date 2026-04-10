from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404

from core.models import Soldier, Leave
from core.utils.data_to_excel import build_soldier_profile_excel, build_soldier_leaves_excel
from django.contrib import messages
from django.utils import timezone
import logging

logger = logging.getLogger('core')


@login_required
def soldier_profile_excel(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    balances = soldier.leave_balances()
    now = timezone.localtime(timezone.now())

    xlsx_bytes = build_soldier_profile_excel(request, soldier, balances, now)

    resp = HttpResponse(
        xlsx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="soldier_{soldier_id}_profile.xlsx"'
    return resp


@login_required
def soldier_leaves_excel(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    leaves = soldier.leaves.all().order_by("-start_date")
    balances = soldier.leave_balances()
    now = timezone.localtime(timezone.now())

    xlsx_bytes = build_soldier_leaves_excel(request, soldier, leaves, balances, now)

    resp = HttpResponse(
        xlsx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="soldier_{soldier_id}_leaves.xlsx"'
    return resp


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

        headers = ['نام', 'نام خانوادگی', 'کد ملی', 'کد پرونده', 'نوع اعزام',
                   'تاریخ شروع خدمت', 'پایان خدمت', 'وضعیت خدمت', 'محل خدمت']
        ws.append(headers)

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        for soldier in soldiers:
            end_date = soldier.service_end_date()
            ws.append([
                soldier.full_name,
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

        headers = ['نام سرباز', 'کد ملی', 'نوع مرخصی', 'تاریخ رفت',
                   'تاریخ برگشت', 'مدت (روز)']
        ws.append(headers)

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        for leave in leaves:
            ws.append([
                leave.soldier.full_name,
                leave.soldier.national_code,
                leave.get_leave_type_display(),
                leave.start_date.strftime('%Y/%m/%d'),
                leave.days
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
