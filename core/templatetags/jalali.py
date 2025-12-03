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
