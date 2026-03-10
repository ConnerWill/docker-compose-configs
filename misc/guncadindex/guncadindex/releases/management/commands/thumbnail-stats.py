from django.core.management.base import BaseCommand
from releases.models import Thumbnail


class Command(BaseCommand):  # pragma: no cover
    help = "Shows you statistics about Thumbnail objects"

    def handle(self, *args, **options):
        total_count = Thumbnail.objects.count()
        self.stdout.write(f"{total_count} thumbnail objects in total")

        no_origin_count = Thumbnail.objects.filter(origin="").count()
        self.stdout.write(f"{no_origin_count} missing an origin URL")

        needs_updated_count = (
            Thumbnail.objects.exclude(origin="")
            .annotate_needs_updated()
            .filter(needs_updated=True)
            .count()
        )
        self.stdout.write(f"{needs_updated_count} in need of updates")
