import random
from datetime import datetime, timedelta

from agegate.mixins import AgeGateRequiredMixin
from didyoumean.utils import get_correction
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
)
from django.core.cache import cache
from django.db.models import (
    CharField,
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    Func,
    Prefetch,
    Q,
    Sum,
    Value,
    Window,
)
from django.db.models.functions import Greatest, Least, Ln, PercentRank
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, RedirectView, TemplateView, View
from odyseescraper.models import (
    FaqEntry,
    OdyseeChannel,
    OdyseeRelease,
    OdyseeReleaseManager,
    Tag,
    TaggingRule,
)
from odyseescraper.serializers import (
    OdyseeChannelSerializer,
    OdyseeReleaseSerializer,
    TaggingRuleSerializer,
    TagSerializer,
)
from rest_framework import permissions, viewsets

from . import odysee
from .models import OdyseeRelease

search_strings = [
    # Big shoutouts to Moderator Gage and the BLC team
    "Search for Black Lotus Coalition...",
    "Search for The Gatalog...",
    "Search for INMC...",
    # Big thanks to the Hoff
    "Search for Hoffman Tactical...",
    # Thanks Alyosha from @3dpfreedom for your contributions
    "Search for 3dprintfreedom...",
    "Search for Aves...",
    "Search for a binary trigger...",
    "Search for a bipod...",
    "Search for a CETME C...",
    "Search for a CETME L...",
    "Search for a gun...",
    "Search for a handgun...",
    "Search for a magazine...",
    "Search for a pistol brace...",
    "Search for a rifle...",
    "Search for a sling mount...",
    "Search for a stock...",
    "Search for a Super Safety...",
    "Search for a suppressor...",
    "Search for an FRT...",
    "Search for an Orca...",
    "Search for a CZ Scorpion...",
    "Search for an AK...",
    "Search for target clips...",
    "Search for sights...",
    "Search for night vision...",
    "Search for a specific caliber...",
    "Search for 9x19mm...",
    "Search for 22 Long Rifle...",
    "Search for 37mm...",
    'Search for "AR-15"...',
    'Search for "AR-22"...',
    'Search for "AR-10"...',
    'Search for "Dev Pack"...',
    'Search for "FGC"...',
    'Search for "Glock"...',
    'Search for "Glong"...',
    'Search for "M-11/9"...',
    'Search for "MP5"...',
    "Search for AR-15 magazines...",
    'Search for "Form 1"...',
    'Search for "Urutau"...',
]


def get_random_search_string():
    return random.choice(search_strings)


search_protips = [
    'You can quote a phrase to match the whole thing: "Glock 17"',
    "You can exclude a phrase by using the minus sign. Try: -glock",
    "This search also matches against tags and channels",
    "This search is not case-sensitive",
    "Look up an author to see everything they've made, you might find something cool",
    "People name their projects after really weird stuff sometimes",
    "See something with a wrong tag or missing ones it should have? Hit the edit button and contribute!",
    "Not everything is legal everywhere. Double-check local laws before printing",
    "Don't know what to search up? Check out the Browse or Discover tabs instead",
    "The asterisk (*) doesn't do anything here, use space-separated keywords instead",
    "Find a cool user? Subscribe to them on Odysee",
    "Find a cool release? Give it a like and a repost on Odysee so it climbs the charts here",
    "When you click a release and see its details, you can click its tags to search for them",
    "See a broken image? That's probably the author's fault -- go bug them about it, not me",
    'Pay attention to releases marked as "Beta" -- you might get more than you bargained for',
    "There are a surprising number of Christmas tree ornaments here",
    "This site runs perfectly fine without JavaScript",
    "Sometimes the site indexes content that's since been hidden. If you see the Unlisted tag, you might not be able to download it :(",
    "All LBRY claims are public, even if you unlist them in Odysee. It's the nature of the platform",
    "If a release has always been unlisted, we won't pick it up. Make it public and it'll show up here",
    "There's an API link at the bottom if you want to poke around",
    "Be responsible. These are not toys",
    "Be responsible. These are not toys (except for the ones that are)",
    "Be responsible. These are not toys (except the FGC-6)",
    "When sorting by relevance, more popular releases are more likely to float to the top",
    'When sorting by random, the paginator becomes a "Reroll" button',
    "Want into the Index? Check out the Wiki -- there's a guide on what you need to do to get added",
    "All gun control laws are an infringement on your God-given rights",
    'There are resources in the "About" page if you\'re new to this',
    "If an author completely abandons their release, it becomes delisted here",
    "Much love to those who contribute, however they do it",
    "Sexbots should not be posted on your GunCAD accounts unless they are armed",
]

if settings.GUNCAD_ADMIN_CONTACT:
    search_protips.append("Want to reach out to the admins? Check the footer")
if settings.GUNCAD_ADMIN_TWITTER:
    search_protips.append(
        "Want to reach out to the admins? There's a Twitter link in the footer"
    )
if settings.GUNCAD_ADMIN_DONATIONS:
    search_protips.append(
        "You can donate to support development and hosting costs -- check the footer"
    )
if settings.GUNCAD_ADMIN_CHAT:
    search_protips.append(
        "Have a question? Stop by the Matrix chat -- link is in the footer"
    )


def get_random_search_protip():
    return random.choice(search_protips)


class AdvancedSearchMixin:
    """
    Mixin that looks at the current query parameters and, for each ?tag=whatever, includes
    that tag into context.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slugs = self.request.GET.getlist("tag")
        handles = self.request.GET.getlist("channel")
        context["queried_tags"] = (
            Tag.objects.filter(slug__in=slugs).order_by("category__name", "slug")
            if slugs
            else Tag.objects.none()
        )
        context["queried_channels"] = (
            OdyseeChannel.objects.filter(handle__in=handles).order_by("name", "handle")
            if handles
            else OdyseeChannel.objects.none()
        )
        return context


class ReleaseStatsMixin:
    """
    Mixin that includes statistics on release count
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "total_size": cache.get_or_set(
                "stat_total_size",
                lambda: odysee.sizeof_fmt(
                    OdyseeRelease.objects.visible().aggregate(Sum("size"))["size__sum"]
                    or 0
                ),
                3600,
            ),
            "total_files": cache.get_or_set(
                "stat_total_files",
                lambda: OdyseeRelease.objects.visible().count(),
                3600,
            ),
            "total_channels": cache.get_or_set(
                "stat_total_channels",
                lambda: OdyseeChannel.objects.visible().count(),
                3600,
            ),
            "month_files": cache.get_or_set(
                "stat_month_files",
                lambda: OdyseeRelease.objects.visible()
                .filter(discovered__gte=timezone.now() - timedelta(weeks=4))
                .count(),
                3600,
            ),
        }
        return context


class OdyseeReleaseListView(
    AgeGateRequiredMixin, ReleaseStatsMixin, AdvancedSearchMixin, ListView
):
    paginate_by = 40
    model = OdyseeRelease
    context_object_name = "items"
    template_name = "release_list.html"

    def get_template_names(self, **kwargs):
        if self.request.headers.get("X-Partial"):
            return ["_release_list_content.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        query = self.request.GET.get("query")
        context = super().get_context_data(**kwargs)
        context["search_string"] = get_random_search_string()
        context["search_protip"] = get_random_search_protip()
        context["search_string_all"] = search_strings
        context["search_protip_all"] = search_protips
        if query:
            orig, corrected = get_correction(query)
            if orig != corrected:
                context["search_correction"] = corrected
        return context

    def get_queryset(self):
        return OdyseeRelease.objects.search_by_request(self.request)


class OdyseeReleaseAdvancedSearchView(
    AgeGateRequiredMixin, ReleaseStatsMixin, AdvancedSearchMixin, ListView
):
    """
    View for picking out some advanced search query parameters, which are then passed through to the main search form.
    Implemented as a ListView for Tags to make some templating easier.
    """

    model = Tag
    context_object_name = "items"
    template_name = "release_list_advanced.html"
    queryset = (
        Tag.objects.prefetch_related("category")
        .all()
        .order_by("category__name", "name")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_string"] = get_random_search_string()
        context["search_protip"] = get_random_search_protip()
        context["search_string_all"] = search_strings
        context["search_protip_all"] = search_protips
        return context


class OdyseeReleaseDetailView(AgeGateRequiredMixin, DetailView):
    model = OdyseeRelease
    template_name = "release_detail.html"

    def get_template_names(self, **kwargs):
        if self.request.headers.get("X-Partial"):
            return ["release.html"]
        return [self.template_name]

    def get_queryset(self):
        return super().get_queryset().prefetch_common()

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get("pk")

        obj = queryset.filter(slug=lookup_value).first()
        if obj:
            return obj

        obj = get_object_or_404(queryset, id=lookup_value)

        if obj.slug:
            return HttpResponseRedirect(reverse("detail", kwargs={"pk": obj.slug}))

        return obj

    def get(self, request, *args, **kwargs):
        lookup_value = self.kwargs.get("pk")
        queryset = self.get_queryset()

        obj = queryset.filter(slug=lookup_value).first()
        if obj:
            self.object = obj
            return super().get(request, *args, **kwargs)

        obj = get_object_or_404(queryset, id=lookup_value)

        if obj.slug:
            return HttpResponseRedirect(reverse("detail", kwargs={"pk": obj.slug}))

        self.object = obj
        return super().get(request, *args, **kwargs)


class OdyseeReleasePartialView(View):
    template_name = "_releases.html"

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("ids[]")
        if not ids:
            return HttpResponseBadRequest("No IDs provided")

        cache_key = "releases_html:" + ",".join(sorted(ids))
        html = cache.get(cache_key)
        if not html:
            # Notably absent from this query: the .visible() filter. This is by design.
            # If the user bookmarks a thing, then we hide it, there's not an easy way
            # for us to then convey to that user that they need to nuke it from their
            # bookmark registry.
            #
            # Plus, they obviously already know about it *and* wanna see it. Whenever
            # they navigate to it next, they'll see the delisted banner anyway
            releases = (
                OdyseeRelease.objects.prefetch_related()
                .filter(id__in=ids)
                .order_by("-popularity")
            )
            html = render_to_string(
                self.template_name, {"releases": releases}, request=request
            )
            cache.set(cache_key, html, 60 * 15)

        return HttpResponse(html)


class OdyseeReleaseShortlinkView(RedirectView):
    query_string = False
    pattern_name = "detail"

    def get_redirect_url(self, *args, **kwargs):
        release = get_object_or_404(
            OdyseeRelease, shortlink__iexact=kwargs["shortlink"]
        )
        kwargs = {"pk": release.slug if release.slug else release.id}
        return super().get_redirect_url(*args, **kwargs)


class LandingView(
    AgeGateRequiredMixin, ReleaseStatsMixin, AdvancedSearchMixin, TemplateView
):
    template_name = "landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The last however many releases
        context["latest"] = cache.get_or_set(
            "most_recent_updates",
            lambda: (OdyseeRelease.objects.visible().recently_updated()[:5]),
            60,
        )
        # Most popular/unique for certain time periods
        one_week_ago = timezone.now() - timedelta(weeks=1)
        one_month_ago = timezone.now() - timedelta(weeks=4)
        three_months_ago = timezone.now() - timedelta(weeks=12)
        context["unique_week"] = cache.get_or_set(
            "most_unique_week",
            lambda: (
                OdyseeRelease.objects.visible()
                .prefetch_common()
                .filter(released__gte=one_week_ago)
                .filter(popularity__gte=1)
                .order_by("-uniqueness")
                .first()
            ),
            60,
        )
        context["popular_week"] = cache.get_or_set(
            "most_popular_week",
            lambda: (
                OdyseeRelease.objects.visible()
                .prefetch_common()
                .filter(released__gte=one_week_ago, released__lte=timezone.now())
                .order_by("-popularity")
                .first()
            ),
            60,
        )
        context["unique_month"] = cache.get_or_set(
            "most_unique_month",
            lambda: (
                OdyseeRelease.objects.visible()
                .prefetch_common()
                .filter(released__gte=one_month_ago, released__lte=one_week_ago)
                .filter(popularity__gte=1)
                .order_by("-uniqueness")
                .first()
            ),
            60,
        )
        context["popular_month"] = cache.get_or_set(
            "most_popular_month",
            lambda: (
                OdyseeRelease.objects.visible()
                .prefetch_common()
                .filter(released__gte=one_month_ago, released__lte=one_week_ago)
                .order_by("-popularity")
                .first()
            ),
            60,
        )
        # Any birthdays from the top whatever%
        today = timezone.localtime(timezone.now()).date()
        seed = datetime.today().strftime("%Y%m%d")
        seeded_random = random.Random(seed)
        context["birthdays"] = cache.get_or_set(
            "most_recent_birthdays",
            lambda: (
                OdyseeRelease.objects.visible()
                .annotate(
                    percentile=Window(
                        expression=PercentRank(),
                        order_by=F("popularity").asc(),
                    ),
                    seeded_random_index=Func(
                        Func(
                            Value(seed),
                            Func("id", function="text", output_field=CharField()),
                            function="concat",
                        ),
                        function="md5",
                        output_field=CharField(),
                    ),
                )
                .filter(
                    percentile__gte=0.98,
                    released__month=today.month,
                    released__day=today.day,
                )
                .exclude(released__year=today.year)
                .order_by("seeded_random_index", "-popularity")[:1]
                .prefetch_common()
            ),
            60,
        )
        # And a funny random quip for the search bar
        context["search_string"] = get_random_search_string()
        context["search_protip"] = get_random_search_protip()
        context["search_string_all"] = search_strings
        context["search_protip_all"] = search_protips
        return context


class DiscoverView(AgeGateRequiredMixin, TemplateView):
    template_name = "discover.html"

    def get_context_data(self, **kwargs):
        # This seed is deliberately coarse and only varies by day
        # This ensures that users get deterministic content every day and
        # that cache invalidations won't re-randomize their shit.
        seed = datetime.today().strftime("%Y%m%d")
        today = timezone.localtime(timezone.now()).date()
        seeded_random = random.Random(seed)

        top_releases_percentage = 5
        unique_releases_percentage = 5
        num_tags = 5
        num_releases = 5
        num_channels = 5
        timeperiod = timezone.now() - timedelta(weeks=4)

        context = super().get_context_data(**kwargs)

        context["top_releases"] = cache.get_or_set(
            "discover_top_releases",
            lambda: list(
                OdyseeRelease.objects.visible()
                .filter(released__gte=timeperiod, released__lte=timezone.now())
                .order_by("-popularity")[:num_releases]
                .prefetch_common()
            ),
            timeout=1200,
        )

        context["birthdays"] = cache.get_or_set(
            f"discover_birthdays_{today}",
            lambda: list(
                OdyseeRelease.objects.visible()
                .filter(released__month=today.month, released__day=today.day)
                .exclude(released__year=today.year)
                .order_by("-popularity")[:num_releases]
                .prefetch_common()
            ),
            timeout=1200,
        )

        top_releases_sample_size = int(
            cache.get_or_set(
                "discover_total_release_count",
                lambda: OdyseeRelease.objects.visible().count(),
                timeout=1200,
            )
            * 0.01
            * top_releases_percentage
        )
        top_releases = cache.get_or_set(
            "discover_top_all_time",
            lambda: list(
                OdyseeRelease.objects.visible()
                .filter(released__lte=timezone.now() - timedelta(weeks=52))
                .order_by("-popularity")[:top_releases_sample_size]
                .prefetch_common()
            ),
            timeout=1200,
        )

        unique_releases_sample_size = int(
            cache.get_or_set(
                "discover_total_release_count",
                lambda: OdyseeRelease.objects.visible().count(),
                timeout=1200,
            )
            * 0.01
            * unique_releases_percentage
        )
        unique_releases = cache.get_or_set(
            "discover_top_all_time",
            lambda: list(
                OdyseeRelease.objects.visible()
                .filter(released__lte=timezone.now() - timedelta(weeks=52))
                .order_by("-uniqueness")[:top_releases_sample_size]
                .prefetch_common()
            ),
            timeout=1200,
        )

        seeded_random.shuffle(top_releases)
        context["top_releases_percentage"] = top_releases_percentage
        context["top_releases_all_time"] = top_releases[:num_releases]
        seeded_random.shuffle(unique_releases)
        context["unique_releases_percentage"] = unique_releases_percentage
        context["unique_releases_all_time"] = unique_releases[:num_releases]

        context["top_channels"] = cache.get_or_set(
            "discover_top_channels",
            lambda: list(
                OdyseeChannel.objects.visible()
                .annotate(
                    release_count=Count(
                        "odyseerelease",
                        filter=Q(
                            odyseerelease__released__gte=timeperiod,
                            odyseerelease__released__lte=timezone.now(),
                        ),
                    )
                )
                .prefetch_common()
                .order_by("-release_count")[:num_channels]
            ),
            timeout=1200,
        )

        tags = cache.get_or_set(
            f"discover_tags_{seed}",
            lambda: list(
                Tag.objects.annotate(
                    seeded_random_index=Func(
                        Func(
                            Value(seed),
                            Func("id", function="text", output_field=CharField()),
                            function="concat",
                        ),
                        function="md5",
                        output_field=CharField(),
                    ),
                    release_count=Count("releases_cache"),
                )
                .filter(release_count__gte=1)
                .prefetch_related("category")
            ),
            timeout=1200,
        )

        context["top_tags"] = sorted(tags, key=lambda t: -t.release_count)[:num_tags]
        context["bottom_tags"] = sorted(tags, key=lambda t: t.release_count)[:num_tags]
        context["random_tags"] = sorted(tags, key=lambda t: t.seeded_random_index)[
            :num_tags
        ]

        return context


class AboutView(AgeGateRequiredMixin, TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["faq"] = cache.get_or_set(
            "faq", lambda: (FaqEntry.objects.order_by("id")), 60
        )
        return context


# API views
class OdyseeReleaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List Odysee releases. Accepts query parameters from the site's main search function.
    """

    lookup_value_regex = "[^/]+"
    queryset = (
        OdyseeRelease.objects.visible()
        .filter(released__lte=timezone.now())
        .order_by("-released")
        .prefetch_common()
    )
    serializer_class = OdyseeReleaseSerializer
    filterset_fields = {
        "tags__name": ["icontains"],
        "name": ["icontains"],
        "channel__name": ["icontains"],
    }

    def get_queryset(self):
        return OdyseeRelease.objects.search_by_request(self.request)

    def get_object(self):
        """
        Override default lookup to support both claim IDs and slug format.

        This allows the API detail endpoint (/api/releases/{id}/) to accept either:
        - 40-character claim IDs (e.g., "abc123...xyz789") - existing behavior
        - Slug format (e.g., "Tiny-11:5") - new feature

        The slug format matches LBRY URL conventions and mirrors the behavior of
        the HTML detail view at /detail/{slug}/. This makes the API more intuitive
        for clients working with LBRY URLs who don't have the full claim ID.

        Returns:
            OdyseeRelease: The matching release object

        Raises:
            Http404: If no matching release is found by either slug or claim ID
        """
        queryset = self.filter_queryset(self.get_queryset())
        lookup_value = self.kwargs["pk"]

        # Try lookup by slug first (e.g., "Tiny-11:5")
        # This is more user-friendly since it matches the LBRY URL format
        obj = queryset.filter(slug=lookup_value).first()
        if obj:
            return obj

        # Fallback to default behavior: lookup by 40-character claim ID
        obj = queryset.filter(pk=lookup_value).first()
        if obj:
            return obj

        # No match found by either method
        from django.http import Http404

        raise Http404


class OdyseeChannelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List monitored Odysee channels.
    """

    queryset = OdyseeChannel.objects.visible().order_by("handle")
    serializer_class = OdyseeChannelSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List tags.
    """

    queryset = Tag.objects.all().order_by("name").prefetch_related("category")
    serializer_class = TagSerializer


class TaggingRuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List automatic tagging rules.
    """

    queryset = (
        TaggingRule.objects.all()
        .order_by("name")
        .prefetch_related(
            Prefetch("tag", queryset=Tag.objects.prefetch_related("category")),
            Prefetch("required_tag", queryset=Tag.objects.prefetch_related("category")),
        )
    )
    serializer_class = TaggingRuleSerializer
