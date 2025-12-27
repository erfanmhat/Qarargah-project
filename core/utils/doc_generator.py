import os
from io import BytesIO
from datetime import date, datetime

from django.conf import settings
from django.utils import timezone

from jdatetime import datetime as jdatetime
from docxtpl import DocxTemplate
from jinja2 import Environment


def to_jalali(value, fmt="%Y/%m/%d"):
    if not value:
        return "-"
    try:
        if isinstance(value, (date, datetime)):
            g_date = value if isinstance(value, date) else value.date()
        elif isinstance(value, str):
            s = value.strip().replace("/", "-")
            if len(s) == 7 and s.count("-") == 1:
                s += "-01"
            g_date = datetime.strptime(s, "%Y-%m-%d").date()
        else:
            return "-"
        jd = jdatetime.fromgregorian(date=g_date)
        return jd.strftime(fmt)
    except Exception as e:
        return str(e)


def jalali_ym(value, fmt="%Y/%m"):
    return to_jalali(value, fmt=fmt)


def build_docx(template_obj, soldier, input_data: dict):
    """
    template_obj: DocumentTemplate
    soldier: Soldier instance
    input_data: dict from user inputs
    Returns: bytes of docx
    """
    now = timezone.now()

    # مسیر پوشه ثابت قالب‌ها
    templates_dir = os.path.join(settings.BASE_DIR, "doc_templates")
    template_path = os.path.join(templates_dir, template_obj.filename)

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template docx not found: {template_path}")

    # docxtpl instance
    doc = DocxTemplate(template_path)

    # Jinja2 env for filters
    jinja_env = Environment(autoescape=False)
    jinja_env.filters["jalali"] = to_jalali
    jinja_env.filters["jalali_ym"] = jalali_ym

    doc.render(
        {
            "soldier": soldier,
            "input": input_data,
            "template": template_obj,
            "now": now,
            "today": now.date(),
        },
        jinja_env=jinja_env
    )

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()
