import logging

from crowdsource.models import TagSuggestion
from django.core.management.base import BaseCommand
from django.db import transaction
from odyseescraper.models import OdyseeRelease, Tag

logger = logging.getLogger("process-suggestions")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Process Tag Suggestions that now have tags or are one char away from a matching tag"

    def handle(self, *args, **options):
        qs = TagSuggestion.objects.needs_cleared()

        if qs:
            for suggestion in qs.select_related("release"):
                with transaction.atomic():
                    try:
                        if not suggestion.release_has_tag:
                            release = suggestion.release
                            tag = Tag.objects.get(name=suggestion.tag)
                            if suggestion.source == TagSuggestion.Source.AI:
                                release.ai_tags.add(tag)
                            else:
                                release.manual_tags.add(tag)
                            release.update_tags()
                            release.save()
                            logger.info(
                                f"Applied {tag.name} to {release.name} ({suggestion.id})"
                            )
                        else:
                            logger.info(
                                f"Removed extraneous suggestion for {tag.name} on {release.name} ({suggestion.id})"
                            )
                        suggestion.delete()
                    except Exception as e:
                        logger.info(
                            self.style.ERROR(f"Error processing {suggestion.id}")
                        )
        logger.info("Done processing tag suggestions")
