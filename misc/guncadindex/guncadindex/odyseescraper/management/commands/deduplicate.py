import logging
import re
import time
import traceback
import uuid
from datetime import datetime, timezone

import odyseescraper
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.db.models import Count
from odyseescraper.models import OdyseeChannel, OdyseeRelease, TaggingRule

logger = logging.getLogger("deduplicate")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Looks at all channels in the database and reports on the popularity and frequency of tags on those channels"

    def handle(self, *args, **options):
        logger.info("Deduplicating releases...")
        starttime = time.perf_counter()
        try:
            duplicated_hashes = (
                OdyseeRelease.objects.visible()
                .values("sha384sum")
                .annotate(count=Count("sha384sum"))
                .exclude(sha384sum="")
                .filter(count__gt=1)
                .values_list("sha384sum", flat=True)
            )
            duplicated_releases = OdyseeRelease.objects.filter(
                sha384sum__in=duplicated_hashes
            ).prefetch_related("channel")
            unique_releases = OdyseeRelease.objects.exclude(
                sha384sum__in=duplicated_hashes
            ).prefetch_related("channel")
            if int(options["verbosity"]) > 1:
                logger.info(
                    f"{(time.perf_counter() - starttime):2f}s - Acquired list of all {len(duplicated_hashes)} dupe hashes, corresponding to {len(duplicated_releases)} releases"
                )
            for shasum in duplicated_hashes:
                if int(options["verbosity"]) > 1:
                    logger.info(f"Investigating dupes for hash: {shasum}...")
                    # Sorting order here is:
                    #  1. Highest effective LBC wins; failing that
                    #  2. The oldest release wins
                releases = (
                    OdyseeRelease.objects.visible()
                    .filter(sha384sum=shasum)
                    .order_by("-popularity", "released")
                    .prefetch_related("channel")
                )
                winner = releases[0]
                losers = releases[1:]
                winner.duplicate = None
                winner.save()
                if int(options["verbosity"]) > 2:
                    logger.info(
                        " ".join(
                            [
                                " +",
                                self.style.SUCCESS(f"[AUTHORITATIVE]"),
                                f"{winner.channel.name} - {winner.name}",
                            ]
                        )
                    )
                for loser in losers:
                    try:
                        if int(options["verbosity"]) > 2:
                            logger.info(
                                " ".join(
                                    [
                                        " +",
                                        self.style.WARNING(f"[DUPLICATE OBJ]"),
                                        f"{loser.channel.name} - {loser.name}",
                                    ]
                                )
                            )
                        loser.duplicate = winner
                        loser.save()
                    except Exception as e:
                        logger.info(
                            " ".join(
                                [
                                    self.style.ERROR("[ERROR]"),
                                    f"{loser.channel.name} - {loser.name}: {e}",
                                ]
                            )
                        )
                        traceback.print_exc()
                        continue
            if int(options["verbosity"]) > 1:
                logger.info(
                    f"{(time.perf_counter() - starttime):2f}s - Finished assigning duplicates"
                )
            try:
                for release in unique_releases:
                    try:
                        release.duplicate = None
                    except Exception as e:
                        logger.info(
                            " ".join(
                                [
                                    self.style.ERROR("[ERROR]"),
                                    f"{release.channel.name} - {release.name}: {e}",
                                ]
                            )
                        )
                        traceback.print_exc()
                        continue
                OdyseeRelease.objects.bulk_update(unique_releases, ["duplicate"])
            except Exception as e:
                logger.info(
                    " ".join(
                        [
                            self.style.ERROR("[ERROR]"),
                            f"Failed to save unique releases: {e}",
                        ]
                    )
                )
                traceback.print_exc()
            if int(options["verbosity"]) > 1:
                logger.info(
                    f"{(time.perf_counter() - starttime):2f}s - Ensured sanity of {len(unique_releases)} other releases"
                )
        except KeyboardInterrupt:
            logger.info(self.style.WARNING("Interrupt received"))
        if int(options["verbosity"]) > 1:
            logger.info(
                f"{(time.perf_counter() - starttime):2f}s - Finished processing all data"
            )
