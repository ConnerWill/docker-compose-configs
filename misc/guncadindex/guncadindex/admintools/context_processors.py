from django.conf import settings
from django.core.cache import cache

from .models import AdminNavbarLink, AdminSiteBanner


def admin_banners(request):
    banners = cache.get_or_set(
        "admin_banners",
        AdminSiteBanner.objects.visible,
        60,
    )
    links = cache.get_or_set(
        "admin_navbar_links",
        AdminNavbarLink.objects.visible,
        60,
    )
    return {"admin_banners": banners, "admin_navbar_links": links}


def admin_is_debug(request):
    return {"is_debug": settings.DEBUG}
