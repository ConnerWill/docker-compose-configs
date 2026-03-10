import itertools
import logging
import re
import time
import traceback
import uuid
from datetime import datetime, timezone

import odyseescraper
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from odyseescraper.models import OdyseeChannel, OdyseeRelease, TaggingRule

logger = logging.getLogger("discover")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Looks for OdyseeChannel objects that could potentially have GunCAD content and adds them to the index"

    # This is a list of tags we look for when we discover new channels.
    # Try to populate this list with only tags that are unambiguously GunCAD. We should
    # urge users to use something like "3d2a", "3dpg", or "guncad" for unambiguous adds
    #
    # Check out ./manage.py analyze-channel-tags if you'd like to see what the tags in
    # the current dataset look like. They might be useful for more discovery
    criteria_tags = [
        "2a3d",
        "2aprintdepot",
        "37mm",
        "3d2a",
        "3d arms",
        "3dg",
        "3dgun",
        "3dguns",
        "3d printable gun",
        "3dprintedweapons",
        "3d print guns",
        "3d printing gun",
        "3dpg",
        "40mm",
        "9mm",
        "arewecoolyet?",
        "awcy",
        "blc",
        "cantstopthesignal",
        "db9",
        "db9 alloy",
        "dd",
        "dd17.2",
        "dd19.2",
        "defcad",
        "deterrence dispensed",
        "diy guns",
        "ez22",
        "fgc9",
        "fgc-9",
        "firearm",
        "firearms",
        "fmda",
        # sic
        "foscad",
        "fosscad",
        "g17",
        "g19",
        "g22",
        "gatalog",
        # sic
        "gatalogue",
        "ghost guns",
        "glock",
        "grenade",
        "groznt",
        "gun",
        "guncad",
        "guncadindex",
        "gun design",
        "guns",
        "gunsmithing",
        "gun tuning",
        "hd22",
        "hd22c",
        "mod9",
        "mod9v2",
        "mp5",
        "notaglock",
        "nylaug",
        "out of battery",
        "p80",
        "pewpew",
        "pistol",
        "pistols",
        "polymer80",
        "printa22",
        "printyour2a",
        "py2a",
        "rehd22c",
        "second amendment",
        "shooting",
        "ss80",
        # sic
        "suppresor",
        "weapons",
        "wtf-9",
    ]
    # Comparably, this is a list of tags that we look for when analyzing a
    # potential channel's releases. If it matches one of these tags, we'll
    # add the channel even if it doesn't match one of the taggingrules exactly
    shibboleth_tags = ["3d2a", "3dpg", "fosscad", "guncad", "guncadindex"]

    # Below this number of original file claims, we don't even look at them
    criteria_min_claims = 1

    # Posting more than this rate of reposts will get you ignored...
    criteria_max_duplicate_rate = 0.75
    # ...and if you have at least this many releases, your channel is then blacklisted
    criteria_dupe_rate_threshold = 5

    def blacklist_channel(self, handle, claimid, reason="Unspecified"):
        return OdyseeChannel.objects.update_or_create(
            handle=handle,
            defaults={
                "claimid": claimid,
                "disabled": True,
                "name": f"Discovered inadequate channel: {handle}",
                "description": f"This channel was ruled inadequate by the discoverer. If this is in error, please reenable this channel and wait for the next scrape job.\n\nThe reason given was: {reason}",
            },
        )

    def add_channel(self, handle, claimid):
        time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return OdyseeChannel.objects.update_or_create(
            handle=handle,
            defaults={
                "claimid": claimid,
                "disabled": False,
                "name": f"{handle}",
                "description": f"This channel was automatically imported by the discoverer job on: {time}",
            },
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes instead of actually committing them",
        )
        parser.add_argument(
            "--the-whole-fucking-blockchain",
            action="store_true",
            help="Instead of doing the smart thing and filtering by channels that have reasonable tags, just start from the most recent channel on the chain and fucking drill down until we hit the end of it. This should never be run more than like once every couple months by hand, cuz this fucker's gonna take HOURS.",
        )

    def discover_channels(self, criteria_tags=[], minimum_taggingrules=2, **options):
        if cache.get("discover_lock"):
            logger.info(
                self.style.WARNING(
                    "Refusing to execute due to existing lock -- is another discover job running?"
                )
            )
            return
        else:
            cache.set("discover_lock", True, 60)
        starttime = time.perf_counter()
        updates = 0
        failures = []
        channelmap = {
            channel.claimid: channel.handle
            for channel in OdyseeChannel.objects.exclude(claimid__exact="")
        }
        idlist = [key for key in channelmap.keys()]
        if int(options["verbosity"]) > 1:
            logger.info(
                f"{(time.perf_counter() - starttime):2f}s - Mapped {len(idlist)} existing channels"
            )
        taggingrules = TaggingRule.objects.all()
        seen_channels = set()
        for channelid, channeldata in itertools.chain(
            odyseescraper.odysee.channel_search_by_streams_with_tag(
                tags=criteria_tags, not_channel_ids=idlist
            ),
            # Removed because it's imperformant and I think we've caught everyone we can this way for right now
            # May revisit in the future
            # odyseescraper.odysee.channel_search(
            #    tags=criteria_tags, not_channel_ids=idlist
            # ),
            odyseescraper.odysee.get_one_degree(ids=idlist),
        ):
            # First, touch up the lock
            cache.set("discover_lock", True, 120)
            if channelid in seen_channels:
                continue
            else:
                seen_channels.add(channelid)
            handle = (
                channeldata.get("canonical_url", "")
                .replace("lbry://", "")
                .replace("#", ":")
            )
            if int(options["verbosity"]) > 2:
                logger.info(f"Investigating channel: {handle}...")
            try:
                #
                # We have four conditions we want this channel to pass:
                #
                # 1. It must have a GunCAD tag in its description (already met); and
                # 2. The channel is not currently in the index (already met); and
                # 3. It has a rate of duplicate claims with stuff in the Index (as evidenced by filehash) of less than some percentage; and
                # 4. At least one of its claims would be tagged by n autotagging rules or match a shibboleth
                #
                # First, let's claim search them and then look at the hashes
                claims = odyseescraper.odysee.claim_search(handle)
                if len(claims) < self.criteria_min_claims:
                    if int(options["verbosity"]) > 2:
                        logger.info(
                            f" Skipping channel {handle} due to low original post rate..."
                        )
                    continue
                elif int(options["verbosity"]) > 2:
                    logger.info(f" Channel {handle} has {len(claims)} releases...")
                claimhashes = [
                    claim.get("value", {}).get("source", {}).get("hash")
                    for claim in claims.values()
                ]
                collisions = OdyseeRelease.objects.filter(
                    sha384sum__in=claimhashes
                ).count()
                duperate = collisions / len(claimhashes)
                if collisions > len(claimhashes) * self.criteria_max_duplicate_rate:
                    if len(claims) > self.criteria_dupe_rate_threshold:
                        if not options["dry_run"]:
                            self.blacklist_channel(
                                handle=handle,
                                claimid=channelid,
                                reason=f"High rate of duplicates ({int(duperate*100)}%)",
                            )
                        logger.info(
                            " ".join(
                                [
                                    self.style.ERROR("[BLACKLIST]"),
                                    f"{handle} - high rate of duplicates ({int(duperate*100)}%)",
                                ]
                            )
                        )
                    else:
                        logger.info(
                            " ".join(
                                [
                                    self.style.WARNING("[SKIPPED]"),
                                    f"{handle} - high rate of duplicates ({int(duperate*100)}%) but low claim count ({len(claims)})",
                                ]
                            )
                        )
                    continue
                elif int(options["verbosity"]) > 2:
                    logger.info(
                        f" Channel {handle} has a duplication rate of {int(duperate*100)}%..."
                    )
                # Next, we should iterate through their claims looking for one that matches *any*
                # TaggingRule.
                matches_shibboleth = False
                matches_taggingrules = 0
                for taggingrule in taggingrules:
                    if taggingrule.license_regex:
                        # Ignore license-related tagging rules
                        continue
                    title_regex = re.compile(
                        taggingrule.title_regex, flags=re.IGNORECASE
                    )
                    description_regex = re.compile(
                        taggingrule.description_regex,
                        flags=re.IGNORECASE | re.MULTILINE,
                    )
                    channel_regex = re.compile(
                        taggingrule.channel_regex, flags=re.IGNORECASE
                    )
                    for release, data in claims.items():
                        value = data.get("value")
                        description = value.get("description", "")
                        if value.get("tags", False):
                            # Short-circuit check for shibboleth tags
                            for tag in value.get("tags", []):
                                if tag in self.shibboleth_tags:
                                    matches_shibboleth = True
                                    if int(options["verbosity"]) > 2:
                                        logger.info(
                                            f" Matched shibboleth against their release {value.get('title')}..."
                                        )
                                    break
                            description += "\n\nLBRY Tags: " + "; ".join(
                                value.get("tags", [])
                            )
                        if (
                            (
                                taggingrule.title_regex
                                and not title_regex.match(value.get("title", ""))
                            )
                            or (
                                taggingrule.description_regex
                                and not description_regex.search(
                                    value.get("description", "")
                                )
                            )
                            or (
                                taggingrule.channel_regex
                                and not channel_regex.match(handle)
                            )
                            or taggingrule.required_tag
                        ):
                            continue
                        else:
                            if int(options["verbosity"]) > 2:
                                logger.info(
                                    f" Matched taggingrule {taggingrule.name} against their release {value.get('title')}..."
                                )
                            matches_taggingrules += 1
                            break
                    if (
                        matches_shibboleth
                        or matches_taggingrules > minimum_taggingrules
                    ):
                        break
                if (
                    not matches_shibboleth
                    and not matches_taggingrules >= minimum_taggingrules
                ):
                    logger.info(
                        " ".join(
                            [
                                self.style.WARNING("[SKIPPED]"),
                                f"{handle} - unable to sufficiently tag any of their {len(claimhashes)} releases with {minimum_taggingrules} tags",
                            ]
                        )
                    )
                    continue
                # We've passed all the checks, add them in
                if not options["dry_run"]:
                    self.add_channel(handle=handle, claimid=channelid)
                logger.info(
                    " ".join([self.style.SUCCESS("[NEW CHANNEL]"), f"{handle}"])
                )
                updates += 1
            except Exception as e:
                logger.info(
                    " ".join(
                        [
                            self.style.ERROR("[ERROR]"),
                            f"{handle}: {e}",
                        ]
                    )
                )
                traceback.print_exc()
                failures.append(
                    {
                        "channel": handle,
                        "error": e,
                    }
                )
                continue
            if False:
                logger.info(
                    " ".join(
                        [
                            self.style.SUCCESS("[IMPORT]"),
                            f"{str(channel)} - {value.get('title')}",
                        ]
                    )
                )
                updates += 1

    def handle(self, *args, **options):
        logger.info("Discovering new Odysee channels...")
        starttime = time.perf_counter()
        updates = 0
        failures = []
        try:
            if options["the_whole_fucking_blockchain"]:
                # Do one pass where we look for channels *without* tags and being slightly more scrutinizing
                logger.info(
                    " ".join(
                        [
                            self.style.WARNING("[WARNING]"),
                            f"You are running this tool with --the-whole-fucking-blockchain enabled. It bears repeating: we are about to scour THE WHOLE BLOCKCHAIN. It will take AGES to complete.",
                        ]
                    )
                )
                self.discover_channels(
                    criteria_tags=[], minimum_taggingrules=2, **options
                )
            else:
                # Do one pass looking for channels with tags and being slightly more generous
                self.discover_channels(
                    criteria_tags=self.criteria_tags + self.shibboleth_tags,
                    minimum_taggingrules=1,
                    **options,
                )
        except KeyboardInterrupt:
            logger.info(self.style.WARNING("Interrupt received"))
        finally:
            cache.delete("discover_lock")
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
                            f'{error["channel"]}: {error["error"]}',
                        ]
                    )
                )
            if updates > 0:
                logger.info(
                    self.style.WARNING(f"Imported {updates} new channels despite this")
                )
        else:
            if updates > 0:
                cache.delete("stat_total_channels")
                logger.info(self.style.SUCCESS(f"Imported {updates} new channels"))
            else:
                logger.info(self.style.SUCCESS("No new imports"))
        if options["dry_run"] and updates > 0:
            logger.info(
                self.style.WARNING(
                    f"This run was a dry-run only; no changes were made. Invoke without the --dry-run flag to commit"
                )
            )
