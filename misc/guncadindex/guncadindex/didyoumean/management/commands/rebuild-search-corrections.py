from didyoumean.models import SearchToken
from didyoumean.utils import add_tokens
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from odyseescraper.models import OdyseeChannel, OdyseeRelease, Tag
from odyseescraper.utils import add_release_to_search_tokens


class Command(BaseCommand):  # pragma: no cover
    help = "Rebuilds the SearchToken table from scratch"

    def handle(self, *args, **options):
        # First, clear the table out
        # Existing searches won't get corrections until the table finishes building
        self.stdout.write("Clearing SearchToken table...")
        SearchToken.objects.all().delete()
        # Add tokens
        self.stdout.write("Building list of tokens...")
        self.stdout.write(" * Working on tags...")
        for tag in Tag.objects.all():
            add_tokens(tag.name, 1.3)
            add_tokens(tag.description, 1.2)
        self.stdout.write(" * Working on channels...")
        for channel in OdyseeChannel.objects.all():
            add_tokens(channel.name, 1.2)
            add_tokens(channel.handle, 0.9)
        self.stdout.write(" * Working on releases...")
        num_releases = 0
        for release in OdyseeRelease.objects.all():
            add_release_to_search_tokens(release)
            num_releases += 1
            if not num_releases % 1000:
                self.stdout.write(f"  * {num_releases}")
