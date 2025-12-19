from fpdf import FPDF
from pathlib import Path
from django.conf import settings

from core.utils.pdf_helpers import fmt_jdt, rtl_table_draw_row, fmt_jdate, rtl_text

FONT_REGULAR = Path(settings.BASE_DIR) / "core/static/fonts/Vazirmatn-Regular.ttf"
FONT_BOLD = Path(settings.BASE_DIR) / "core/static/fonts/Vazirmatn-Bold.ttf"
LINE_HEIGHT = 8


def build_soldier_profile_pdf(soldier, balances, now):
    pdf = FPDF("P", "mm", "A5")
    pdf.set_auto_page_break(True, 12)
    pdf.add_page()

    pdf.add_font("Vazir", "", str(FONT_REGULAR), uni=True)
    pdf.add_font("Vazir", "B", str(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR), uni=True)
    pdf.set_text_color(0, 0, 0)

    pdf.set_font("Vazir", "B", 16)
    pdf.cell(0, 10, rtl_text("پروفایل سرباز"), 0, 1, "C")

    pdf.set_font("Vazir", "", 10)
    pdf.cell(0, 6, fmt_jdt(now) + rtl_text("تاریخ صدور: "), 0, 1, "C")
    pdf.ln(2)

    pdf.set_font("Vazir", "B", 11)
    pdf.cell(0, 7, rtl_text("اطلاعات سرباز"), 0, 1, "R")

    table_w = pdf.w - pdf.l_margin - pdf.r_margin

    w_value = table_w * 0.5
    w_label = table_w - w_value
    widths = [w_value, w_label]

    y = pdf.get_y()
    pdf.set_font("Vazir", "B", 10)
    rtl_table_draw_row(pdf, y, widths, ["مقدار", "عنوان"], h=LINE_HEIGHT, border=1, align="C", row_index=-1)
    pdf.set_y(y + LINE_HEIGHT)

    pdf.set_font("Vazir", "", 10)

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

    for index, (label, value) in enumerate(fields):
        y = pdf.get_y()
        rtl_table_draw_row(pdf, y, widths, [value, f"{label}"], h=LINE_HEIGHT, border=1, align="R", row_index=index)
        pdf.set_y(y + LINE_HEIGHT)

    pdf.ln(3)

    pdf.set_font("Vazir", "B", 11)
    pdf.cell(0, 7, rtl_text("مانده مرخصی‌ها"), 0, 1, "R")

    type_title = {"entitlement": "استحقاقی", "medical": "استعلاجی", "reward": "تشویقی"}
    rows = []
    if isinstance(balances, dict):
        for k in ("entitlement", "medical", "reward"):
            item = balances.get(k) or {}
            rows.append([
                type_title.get(k, k),
                item.get("allowed", 0),
                item.get("used", 0),
                item.get("remaining", 0),
            ])

    widths2 = [table_w * 0.25, table_w * 0.25, table_w * 0.25, table_w * 0.25]

    y = pdf.get_y()
    pdf.set_font("Vazir", "B", 10)
    rtl_table_draw_row(pdf, y, widths2, ["مانده", "مصرف شده", "مجاز", "نوع"], h=LINE_HEIGHT, border=1, align="C",
                       row_index=-1)
    pdf.set_y(y + LINE_HEIGHT)

    pdf.set_font("Vazir", "", 10)

    if rows:
        for index, row in enumerate(rows):
            y = pdf.get_y()
            (t, allowed, used, remaining) = row
            rtl_table_draw_row(pdf, y, widths2, [remaining, used, allowed, t], h=LINE_HEIGHT, border=1, align="C",
                               row_index=index)
            pdf.set_y(y + LINE_HEIGHT)
    else:
        y = pdf.get_y()
        rtl_table_draw_row(pdf, y, widths2, ["-", "-", "-", "اطلاعاتی موجود نیست"], h=LINE_HEIGHT, border=1, align="C",
                           row_index=0)
        pdf.set_y(y + LINE_HEIGHT)

    return bytes(pdf.output(dest="S"))


def build_soldier_leaves_pdf(soldier, leaves, balances, now):
    pdf = FPDF("P", "mm", "A4")
    pdf.set_auto_page_break(True, 12)
    pdf.add_page()

    pdf.add_font("Vazir", "", str(FONT_REGULAR), uni=True)
    pdf.add_font("Vazir", "B", str(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR), uni=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Vazir", "B", 16)
    pdf.cell(0, 10, rtl_text("گزارش مرخصی‌های سرباز"), 0, 1, "C")

    pdf.set_font("Vazir", "", 10)
    pdf.cell(0, 6, fmt_jdt(now) + rtl_text("تاریخ: "), 0, 1, "R")
    pdf.cell(0, 6, rtl_text(getattr(soldier, 'full_name', '-') or '-') + rtl_text("سرباز: "), 0, 1, "R")
    pdf.ln(2)

    table_w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_font("Vazir", "B", 11)
    pdf.cell(0, 7, rtl_text("خلاصه مانده مرخصی‌ها"), 0, 1, "R")

    widths_bal = [table_w * 0.25, table_w * 0.25, table_w * 0.25, table_w * 0.25]
    y = pdf.get_y()
    pdf.set_font("Vazir", "B", 10)
    rtl_table_draw_row(pdf, y, widths_bal, ["مانده", "مصرف", "مجاز", "نوع"], h=LINE_HEIGHT, border=1, align="C",
                       row_index=-1)
    pdf.set_y(y + LINE_HEIGHT)

    pdf.set_font("Vazir", "", 10)

    type_title = {"entitlement": "استحقاقی", "medical": "استعلاجی", "reward": "تشویقی"}
    if isinstance(balances, dict):
        for index, k in enumerate(["entitlement", "medical", "reward"]):
            item = balances.get(k) or {}
            y = pdf.get_y()
            rtl_table_draw_row(
                pdf, y, widths_bal,
                [item.get("remaining", 0), item.get("used", 0), item.get("allowed", 0), type_title.get(k, k)],
                h=LINE_HEIGHT, border=1, align="C",
                row_index=index
            )
            pdf.set_y(y + LINE_HEIGHT)
    else:
        y = pdf.get_y()
        rtl_table_draw_row(pdf, y, widths_bal, ["-", "-", "-", "اطلاعاتی موجود نیست"], h=LINE_HEIGHT, border=1,
                           align="C")
        pdf.set_y(y + LINE_HEIGHT)

    pdf.ln(3)

    def draw_leaves_header():
        pdf.set_font("Vazir", "B", 10)

        widths = [table_w * 0.20, table_w * 0.16, table_w * 0.16, table_w * 0.16, table_w * 0.16, table_w * 0.16]
        y = pdf.get_y()
        rtl_table_draw_row(pdf, y, widths, ["توضیحات", "روز", "تا تاریخ", "از تاریخ", "نوع", "ردیف"], h=LINE_HEIGHT,
                           border=1,
                           align="C", row_index=-1)
        pdf.set_y(y + LINE_HEIGHT)

        pdf.set_font("Vazir", "", 10)
        return widths

    pdf.set_font("Vazir", "B", 11)
    pdf.cell(0, 7, rtl_text("مرخصی‌ها"), 0, 1, "R")
    widths = draw_leaves_header()

    for index, lv in enumerate(leaves):
        if pdf.get_y() > (pdf.h - pdf.b_margin - 18):
            pdf.add_page()
            widths = draw_leaves_header()

        leave_type_label = getattr(lv, "get_leave_type_display", lambda: getattr(lv, "leave_type", "-"))()
        start = fmt_jdate(getattr(lv, "start_date", None))
        end = fmt_jdate(getattr(lv, "end_date", None))
        days = getattr(lv, "days", "-") or "-"
        notes = (getattr(lv, "notes", "") or "-").strip() or "-"

        y = pdf.get_y()
        rtl_table_draw_row(
            pdf, y,
            widths=widths,
            texts=[notes, days, end, start, leave_type_label, index + 1],
            border=1,
            row_index=index
        )
        pdf.set_y(y + LINE_HEIGHT)

    return bytes(pdf.output(dest="S"))
