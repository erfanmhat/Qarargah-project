from django import template
from jdatetime import datetime as jdatetime
from datetime import datetime, date

register = template.Library()


@register.filter
def to_jalali(value, fmt='%Y/%m/%d'):
    if not value:
        return '-'

    try:
        # If it's already a date/datetime
        if isinstance(value, (date, datetime)):
            jd = jdatetime.fromgregorian(date=value)

        # If it's a string like "2025-08-14"
        elif isinstance(value, str):
            g_date = datetime.strptime(value, "%Y-%m-%d").date()
            jd = jdatetime.fromgregorian(date=g_date)

        else:
            return '-'

        return jd.strftime(fmt)

    except Exception:
        return '-'


@register.filter
def to_jalali_full(date):
    if not date:
        return '-'
    try:
        jd = jdatetime.fromgregorian(datetime=date)
        return jd.strftime('%A %d %B %Y')
    except:
        return '-'


@register.simple_tag
def jalali_now(format='%Y/%m/%d'):
    """Get current date in Jalali format"""
    try:
        from django.utils import timezone
        now = timezone.now()
        jd = jdatetime.fromgregorian(datetime=now)
        return jd.strftime(format)
    except:
        return ''
