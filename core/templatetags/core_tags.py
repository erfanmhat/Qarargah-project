from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    دریافت مقدار از دیکشنری بر اساس کلید
    """
    if type(dictionary) is dict:
        return dictionary.get(key)
    return None
