from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from . import utils
from .models import Vendor


@receiver(post_save, sender=Vendor)
@receiver(post_delete, sender=Vendor)
def clear_cache_on_vendor_change(sender, instance, **kwargs):
    utils.clear_caches()
