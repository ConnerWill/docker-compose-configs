from django.contrib.sitemaps import Sitemap
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone


class LegaleseSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return ["legal"]

    def location(self, item):
        return reverse(item)
