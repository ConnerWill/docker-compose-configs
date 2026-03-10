#! /usr/bin/env python3
import datetime
import re
import time
import uuid
from csv import DictReader

import odyseescraper
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from odyseescraper.models import OdyseeChannel


class Command(BaseCommand):
    help = "Imports a CSV of authors, like from BLC"

    def add_arguments(self, parser):
        parser.add_argument("file", help="The file to import")

    def handle(self, *args, **options):
        self.stdout.write("Importing CSV data...")
        updates = 0
        failures = []
        try:
            objects = []
            channel_regex = re.compile("https://odysee.com/(@.*)$", re.IGNORECASE)
            with open(options["file"]) as csv:
                reader = DictReader(csv)
                for row in reader:
                    try:
                        description = (
                            row.get("Description") or "Added automatically by importer"
                        )
                        handle = row.get("Handle")
                        name = row.get("Developer") or handle
                        disabled = row.get("Disabled") or False
                        objects.append(
                            OdyseeChannel(
                                name=name,
                                handle=handle,
                                description=description,
                                disabled=disabled,
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            " ".join([self.style.ERROR("[ERROR]"), f"{str(row)}: {e}"])
                        )
                        failures.append({"line": row, "error": e})
            OdyseeChannel.objects.bulk_create(
                objs=objects, batch_size=250, ignore_conflicts=True
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Interrupt received"))
        except Exception as e:
            self.stdout.write(" ".join([self.style.ERROR("[ERROR]"), f"{str(e)}"]))
            return
        if failures:
            self.stdout.write(self.style.ERROR("Errors occurred while importing data:"))
            for error in failures:
                self.stdout.write(
                    " ".join(
                        [
                            self.style.ERROR("[ERROR]"),
                            f'{error["channel"]} - {error["item"]}: {error["error"]}',
                        ]
                    )
                )
            if updates > 0:
                self.stdout.write(
                    self.style.WARNING(f"Imported {updates} new channels despite this")
                )
        else:
            self.stdout.write(self.style.SUCCESS("CSV imported successfully"))
