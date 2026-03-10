from django.contrib.sitemaps import Sitemap
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from .models import AdminNavbarLink


class AdminNavbarLinkSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return (
            AdminNavbarLink.objects.filter(visible=True)
            .exclude(link__startswith="http")
            .order_by("id")
        )

    def location(self, item):
        return item.destination
