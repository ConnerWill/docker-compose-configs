from django.contrib.sitemaps import Sitemap
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from .models import OdyseeRelease


class OdyseeReleaseRecentSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return (
            OdyseeRelease.objects.visible()
            .filter(released__lte=timezone.now())
            .order_by("-released")
        )

    def lastmod(self, obj):
        return obj.last_updated or obj.released

    def location(self, obj):
        return reverse("detail", args=[obj.slug if obj.slug else obj.id])
