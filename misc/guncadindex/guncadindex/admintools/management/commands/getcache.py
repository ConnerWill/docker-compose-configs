import json

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Dumps the cache contents. Optionally provide a key to dump just that."

    def add_arguments(self, parser):
        parser.add_argument("key", nargs="?", default=None, help="Optional cache key")

    def handle(self, *args, **options):
        key = options["key"]
        if key:
            value = cache.get(key)
            if value is None:
                self.stdout.write(self.style.WARNING(f"No value found for key: {key}"))
            else:
                self.stdout.write(repr(value))
                # self.stdout.write(json.dumps(value, indent=2, default=str))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Cannot dump full cache — backend does not support iteration."
                )
            )
