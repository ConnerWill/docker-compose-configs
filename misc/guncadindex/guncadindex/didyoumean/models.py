from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import TrigramDistance
from django.db import connection, models
from django.db.models import Case, F, IntegerField, Value, When
from django.db.models.functions import Abs, Length
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin


class SearchTokenManager(models.query.QuerySet):
    def visible(self):
        return self.exclude(disabled=True)

    def closest(self, token):
        """
        Gets the closest trigram match to token
        """
        with connection.cursor() as cursor:
            cursor.execute("SET pg_trgm.similarity_threshold TO 0.2")
        return (
            self.visible()
            .filter(token__trigram_similar=token)
            .annotate(
                distance=TrigramDistance("token", token),
                length_distance=Abs(Length("token") - Value(len(token))),
                is_exact=Case(
                    When(token=Value(token), then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                score=(
                    1  # Baseline score
                    + (
                        # Gigantic bonus if there's an exact match so it doesn't drown
                        F("is_exact")
                        * Value(100.0)
                    )
                    + (
                        # Bonus (or malus) for popularity
                        F("popularity")
                        - 1
                    )
                    - (
                        # Minus trigram distance penalty
                        F("distance")
                        * Value(1.0)
                    )
                    - (
                        # Minus length distance penalty
                        F("length_distance")
                        * Value(0.05)
                    )
                ),
            )
            .order_by("-score")
        )


class SearchToken(ExportModelOperationsMixin("tag"), models.Model):
    """
    A search token, used in autocorrection
    """

    class Meta:
        indexes = [
            GinIndex(
                name="searchtoken_trgm_ops",
                fields=["token"],
                opclasses=["gin_trgm_ops"],
            ),
        ]
        verbose_name = "search token"
        verbose_name_plural = "search tokens"

    objects = SearchTokenManager().as_manager()
    token = models.CharField(
        primary_key=True, max_length=512, db_index=True, help_text="The token"
    )
    added = models.DateTimeField(
        editable=False,
        default=timezone.now,
        help_text="The time this token was added to the database",
        db_index=True,
    )
    disabled = models.BooleanField(
        default=False,
        help_text="Disabled tokens are not considered in search corrections",
    )
    popularity = models.FloatField(
        default=1.0,
        help_text="The popularity of the highest-popularity release where this token originated from. If this token didn't originate from a release, this number is arbitrary (but can be supplanted if a release with a higher popularity shows up later)",
        db_index=True,
        editable=False,
    )
