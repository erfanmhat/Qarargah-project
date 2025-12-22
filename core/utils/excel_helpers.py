from datetime import date, datetime
from jdatetime import datetime as jdt


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
