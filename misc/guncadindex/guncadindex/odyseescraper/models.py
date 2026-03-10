import math
import os
import urllib.parse
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
    SearchVectorField,
    TrigramDistance,
    TrigramSimilarity,
)
from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import connection, models, transaction
from django.db.models import (
    Case,
    CharField,
    Count,
    DateTimeField,
    DurationField,
    ExpressionWrapper,
    F,
    FloatField,
    Func,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    Value,
    When,
    Window,
)
from django.db.models.functions import Coalesce, Greatest, Least, Ln, RowNumber
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_prometheus.models import ExportModelOperationsMixin
from lemmy.util import search as lemmysearch
from releases.models import LastUpdatedManagerMixin, LastUpdatedMixin, Thumbnail

from . import odysee


class ReleaseState(models.IntegerChoices):
    DANGEROUS = -2
    RELEASED = 0
    VERIFIED = 1


class TagCategory(ExportModelOperationsMixin("tagcategory"), models.Model):
    """
    A category for a tag
    """

    class Meta:
        verbose_name = "tag category"
        verbose_name_plural = "tag categories"

    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this category",
    )
    name = models.CharField(
        max_length=256,
        unique=True,
        help_text="The name for this category as it should be displayed across UIs",
    )
    color = models.CharField(
        max_length=16,
        blank=True,
        validators=[
            RegexValidator(
                #                        v How many bytes per channel (1 or 2)
                #                              v How many channels total (RGB or RGBA)
                regex=r"^#(?:[0-9a-fA-F]{1,2}){3,4}$",
                message='Field must be a valid hex RGB color code prepended with "#"',
                code="invalid",
            )
        ],
        help_text="The RGB hex code (with #) of all tags in the category. If unspecified, a default will be chosen",
    )
    description = models.TextField(
        help_text="A user-facing description of the category"
    )
    useforweighting = models.BooleanField(
        default=True,
        verbose_name="use for weighting",
        help_text="Should tags in this category be used for things like search and uniqueness weighting?",
    )


class Tag(ExportModelOperationsMixin("tag"), models.Model):
    """
    A bog-standard tag, applicable to any OdyseeRelease
    """

    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this tag",
    )
    slug = models.SlugField(
        max_length=64,
        null=True,
        editable=False,
        unique=True,
        help_text="The slug for this tag",
    )
    name = models.CharField(
        max_length=256,
        unique=True,
        help_text="The name for this tag as it should be displayed across UIs",
    )
    custom_color = models.CharField(
        max_length=16,
        blank=True,
        validators=[
            RegexValidator(
                #                        v How many bytes per channel (1 or 2)
                #                              v How many channels total (RGB or RGBA)
                regex=r"^#(?:[0-9a-fA-F]{1,2}){3,4}$",
                message='Field must be a valid hex RGB color code prepended with "#"',
                code="invalid",
            )
        ],
        help_text="The RGB hex code (with #) of the color of the tag. If unspecified, a default will be chosen",
    )
    category = models.ForeignKey(
        TagCategory,
        related_name="targetcategory",
        null=True,
        on_delete=models.SET_NULL,
        db_index=True,
        help_text="The category to associate with this tag",
    )
    description = models.TextField(help_text="A user-facing description of the tag")

    @property
    def color(self):
        if self.custom_color:
            return self.custom_color
        elif self.category and self.category.color:
            return self.category.color
        else:
            return ""

    @property
    def text_color(self):
        if not self.color:
            return ""
        # https://nemecek.be/blog/172/how-to-calculate-contrast-color-in-python
        color = self.color[1:]
        hex_red = int(color[0:2], base=16)
        hex_green = int(color[2:4], base=16)
        hex_blue = int(color[4:6], base=16)
        luminance = hex_red * 0.2126 + hex_green * 0.7152 + hex_blue * 0.0722
        if luminance < 140:
            return "rgba(255,255,255,0.95)"
        else:
            return "rgba(0,0,0,0.95)"

    @property
    def description_array(self):
        return self.description.split("\n")

    def __str__(self):
        return self.name


class FaqEntry(ExportModelOperationsMixin("faqentry"), models.Model):
    """
    An entry in the FAQ on the site
    """

    class Meta:
        verbose_name = "FAQ entry"
        verbose_name_plural = "FAQ entries"

    id = models.IntegerField(
        primary_key=True,
        editable=True,
        db_index=True,
        help_text="The ID of this FAQ entry. All entries will be displayed in ascending order by this field.",
    )
    question = models.CharField(
        max_length=512, editable=True, blank=True, help_text="The question"
    )
    answer = models.TextField(blank=True, help_text="The answer to the question")


class TaggingRule(ExportModelOperationsMixin("taggingrule"), models.Model):
    """
    Defines a rule run against releases to assign them with tags automatically. See `./manage.py odyseetag --help` for details on cron-ing this
    """

    class Meta:
        verbose_name = "tagging rule"
        verbose_name_plural = "tagging rules"

    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this tagging rule",
    )
    name = models.CharField(
        max_length=1024, help_text="A non-user-facing name for the rule"
    )
    title_regex = models.CharField(
        max_length=512,
        blank=True,
        help_text="A regular expression to match against the title of a release. If the release's title matches, the tag is applied. If this value is blank, it is ignored.",
    )
    description_regex = models.CharField(
        max_length=512,
        blank=True,
        help_text="A regular expression to match against the description of a release. If it matches, the tag is applied. If this value is blank, it is ignored.",
    )
    channel_regex = models.CharField(
        max_length=512,
        blank=True,
        help_text="A regular expression to match against the channel HANDLE of a release. If it matches, the tag is applied. If this value is blank, it is ignored.",
        verbose_name="channel handle regex",
    )
    license_regex = models.CharField(
        max_length=512,
        blank=True,
        help_text="A regular expression to match against the license field of a release. If it matches, the tag is applied. If this value is blank, it is ignored.",
        verbose_name="channel handle regex",
    )
    required_tag = models.ForeignKey(
        Tag,
        related_name="required_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="A tag to match against a release. If this value is blank, it is ignored.",
    )
    tag = models.ForeignKey(
        Tag,
        related_name="targeted_by",
        on_delete=models.CASCADE,
        db_index=True,
        help_text="The tag to assign a release with",
        verbose_name="assigned tag",
    )

    def __str__(self):
        return str(self.name)


class OdyseeChannelManager(models.query.QuerySet):
    def annotate_common(self):
        return self.annotate_release_count().annotate_duplicate_releases()

    def annotate_release_count(self):
        return self.annotate(release_count=Count("odyseerelease"))

    def annotate_duplicate_releases(self):
        return self.annotate(
            dupe_count=Count(
                "odyseerelease", filter=Q(odyseerelease__duplicate__isnull=False)
            )
        )

    def visible(self):
        return self.exclude(disabled=True)

    def prefetch_common(self):
        return self.prefetch_related("thumbnail_manager")


class OdyseeChannel(ExportModelOperationsMixin("odyseechannel"), models.Model):
    """
    An Odysee channel to monitor for releases. See `./manage.py odyseescrape --help` for details on cron-ing this
    """

    class Meta:
        verbose_name = "Odysee channel"
        verbose_name_plural = "Odysee channels"

    objects = OdyseeChannelManager().as_manager()
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this channel",
    )
    disabled = models.BooleanField(
        default=False,
        help_text="Should this channel be excluded from automatic updates?",
    )
    lbry_only = models.BooleanField(
        default=False,
        help_text='Is this channel only navigable via LBRY? Usually only applicable to channels marked "mature"',
        verbose_name="LBRY only",
    )
    name = models.CharField(
        max_length=1024,
        help_text="The human-readable name of the channel. Does not, and often will not, necessarily correlate with the channel's handle",
    )
    description = models.TextField(
        blank=True,
        help_text="A user-facing description of the channel, its owners, and its content. May also contain links to related resources and websites.",
    )
    default_release_state = models.IntegerField(
        default=ReleaseState.RELEASED,
        choices=ReleaseState,
        help_text="What state of release should we assign to this channel?",
    )
    claimid = models.CharField(
        default="",
        max_length=64,
        editable=False,
        help_text="The LBRY claim ID of the channel",
        verbose_name="claim ID",
    )
    handle = models.CharField(
        unique=True,
        max_length=1024,
        help_text="The @tag of the user. May be a short tag (@someuser) or qualified with claimid (@someuser:4ab8)",
    )
    thumbnail = models.URLField(
        default="",
        max_length=512,
        editable=False,
        help_text="The URL to the Odysee-hosted thumbnail of the channel",
    )
    discovered = models.DateTimeField(
        editable=False,
        default=timezone.now,
        help_text="The time that this channel was added",
        db_index=True,
    )

    @property
    def thumbnail_small(self):
        if hasattr(self, "thumbnail_manager") and self.thumbnail_manager.is_usable:
            return self.thumbnail_manager.small.url
        return f"{settings.STATIC_URL}no-image-user.webp"

    @property
    def thumbnail_large(self):
        if hasattr(self, "thumbnail_manager") and self.thumbnail_manager.is_usable:
            return self.thumbnail_manager.large.url
        return f"{settings.STATIC_URL}no-image-user.webp"

    @property
    def url(self):
        return f"https://odysee.com/{self.handle}"

    def __str__(self):
        return self.name


class OdyseeReleaseManager(models.query.QuerySet):
    def visible(self):
        """
        Return all objects that should be visible on the Index
        """
        return self.no_hidden().no_abandoned().annotate_common()

    def recently_updated(self):
        """
        Sort by objects that were either updated recently or recently acquired
        Max 1 release per channel
        """
        # Coalesce verification state
        canonical_state = Coalesce(
            F("release_state"),
            F("duplicate__release_state"),
            F("channel__default_release_state"),
            output_field=IntegerField(),
        )
        # Verified releases get a 12-hour "boost" in the rankings
        verified_boost = Case(
            When(
                canonical_state__gte=1,
                then=Value(timedelta(hours=12)),
            ),
            default=Value(timedelta(0)),
            output_field=DurationField(),
        )
        effective_order = ExpressionWrapper(
            F("last_updated") + verified_boost,
            output_field=DateTimeField(),
        )

        latest = (
            OdyseeRelease.objects.filter(
                channel=OuterRef("channel"),
                released__lte=timezone.now(),
            )
            .annotate(canonical_state=canonical_state, effective_order=effective_order)
            .order_by("-effective_order")
        )
        return (
            self.annotate(
                canonical_state=canonical_state, effective_order=effective_order
            )
            .filter(id=Subquery(latest.values("id")[:1]))
            .order_by("-effective_order")
            .prefetch_common()
        )

    def no_hidden(self):
        """
        Exclude objects manually hidden by moderators
        """
        return self.exclude(hidden=True)

    def no_abandoned(self):
        """
        Exclude objects whose LBRY claims have been abandoned
        """
        return self.exclude(abandoned=True)

    def no_future(self):
        return self.filter(released__lte=timezone.now())

    def just_lbry_only(self):
        """
        Filter to just objects that are only visible through LBRY Desktop. The claim is good, but Odysee does not work for viewing them
        """
        return self.visible().filter(Q(lbry_only=True) | Q(channel__lbry_only=True))

    def annotate_common(self):
        """
        Annotates a QuerySet with commonly-used annotations
        """
        return self

    def prefetch_common(self):
        """
        Prefetch some commonly-used data, like essential FK relationships
        """
        return self.prefetch_related(
            "thumbnail_manager",
            Prefetch(
                "lemmy_manager", queryset=OdyseeReleaseLemmy.objects.annotate_common()
            ),
            Prefetch(
                "channel",
                queryset=OdyseeChannel.objects.prefetch_related("thumbnail_manager"),
            ),
            Prefetch("tags", queryset=Tag.objects.prefetch_related("category")),
        )

    def prefetch_comprehensive(self):
        """
        Prefetch everything
        """
        return self.prefetch_common().prefetch_related(
            "tag_rules", "manual_tags", "ai_tags", "blacklisted_tags"
        )

    def search_by_request(self, request):
        """
        Wrapper for search() that parses out a request object
        """
        return self.search(
            query=request.GET.get("query", ""),
            sort=request.GET.get("sort", ""),
            datefilter=request.GET.get("time", ""),
            tags=request.GET.getlist("tag", []),
            channels=request.GET.getlist("channel", []),
        )

    def search(self, query, sort="rank", datefilter="alltime", tags=[], channels=[]):
        """
        Search through OdyseeRelease objects given a query and a sort method

            query           The full text search query given by the user
            tags            A list of tags to filter by. All results will have at least these tags
            channels        A list of channels for

        Returns a QuerySet
        """

        def parse_query_terms(query):
            """
            Take a user's query and return two lists of strings:
            1. The list of strings they want to see; and
            2. Their negations
            This doesn't do additional websearch logic, but it stops
            trigram matching from including things users explicitly
            requested not to see.
            """
            terms = query.strip().split()
            include = []
            exclude = []
            for term in terms:
                if term.startswith("-") and len(term) > 1:
                    exclude.append(term[1:])
                else:
                    include.append(term)
            return include, exclude

        sorts = {
            "rank": "-rank",
            "newest": "-last_updated",
            "oldest": "released",
            "updated": "-last_updated",
            "random": "?",
            "popular": "-popularity",
            "unique": "-uniqueness",
            "biggest": "-size",
            "smallest": "size",
        }
        datefilters = {
            "day": timezone.now() - timedelta(days=1),
            "week": timezone.now() - timedelta(weeks=1),
            "month": timezone.now() - timedelta(weeks=4),
            "season": timezone.now() - timedelta(weeks=13),
            "year": timezone.now() - timedelta(weeks=52),
            "alltime": datetime.min,
        }
        s = sorts.get(sort, sorts["rank"])
        t = datefilters.get(datefilter, datefilters["alltime"])
        q = query.lower()[:255]
        queryset = self.visible()
        if sort == "updated":
            queryset = queryset.exclude(Q(released=F("last_updated")))
        if channels:
            queryset = queryset.filter(channel__handle__in=channels)
        # Before anything else, filter tags
        for tag in tags:
            if type(tag) == str:
                # If it's a string, we probably have a list of slugs
                queryset = queryset.filter(tags__slug=tag)
            else:
                # Otherwise, assume we have a list of objects
                queryset = queryset.filter(tags__slug=tag.slug)
        if q:
            include_terms, exclude_terms = parse_query_terms(q)
            search_query = SearchQuery(q, search_type="websearch")
            trigram_query = " ".join(include_terms)
            search_vector = F("search_vector")

            # Trigram search results. This one's not as good as FTS, but it lets us do
            # some amount of partial string matching against titles.
            # Start off by setting our similarity threshold
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET pg_trgm.similarity_threshold TO 0.2")
                trgm_queryset = (
                    (
                        queryset.filter(name__trigram_similar=trigram_query)
                        .annotate(
                            distance=TrigramDistance("name", trigram_query),
                            rank=ExpressionWrapper(
                                (1.0 - F("distance")) * F("popularity"),
                                output_field=FloatField(),
                            ),
                        )
                        .order_by("-rank")[:50]
                    )
                    if include_terms
                    else queryset.none()
                )
            # Cast to a list of IDs so we can filter by it later
            trgm_ids = list(trgm_queryset.values_list("id", flat=True))
            # Full-text-search results. This is good for exact matches, but doesn't
            # match partial words at all.
            queryset = (
                queryset.filter(Q(search_vector=search_query) | Q(id__in=trgm_ids))
                .annotate(
                    fts_rank=SearchRank(search_vector, search_query),
                    trigram_rank=TrigramSimilarity("name", trigram_query),
                    rank=Greatest(
                        # FTS results are unbounded, as they come from a stricter, narrower
                        # search that's more likely to hit what the user wants
                        F("fts_rank") * F("popularity"),
                        # Trigram ranking is boosted significantly to compete with FTS
                        # similarity, but is capped at (at time of writing) the median
                        # popularity of a release. This ensures exceedingly popular releases
                        # with potentially better release standards that come from the FTS
                        # aren't drowned
                        Least(F("trigram_rank") * F("popularity") * 1.50, 1.12),
                    ),
                    highlighted_name=SearchHeadline(
                        "name", search_query, start_sel="<b>", stop_sel="</b>"
                    ),
                    highlighted_description=SearchHeadline(
                        "description", search_query, start_sel="<b>", stop_sel="</b>"
                    ),
                )
                .order_by(s)
            )
            for term in exclude_terms:
                queryset = queryset.exclude(name__icontains=term)
        else:
            queryset = queryset.filter(released__lte=timezone.now()).order_by(
                s if s != "-rank" else "-last_updated"
            )

        return queryset.filter(
            released__lte=timezone.now(), released__gte=t
        ).prefetch_common()


class OdyseeRelease(ExportModelOperationsMixin("odyseerelease"), models.Model):
    """
    An Odysee release, as (hopefully) pulled from the odyseescrape command (see above). Contains a lot of details about a release
    """

    class Meta:
        indexes = [
            GinIndex(fields=["search_vector"]),
            GinIndex(fields=["similarity_vector"]),
            GinIndex(
                name="odyseerelease_trgm_ops",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            ),
        ]
        verbose_name = "Odysee release"
        verbose_name_plural = "Odysee releases"

    objects = OdyseeReleaseManager().as_manager()
    id = models.CharField(
        primary_key=True,
        max_length=512,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        help_text="A unique identifier for this release. Usually the LBRY claim ID, if available",
    )
    hidden = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Should this release be hidden from the index? Hidden releases will not show up in searches or the API",
    )
    abandoned = models.BooleanField(
        default=False,
        editable=False,
        db_index=True,
        help_text="Has this release had its support withdrawn by its author? This results in complete inaccessibility of the release",
    )
    lbry_only = models.BooleanField(
        default=False,
        help_text="Is this release only navigable via LBRY? Can be a result of a lot of things, like unlisting from Odysee",
        verbose_name="LBRY only",
    )
    duplicate = models.ForeignKey(
        "self",
        default=None,
        on_delete=models.SET_NULL,
        related_name="release_duplicate",
        editable=False,
        null=True,
        help_text="If this file is a duplicate, this is the release it's a duplicate of",
    )
    channel = models.ForeignKey(
        OdyseeChannel,
        on_delete=models.CASCADE,
        db_index=True,
        editable=False,
        help_text="The channel that this release came from",
    )
    name = models.CharField(
        max_length=1024,
        help_text="The human-readable name of this release",
        editable=False,
    )
    description = models.TextField(
        blank=True,
        editable=False,
        help_text="A user-facing description of this release. This should mirror the official post from Odysee, if available",
    )
    license = models.CharField(
        blank=True,
        max_length=1024,
        help_text="The license this release is under",
        editable=False,
    )
    sd_hash = models.CharField(
        default="",
        max_length=256,
        help_text="The sd_hash of the file, representing the blob which describes the rest of the file.",
        editable=False,
        db_index=True,
    )
    sha384sum = models.CharField(
        default="",
        max_length=256,
        help_text="The file hash of this file, in SHA384 (it's a LBRY thing don't question it)",
        editable=False,
        db_index=True,
    )
    released = models.DateTimeField(
        editable=False,
        help_text="The time that this release was posted in UTC",
        db_index=True,
    )
    last_updated = models.DateTimeField(
        null=True,
        editable=False,
        help_text="The time that this release was last updated in UTC",
        db_index=True,
    )
    discovered = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="The date this release was discovered",
    )
    release_state = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        choices=ReleaseState,
        help_text="What state of release is this item in? If unset, defaults to the channel's default release state.",
    )
    size = models.BigIntegerField(
        help_text="The size of the release in bytes", editable=False
    )
    slug = models.CharField(
        max_length=512,
        unique=True,
        null=True,
        editable=False,
        help_text="The short_url of the object, which is the shortest possible resolvable name the claim can sit under.",
    )
    url = models.URLField(
        max_length=512,
        editable=False,
        help_text="The URL to the Odysee page where the release can be downloaded. It is NOT a direct download link",
    )
    url_lbry = models.CharField(
        max_length=512,
        blank=True,
        editable=False,
        help_text="The URL to the LBRY claim for this release.",
    )
    thumbnail = models.URLField(
        max_length=512,
        editable=False,
        help_text="The URL to the Odysee-hosted thumbnail of the release",
    )

    shortlink = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        help_text="A custom slug for a shortlink which will be made available at guncadindex.com/s/<shortlink>. Use sparingly",
        unique=True,
    )

    tag_rules = models.ManyToManyField(
        TaggingRule,
        related_name="releases",
        blank=True,
        editable=False,
        help_text="A list of TaggingRules associated with this release",
    )

    tags = models.ManyToManyField(
        Tag,
        related_name="releases_cache",
        blank=True,
        editable=False,
        help_text="A list of tags manually associated with this release.",
    )
    manual_tags = models.ManyToManyField(
        Tag,
        related_name="releases_manual",
        blank=True,
        help_text="A list of tags manually associated with this release.",
    )
    ai_tags = models.ManyToManyField(
        Tag,
        related_name="releases_ai",
        blank=True,
        editable=False,
        help_text="A list of tags the linked LLM thinks this release should have.",
    )
    blacklisted_tags = models.ManyToManyField(
        Tag,
        related_name="releases_blacklist",
        blank=True,
        help_text="A list of tags this release should NEVER have, even when added by TaggingRules",
    )

    # Odysee site metadata, used for stats and weighting in search results
    odysee_views = models.BigIntegerField(
        default=0,
        help_text="The number of views this release has on Odysee",
        verbose_name="Odysee views",
        editable=False,
    )
    odysee_likes = models.BigIntegerField(
        default=0,
        help_text="The number of likes this release has on Odysee",
        verbose_name="Odysee likes",
        editable=False,
    )
    odysee_dislikes = models.BigIntegerField(
        default=0,
        help_text='The number of "slimes" (dislikes) this release has on Odysee',
        verbose_name="Odysee slimes",
        editable=False,
    )
    odysee_last_updated = models.DateTimeField(
        null=True,
        editable=False,
        help_text="The last time that this model had its Odysee statistics updated",
    )

    # LBRY claim metadata, used for stats and weighting in search results
    lbry_effective_amount = models.FloatField(
        default=0,
        help_text="The effective amount of the claim of this release in LBC",
        verbose_name="LBRY effective amount",
        db_index=True,
        editable=False,
    )
    lbry_support_amount = models.FloatField(
        default=0,
        help_text="The subset of the effective amount that was community-contributed in LBC",
        verbose_name="LBRY support amount",
        db_index=True,
        editable=False,
    )
    # Number of reposts of this release, used for stats and weighting in search results
    lbry_reposts = models.BigIntegerField(
        help_text="The number of times this claim has been reposted on LBRY",
        verbose_name="LBRY reposts",
        db_index=True,
        editable=False,
    )

    # These search fields are for internal indexing
    search_vector = SearchVectorField(null=True, editable=False)
    similarity_vector = SearchVectorField(null=True, editable=False)
    search_tag_list = models.CharField(
        max_length=512,
        blank=True,
        editable=False,
        help_text="Internal. Concatenated string of all tags, updated on save()",
    )
    search_channel = models.CharField(
        max_length=512,
        blank=True,
        editable=False,
        help_text="Internal. Name of the owning channel, updated on save()",
    )
    search_channel_handle = models.CharField(
        max_length=512,
        blank=True,
        editable=False,
        help_text="Internal. Handle of the owning channel, updated on save()",
    )
    popularity = models.FloatField(
        default=1.0,
        db_index=True,
        editable=False,
        help_text="What is the ranking factor of this release? This field is automatically calculated based on a number of statistics about this release.",
    )
    uniqueness = models.FloatField(
        default=0.0,
        db_index=True,
        editable=False,
        help_text="How unique is this release? This is evaluated elsewhere in a management command based on factors like tag rarity",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track original sd_hash for comparison later
        self._original_sha384sum = self.sha384sum

    def save(self, *args, **kwargs):
        # Sanitization
        if self.shortlink:
            self.shortlink = str(self.shortlink.lower())
        # Search optimization
        self.search_tag_list = " ".join(self.tags.values_list("name", flat=True))
        self.search_channel = self.channel.name
        self.search_channel_handle = self.channel.handle

        # Update last_updated based on file hash
        if not self.last_updated:
            if self.released:
                self.last_updated = self.released
            else:
                self.last_updated = timezone.now()
        elif (
            self.sha384sum
            and self.sha384sum != self._original_sha384sum
            and getattr(settings, "GUNCAD_TRACK_UPDATES", True)
            and self.released < timezone.now()
        ):
            self.last_updated = timezone.now()

        self.search_vector = (
            SearchVector(Value(self.name), weight="A")
            + SearchVector(Value(self.search_tag_list), weight="B")
            + SearchVector(Value(self.description), weight="D")
            + SearchVector(Value(self.search_channel), weight="A")
            + SearchVector(Value(self.search_channel_handle), weight="A")
        )
        self.similarity_vector = (
            SearchVector(Value(self.name), weight="C")
            + SearchVector(Value(self.search_tag_list), weight="D")
            + SearchVector(Value(self.search_channel), weight="A")
            + SearchVector(Value(self.search_channel_handle), weight="A")
        )
        super().save(*args, **kwargs)
        self._original_sha384sum = self.sha384sum

    def update_tags(self):
        tag_rule_ids = self.tag_rules.values_list("tag", flat=True)
        tags_rules = Tag.objects.filter(id__in=tag_rule_ids)
        tags_ai = self.ai_tags.all()
        tags_manual = self.manual_tags.all()
        tags_blacklist = self.blacklisted_tags.all()
        final_tags = (set(tags_manual) | set(tags_ai) | set(tags_rules)) - set(
            tags_blacklist
        )
        self.tags.set(final_tags)

    def update_odysee_stats(self, auth_token):
        if not auth_token:
            return None
        stats = odysee.odysee_get_stats(auth_token=auth_token, claimid=self.id)
        likes = stats.get("likes")
        dislikes = stats.get("dislikes")
        views = stats.get("views")
        if likes:
            self.odysee_likes = likes
        if dislikes:
            self.odysee_dislikes = dislikes
        if views:
            self.odysee_views = views
        self.odysee_last_updated = timezone.now()
        self.save()
        return {
            "views": self.odysee_views,
            "likes": self.odysee_likes,
            "dislikes": self.odysee_dislikes,
        }

    @property
    def repost_weight(self):
        return min(math.log(self.lbry_reposts + 2.72) * 0.005, 0.05)

    @property
    def support_weight(self):
        return max(math.log(self.lbry_support_amount + 0.001) * 0.01, 0.0)

    @property
    def effective_weight(self):
        return max(math.log(self.lbry_effective_amount + 0.001) * 0.005, 0.0)

    @property
    def view_weight(self):
        return min(math.log(self.odysee_views + 1) * 0.03, 0.40)

    @property
    def like_weight(self):
        return min((self.odysee_likes - (4 * self.odysee_dislikes)) * 0.0015, 0.30)

    @property
    def release_state_weight(self):
        return self.canonical_release_state * 0.05

    @property
    def get_popularity_score(self):
        # "Popularity" is some ranking based around 1, where values >1 are
        # considered "more popular", and values <1 are the opposite. This
        # is used to modulate search algorithms and the like.
        score = (
            1
            + self.repost_weight
            + self.support_weight
            + self.effective_weight
            + self.view_weight
            + self.like_weight
            + self.release_state_weight
        )
        # Duplicates face a massive penalty
        if self.duplicate_id is not None:
            score *= 0.4
        return score

    def update_popularity(self):
        self.popularity = self.get_popularity_score

    @property
    def odysee_like_ratio(self):
        if self.odysee_dislikes < 1:
            return 1.0
        else:
            total = self.odysee_likes + self.odysee_dislikes
            return self.odysee_likes / total

    @property
    def similar(self):
        """
        Get releases similar to this one.
        """
        if (
            hasattr(self, "similar_manager")
            and self.similar_manager.similar_releases.count() > 0
        ):
            return self.similar_manager.similar_releases
        else:
            query = SearchQuery(str(self.similarity_vector))
            result = cache.get_or_set(
                f"{self.id}-similar",
                lambda: (
                    OdyseeRelease.objects.no_hidden()
                    .no_abandoned()
                    .no_future()
                    .annotate(rank=SearchRank("similarity_vector", query))
                    .exclude(id=self.id)
                    .prefetch_common()
                    .order_by("-rank")[:4]
                ),
                3600 * 24 * 7,
            )
            return result

    @property
    def authoritative_repost(self):
        return cache.get_or_set(
            f"{self.id}-authoritative-repost",
            lambda: (
                OdyseeRelease.objects.visible()
                .filter(duplicate=self.id, lbry_only=False)
                .order_by("popularity")
                .first()
            ),
            3600 * 24,
        )

    @property
    def tag_list(self):
        return ", ".join(self.tags.values_list("name", flat=True))

    @property
    def is_birthday(self):
        now = timezone.localtime(timezone.now())
        local_released = timezone.localtime(self.released)
        return (
            local_released.month == now.month
            and local_released.day == now.day
            and not local_released.year == now.year
        )

    @property
    def rarity(self):
        """
        Uses the uniqueness metric to determine what "rarity" this release
        should be categorized as. Used for funny CSS at the template level
        """
        scores = cache.get_or_set(
            "uniqueness_value_list",
            lambda: (
                list(
                    OdyseeRelease.objects.values_list("uniqueness", flat=True).order_by(
                        "uniqueness"
                    )
                )
            ),
            3600 * 24 * 7,
        )
        n = len(scores)
        if n < 100:
            return "common"
        else:
            top10_cutoff = scores[math.floor(n * 0.90)]
            top5_cutoff = scores[math.floor(n * 0.95)]
            top1_cutoff = scores[math.floor(n * 0.99)]

        if self.uniqueness > top1_cutoff:
            return "legendary"
        elif self.uniqueness > top5_cutoff:
            return "rare"
        elif self.uniqueness > top10_cutoff:
            return "uncommon"
        else:
            return "common"

    @property
    def thumbnail_small(self):
        if hasattr(self, "thumbnail_manager") and self.thumbnail_manager.is_usable:
            return self.thumbnail_manager.small.url
        return f"{settings.STATIC_URL}no-image-release.webp"

    @property
    def thumbnail_large(self):
        if hasattr(self, "thumbnail_manager") and self.thumbnail_manager.is_usable:
            return self.thumbnail_manager.large.url
        return f"{settings.STATIC_URL}no-image-release.webp"

    @property
    def size_friendly(self):
        return odysee.sizeof_fmt(self.size)

    @property
    def description_array(self):
        return self.description.split("\n")

    @property
    def visible_on_odysee(self):
        return not (self.lbry_only or self.channel.lbry_only)

    @property
    def lbry_support_ratio(self):
        n = self.lbry_support_amount
        d = self.lbry_effective_amount
        return (n / d if d else 0) * 100

    @property
    def canonical_release_state(self):
        return (
            self.release_state
            if not self.release_state == None
            else (
                self.duplicate.canonical_release_state
                if self.duplicate
                else self.channel.default_release_state
            )
        )

    @property
    def url_lbry_legacy(self):
        return "lbry://" + (self.slug.replace(":", "#") or "")

    def __str__(self):
        return self.name


class OdyseeReleaseThumbnail(Thumbnail):
    release = models.OneToOneField(
        OdyseeRelease,
        help_text="The release this thumbnail represents",
        on_delete=models.CASCADE,
        related_name="thumbnail_manager",
    )


class OdyseeChannelThumbnail(Thumbnail):
    release = models.OneToOneField(
        OdyseeChannel,
        help_text="The release this thumbnail represents",
        on_delete=models.CASCADE,
        related_name="thumbnail_manager",
    )


class OdyseeReleaseSimilarManager(LastUpdatedManagerMixin):
    REFRESH_DELTA = timedelta(days=7)


class OdyseeReleaseSimilar(LastUpdatedMixin):
    """
    A manager for how many releases are similar to another given one
    """

    class Meta:
        verbose_name = "Odysee release similarity manager"
        verbose_name_plural = "Odysee release similarity managers"

    objects = OdyseeReleaseSimilarManager().as_manager()

    release = models.OneToOneField(
        OdyseeRelease,
        help_text="The release this similarity manager represents",
        on_delete=models.CASCADE,
        related_name="similar_manager",
    )
    similar = models.ManyToManyField(
        OdyseeRelease,
        blank=True,
        help_text="The releases this release is similar to",
        related_name="similar_to",
    )

    def update_similar(self, limit=4):
        query = SearchQuery(str(self.release.similarity_vector))
        result = (
            OdyseeRelease.objects.no_hidden()
            .no_abandoned()
            .no_future()
            .annotate(rank=SearchRank("similarity_vector", query))
            .exclude(id=self.release.id)
            .prefetch_common()
            .order_by("-rank")[:limit]
        )
        self.similar.set(result)

    def update(self):
        return self.try_update(lambda: self.update_similar())

    @property
    def similar_releases(self):
        return self.similar.all().prefetch_common().order_by("-popularity")


class OdyseeReleaseLemmyManager(LastUpdatedManagerMixin):
    REFRESH_DELTA = timedelta(days=1)

    def annotate_common(self):
        return self.annotate_counts()

    def annotate_counts(self):
        return (
            self.annotate(
                post_count=Func(
                    Coalesce(F("search_results__posts"), Value([], output_field=None)),
                    function="jsonb_array_length",
                    output_field=IntegerField(),
                ),
                comment_count=Func(
                    Coalesce(
                        F("search_results__comments"), Value([], output_field=None)
                    ),
                    function="jsonb_array_length",
                    output_field=IntegerField(),
                ),
            )
            .annotate(activity_count=F("post_count") + F("comment_count"))
            .order_by("-activity_count")
        )


class OdyseeReleaseLemmy(LastUpdatedMixin):
    """
    Lemmy stats that pertain to a given release
    """

    class Meta:
        verbose_name = "Odysee release lemmy manager"
        verbose_name_plural = "Odysee release lemmy managers"

    objects = OdyseeReleaseLemmyManager().as_manager()

    release = models.OneToOneField(
        OdyseeRelease,
        on_delete=models.CASCADE,
        related_name="lemmy_manager",
    )

    def _default_search_results():
        return {"posts": [], "comments": [], "communities": [], "users": []}

    def _validate_search_results(value):
        """
        Ensures `search_results` is a dict with keys: posts, comments, communities, users,
        and that each key maps to a list.
        """
        if not isinstance(value, dict):
            raise ValidationError("search_results must be a dict.")

        expected_keys = {"posts", "comments", "communities", "users"}

        missing = expected_keys - value.keys()
        if missing:
            raise ValidationError(
                f"Missing keys in search_results: {', '.join(missing)}"
            )

        for key in expected_keys:
            if not isinstance(value[key], list):
                raise ValidationError(f"search_results['{key}'] must be a list.")

    search_results = models.JSONField(
        null=True,
        default=_default_search_results,
        help_text="The results of a search for the associated release",
        validators=[_validate_search_results],
    )

    def update_lemmy(self):
        self.search_results = lemmysearch([self.release.name, self.release.slug])
        self.save()

    def update(self):
        return self.try_update(lambda: self.update_lemmy())

    @property
    def lemmy_url(self):
        return settings.GUNCAD_LEMMY_INSTANCE

    @property
    def posts(self):
        return self.search_results.get("posts", {})

    @property
    def posts_carousel(self):
        return sorted(
            self.posts,
            key=lambda p: (
                p.get("counts", {}).get("score", 1),
                p.get("counts", {}).get("comments", 0),
            ),
            reverse=True,
        )[:3]

    @property
    def comments(self):
        return self.search_results.get("comments", {})

    @property
    def comments_carousel(self):
        return sorted(
            self.comments,
            key=lambda p: (
                p.get("counts", {}).get("score", 1),
                p.get("counts", {}).get("child_count", 0),
            ),
            reverse=True,
        )[:3]

    @property
    def _activity_count(self):
        return self.post_count + self.comment_count

    @property
    def _post_count(self):
        return len(self.posts)

    @property
    def _comment_count(self):
        return len(self.comments)
