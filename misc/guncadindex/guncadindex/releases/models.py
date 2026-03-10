import logging
import random
import uuid
from collections import Counter
from datetime import timedelta
from io import BytesIO

import requests
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import BooleanField, Case, F, Q, Value, When
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin
from PIL import Image

from . import origins


class ReleaseState(models.IntegerChoices):
    DANGEROUS = -2
    RELEASED = 0
    VERIFIED = 1


class Origin(models.IntegerChoices):
    MANUAL = 0
    LBRY = 1

    def get_origin_choice(obj):
        for choice, cls in ORIGIN_CLASSES.items():
            if isinstance(obj, cls):
                return choice
        return None

    def get_property(origin: int, field: str):
        return ORIGIN_DETAILS.get(origin, {}).get(field, None)


ORIGIN_CLASSES = {
    Origin.MANUAL: origins.ManualOrigin,
    Origin.LBRY: origins.LbryOrigin,
}


class LastUpdatedManagerMixin(models.query.QuerySet):
    # How old does something need to be to be considered stale and in need of a refresh
    REFRESH_DELTA = timedelta(weeks=2)

    def annotate_needs_updated(self):
        refresh_delta = models.ExpressionWrapper(
            timezone.now() - self.REFRESH_DELTA, output_field=models.DateTimeField()
        )
        return self.annotate(
            needs_updated=Case(
                When(
                    # When the date isn't in the future...
                    (~Q(updated__gt=timezone.now()))
                    # ...and we're either missing an image...
                    & (
                        # ...and the images have gone stale...
                        Q(updated__lt=timezone.now() - self.REFRESH_DELTA)
                    ),
                    # ...then we'll need to refresh.
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )


class LastUpdatedMixin(models.Model):
    BACKOFF_DAYS = 7
    BACKOFF_DAYS_JITTER = 2

    class Meta:
        abstract = True

    updated = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="The time that this model was last updated. If this date is in the future, the model has a backoff timer set",
    )

    def backoff(self):
        self.updated = timezone.now() + timedelta(
            days=(self.BACKOFF_DAYS + random.uniform(0, self.BACKOFF_DAYS_JITTER))
        )
        self.save()

    def try_update(self, func, *args, **kwargs):
        """
        Calls func(*args, **kwargs). If an exception occurs, logs it and sets a backoff.
        Returns True if successful, False if it hit an exception.
        """
        logger = logging.getLogger(__name__)
        try:
            func(*args, **kwargs)
            self.updated = timezone.now()
            self.save()
            return True
        except Exception as e:
            logger.warning(f"Failed to update {self.__class__.__name__} {self.pk}")
            logger.exception(e)
            self.backoff()
            return False


class Channel(ExportModelOperationsMixin("channel"), models.Model):
    """
    A GunCAD channel.
    """

    class Meta:
        verbose_name = "channel"
        verbose_name_plural = "channels"

    # Internal data
    id = models.CharField(
        primary_key=True,
        max_length=64,
        default=uuid.uuid4,
        editable=False,
        help_text="A unique identifier for this channel",
    )
    hidden = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Should this channel be hidden from the Index? Hiding a channel also disables indexing it and hides all of its releases",
    )

    # User-facing data that is a direct copy of or derived from the original source
    name = models.CharField(
        max_length=1024,
        help_text="The human-readable name of this release. It should mirror the original source",
    )
    description = models.TextField(
        blank=True,
        help_text="A user-facing description of this release. This should mirror the original source",
    )

    # Dates, for keeping track of timelines
    discovered = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="The time that this release was discovered (added to the database)",
    )

    # Integral original data
    release_state = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        choices=ReleaseState,
        help_text="What state of release is this item in? If unset, defaults to 0 or inherits from the channel",
    )

    def __str__(self):
        return self.name if self.name else self.id


class Release(ExportModelOperationsMixin("release"), models.Model):
    """
    A GunCAD release.
    """

    class Meta:
        verbose_name = "release"
        verbose_name_plural = "releases"

    # Internal data
    id = models.CharField(
        primary_key=True,
        max_length=64,
        default=uuid.uuid4,
        editable=False,
        help_text="A unique identifier for this release",
    )
    hidden = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Should this release be hidden from the Index?",
    )

    # User-facing data that is a direct copy of or derived from the original source
    name = models.CharField(
        max_length=1024,
        help_text="The human-readable name of this release. It should mirror the original source",
    )
    description = models.TextField(
        blank=True,
        help_text="A user-facing description of this release. This should mirror the original source",
    )
    channel = models.ForeignKey(
        Channel,
        null=True,
        help_text="The channel this release should be attached to. If unset, the release is anonymous",
        on_delete=models.CASCADE,
        related_name="releases",
    )

    # Dates, for keeping track of timelines
    discovered = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="The time that this release was discovered (added to the database)",
    )
    released = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="The time that this release was originally posted",
    )
    updated = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="The time that this release was last updated",
    )

    # Integral original data
    release_state = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        choices=ReleaseState,
        help_text="What state of release is this item in? If unset, defaults to 0 or inherits from the channel",
    )

    def __str__(self):
        return self.name if self.name else self.id


class DownloadMethodManager(LastUpdatedManagerMixin):
    REFRESH_DELTA = timedelta(days=1)


class DownloadMethod(
    ExportModelOperationsMixin("downloadmethod"), LastUpdatedMixin, models.Model
):
    """
    A method by which a Release can be downloaded or a Channel can be refreshed
    """

    class Meta:
        verbose_name = "download method"
        verbose_name_plural = "download methods"
        unique_together = [["origin", "link"]]
        ordering = ["origin"]

    objects = DownloadMethodManager().as_manager()

    id = models.CharField(
        primary_key=True,
        max_length=64,
        default=uuid.uuid4,
        editable=False,
        help_text="A unique identifier for this download method",
    )
    origin = models.IntegerField(
        default=Origin.MANUAL,
        db_index=True,
        choices=Origin,
        help_text="Where does this download method point to?",
    )
    link = models.CharField(
        blank=True,
        max_length=512,
        help_text="The URI/CID/magnet link/whatever that this download method represents",
    )

    @property
    def links(self):
        return ORIGIN_CLASSES.get(self.origin).get_links(self.link)

    @property
    def link_name(self):
        return Origin.get_property(self.origin, "download_link_name") or "Unknown Link"

    @property
    def link_desc(self):
        return (
            Origin.get_property(self.origin, "download_link_desc")
            or "Please submit a bug report"
        )

    def update(self):
        # This function should be overridden in any child classes
        pass


class ReleaseDownloadMethod(DownloadMethod):
    release = models.ForeignKey(
        Release,
        help_text="The release this download method represents",
        on_delete=models.CASCADE,
        related_name="download_methods",
    )

    def update(self):
        origin_cls = ORIGIN_CLASSES.get(self.origin)
        if origin_cls:
            return self.try_update(
                lambda: origin_cls().update(
                    release=self.release, origin=self.origin, link=self.link
                )
            )


class ChannelDownloadMethod(DownloadMethod):
    channel = models.ForeignKey(
        Channel,
        help_text="The channel this download method represents",
        on_delete=models.CASCADE,
        related_name="download_methods",
    )

    def update(self):
        origin_cls = ORIGIN_CLASSES.get(self.origin)
        if origin_cls:
            return self.try_update(
                lambda: origin_cls().update(
                    channel=self.channel, origin=self.origin, link=self.link
                )
            )


class ThumbnailManager(LastUpdatedManagerMixin):
    REFRESH_DELTA = timedelta(weeks=4)

    def annotate_needs_updated(self):
        refresh_delta = models.ExpressionWrapper(
            timezone.now() - self.REFRESH_DELTA, output_field=models.DateTimeField()
        )
        return self.annotate(
            needs_updated=Case(
                When(
                    # When the date isn't in the future...
                    (~Q(updated__gt=timezone.now()))
                    # ...and we're either missing an image...
                    & (
                        Q(small="")
                        | Q(large="")
                        # ...or the images have gone stale...
                        | Q(updated__lt=timezone.now() - self.REFRESH_DELTA)
                    ),
                    # ...then we'll need to refresh.
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )


class Thumbnail(ExportModelOperationsMixin("thumbnail"), LastUpdatedMixin):
    """
    A manager for a thumbnail. Includes various helper methods to refresh from an origin
    This base class has some children with FK relationships. GFK is not used here because it's
    a bit of a lame footgun with lackluster support.
    """

    SIZE_SMALL = 384
    SIZE_LARGE = 768
    QUALITY = 85

    class Meta:
        verbose_name = "thumbnail"
        verbose_name_plural = "thumbnails"

    objects = ThumbnailManager().as_manager()

    id = models.CharField(
        primary_key=True,
        max_length=64,
        default=uuid.uuid4,
        editable=False,
        help_text="A unique identifier for this thumbnail",
    )
    origin = models.URLField(
        blank=True,
        max_length=512,
        help_text="A URL to an upstream form of this thumbnail that we're caching from",
    )
    color = models.CharField(
        max_length=1024,
        editable=False,
        blank=True,
        help_text="The dominant color of this thumbnail. Used as a placeholder while the image loads",
    )
    small = models.ImageField(
        upload_to="thumbnails/",
        blank=True,
        null=True,
        help_text="The small form of this thumbnail",
    )
    large = models.ImageField(
        upload_to="thumbnails/",
        blank=True,
        null=True,
        help_text="The large form of this thumbnail",
    )

    @property
    def is_usable(self) -> bool:
        """
        Is this thumbnail suitable in all use cases? If this returns false, a placeholder should be used instead
        """
        return bool(self.small) and bool(self.large)

    @property
    def style(self):
        if not self.color:
            return ""
        return f"background-color:{self.color};color:transparent;"

    def refresh_color(self, image_bytes: bytes):
        """
        Establishes the dominant color of the image based on an image (in bytes)
        """
        img = Image.open(BytesIO(image_bytes)).convert("RGB").resize((50, 50))
        pixels = list(img.getdata())
        most_common = Counter(pixels).most_common(1)[0][0]
        self.color = "#{:02x}{:02x}{:02x}".format(*most_common)
        self.save()

    def refresh_thumbnails(self, image_bytes: bytes):
        """
        Refreshes the thumbnails given some source image, then saves the model
        """
        image = Image.open(BytesIO(image_bytes))
        # Verify that we're not about to explode memory
        MAX_PIXELS = 8192 * 8192
        width, height = image.size
        if width * height > MAX_PIXELS:
            raise ValueError(
                f"Origin too large ({width}x{height}, {width*height}px, limit {MAX_PIXELS})"
            )
        # Do work on the image no that we've somewhat verified its safety
        is_animated = getattr(image, "is_animated", False)
        if is_animated:
            # Save animated images straight across
            file = ContentFile(image_bytes)
            self.large.save(
                f"thumbnail-raw-{self.id}-large.{str.lower(image.format)}",
                file,
                save=False,
            )
            self.small.save(
                f"thumbnail-raw-{self.id}-small.{str.lower(image.format)}",
                file,
                save=False,
            )
        else:
            # For all else, we downsample
            image = image.convert("RGB")
            for size in self.SIZE_LARGE, self.SIZE_SMALL:
                # Otherwise, scale it down
                filename = f"thumbnail-{self.id}-{size}.webp"
                new_image = image.copy()
                new_image.thumbnail((size, size))
                # Prepare a buffer to save the image to
                buffer = BytesIO()
                new_image.save(buffer, format="WEBP", quality=self.QUALITY)
                buffer.seek(0)
                # Push it into the image field
                if size == self.SIZE_LARGE:
                    self.large.save(filename, ContentFile(buffer.read()), save=False)
                elif size == self.SIZE_SMALL:
                    self.small.save(filename, ContentFile(buffer.read()), save=False)
        self.updated = timezone.now() + timedelta(
            days=random.uniform(0, self.BACKOFF_DAYS_JITTER)
        )
        self.save()
        self.refresh_color(image_bytes)

    def refresh_from_origin(self):
        """
        Refreshes thumbnails from the origin field
        """
        if not self.origin:
            self.backoff()
            return False
        useragent = f"GunCADIndex-ImageCacher/1.0 (https://guncadindex.com) {requests.utils.default_user_agent()}"
        try:
            # Pull the file, update our thumbnails
            response = requests.get(self.origin, headers={"User-Agent": useragent})
            response.raise_for_status()
            self.refresh_thumbnails(response.content)
            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to refresh thumbnails from origin for thumbnail {self.id}"
            )
            logger.exception(e)
            self.backoff()
            return False


class ReleaseThumbnail(Thumbnail):
    release = models.OneToOneField(
        Release,
        help_text="The release this thumbnail represents",
        on_delete=models.CASCADE,
        related_name="thumbnail",
    )


class ChannelThumbnail(Thumbnail):
    release = models.OneToOneField(
        Channel,
        help_text="The channel this thumbnail represents",
        on_delete=models.CASCADE,
        related_name="thumbnail",
    )
