import re
import time
import traceback
import uuid
from datetime import datetime, timezone

import odyseescraper
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from odyseescraper.models import OdyseeChannel, OdyseeRelease, TaggingRule


class Command(BaseCommand):  # pragma: no cover
    help = "Looks at all channels in the database and reports on the popularity and frequency of tags on those channels"

    def handle(self, *args, **options):
        self.stdout.write("Analyzing tag frequency...")
        starttime = time.perf_counter()
        try:
            channelmap = {
                channel.claimid: channel.handle
                for channel in OdyseeChannel.objects.exclude(claimid__exact="").filter()
            }
            idlist = [key for key in channelmap.keys()]
            tagcount = {}
            untagged_channel_count = 0
            if int(options["verbosity"]) > 1:
                self.stdout.write(
                    f"{(time.perf_counter() - starttime):2f}s - Mapped {len(idlist)} existing channels"
                )
            for channelid, handle in channelmap.items():
                if int(options["verbosity"]) > 2:
                    self.stdout.write(f"Investigating channel: {handle}...")
                try:
                    channeldata = odyseescraper.odysee.resolve(handle)
                    tags = channeldata.get("value", {}).get("tags", [])
                    if not tags:
                        untagged_channel_count += 1
                        if int(options["verbosity"]) > 2:
                            self.stdout.write(f" untagged {untagged_channel_count}")
                    else:
                        for tag in tags:
                            tagcount[tag] = (
                                1 if not tag in tagcount.keys() else tagcount[tag] + 1
                            )
                            if int(options["verbosity"]) > 2:
                                self.stdout.write(f" {tag} {tagcount[tag]}")
                except Exception as e:
                    self.stdout.write(
                        " ".join(
                            [
                                self.style.ERROR("[ERROR]"),
                                f"{handle}: {e}",
                            ]
                        )
                    )
                    traceback.print_exc()
                    continue
            for tag, count in sorted(
                tagcount.items(), key=lambda item: item[1], reverse=True
            ):
                print(f"{tag} - {count}")
            print(f"{untagged_channel_count} untagged channels")
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Interrupt received"))
        if int(options["verbosity"]) > 1:
            self.stdout.write(
                f"{(time.perf_counter() - starttime):2f}s - Finished processing all data"
            )
