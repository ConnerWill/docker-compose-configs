#! /usr/bin/env python3
import logging
import re
import time

import odyseescraper
from django.core.management.base import BaseCommand, CommandError
from django.db import models

logger = logging.getLogger("tag")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Runs tagging rules against every release in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes instead of actually committing them",
        )

    def apply_tags(self, releases, options):
        failures = []
        changes = []
        modified_set = set()
        # Before we do costly stuff, start the clock
        starttime = time.perf_counter()
        release_tag_map = {}  # Store precomputed tags for each release
        for release in releases:
            release_tag_map[release.id] = {tag.id for tag in release.tags.all()}
        release_rule_map = {}  # Store precomputed rules for each release
        for release in releases:
            release_rule_map[release.id] = {rule.id for rule in release.tag_rules.all()}
        reflags = re.IGNORECASE
        if int(options["verbosity"]) > 1:
            logger.info(
                f"{(time.perf_counter() - starttime):2f}s - Mapping tags and rules for {len(releases)} releases"
            )
        # Yeah I know this scales multidimensionally based on how big the releases list is and the taggingrule list is
        # This command is written assuming that's not an issue. Realistically, this should be done at time of release import,
        # but having this functionality in place is good for if you have to edit/redact a title or implement a tagging rule
        # in light of a surge of new releases or something.
        for taggingrule in odyseescraper.models.TaggingRule.objects.all():
            tag_starttime = time.perf_counter()
            # Precompile regex
            title_regex = re.compile(taggingrule.title_regex, flags=reflags)
            description_regex = re.compile(
                taggingrule.description_regex, flags=reflags | re.MULTILINE
            )
            channel_regex = re.compile(taggingrule.channel_regex, flags=reflags)
            license_regex = re.compile(taggingrule.license_regex, flags=reflags)
            if int(options["verbosity"]) > 2:
                logger.info(f"  {taggingrule}")
                logger.info(f"  t {taggingrule.title_regex}")
                logger.info(f"  d {taggingrule.description_regex}")
                logger.info(f"  c {taggingrule.channel_regex}")
                logger.info(f"  l {taggingrule.license_regex}")
                logger.info(f"  g {taggingrule.required_tag}")
            for release in releases:
                try:
                    if (
                        (
                            taggingrule.title_regex
                            and not title_regex.match(release.name)
                        )
                        or (
                            taggingrule.description_regex
                            and not description_regex.search(release.description)
                        )
                        or (
                            taggingrule.license_regex
                            and not license_regex.search(release.license)
                        )
                        or (
                            taggingrule.channel_regex
                            and not channel_regex.match(release.channel.handle)
                        )
                        or (
                            taggingrule.required_tag_id
                            and not taggingrule.required_tag_id
                            in release_tag_map[release.id]
                        )
                    ):
                        # We fall to this code path if the object does not meet this tag rule
                        # So we should remove it
                        if taggingrule.id in release_rule_map[release.id]:
                            if int(options["verbosity"]) > 2:
                                logger.info(f"   - {str(release)}")
                            changes.append(
                                " ".join(
                                    [
                                        " -",
                                        self.style.ERROR(f"[{str(taggingrule.tag)}]"),
                                        f"({str(taggingrule)})",
                                        f"{str(release.channel)} - {str(release)}",
                                    ]
                                )
                            )
                            modified_set.add(release)
                            if not options["dry_run"]:
                                release.tag_rules.remove(taggingrule)
                    elif not taggingrule.id in release_rule_map[release.id]:
                        # We've met all the conditions for this rule and don't have it, so let's add it
                        if int(options["verbosity"]) > 2:
                            logger.info(f"   + {str(release)}")
                        changes.append(
                            " ".join(
                                [
                                    " +",
                                    self.style.SUCCESS(f"[{str(taggingrule.tag)}]"),
                                    f"({str(taggingrule)})",
                                    f"{str(release.channel)} - {str(release)}",
                                ]
                            )
                        )
                        modified_set.add(release)
                        if not options["dry_run"]:
                            release.tag_rules.add(taggingrule)
                    else:
                        # We're all set
                        continue
                except Exception as e:
                    logger.info(
                        self.style.WARNING(
                            f"Failed to apply rule {str(taggingrule.name)}: {e}"
                        )
                    )
                    failures.append(
                        {"release": str(release), "rule": taggingrule.name, "error": e}
                    )
            elapsed_time = time.perf_counter() - tag_starttime
            if int(options["verbosity"]) > 1:
                logger.info(f"{elapsed_time:2f}s - {str(taggingrule)}")
            elif elapsed_time > 0.1:
                logger.info(
                    " ".join(
                        [
                            self.style.WARNING("[WARNING]"),
                            f"Rule took {elapsed_time:2f}s to run: {str(taggingrule)}",
                        ]
                    )
                )
        # Now, return our information
        elapsed_time = time.perf_counter() - starttime
        return len(modified_set), failures, changes, elapsed_time, list(modified_set)

    def save_all(self, releases):
        for release in releases:
            release.save()

    def handle(self, *args, **options):
        starttime = time.perf_counter()
        if options["dry_run"]:
            logger.info("Dry-running tagging rules...")
        else:
            logger.info("Tagging releases...")
        # To aid in performance, query our releases once instead of a bunch of times for no reason
        # Additionally, prefetch related resources so we can iterate over them faster
        releases = (
            odyseescraper.models.OdyseeRelease.objects.select_related("channel")
            .prefetch_related("tag_rules")
            .prefetch_related("tags")
            .prefetch_related("manual_tags")
            .prefetch_related("blacklisted_tags")
        )
        if not options["dry_run"]:
            logger.info("Refreshing tagging cache on all releases...")
            for release in releases:
                release.update_tags()
        # Quick perf note
        if int(options["verbosity"]) > 1:
            logger.info(
                f"{(time.perf_counter() - starttime):2f}s - Data prefetch and sanity chehck"
            )
        # Set up some variables in this scope so we can change them later
        total_updates = 0
        updates = 1
        failures = []
        changes = []
        to_save = []
        elapsed_time = 0
        try:
            while updates > 0:
                if int(options["verbosity"]) > 1:
                    logger.info("Beginning iteration of tagging")
                # We repeat this to handle recursive tag dependencies
                # Because we only ever append tags, not remove, this is effectively
                # a breadth-first tagging algo, which is guaranteed to complete
                u, f, c, e, m = self.apply_tags(releases=releases, options=options)
                total_updates += u
                updates = u
                failures += f
                changes += c
                elapsed_time += e
                # Overwrite the remaining list of releases with the set of objects
                # that were modified.
                releases = m
                # Also append them to a list so we can save() them later
                to_save += m
                # Break out of the loop at the first iteration if we're dry-running
                # otherwise we'd just sit here and spin forever, not making changes
                if options["dry_run"]:
                    break
                else:
                    #
                    # NOTE: This is a very important step
                    # TODO: Make this NOT a very important step through intelligent signalling
                    # We rely on the OdyseeRelease object's save() method here to update its search
                    # vector, which has changed now that we've modified its tags.
                    #
                    # It's important we do this here so we update the list of tags for all releases.
                    # That way TaggingRules that depend on other tags are impacted appropriately
                    if int(options["verbosity"]) > 1:
                        logger.info(f"Saving {len(m)} modified models...")
                    self.save_all(m)
            if not options["dry_run"] and total_updates < 1:
                logger.info("No tags to update -- refreshing release caches...")
                self.save_all(releases)
        except KeyboardInterrupt:
            logger.info(self.style.WARNING("Interrupt received"))
        if changes:
            changes.sort()
            for change in changes:
                logger.info(change)
        if failures:
            logger.info(self.style.ERROR("Errors occurred while tagging:"))
            for error in failures:
                logger.info(
                    self.style.ERROR(
                        f'{error["rule"]} - {error["release"]} - {error["error"]}'
                    )
                )
            if total_updates > 0:
                logger.info(
                    self.style.WARNING(
                        f"Applied {total_updates} tagging rules despite this"
                    )
                )
        else:
            if total_updates > 0:
                logger.info(
                    self.style.SUCCESS(
                        f"Applied {total_updates} tagging rules to releases"
                    )
                )
            else:
                logger.info(self.style.SUCCESS(f"No new tagging rules applied"))
        if options["dry_run"] and total_updates > 0:
            logger.info(
                self.style.WARNING(
                    f"This run was a dry-run only; no changes were made. Invoke without the --dry-run flag to commit"
                )
            )
        if int(options["verbosity"]) > 1:
            logger.info(
                f"Took {(time.perf_counter() - starttime):2f}s to complete work"
            )
