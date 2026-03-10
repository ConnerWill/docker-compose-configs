import argparse
import time

from didyoumean.utils import get_correction
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):  # pragma: no cover
    help = "Gets a correction for a given sample search query"

    def add_arguments(self, parser):
        parser.add_argument("query", nargs=argparse.REMAINDER)

    def handle(self, *args, **options):
        query = " ".join(options["query"])
        starttime = time.perf_counter()
        original, result = get_correction(query)
        self.stdout.write(f"O: {original}")
        self.stdout.write(f"C: {result}")
        self.stdout.write(f"{((time.perf_counter() - starttime) * 1000):.0f}ms")
