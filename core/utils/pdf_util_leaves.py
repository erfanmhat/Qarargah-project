from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def build_soldier_leaves_pdf(soldier, leaves, balances, now):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    y = h - 15*mm
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(w - 10*mm, y, "گزارش مرخصی‌های سرباز")
    y -= 8*mm

    c.setFont("Helvetica", 10)
    c.drawRightString(w - 10*mm, y, f"تاریخ: {now.strftime('%Y-%m-%d %H:%M')}")
    y -= 8*mm
    c.drawRightString(w - 10*mm, y, f"سرباز: {getattr(soldier, 'name', '')} {getattr(soldier, 'family', '')}")
    y -= 12*mm

    # عنوان جدول ساده
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(w - 10*mm, y, "ردیف | از | تا | تعداد روز | توضیح")
    y -= 7*mm
    c.setFont("Helvetica", 9)

    idx = 1
    for lv in leaves:
        if y < 20*mm:
            c.showPage()
            y = h - 15*mm
            c.setFont("Helvetica", 9)

        start = getattr(lv, "start_date", "")
        end = getattr(lv, "end_date", "")
        days = getattr(lv, "days", "")
        note = getattr(lv, "note", "") or getattr(lv, "description", "") or ""

        text = f"{idx} | {start} | {end} | {days} | {note}"
        c.drawRightString(w - 10*mm, y, text)
        y -= 6*mm
        idx += 1

    c.showPage()
    c.save()
    pdf = buf.getvalue()
    buf.close()
    return pdf
