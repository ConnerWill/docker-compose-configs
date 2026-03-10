from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import (
    OdyseeChannel,
    OdyseeChannelThumbnail,
    OdyseeRelease,
    OdyseeReleaseThumbnail,
    Tag,
    TagCategory,
)
from .utils import add_release_to_search_tokens


@receiver(post_save, sender=OdyseeChannel)
def channel_update_thumbnail_manager(sender, instance, **kwargs):
    # When a channel is saved, ensure it has a thumbnail manager
    tobj, tcreated = OdyseeChannelThumbnail.objects.update_or_create(
        release=instance,
        defaults={"origin": instance.thumbnail or ""},
    )


@receiver(post_save, sender=OdyseeRelease)
def release_update_thumbnail_manager(sender, instance, **kwargs):
    # When a release is saved, ensure it has a thumbnail manager
    tobj, tcreated = OdyseeReleaseThumbnail.objects.update_or_create(
        release=instance,
        defaults={"origin": instance.thumbnail or ""},
    )


@receiver(m2m_changed, sender=OdyseeRelease.tag_rules.through)
@receiver(m2m_changed, sender=OdyseeRelease.manual_tags.through)
@receiver(m2m_changed, sender=OdyseeRelease.blacklisted_tags.through)
def update_tags_on_m2m_change(sender, instance, action, **kwargs):
    # Update tags cache whenever an M2M relationship is modified.
    if action in ("post_add", "post_remove", "post_clear"):
        instance.update_tags()


@receiver(post_save, sender=OdyseeRelease)
def update_tags_on_save(sender, instance, **kwargs):
    # Ensure tags are updated when an OdyseeRelease is first created,
    # since m2m_changed won't fire on initial creation.
    instance.update_tags()


@receiver(post_save, sender=OdyseeRelease)
def clear_caches_on_save(sender, instance, created, **kwargs):
    # When an OdyseeRelease is saved, we should make sure we clean out certain caches
    # Deletion is infrequent enough that we just wait for the cache to expire
    cache.delete(f"{instance.id}-similar")
    if created:
        caches = [
            "stat_total_size",
            "stat_total_files",
            "stat_month_files",
            "most_recent_updates",
        ]
        for key in caches:
            cache.delete(key)


@receiver(post_save, sender=OdyseeRelease)
def update_search_tokens_on_save(sender, instance, **kwargs):
    # When an OdyseeRelease is saved, we should add its name's tokens to the SearchToken table
    add_release_to_search_tokens(instance)


@receiver(pre_save, sender=OdyseeRelease)
def update_url_lbry(sender, instance, **kwargs):
    # Updates the LBRY-accessible URL of a release, avoiding legacy naming in the DB
    if instance.url and not instance.url_lbry:
        instance.url = instance.url.replace("#", ":")
        instance.url_lbry = instance.url.replace("https://odysee.com/", "lbry://")


@receiver(pre_save, sender=OdyseeRelease)
def update_license(sender, instance, **kwargs):
    # Updates blank licenses for data consistency. Sometimes they sneak through
    if instance.license == "":
        instance.license = "None"


@receiver(pre_save, sender=OdyseeRelease)
def update_popularity(sender, instance, **kwargs):
    # Updates the popularity statistic when an instance is saved
    instance.update_popularity()


@receiver(pre_save, sender=OdyseeChannel)
def update_url_lbry(sender, instance, **kwargs):
    # Updates the LBRY handle of an OdyseeChannel to avoid legacy nomenclature in the DB
    instance.handle = instance.handle.replace("#", ":")


@receiver(pre_save, sender=OdyseeRelease)
def update_url_from_slug(sender, instance, **kwargs):
    # When an instance is saved, if we have a slug for it, we should use it to
    # construct better canonical Odysee/LBRY URLs
    if instance.slug:
        instance.url = f"https://odysee.com/{instance.slug}"
        instance.url_lbry = f"lbry://{instance.slug}"


@receiver(post_save, sender=OdyseeChannel)
def clear_channel_caches_on_save(sender, instance, created, **kwargs):
    # When an OdyseeChannel is saved, we should make sure we clean out certain caches
    cache.delete("stat_total_channels")


@receiver(pre_save, sender=Tag)
def update_tag_slug(sender, instance, **kwargs):
    # When a Tag is saved, we should construct a slug for it if it doesn't have one yet
    if not instance.slug:
        instance.slug = slugify(instance.name)
