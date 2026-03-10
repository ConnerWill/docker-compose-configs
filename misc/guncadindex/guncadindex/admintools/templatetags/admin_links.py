from urllib.parse import urlparse

from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def admin_edit_url(obj):
    if not obj:
        return ""
    try:
        return reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk]
        )
    except Exception:
        return ""


@register.filter
def absolutify(url, request):
    if not url:
        return ""
    if urlparse(url).scheme:
        return url
    return request.build_absolute_uri(url)
