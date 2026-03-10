import argparse
import time

from didyoumean import utils
from didyoumean.models import SearchToken
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):  # pragma: no cover
    help = "Analyze the correction results for a given search token"

    def add_arguments(self, parser):
        parser.add_argument("token")

    def handle(self, *args, **options):
        token = utils.tokenize(options["token"])[0]
        if not utils.validate_token(token):
            self.stdout.write(self.style.ERROR(f"Invalid token: {token}"))
            return False
        results = SearchToken.objects.closest(token)
        if not results:
            self.stdout.write(self.style.WARNING(f"No results for token: {token}"))
            return
        self.stdout.write("Possible matches:")
        for result in results:
            self.stdout.write(f" - " + self.style.SUCCESS(f"{result.token}"))
            self.stdout.write(f"    distance        {result.distance}")
            self.stdout.write(f"    length_distance {result.length_distance}")
            self.stdout.write(f"    is_exact        {result.is_exact}")
            self.stdout.write(f"    popularity      {result.popularity}")
            self.stdout.write(
                f"    " + self.style.WARNING("SCORE") + f"           {result.score}"
            )
