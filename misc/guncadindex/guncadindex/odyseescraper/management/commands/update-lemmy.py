import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from odyseescraper.models import OdyseeRelease, OdyseeReleaseLemmy

logger = logging.getLogger("update-lemmy")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Updates all Lemmy managers that need buffed up"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Refresh ALL LemmyManagers instead of just those that are stale",
        )
        parser.add_argument(
            "--destroy",
            action="store_true",
            help="Delete ALL LemmyManagers",
        )

    def handle(self, *args, **options):
        if options["destroy"]:
            OdyseeReleaseLemmy.objects.all().delete()
            return
        to_initialize = OdyseeRelease.objects.all().filter(lemmy_manager=None)
        if to_initialize:
            logger.info(f"Initializing {to_initialize.count()} models...")
            for t in to_initialize:
                try:
                    tobj, tcreated = OdyseeReleaseLemmy.objects.update_or_create(
                        release=t,
                        defaults={
                            # Defaulting to a really far back value so it gets updated soon
                            "updated": timezone.now()
                            - timedelta(weeks=52)
                        },
                    )
                    if not tcreated:
                        logger.info(
                            self.style.WARNING(
                                f"Similarity manager already exists for {t.id}?"
                            )
                        )
                except Exception as e:
                    logger.info(self.style.ERROR(f"Error initializing {t.id}: {e}"))

        if options["all"]:
            to_refresh = OdyseeReleaseLemmy.objects.all()
        else:
            to_refresh = OdyseeReleaseLemmy.objects.annotate_needs_updated().filter(
                needs_updated=True
            )
        if to_refresh:
            logger.info(f"Refreshing {to_refresh.count()} Lemmy managers...")
            for t in to_refresh.order_by("?"):
                try:
                    logger.info(f"Refreshing Lemmy manager for: {t.release.name}")
                    result = t.update()
                    if t._post_count > 0:
                        logger.info(f" - Found {t._post_count} posts")
                    if t._comment_count > 0:
                        logger.info(f" - Found {t._comment_count} comments")
                    if not result:
                        logger.info(
                            self.style.ERROR(f"Error while updating -- backing off")
                        )
                except Exception as e:
                    logger.info(self.style.ERROR(f"Error updating {t.id}: {e}"))

        logger.info("Done refreshing Lemmy stats")
