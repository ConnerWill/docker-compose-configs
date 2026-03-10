import json
import logging
import os
import re
import time
from itertools import chain

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone
from odyseescraper import odysee
from odyseescraper.models import OdyseeRelease

logger = logging.getLogger("odysee-stats")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Scrapes for updates to releases' Odysee metadata (views, likes, dislikes, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes instead of actually committing them",
        )
        parser.add_argument(
            "--update-first-page",
            action="store_true",
            help="Also update the first page",
        )
        parser.add_argument(
            "--all-null",
            action="store_true",
            help="Also update any releases that don't have stats yet",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="How many releases to hit at once. Defaults to 5.",
        )
        parser.add_argument(
            "--pace",
            type=float,
            default=0.5,
            help="How long to wait between fetches of data. Setting this too low could result in rate limiting or Bad Times",
        )

    def handle(self, *args, **options):
        # Start work
        starttime = time.perf_counter()
        if not getattr(settings, "GUNCAD_TRACK_ODYSEE", True):
            logger.info(
                self.style.WARNING(
                    "Not invoking this command as GUNCAD_TRACK_ODYSEE is disabled"
                )
            )
            return
        if options["dry_run"]:
            logger.info("Dry-running ...")
        else:
            logger.info("Getting meta for releases...")
        # To aid in performance, query our releases once instead of a bunch of times for no reason
        # Additionally, prefetch related resources so we can iterate over them faster
        querysets = []
        if options["update_first_page"]:
            querysets.append(
                OdyseeRelease.objects.visible()
                .filter(released__lte=timezone.now())
                .order_by("-last_updated")[:60]
            )
            logger.info("Also hitting the front page of releases")
        if options["all_null"]:
            all_null_queryset = (
                OdyseeRelease.objects.visible()
                .filter(released__lte=timezone.now())
                .filter(odysee_last_updated=None)
                .order_by("-last_updated")
            )
            if all_null_queryset.count() > 0:
                logger.info(
                    f"Also hitting {all_null_queryset.count()} uninitialized releases"
                )
                querysets.append(all_null_queryset)
        querysets.append(
            OdyseeRelease.objects.visible().order_by(
                "-odysee_last_updated", "-last_updated", "-released"
            )[: options["batch_size"]]
        )
        releases = chain(*querysets)
        # Quick perf note
        if int(options["verbosity"]) > 1:
            logger.info(f"{(time.perf_counter() - starttime):2f}s - Data prefetch")
        try:
            a = odysee.odysee_authenticate()
            for release in releases:
                release_starttime = time.perf_counter()
                updates = release.update_odysee_stats(auth_token=a)
                time.sleep(
                    max(
                        0,
                        (options["pace"] or 0.5)
                        - (time.perf_counter() - release_starttime),
                    )
                )
                if updates:
                    logger.info(
                        " ".join(
                            [
                                self.style.SUCCESS("[UPDATED]"),
                                f"{release.name} - {updates}",
                            ]
                        )
                    )
                else:
                    logger.info(
                        " ".join([self.style.ERROR("[ERROR]"), f"{release-name}"])
                    )
        except KeyboardInterrupt:
            logger.info(self.style.WARNING("Interrupt received"))
        # Return
        logger.info(f"Took {(time.perf_counter() - starttime):2f}s to complete work")
