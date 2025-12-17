from io import BytesIO
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def build_soldier_profile_pdf(soldier, balances, now):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A5)
    w, h = A5

    y = h - 15*mm
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(w - 10*mm, y, "پروفایل سرباز")
    y -= 8*mm

    c.setFont("Helvetica", 10)
    c.drawRightString(w - 10*mm, y, f"تاریخ: {now.strftime('%Y-%m-%d %H:%M')}")
    y -= 10*mm

    lines = [
        f"کد: {soldier.id}",
        f"نام: {getattr(soldier, 'name', '')}",
        f"نام خانوادگی: {getattr(soldier, 'family', '')}",
        f"یگان/واحد: {getattr(soldier, 'unit', '')}",
    ]
    for line in lines:
        c.drawRightString(w - 10*mm, y, line)
        y -= 6*mm

    y -= 6*mm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(w - 10*mm, y, "مانده مرخصی‌ها")
    y -= 8*mm

    c.setFont("Helvetica", 10)
    if isinstance(balances, dict):
        for k, v in balances.items():
            c.drawRightString(w - 10*mm, y, f"{k}: {v}")
            y -= 6*mm
    else:
        c.drawRightString(w - 10*mm, y, str(balances))
        y -= 6*mm

    c.showPage()
    c.save()
    pdf = buf.getvalue()
    buf.close()
    return pdf
