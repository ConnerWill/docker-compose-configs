from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


# settings value
@register.simple_tag
def settings_value(name, safe=False):
    value = getattr(settings, name, "")
    return mark_safe(value) if safe else value
