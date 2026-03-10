from itertools import chain

import releases.origins
from django.core.management.base import BaseCommand
from django.db.models import Q
from releases.models import (
    ORIGIN_CLASSES,
    ChannelDownloadMethod,
    Origin,
    ReleaseDownloadMethod,
)


class Command(BaseCommand):
    help = "Updates all DownloadMethod objects"

    def add_arguments(self, parser):
        parser.add_argument(
            "--discover",
            action="store_true",
            help="In addition to updating DownloadManagers, use each Origin to discover new content",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Refresh ALL DownloadManagers instead of just those that are stale",
        )

    def handle(self, *args, **options):
        if options["all"]:
            to_refresh_from_origin = chain(
                ChannelDownloadMethod.objects.all(), ReleaseDownloadMethod.objects.all()
            )
        else:
            to_refresh_from_origin = chain(
                ChannelDownloadMethod.objects.annotate_needs_updated().filter(
                    needs_updated=True
                ),
                ReleaseDownloadMethod.objects.annotate_needs_updated().filter(
                    needs_updated=True
                ),
            )
        if options["discover"]:
            self.stdout.write("Discovering...")
            for k, v in ORIGIN_CLASSES.items():
                try:
                    self.stdout.write(f"Discovering for {str(v)}")
                    v().discover()
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error discovering {str(v)}: {e}")
                    )
        if to_refresh_from_origin:
            self.stdout.write("Refreshing DownloadMethods...")
            for t in to_refresh_from_origin:
                try:
                    self.stdout.write(f"Refreshing manager: {t.id} for {t.link}")
                    result = t.update()
                    if not result:
                        self.stdout.write(
                            self.style.ERROR(f"Error while updating -- backing off")
                        )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error updating {t.id}: {e}"))
        self.stdout.write("Done refreshing")
