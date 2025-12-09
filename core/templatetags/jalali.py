from django import template
from jdatetime import datetime as jdatetime

register = template.Library()


@register.filter
def to_jalali(date, format='%Y/%m/%d'):
    if not date:
        return '-'
    try:
        jd = jdatetime.fromgregorian(datetime=date)
        return jd.strftime(format)
    except:
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