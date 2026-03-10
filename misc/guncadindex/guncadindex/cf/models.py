from django.db import models
from django.db.models import Q
from django.utils import timezone


class CuckAction(models.IntegerChoices):
    RESTRICT_ACCESS_HEAVY = 50
    BLOCK = 100


class CuckManager(models.query.QuerySet):
    def annotate_visible(self):
        return self.annotate(
            visible=(Q(disabled=False) & Q(valid_after__lte=timezone.now()))
        )

    def visible(self):
        return self.annotate_visible().filter(visible=True)


class Cuck(models.Model):
    objects = CuckManager().as_manager()
    disabled = models.BooleanField(
        default=False,
        help_text="Should this geoblocking rule be disabled?",
    )
    valid_after = models.DateTimeField(
        default=timezone.now,
        help_text="The date and time this geoblocking rule should take effect after",
    )
    region = models.CharField(
        max_length=8,
        blank=True,
        help_text="The region string to match against",
    )
    action = models.IntegerField(
        default=CuckAction.BLOCK,
        choices=CuckAction,
        help_text="What should we do for users in this region?",
    )
    reason = models.TextField(
        default="No reason given",
        help_text="The reason to display on the block page",
    )

    def __str__(self):
        return f"{self.region}"
