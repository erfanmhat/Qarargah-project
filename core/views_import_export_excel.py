import uuid

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from rest_framework.exceptions import ValidationError

from core.forms import ExcelImportForm, ExcelImportConfirmForm
from core.models import Soldier, Leave
from core.utils.data_to_excel import build_soldier_profile_excel, build_soldier_leaves_excel
from core.utils.excel_parser import parse_workbook
from core.utils.utils import jalali_yyyySmmSdd_to_date, deep_jsonable, iso_to_date
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
import logging

logger = logging.getLogger('core')


@login_required
@require_http_methods(["GET", "POST"])
def import_excel(request):
    if request.method == "GET":
        return render(request, "dashboard/import_excel.html", {"form": ExcelImportForm()})

    form = ExcelImportForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "dashboard/import_excel.html", {"form": form})

    f = form.cleaned_data["file"]
    parsed = parse_workbook(f)

    errors = []
    normalized_items = []

    def add_error(sheet, section, field, message, value=None):
        errors.append({
            "sheet": sheet,
            "section": section,
            "field": field,
            "message": message,
            "value": value,
        })

    for item in parsed:
        sheet = item.get("sheet_name")
        sdata = item.get("soldier") or {}

        full_name = sdata.get("full_name")
        dossier_code = sdata.get("dossier_code")
        dispatch_jalali = sdata.get("dispatch_jalali")

        if not full_name:
            add_error(sheet, "Soldier", "full_name", "نام کامل از سلول B6 خوانده نشد.", sdata.get("full_name"))
        if not dossier_code:
            add_error(sheet, "Soldier", "dossier_code", "کد پرونده از سلول B6 (بعد از خط تیره) خوانده نشد.",
                      sdata.get("dossier_code"))
        if not dispatch_jalali:
            add_error(sheet, "Soldier", "dispatch_date", "تاریخ اعزام از سلول‌های G3/H3/I3 خوانده نشد.",
                      sdata.get("dispatch_jalali"))

        soldier_payload = {
            "full_name": full_name,
            "dossier_code": dossier_code,
        }

        if dispatch_jalali:
            try:
                soldier_payload["service_start_date"] = jalali_yyyySmmSdd_to_date(dispatch_jalali)
            except Exception as e:
                add_error(sheet, "Soldier", "service_start_date",
                          f"تبدیل تاریخ اعزام (جلالی→میلادی) ناموفق: {e}", dispatch_jalali)

        try:
            tmp_soldier = Soldier(**soldier_payload)
            tmp_soldier.clean_fields()
        except ValidationError as ve:
            for field, msgs in ve.message_dict.items():
                for m in msgs:
                    add_error(sheet, "Soldier", field, m, soldier_payload.get(field))

        validated_leaves = []
        raw_leaves = item.get("leaves") or []

        for l in raw_leaves:
            leave_type = {
                "استعلاجی": "medical",
                "تشویقی": "reward",
                "استحقاقی": "entitlement"
            }[l.get("leave_type_fa")]
            start_jalali = l.get("start_jalali")
            end_jalali = l.get("end_jalali")
            duration_days = l.get("duration_days")
            row = l.get("row")

            if not leave_type:
                add_error(sheet, "Leave", "leave_type",
                          "نوع مرخصی معتبر نیست.", l.get("leave_type_fa"))
                continue

            if not start_jalali:
                add_error(sheet, "Leave", "start_date",
                          "از تاریخ مرخصی خوانده نشد/نامعتبر است.", {"row": row, **l})
                continue

            if not duration_days:
                add_error(sheet, "Leave", "duration_days",
                          "مدت مرخصی (ستون D) خوانده نشد/نامعتبر است.", {"row": row, **l})
                continue

            if not end_jalali:
                add_error(sheet, "Leave", "end_date",
                          "تا تاریخ خالی است و محاسبه هم انجام نشد.", {"row": row, **l})
                continue

            try:
                start_date = jalali_yyyySmmSdd_to_date(start_jalali)
                end_date = jalali_yyyySmmSdd_to_date(end_jalali)
            except Exception as e:
                add_error(sheet, "Leave", "date",
                          f"تبدیل تاریخ مرخصی (جلالی→میلادی) ناموفق: {e}", {"row": row, **l})
                continue

            try:
                dummy_soldier = Soldier(**soldier_payload)
                leave_obj = Leave(
                    soldier=dummy_soldier,
                    leave_type=leave_type,
                    start_date=start_date,
                    end_date=end_date,
                    notes="",
                )
                leave_obj.clean_fields()
            except ValidationError as ve:
                for field, msgs in ve.message_dict.items():
                    for m in msgs:
                        add_error(sheet, "Leave", field, m, {"row": row, **l})
                continue
            validated_leaves.append({
                "leave_type": leave_type,
                "start_date": start_date,
                "end_date": end_date,
                "duration_days": duration_days,
                "row": row,
                "leave_type_fa": leave_type,
                "notes": l.get("notes", ""),
            })

        seen = set()
        for lv in validated_leaves:
            key = (lv["leave_type"], lv["start_date"], lv["end_date"])
            if key in seen:
                add_error(sheet, "Leave", "duplicate",
                          "مرخصی تکراری (نوع و بازه تاریخ کاملاً یکسان) در فایل وجود دارد.",
                          {"row": lv.get("row"), "leave_type": lv["leave_type"], "start": lv["start_date"],
                           "end": lv["end_date"]})
            else:
                seen.add(key)

        normalized_items.append({
            "sheet_name": sheet,
            "soldier": deep_jsonable(soldier_payload),
            "leaves": deep_jsonable(validated_leaves),
            "reductions": deep_jsonable(item.get("reductions", [])),
            "raw_soldier": sdata,
        })

    token = str(uuid.uuid4())
    request.session[f"import_preview_{token}"] = deep_jsonable({
        "items": normalized_items,
        "errors": errors,
    })
    request.session.modified = True

    return render(request, "dashboard/import_preview.html", {
        "token": token,
        "items": normalized_items,
        "errors": errors,
        "can_confirm": (len(errors) == 0),
        "confirm_form": ExcelImportConfirmForm(initial={"token": token}),
    })


@login_required
@require_http_methods(["POST"])
def import_excel_confirm(request):
    form = ExcelImportConfirmForm(request.POST)
    if not form.is_valid():
        messages.error(request, "درخواست نامعتبر است.")
        return redirect("import_excel")

    token = form.cleaned_data["token"]
    payload = request.session.get(f"import_preview_{token}")
    if not payload:
        messages.error(request, "اطلاعات پیش‌نمایش منقضی شده یا یافت نشد.")
        return redirect("import_excel")

    items = payload["items"]
    errors = payload["errors"]
    if errors:
        messages.error(request, "هنوز خطا دارید؛ ابتدا اصلاح کنید.")
        return redirect("import_excel")

    with transaction.atomic():
        for item in items:
            sdata = item["soldier"]

            if sdata.get("service_start_date"):
                sdata["service_start_date"] = iso_to_date(sdata["service_start_date"])

            for l in item["leaves"]:
                if l.get("start_date"):
                    l["start_date"] = iso_to_date(l["start_date"])
                if l.get("end_date"):
                    l["end_date"] = iso_to_date(l["end_date"])

            soldier, created = Soldier.objects.update_or_create(
                dossier_code=sdata["dossier_code"],
                defaults=sdata
            )

            for l in item["leaves"]:
                Leave.objects.get_or_create(
                    soldier=soldier,
                    leave_type=l["leave_type"],
                    start_date=l["start_date"],
                    end_date=l["end_date"],
                    defaults={"notes": ""}
                )

    try:
        del request.session[f"import_preview_{token}"]
    except KeyError:
        pass

    messages.success(request, "دیتا با موفقیت ذخیره شد.")
    return redirect("import_excel")


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
                leave.end_date.strftime('%Y/%m/%d'),
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
