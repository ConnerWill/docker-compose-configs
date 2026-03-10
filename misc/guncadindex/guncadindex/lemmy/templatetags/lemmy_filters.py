import re
from urllib.parse import quote

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def lemmyverse_link(url):
    if not url:
        return ""
    if url.startswith("http://"):
        url = url[len("http://") :]
    elif url.startswith("https://"):
        url = url[len("https://") :]
    return f"{settings.GUNCAD_LEMMY_LEMMYVERSE_URL}/{quote(url, safe="/")}"


@register.filter
def no_links(text):
    """
    This'll mark the output as safe, but that *entirely* depends on if the
    input text was safe too. Be careful! Footguns abound!

    Required because django-markdownify is retarded with its whitelist
    """
    return mark_safe(re.sub(r"</?a[^>]*>", "", text))
