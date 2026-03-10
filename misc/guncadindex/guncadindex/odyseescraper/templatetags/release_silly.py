from django import template
from django.conf import settings
from django.core.cache import cache
from django.utils.safestring import mark_safe
from odyseescraper.models import OdyseeRelease

register = template.Library()


# settings value
@register.simple_tag
def is_over_9000(safe=False):
    c = cache.get_or_set(
        "stat_total_files", lambda: OdyseeRelease.objects.visible().count(), 3600
    )
    return 9013 > c > 9000
