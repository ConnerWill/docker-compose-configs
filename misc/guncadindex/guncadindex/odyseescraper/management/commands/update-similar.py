import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from odyseescraper.models import OdyseeRelease, OdyseeReleaseSimilar

logger = logging.getLogger("update-similar")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Updates all similarity relationships that need buffed up"

    def handle(self, *args, **options):
        to_initialize = OdyseeRelease.objects.all().filter(similar_manager=None)
        if to_initialize:
            logger.info(f"Initializing {to_initialize.count()} models...")
            for t in to_initialize:
                try:
                    tobj, tcreated = OdyseeReleaseSimilar.objects.update_or_create(
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

        to_refresh = OdyseeReleaseSimilar.objects.annotate_needs_updated().filter(
            needs_updated=True
        )[:500]
        if to_refresh:
            logger.info(f"Refreshing {to_refresh.count()} similarity managers...")
            for t in to_refresh:
                try:
                    logger.info(f"Refreshing similarity manager for: {t.release.name}")
                    result = t.update()
                    if not result:
                        logger.info(
                            self.style.ERROR(f"Error while updating -- backing off")
                        )
                except Exception as e:
                    logger.info(self.style.ERROR(f"Error updating {t.id}: {e}"))

        logger.info("Done refreshing similarity stats")
