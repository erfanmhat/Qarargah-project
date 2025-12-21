# core/utils/pdf_xhtml2pdf.py
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

from xhtml2pdf import pisa

from core.utils.pdf_helpers import fmt_jdt, fmt_jdate

FONT_REGULAR = Path(settings.BASE_DIR) / "core/static/fonts/Vazirmatn-Regular.ttf"
FONT_BOLD = Path(settings.BASE_DIR) / "core/static/fonts/Vazirmatn-Bold.ttf"


def _link_callback(uri: str, rel: str) -> str:
    """
    xhtml2pdf needs absolute filesystem paths for static/media files.
    """
    # Static files (recommended for fonts)
    if uri.startswith(settings.STATIC_URL):
        path = Path(settings.BASE_DIR) / "core" / uri.replace(settings.STATIC_URL, "static/")
        if path.exists():
            return str(path)

    # Media files (if you ever use them in PDF)
    if hasattr(settings, "MEDIA_URL") and uri.startswith(settings.MEDIA_URL):
        path = Path(settings.MEDIA_ROOT) / uri.replace(settings.MEDIA_URL, "")
        if path.exists():
            return str(path)

    # Fallback: maybe already a filesystem path
    return uri


def _render_pdf_from_template(template_name: str, context: dict) -> bytes:
    html = render_to_string(template_name, context)
    result = BytesIO()

    pdf_status = pisa.CreatePDF(
        src=html,
        dest=result,
        link_callback=_link_callback,
        encoding="utf-8",
    )
    if pdf_status.err:
        # برای دیباگ بهتر: می‌تونی html را هم لاگ کنی
        raise RuntimeError("PDF generation failed with xhtml2pdf.")
    return result.getvalue()


def build_soldier_profile_pdf(request, soldier, balances, now) -> bytes:
    # balances ساختار dict دارد (مثل قبل) :contentReference[oaicite:2]{index=2}
    type_title = {"entitlement": "استحقاقی", "medical": "استعلاجی", "reward": "تشویقی"}
    bal_rows = []
    if isinstance(balances, dict):
        for k in ("entitlement", "medical", "reward"):
            item = balances.get(k) or {}
            bal_rows.append({
                "type": type_title.get(k, k),
                "allowed": item.get("allowed", 0),
                "used": item.get("used", 0),
                "remaining": item.get("remaining", 0),
            })

    fields = [
        ("کد سیستم", getattr(soldier, "id", "-")),
        ("نام و نام خانوادگی", getattr(soldier, "full_name", "-") or "-"),
        ("کد ملی", getattr(soldier, "national_code", "-") or "-"),
        ("کد پرونده", getattr(soldier, "dossier_code", "-") or "-"),
        ("نوع اعزامی", getattr(soldier, "get_dispatch_type_display", lambda: "-")() or "-"),
        ("تاریخ شروع خدمت", fmt_jdate(getattr(soldier, "service_start_date", None))),
        ("تاریخ پایان خدمت", fmt_jdate(getattr(soldier, "service_end_date", lambda: None)())),

        ("شماره همراه", getattr(soldier, "phone_personal", "-") or "-"),
        ("کد پاسداری", getattr(soldier, "guard_code", "-") or "-"),
    ]

    ctx = {
        "title": "پروفایل سرباز",
        "issue_date": fmt_jdt(now),
        "fields": fields,
        "balances": bal_rows,
        "font_regular": str(FONT_REGULAR).replace("\\", "/"),
        "font_bold": str(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR).replace("\\", "/"),
        "page_size": "A5",
    }
    return _render_pdf_from_template("pdf/soldier_profile.html", ctx)


def build_soldier_leaves_pdf(request, soldier, leaves, balances, now) -> bytes:
    type_title = {"entitlement": "استحقاقی", "medical": "استعلاجی", "reward": "تشویقی"}
    bal_rows = []
    if isinstance(balances, dict):
        for k in ("entitlement", "medical", "reward"):
            item = balances.get(k) or {}
            bal_rows.append({
                "type": type_title.get(k, k),
                "allowed": item.get("allowed", 0),
                "used": item.get("used", 0),
                "remaining": item.get("remaining", 0),
            })

    leave_rows = []
    for idx, lv in enumerate(leaves, start=1):
        leave_type_label = getattr(lv, "get_leave_type_display", lambda: getattr(lv, "leave_type", "-"))()
        leave_rows.append({
            "idx": idx,
            "type": leave_type_label,
            "start": fmt_jdate(getattr(lv, "start_date", None)),
            "end": fmt_jdate(getattr(lv, "end_date", None)),
            "days": getattr(lv, "days", "-") or "-",
            "notes": (getattr(lv, "notes", "") or "-").strip() or "-",
        })

    ctx = {
        "title": "گزارش مرخصی‌های سرباز",
        "date": fmt_jdt(now),
        "soldier_name": getattr(soldier, "full_name", "-") or "-",
        "balances": bal_rows,
        "leaves": leave_rows,
        "font_regular": str(FONT_REGULAR).replace("\\", "/"),
        "font_bold": str(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR).replace("\\", "/"),
        "page_size": "A4",
    }
    return _render_pdf_from_template("pdf/soldier_leaves.html", ctx)
