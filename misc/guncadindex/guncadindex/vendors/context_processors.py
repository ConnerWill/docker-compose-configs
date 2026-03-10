from django.core.cache import cache

from .models import Vendor


def sponsored_vendors(request):
    vendors_footer = cache.get_or_set(
        "vendors_footer",
        lambda: (Vendor.objects.footer().order_by("?")),
        3600 * 3,
    )
    should_render_extra_vendors = cache.get_or_set(
        "should_render_extra_vendors",
        lambda: (Vendor.objects.filter(disabled=False, footer=False).count() > 0),
        60,
    )
    return {
        "vendors_footer": vendors_footer,
        "should_render_extra_vendors": should_render_extra_vendors,
    }
