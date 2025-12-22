import arabic_reshaper
from bidi.algorithm import get_display
from datetime import date, datetime
from jdatetime import datetime as jdt


def rtl_text(txt: str) -> str:
    """
    Apply Arabic reshaper + bidi to correctly display Persian text in fpdf2.
    """
    if not txt:
        return ""
    reshaped = arabic_reshaper.reshape(txt)
    bidi = get_display(reshaped)
    return bidi


def fmt_jdate(d) -> str:
    if not d:
        return "-"
    if isinstance(d, datetime):
        d = d.date()
    if isinstance(d, date):
        return jdt.fromgregorian(date=d).strftime("%Y/%m/%d")
    try:
        g = datetime.strptime(str(d), "%Y-%m-%d").date()
        return jdt.fromgregorian(date=g).strftime("%Y/%m/%d")
    except Exception:
        return str(d)


def fmt_jdt(dt) -> str:
    if not dt:
        return "-"
    if isinstance(dt, datetime):
        return jdt.fromgregorian(datetime=dt).strftime("%Y/%m/%d  %H:%M")
    return str(dt)


def rtl_table_draw_row(
        pdf,
        y,
        widths: list,
        texts: list,
        row_index: int,
        h=8,
        border=1,
        align="C"
):
    """
    Draws a whole row from RIGHT to LEFT with zebra striping.
    widths and texts must be same length.
    """

    if row_index == -1:
        pdf.set_fill_color(168, 245, 147)
    elif row_index % 2 == 0:
        pdf.set_fill_color(255, 255, 255)
    else:
        pdf.set_fill_color(214, 247, 205)

    x = pdf.w - pdf.r_margin
    texts.reverse()
    for w, t in zip(widths, texts):
        pdf.set_xy(x - w, y)
        pdf.cell(
            w,
            h,
            rtl_text(str(t)),
            border=border,
            align=align,
            fill=True
        )
        x -= w
