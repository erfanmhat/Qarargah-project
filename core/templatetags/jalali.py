from datetime import datetime, date

import jdatetime
from django.utils import timezone
from django import template

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
def to_jalali_ym(value, fmt="%Y/%m"):
    """
    Converts a Gregorian date/datetime OR year-month string to Jalali year-month only.

    Accepts:
      - date / datetime
      - "YYYY-MM-DD"
      - "YYYY-MM"
      - "YYYY/MM"
      - "YYYY/MM/DD"
    """

    if not value:
        return "-"

    try:
        # ✅ If it's already date/datetime
        if isinstance(value, (date, datetime)):
            g_date = value if isinstance(value, date) else value.date()

        # ✅ If it's a string
        elif isinstance(value, str):
            s = value.strip()

            # normalize slash to dash
            s = s.replace("/", "-")

            # "YYYY-MM"  -> add day=1
            if len(s) == 7 and s.count("-") == 1:
                s = s + "-01"

            # now should be "YYYY-MM-DD"
            g_date = datetime.strptime(s, "%Y-%m-%d").date()

        else:
            return "-"

        jd = jdatetime.fromgregorian(date=g_date)

        # ✅ return only year-month
        return jd.strftime(fmt)

    except Exception:
        return "-"


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
    """Get current date in Jalali format with manual Persian mapping"""
    try:
        now = timezone.now()
        jd = jdatetime.datetime.fromgregorian(datetime=now)

        # ۱. مپر نام ماه‌های شمسی
        persian_months = {
            1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد',
            4: 'تیر', 5: 'مرداد', 6: 'شهریور',
            7: 'مهر', 8: 'آبان', 9: 'آذر',
            10: 'دی', 11: 'بهمن', 12: 'اسفند'
        }

        # اگر فرمت شامل %B (نام کامل) یا %b (نام اختصاری) بود، آن را با معادل فارسی جایگزین می‌کنیم
        if '%B' in format or '%b' in format:
            fa_month_name = persian_months[jd.month]
            format = format.replace('%B', fa_month_name).replace('%b', fa_month_name)

        # ساختن تاریخ (که الان ماه‌ها در آن فارسی شده‌اند، اما اعداد ممکن است انگلیسی باشند)
        formatted_date = jd.strftime(format)

        # ۲. مپر تبدیل اعداد انگلیسی به فارسی
        en_to_fa_digits = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

        # اعمال تبدیل اعداد و برگرداندن خروجی نهایی
        final_date = formatted_date.translate(en_to_fa_digits)

        return final_date

    except Exception as e:
        return ''
