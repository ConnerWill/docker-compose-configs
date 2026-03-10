import logging
from collections import defaultdict
from math import cos, log1p, pi

from django.core.management.base import BaseCommand
from django.db.models import Count
from odyseescraper.models import OdyseeRelease, Tag

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Calculate historical uniqueness score for each OdyseeRelease"

    def handle(self, *args, **options):
        logger.info("Updating uniqueness...")

        releases = (
            OdyseeRelease.objects.prefetch_common()
            .visible()
            .filter(released__isnull=False)
            .order_by("released")
        )
        total = releases.count()
        tag_counts = defaultdict(int)
        to_update = []

        logger.info(f"Processing {total} releases...")

        for idx, release in enumerate(releases):
            tags = [
                tag
                for tag in release.tags.all()
                if not tag.category or tag.category.useforweighting
            ]

            score = 0.0
            appliedtags = 0

            for tag in tags:
                usage = tag_counts.get(tag.id, 0)
                # This line here boosts the first occurrence of each tag
                # significantly.
                tag_score = 1 / log1p(usage) if usage > 0 else 1.0
                score += tag_score
                # Only count uninflated tags toward scoring. Otherweise,
                # tags that become commonplace eventually end up hurting
                # something's score for no reason
                if tag_score > 0.05:
                    appliedtags += 1

            # Derank early releases using a cosine fade-in for the first
            # whatever%. This is because they're highly likely to have a
            # lot of non-novel "first"s
            progress = idx / total
            threshold = 0.03
            if progress < threshold:
                fade_multiplier = (1 - cos(pi * (progress / threshold))) / 2  # 0 to 1
            else:
                fade_multiplier = 1.0

            # Apply the calculated uniqueness to the release, with a multiplier
            # for popularity.
            if appliedtags > 0:
                normalized = (score / appliedtags) * release.popularity
                release.uniqueness = normalized * fade_multiplier
            else:
                release.uniqueness = 0

            to_update.append(release)

            # Update tag counts after scoring
            for tag in tags:
                tag_counts[tag.id] += 1

        logger.info("Saving...")
        OdyseeRelease.objects.bulk_update(to_update, ["uniqueness"], batch_size=500)
        logger.info(self.style.SUCCESS("Historical uniqueness calculation complete."))
