import os
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync all files under MEDIA_ROOT to S3"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be uploaded without actually uploading",
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root:
            self.stderr.write(f"MEDIA_ROOT is not defined!")
            return
        if not media_root.exists():
            self.stderr.write(f"MEDIA_ROOT '{media_root}' does not exist!")
            return

        dry_run = options["dry_run"]
        count = 0

        for filepath in media_root.rglob("*"):
            if filepath.is_file():
                relative_path = filepath.relative_to(media_root).as_posix()
                if dry_run:
                    self.stdout.write(f"[DRY RUN] Would upload: {relative_path}")
                    count += 1
                else:
                    with filepath.open("rb") as f:
                        django_file = File(f)
                        # Save via default storage (MediaStorage), overwriting S3
                        default_storage.save(relative_path, django_file)
                        count += 1
                        self.stdout.write(f"Uploaded: {relative_path}")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Done! Uploaded {count} files to S3"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Would have uploaded {count} files to S3")
            )
