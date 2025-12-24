import datetime as dt
from datetime import timedelta, datetime
from jdatetime import datetime as jdatetime


def to_jsonable(v):
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return v


def deep_jsonable(obj):
    if isinstance(obj, dict):
        return {k: deep_jsonable(to_jsonable(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_jsonable(to_jsonable(x)) for x in obj]
    return to_jsonable(obj)


def iso_to_date(s):
    if not s:
        return None
    return dt.date.fromisoformat(s)


def parse_date_input(value):
    """
    Accepts Jalali (YYYY/MM/DD) or Gregorian (YYYY-MM-DD) strings and returns (gregorian_date, jalali_display).
    """
    value = (value or '').strip()
    if not value:
        return None, ''
    try:
        if '/' in value:
            jd = jdatetime.strptime(value, '%Y/%m/%d')
            greg = jd.togregorian().date()
        else:
            greg = datetime.fromisoformat(value).date()
        jalali_display = jdatetime.fromgregorian(date=greg).strftime('%Y/%m/%d')
        return greg, jalali_display
    except Exception:
        return None, value


def prev_month_start(d):
    """Return the first day of the previous month for a given date d (date object)."""
    first = d.replace(day=1)
    prev_last = first - timedelta(days=1)
    return prev_last.replace(day=1)


def jalali_ym(d):
    """Format a Gregorian date as Jalali YYYY/MM (string)."""
    try:
        jd = jdatetime.date.fromgregorian(date=d)
        return jd.strftime("%Y/%m")
    except Exception:
        return d.strftime("%Y/%m")


def jalali_yyyySmmSdd_to_date(jalali_yyyySmmSdd: str):
    """
    14040401 -> datetime.date میلادی
    نیازمند: pip install jdatetime
    """
    import jdatetime
    s = str(jalali_yyyySmmSdd)
    y = int(s.split("/")[0])
    m = int(s.split("/")[1])
    d = int(s.split("/")[2])
    return jdatetime.date(y, m, d).togregorian()
