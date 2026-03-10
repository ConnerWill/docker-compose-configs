import logging

from django.core.management.base import BaseCommand
from django.db.models import Q
from releases.models import Thumbnail

logger = logging.getLogger("release-update-thumbnails")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Updates all thumbnails that need handling"

    def handle(self, *args, **options):
        to_refresh_from_origin = (
            Thumbnail.objects.annotate_needs_updated()
            .filter(needs_updated=True)
            .exclude(origin="")
        )
        if to_refresh_from_origin:
            logger.info(f"Refreshing {to_refresh_from_origin.count()} thumbnails...")
            for t in to_refresh_from_origin:
                try:
                    logger.info(f"Refreshing thumbnail: {t.id}")
                    result = t.refresh_from_origin()
                    if not result:
                        logger.info(
                            self.style.ERROR(f"Error while updating -- backing off")
                        )
                except Exception as e:
                    logger.info(self.style.ERROR(f"Error updating {t.id}: {e}"))

        to_refresh_color = (
            Thumbnail.objects.annotate_needs_updated()
            .filter(needs_updated=False, color="")
            .exclude(Q(small="") | Q(large=""))
        )
        if to_refresh_color:
            logger.info(f"Refreshing {to_refresh_color.count()} colors...")
            for t in to_refresh_color:
                try:
                    t.refresh_color()
                    logger.info(f"Refreshed color: {t.id}")
                except Exception as e:
                    # We're masking errors here deliberately because:
                    #  * This can get really noisy depending on the environment
                    #  * The only way this can fail is if we're missing a file,
                    #    which is a way bigger data integrity fail
                    # logger.info(self.style.ERROR(f"Error updating {t.id}: {e}"))
                    pass

        logger.info("Done refreshing thumbnails")
