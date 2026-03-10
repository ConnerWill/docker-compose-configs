from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import AdminNavbarLink, AdminSiteBanner


@receiver(post_save, sender=AdminSiteBanner)
def clear_caches_on_site_banner_save(sender, instance, created, **kwargs):
    cache.delete(f"admin_banners")


@receiver(post_save, sender=AdminNavbarLink)
def clear_caches_on_navbar_link_save(sender, instance, created, **kwargs):
    cache.delete(f"admin_navbar_links")
