import uuid

from django.db import models


class TrafficClassifier(models.Model):
    KIND_CHOICES = [
        ("user_agent", "User Agent"),
        ("referrer", "Referrer Header"),
        ("host", "Host Header"),
        ("xff", "X-Forwarded-For IP"),
        ("path", "Request Path"),
    ]

    priority = models.IntegerField(
        default=100,
        help_text="The priority of this rule. Higher-priority rules are processed first",
    )
    kind = models.CharField(
        default="user_agent",
        max_length=20,
        choices=KIND_CHOICES,
        help_text="The field this traffic classifier should act on",
    )
    pattern = models.CharField(
        max_length=255,
        blank=True,
        help_text='The substring pattern of this traffic classifier rule. Special string ":empty:" will match empty strings',
    )
    value = models.CharField(
        default="human",
        max_length=50,
        help_text='The value to tag this request with. Requests that don\'t match any of these rules will be tagged as "human"',
    )
    description = models.TextField(
        default="Unnamed Traffic Rule",
        help_text="An admin-facing description of this traffic classifier rule",
    )

    def __str__(self):
        return f"{self.kind}:{self.pattern} -> {self.value}"
