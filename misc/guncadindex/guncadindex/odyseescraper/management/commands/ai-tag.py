import json
import logging
import os
import re
import time

from crowdsource.models import TagSuggestion
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from odyseescraper.models import OdyseeRelease, Tag
from openai import OpenAI

logger = logging.getLogger("ai-tag")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Runs some releases by the linked LLM to see what tags they should have"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes instead of actually committing them",
        )
        parser.add_argument(
            "--print-prompts",
            action="store_true",
            help="Print prompts as we generate them",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5,
            help="How many releases to hit at once. Defaults to 5.",
        )
        parser.add_argument(
            "--retag",
            action="store_true",
            help="If we're out of stuff that has yet to receive AI tags, retag some existing releases",
        )

    def retry(self, fn, max_attempts=5, delay=0):
        for attempt in range(max_attempts):
            try:
                return fn()
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                else:
                    raise

    def _validate_list_of_strings(self, obj):
        # Attempt to jsonify it
        completion_json = json.loads(obj)
        # Make sure it's a list of strings
        if not isinstance(completion_json, list):
            raise ValueError("Expected a list")
        if not all(isinstance(item, str) for item in completion_json):
            raise ValueError(f"All items must be of type str")
        # If we made it this far, we're good
        return completion_json

    def _get_llm_response(self, prompt, llm, model):
        # Define a prompt for suggestions
        suggestion_prompt = """
        Now, return an array of tags (the pretty name, not slugs) that you think should be added to this YAML file in order to give you the options to properly describe it.

        Keep the following in mind:
         * You are not required to make suggestions. An empty array is an appropriate response
         * Make a suggestion only if you feel the release is not adequately described by its current tags
         * Be mindful of the categories in the YAML file, and try to abide by them
        """
        # Get our response
        completion = llm.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        # Try and jsonify it
        tag_votes = self._validate_list_of_strings(
            completion.choices[0].message.content
        )
        # Now prod it for tag suggestions
        completion2 = llm.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": completion.choices[0].message.content},
                {"role": "user", "content": suggestion_prompt},
            ],
        )
        tag_suggestions = self._validate_list_of_strings(
            completion2.choices[0].message.content
        )
        # We're gucci, return our array
        return tag_votes, tag_suggestions

    def get_response(self, prompt, llm, model):
        try:
            return self.retry(fn=lambda: self._get_llm_response(prompt, llm, model))
        except Exception as e:
            return [], []

    def handle(self, *args, **options):
        # Get our AI set up
        # If we add support for other LLMs, we need to add them to the list here
        if apikey := os.getenv("GUNCAD_AI_XAI_API_KEY", False):
            llm = OpenAI(
                api_key=apikey,
                base_url="https://api.x.ai/v1",
            )
            model = "grok-3-mini-beta"
            prompt = """
            Here are the details for a release in a search engine of 3D-printable and DIY firearms and accessories:

            Title: {release.name}
            Current tags: {release.tag_list}
            Author: {release.channel.name}
            Released: {release.released}
            Last Updated: {release.last_updated}
            Thumbnail: {release.thumbnail}
            Size: {release.size_friendly}
            Description:
            ```
            {release.description}
            ```

            Using the contents of the following YAML file, please select an array of tags (by slug) that best fit this release.
            Return a valid, well-formatted JSON array. If none are suitable, return an empty array. Do not wrap your response in markdown:

            ```yaml
            {tagfile}
            ```

            Keep the following in mind:
             * Not everything is a gun
             * Things that aren't guns are not necessarily accessories or furniture
             * Do not add tags for Release Group
             * Only add tags that you're 100% sure of
             * Don't tag individual furniture features of guns. A PDW should not get "Pistol Brace", for example
             * Pay VERY close attention to the description of each tag, as they may be counterintuitive. For example, a Glock PDW is a PCC, not a Handgun
             * This release may have a short, terrible description. You don't have to tag it if you're unsure -- an empty array is a perfectly valid response
             * Meta tags can have their definitions stretched a bit -- Alphas are Betas, etc.
             * Single-stack Glocks and double-stack Glocks are NOT the same platform
             * All M16s, M4s, etc. are ALL AR-15s

            If you need a tag that's not currently in this YAML file, you will be asked in a second to suggest it. Do not add its closest neighbor.
            """
        else:
            logger.info(
                self.style.ERROR(
                    "Unable to configure any LLM. See documentation. Exiting..."
                )
            )
            return
        # Start work
        starttime = time.perf_counter()
        if options["dry_run"]:
            logger.info("Dry-running AI tagging...")
        else:
            logger.info("Tagging releases...")
        # To aid in performance, query our releases once instead of a bunch of times for no reason
        # Additionally, prefetch related resources so we can iterate over them faster
        releases = (
            # Get some releases that we haven't tagged yet
            OdyseeRelease.objects.visible()
            .filter(ai_tags=None)
            .prefetch_comprehensive()
            .order_by("?")[: options["batch_size"]]
        )
        if not releases:
            if options["retag"]:
                releases = (
                    # Failing that, just go over some stuff we've already hit
                    # Yaknow, to make sure it's still accurate
                    OdyseeRelease.objects.visible()
                    .prefetch_comprehensive()
                    .order_by("?")[: options["batch_size"]]
                )
            else:
                logger.info("Nothing to do")
                return
        if not options["dry_run"]:
            logger.info("Refreshing tagging cache on all releases...")
            for release in releases:
                release.update_tags()
        # Quick perf note
        if int(options["verbosity"]) > 1:
            logger.info(
                f"{(time.perf_counter() - starttime):2f}s - Data prefetch and sanity chehck"
            )
        try:
            with open("default-tags.yml", "r") as tagfile:
                defaulttags = tagfile.read()
            logger.info(f"Tagging {releases.count()} releases")
            # TODO: This is all serial, but 99% of our time is spent just waiting for
            # the LLM. We could parallelize up to some request limit.
            for release in releases:
                focusedprompt = prompt.format(tagfile=defaulttags, release=release)
                if options["print_prompts"]:
                    print(focusedprompt)
                logger.info(
                    " ".join(
                        [
                            self.style.WARNING("[...]"),
                            f"{release.channel.name} - {release.name}",
                        ]
                    )
                )
                new_tags, suggested_tags = self.get_response(
                    prompt=focusedprompt,
                    llm=llm,
                    model=os.getenv("GUNCAD_AI_MODEL", model),
                )
                if new_tags:
                    logger.info(
                        " ".join(
                            [
                                self.style.SUCCESS("[TAG]"),
                                f"AI responded with tags: {new_tags}",
                            ]
                        )
                    )
                else:
                    logger.info(
                        " ".join(
                            [
                                self.style.WARNING("[SKIP]"),
                                f"AI responded with no new tags",
                            ]
                        )
                    )
                if suggested_tags:
                    logger.info(
                        " ".join(
                            [
                                self.style.SUCCESS("[SUG]"),
                                f"AI responded with suggestions: {suggested_tags}",
                            ]
                        )
                    )
                if not options["dry_run"]:
                    release.ai_tags.clear()
                    for tag in new_tags:
                        try:
                            tag_object = Tag.objects.filter(slug=tag).first()
                            if not tag_object:
                                continue
                            release.ai_tags.add(tag_object)
                        except Exception as e:
                            logger.info(
                                self.style.ERROR(
                                    f"Exception when applying tag {tag}: {e}"
                                )
                            )
                    release.save()
                    for tag in suggested_tags:
                        try:
                            TagSuggestion.objects.create(
                                source=2, tag=tag, release=release
                            )
                        except Exception as e:
                            print(f"Error adding tag suggestion: {e}")
                            continue

        except KeyboardInterrupt:
            logger.info(self.style.WARNING("Interrupt received"))
        # Return
        logger.info(f"Took {(time.perf_counter() - starttime):2f}s to complete work")
