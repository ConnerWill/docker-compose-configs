import logging
import time
import traceback
import uuid
from datetime import datetime, timezone

import odyseescraper
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from odyseescraper import odysee
from odyseescraper.models import OdyseeRelease

logger = logging.getLogger("scrape")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Updates all OdyseeChannel objects, creating OdyseeRelease objects for anything new"

    no_title_string = "Untitled Release"
    no_description_string = "No description provided for this release"

    def handle(self, *args, **options):
        logger.info("Scraping Odysee channels for new content...")
        starttime = time.perf_counter()
        updates = 0
        to_save = []
        failures = []
        try:
            # If we've set things up to track Odysee stats, lease an authentication token
            if getattr(settings, "GUNCAD_TRACK_UPDATES", True):
                auth_token = odysee.odysee_authenticate()
            else:
                auth_token = None
            unpopulated_channels = odyseescraper.models.OdyseeChannel.objects.filter(
                claimid__exact=""
            )
            if unpopulated_channels.count() > 0:
                for channel in unpopulated_channels:
                    channeldata = odyseescraper.odysee.resolve(channel.handle)
                    channel.claimid = channeldata.get("claim_id", "")
                    channel.name = channeldata.get("value", {}).get(
                        "title", channel.handle.split(":")[0]
                    )
                    channel.lbry_only = "c:mature" in channeldata.get("value", {}).get(
                        "tags", []
                    )
                    channel.thumbnail = (
                        channeldata.get("value", {}).get("thumbnail", {}).get("url", "")
                    )
                    channel.save()
                if int(options["verbosity"]) > 1:
                    logger.info(
                        f"{(time.perf_counter() - starttime):2f}s - Populated claimids for {unpopulated_channels.count()} channels"
                    )
            channelmap = {
                channel.claimid: channel.handle
                for channel in odyseescraper.models.OdyseeChannel.objects.visible().exclude(
                    claimid__exact=""
                )
            }
            idlist = [key for key in channelmap.keys()]
            if int(options["verbosity"]) > 1:
                logger.info(
                    f"{(time.perf_counter() - starttime):2f}s - Mapped {len(idlist)} channels"
                )
            releases = odyseescraper.odysee.bulk_claim_search(idlist)
            if int(options["verbosity"]) > 1:
                logger.info(
                    f"{(time.perf_counter() - starttime):2f}s - Acquired {sum(len(v) for v in releases.values())} releases"
                )
            # Before we dive into processing new releases, we should look for abandoned claims
            # We start by searching for all releases in the DB that we didn't just find from the
            # blockchain:
            logger.info("Quickly looking for abandoned claims...")
            release_idlist = [key for release in releases.values() for key in release]
            for release in odyseescraper.models.OdyseeRelease.objects.visible().exclude(
                id__in=release_idlist
            ):
                resolved_claim = odyseescraper.odysee.resolve(release.url_lbry)
                if not resolved_claim or resolved_claim.get("claim_id") != release.id:
                    todays_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(
                        " ".join(
                            [
                                self.style.SUCCESS("[ABANDONED]"),
                                f"{release.channel.name} - {release.name}",
                            ]
                        )
                    )
                    release.abandoned = True
                    release.save()
                else:
                    release.abandoned = False
                    release.save()
            logger.info("Looking for new content...")
            for channelid, releases in releases.items():
                channel = odyseescraper.models.OdyseeChannel.objects.get(
                    claimid=channelid
                )
                # Update channel meta while we have it
                try:
                    # Sometimes we can get a release that doesn't have a signing_channel. I don't know enough LBRY
                    # to tell you why this happens, but it does, and we should fall back to a known-good source of
                    # channel data. In this case, we just issue a request to the LBRY daemon.
                    #
                    # This fires every one in like... 20? 30? channels, so of a dataset of 1k channels we could
                    # lose maybe... 5-10 seconds here?
                    channeldata = next(iter(releases.values()), {}).get(
                        "signing_channel", None
                    ) or odyseescraper.odysee.resolve(channel.handle)
                    channel.claimid = channeldata.get("claim_id", "")
                    channel.name = channeldata.get("value", {}).get(
                        "title", channel.handle.split(":")[0]
                    )
                    channel.thumbnail = (
                        channeldata.get("value", {}).get("thumbnail", {}).get("url", "")
                    )
                    channel.save()
                except Exception as e:
                    logger.info(
                        " ".join(
                            [
                                self.style.ERROR("[ERROR]"),
                                f"Updating meta for channel: {str(channel)}: {e}",
                            ]
                        )
                    )
                # Get all those claims
                if int(options["verbosity"]) > 2:
                    logger.info(f"Updating channel: {str(channel)}...")
                for release, data in releases.items():
                    value = data.get("value")
                    try:
                        description = value.get(
                            "description", self.no_description_string
                        )
                        released = (
                            int(value.get("release_time", 0))
                            if int(value.get("release_time", 0))
                            > (
                                data.get("meta", {}).get("creation_timestamp", 0)
                                - (60 * 60 * 24)
                            )
                            else data.get("meta", {}).get("creation_timestamp")
                        )
                        slug = (
                            data.get("short_url")
                            .replace("#", ":")
                            .replace("lbry://", "")
                        )
                        if value.get("tags", False):
                            description += "\n\nLBRY Tags: " + "; ".join(
                                value.get("tags", [])
                            )
                        # If this is a new release and has the unlisted tag...
                        if not OdyseeRelease.objects.filter(
                            id=data.get("claim_id")
                        ).exists() and "c:unlisted" in value.get("tags", []):
                            # ...skip it
                            logger.info(
                                " ".join(
                                    [
                                        self.style.WARNING("[NOT YET RELEASED]"),
                                        f"{str(channel)} - {value.get('title')}",
                                    ]
                                )
                            )
                            continue
                        # Update or create the release
                        obj, created = (
                            odyseescraper.models.OdyseeRelease.objects.update_or_create(
                                id=data.get("claim_id"),
                                defaults={
                                    "lbry_only": "c:unlisted" in value.get("tags", []),
                                    "channel": channel,
                                    "name": value.get("title"),
                                    "description": description,
                                    "license": value.get("license") or "None",
                                    "released": datetime.fromtimestamp(
                                        released, tz=timezone.utc
                                    ),
                                    "slug": slug,
                                    "size": int(value.get("source", {}).get("size", 0)),
                                    "sd_hash": value.get("source", {}).get(
                                        "sd_hash", ""
                                    ),
                                    "sha384sum": value.get("source", {}).get(
                                        "hash", ""
                                    ),
                                    # TODO: We should make canonical_url a FCS and do this conversion to Odysee at the model as a property
                                    "url": data.get("canonical_url", "").replace(
                                        "lbry://", "https://odysee.com/"
                                    ),
                                    "thumbnail": value.get("thumbnail", {}).get(
                                        "url", ""
                                    ),
                                    "lbry_effective_amount": float(
                                        data.get("meta", {}).get("effective_amount", 0)
                                    ),
                                    "lbry_support_amount": float(
                                        data.get("meta", {}).get("support_amount", 0)
                                    ),
                                    "lbry_reposts": int(
                                        data.get("meta", {}).get("reposted", 0)
                                    ),
                                },
                            )
                        )
                        tobj, tcreated = (
                            odyseescraper.models.OdyseeReleaseThumbnail.objects.update_or_create(
                                release=obj,
                                defaults={
                                    "origin": value.get("thumbnail", {}).get("url", ""),
                                },
                            )
                        )
                        if not tcreated:
                            to_save.append(tobj)
                        if not created:
                            to_save.append(obj)
                        elif auth_token:
                            obj.update_odysee_stats(auth_token=auth_token)
                    except Exception as e:
                        logger.info(
                            " ".join(
                                [
                                    self.style.ERROR("[ERROR]"),
                                    f"{str(channel)} - {value.get('title')}: {e}",
                                ]
                            )
                        )
                        print(release)
                        print(data)
                        traceback.print_exc()
                        failures.append(
                            {
                                "channel": str(channel),
                                "item": value.get("title"),
                                "error": e,
                            }
                        )
                        continue
                    if created:
                        logger.info(
                            " ".join(
                                [
                                    self.style.SUCCESS("[IMPORT]"),
                                    f"{str(channel)} - {value.get('title')}",
                                ]
                            )
                        )
                        updates += 1
            if int(options["verbosity"]) > 1:
                logger.info(
                    f"{(time.perf_counter() - starttime):2f}s - Finished importing new releases"
                )
            # Lastly, make a pass on all the objects that we need to save
            for release in to_save:
                release.save()
            if int(options["verbosity"]) > 1:
                logger.info(
                    f"{(time.perf_counter() - starttime):2f}s - Updated {len(to_save)} existing releases with new metadata"
                )
        except KeyboardInterrupt:
            logger.info(self.style.WARNING("Interrupt received"))
        if int(options["verbosity"]) > 1:
            logger.info(
                f"{(time.perf_counter() - starttime):2f}s - Finished processing all data"
            )
        if failures:
            logger.info(self.style.ERROR("Errors occurred while importing data:"))
            for error in failures:
                logger.info(
                    " ".join(
                        [
                            self.style.ERROR("[ERROR]"),
                            f'{error["channel"]} - {error["item"]}: {error["error"]}',
                        ]
                    )
                )
            if updates > 0:
                logger.info(
                    self.style.WARNING(f"Imported {updates} new releases despite this")
                )
        else:
            if updates > 0:
                cache.delete("stat_total_size")
                cache.delete("stat_total_files")
                cache.delete("stat_month_files")
                logger.info(self.style.SUCCESS(f"Imported {updates} new releases"))
            else:
                logger.info(self.style.SUCCESS("No new imports"))
