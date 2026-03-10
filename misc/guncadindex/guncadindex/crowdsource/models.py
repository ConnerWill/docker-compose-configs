import uuid

from django.db import models
from django.db.models import Exists, OuterRef
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin
from odyseescraper.models import OdyseeRelease, Tag


# Create your models here.
class TagVote(ExportModelOperationsMixin("tagvote"), models.Model):
    """
    A modification to an OdyseeRelease that has yet to be committed
    """

    class Meta:
        unique_together = ["voter", "release", "tag"]
        verbose_name = "tag vote"
        verbose_name_plural = "tag votes"

    class Operation(models.IntegerChoices):
        UPVOTE = 1
        DOWNVOTE = -1

    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this TagEdit",
    )
    voter = models.CharField(
        max_length=128,
        editable=False,
        help_text="The hash of the IP of the user who submitted this vote",
    )
    release = models.ForeignKey(
        OdyseeRelease,
        editable=False,
        related_name="votedrelease",
        on_delete=models.CASCADE,
        help_text="The OdyseeRelease this edit intends to modify",
    )
    tag = models.ForeignKey(
        Tag,
        editable=False,
        related_name="votedtag",
        on_delete=models.CASCADE,
        help_text="The Tag this edit intends to either append or remove",
    )
    value = models.IntegerField(
        editable=False, choices=Operation, help_text="The value of this particular vote"
    )


class Report(ExportModelOperationsMixin("report"), models.Model):
    """
    A flag-down from a user
    """

    REPORT_REASONS = (
        "Not GunCAD-related",
        "Copyright or other IP infringement",
        "It's mine and I want it taken down",
        "Malicious content",
        "Misleading content",
        "Other",
    )

    class Meta:
        verbose_name = "report"
        verbose_name_plural = "reports"

    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this report",
    )
    voter = models.CharField(
        max_length=128,
        editable=False,
        help_text="The hash of the IP of the user who submitted this report",
    )
    reason_index = models.PositiveSmallIntegerField(
        choices=[(i, label) for i, label in enumerate(REPORT_REASONS)],
        help_text="Index of the reason for reporting",
    )
    release = models.ForeignKey(
        OdyseeRelease,
        editable=False,
        related_name="reports",
        on_delete=models.CASCADE,
        help_text="The OdyseeRelease this edit intends to modify",
    )

    @property
    def reason_label(self):
        """
        Return the human-readable label of the report reason
        """
        try:
            return self.REPORT_REASONS[self.reason_index]
        except IndexError:
            return "Unknown"


class TagSuggestionManager(models.QuerySet):
    def needs_cleared(self):
        return self.annotate(
            tag_exists=Exists(Tag.objects.filter(name=OuterRef("tag"))),
            release_has_tag=Exists(
                Tag.objects.filter(
                    name__iexact=OuterRef("tag"),
                    releases_cache=OuterRef("release"),
                )
            ),
        ).filter(tag_exists=True)


class TagSuggestion(ExportModelOperationsMixin("tagsuggestion"), models.Model):
    """
    A suggestion for the addition of a new tag
    """

    objects = TagSuggestionManager().as_manager()

    class Meta:
        unique_together = ["tag", "release"]
        verbose_name = "tag suggestion"
        verbose_name_plural = "tag suggestions"

    class Source(models.IntegerChoices):
        HUMAN = 1
        AI = 2

    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this TagSuggestion",
    )
    created = models.DateTimeField(
        editable=False,
        default=timezone.now,
        help_text="When this suggestion was made",
    )
    source = models.IntegerField(
        editable=False, choices=Source, help_text="Where this suggestion came from"
    )
    tag = models.CharField(
        max_length=128,
        editable=False,
        help_text="The name of the tag that should be added",
    )
    release = models.ForeignKey(
        OdyseeRelease,
        null=True,
        editable=False,
        related_name="suggested_tag",
        on_delete=models.CASCADE,
        help_text="The OdyseeRelease this suggestion is intended for",
    )
