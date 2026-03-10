import math
import time

from crowdsource.models import Report, TagVote
from django.db.models import Count
from django_redis import get_redis_connection
from odyseescraper.models import OdyseeChannel, OdyseeRelease, Tag
from prometheus_client import Gauge
from releases.models import Thumbnail

# Gauges for simple counters
g_pending_tagvotes = Gauge(
    "tagvotes_unhandled_total",
    "Number of TagVote objects pending handling",
    multiprocess_mode="mostrecent",
)
g_pending_reports = Gauge(
    "reports_unhandled_total",
    "Number of Report objects pending handling",
    multiprocess_mode="mostrecent",
)
g_visible = Gauge(
    "odysee_releases_visible_total",
    "Visible releases (not hidden or abandoned)",
    multiprocess_mode="mostrecent",
)
g_hidden = Gauge(
    "odysee_releases_hidden_total", "Hidden releases", multiprocess_mode="mostrecent"
)
g_abandoned = Gauge(
    "odysee_releases_abandoned_total",
    "Abandoned releases",
    multiprocess_mode="mostrecent",
)
g_lbry_only = Gauge(
    "odysee_releases_lbry_only_total",
    "Releases only visible on LBRY Desktop",
    multiprocess_mode="mostrecent",
)
g_release_count_buckets = Gauge(
    "odysee_release_count_bucket",
    "Releases per channel",
    ["bucket"],
    multiprocess_mode="mostrecent",
)
g_tag = Gauge(
    "odysee_releases_by_tag_total",
    "Releases per tag",
    ["tag"],
    multiprocess_mode="mostrecent",
)
g_dupes = Gauge(
    "odysee_releases_duplicates_total",
    "Releases marked as duplicates",
    multiprocess_mode="mostrecent",
)
g_size_buckets = Gauge(
    "odysee_release_file_size_bytes_bucket",
    "File size distribution of releases",
    ["bucket"],
    multiprocess_mode="mostrecent",
)
g_amount_buckets = Gauge(
    "odysee_release_effective_amount_lbc_bucket",
    "Effective LBC claim amount distribution",
    ["bucket"],
    multiprocess_mode="mostrecent",
)
g_popularity_buckets = Gauge(
    "odysee_release_popularity_bucket",
    "Popularity distribution",
    ["bucket"],
    multiprocess_mode="mostrecent",
)
g_uniqueness_buckets = Gauge(
    "odysee_release_uniqueness_bucket",
    "Uniqueness distribution",
    ["bucket"],
    multiprocess_mode="mostrecent",
)
g_tag_buckets = Gauge(
    "odysee_release_tag_count_bucket",
    "Number of tags on releases",
    ["bucket"],
    multiprocess_mode="mostrecent",
)
g_repost_buckets = Gauge(
    "odysee_release_reposts_total_bucket",
    "Repost count distribution",
    ["bucket"],
    multiprocess_mode="mostrecent",
)
g_thumbnails_total = Gauge(
    "releases_thumbnails_total",
    "Total number of Thumbnail objects",
    multiprocess_mode="mostrecent",
)
g_thumbnails_needs_updated_total = Gauge(
    "releases_thumbnails_needs_updated_total",
    "Total number of Thumbnail objects that are in need of updates",
    multiprocess_mode="mostrecent",
)
g_thumbnails_no_origin_total = Gauge(
    "releases_thumbnails_no_origin_total",
    "Total number of Thumbnail objects that have no origin URL",
    multiprocess_mode="mostrecent",
)
g_unique_visitors_daily = Gauge(
    "unique_visitors_daily",
    "Unique users in the last day",
    multiprocess_mode="mostrecent",
)
g_unique_visitors_weekly = Gauge(
    "unique_visitors_weekly",
    "Unique users in the last week",
    multiprocess_mode="mostrecent",
)
g_unique_visitors_monthly = Gauge(
    "unique_visitors_monthly",
    "Unique users in the last month",
    multiprocess_mode="mostrecent",
)


def bucketize(values, buckets):
    """Helper to bucket values based on upper bounds."""
    counts = {str(b): 0 for b in buckets}
    counts["+Inf"] = 0
    for v in values:
        placed = False
        for b in buckets:
            if v <= b:
                counts[str(b)] += 1
                placed = True
                break
        if not placed:
            counts["+Inf"] += 1
    return counts


def collect_metrics():
    # Raw redis access, for complicated metrics
    r = get_redis_connection("default")

    # Crowdsource shit
    g_pending_tagvotes.set(TagVote.objects.count())
    g_pending_reports.set(Report.objects.count())
    # Visibility statistics
    g_visible.set(OdyseeRelease.objects.visible().count())
    g_hidden.set(OdyseeRelease.objects.filter(hidden=True).count())
    g_abandoned.set(OdyseeRelease.objects.filter(abandoned=True).count())
    g_lbry_only.set(OdyseeRelease.objects.just_lbry_only().count())
    g_dupes.set(OdyseeRelease.objects.filter(duplicate__isnull=False).count())
    # Thumbnail stats
    g_thumbnails_total.set(Thumbnail.objects.count())
    g_thumbnails_needs_updated_total.set(
        Thumbnail.objects.annotate_needs_updated()
        .exclude(origin="")
        .filter(needs_updated=True)
        .count()
    )
    g_thumbnails_no_origin_total.set(Thumbnail.objects.filter(origin="").count())

    # Unique visitor stats
    now = time.time()
    for days, gauge in [
        (1, g_unique_visitors_daily),
        (7, g_unique_visitors_weekly),
        (30, g_unique_visitors_monthly),
    ]:
        window = 86400 * days
        count = r.zcount("uniq:visitors", now - window, now)
        gauge.set(count)

    # Channel release count statistics
    release_counts = (
        OdyseeChannel.objects.visible()
        .annotate_release_count()
        .values_list("release_count", flat=True)
    )
    release_count_buckets = [
        0,
        5,
        10,
        25,
        50,
        100,
        150,
        200,
        250,
        300,
    ]
    release_count_counts = bucketize(release_counts, release_count_buckets)
    for b, c in release_count_counts.items():
        g_release_count_buckets.labels(bucket=b).set(c)

    # Tag stats
    by_tag = (
        Tag.objects.annotate(count=Count("releases_cache"))
        .filter(count__gt=0)
        .values_list("slug", "count")
    )
    for slug, count in by_tag:
        g_tag.labels(tag=slug).set(count)

    # File size distribution
    sizes = OdyseeRelease.objects.visible().values_list("size", flat=True)
    size_buckets = [
        1024,
        10240,
        102400,
        1048576,
        10485760,
        104857600,
        1073741824,
        10737418240,
    ]
    size_counts = bucketize(sizes, size_buckets)
    for b, c in size_counts.items():
        g_size_buckets.labels(bucket=b).set(c)

    # LBC effective amount distribution
    amounts = OdyseeRelease.objects.visible().values_list(
        "lbry_effective_amount", flat=True
    )
    amount_buckets = [
        0.01,
        0.05,
        0.1,
        0.5,
        1.0,
        2.0,
        5.0,
        10.0,
        50.0,
        100.0,
        500.0,
        1000.0,
    ]
    amount_counts = bucketize(amounts, amount_buckets)
    for b, c in amount_counts.items():
        g_amount_buckets.labels(bucket=b).set(c)

    # Popularity distribution
    popularitys = OdyseeRelease.objects.visible().values_list("popularity", flat=True)
    popularity_buckets = [
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.1,
        1.2,
        1.3,
        1.4,
        1.5,
        1.6,
        1.7,
        1.8,
        1.9,
        2.0,
    ]
    popularity_counts = bucketize(popularitys, popularity_buckets)
    for b, c in popularity_counts.items():
        g_popularity_buckets.labels(bucket=b).set(c)

    # Uniqueness distribution
    uniquenesses = OdyseeRelease.objects.visible().values_list("uniqueness", flat=True)
    uniqueness_buckets = [
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
        1.1,
        1.2,
        1.3,
        1.4,
        1.5,
        1.6,
        1.7,
        1.8,
        1.9,
        2.0,
    ]
    uniqueness_counts = bucketize(uniquenesses, uniqueness_buckets)
    for b, c in uniqueness_counts.items():
        g_uniqueness_buckets.labels(bucket=b).set(c)

    # Tag count distribution
    tag_counts = (
        OdyseeRelease.objects.visible()
        .annotate(tag_count=Count("tags"))
        .values_list("tag_count", flat=True)
    )
    tag_count_buckets = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    tag_counts_bucketized = bucketize(tag_counts, tag_count_buckets)
    for b, c in tag_counts_bucketized.items():
        g_tag_buckets.labels(bucket=b).set(c)

    # Repost distribution
    reposts = OdyseeRelease.objects.visible().values_list("lbry_reposts", flat=True)
    repost_buckets = [1, 2, 5, 10, 25]
    repost_counts = bucketize(reposts, repost_buckets)
    for b, c in repost_counts.items():
        g_repost_buckets.labels(bucket=b).set(c)
