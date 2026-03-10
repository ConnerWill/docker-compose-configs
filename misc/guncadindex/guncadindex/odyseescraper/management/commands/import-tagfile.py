#! /usr/bin/env python3
import re

import odyseescraper
import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import models


class Command(BaseCommand):
    help = "Imports a .yml file of tags and rules into the instance"

    def add_arguments(self, parser):
        parser.add_argument("file", help="The file to import")

    def import_tag(self, tag, slug="", category=None):
        """
        Takes the YAML construction of a tag and imports it
        Returns a tuple:
            Bool                Did we operated successfully?
            Bool/Exception      A bool if we operated successfully determining if we created a new object or not
                                Otherwise, the exception if we failed.
        """
        try:
            obj, created = odyseescraper.models.Tag.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": tag.get("name"),
                    "description": tag.get("description") or "No description provided",
                    "custom_color": tag.get("color") or "",
                    "category": category,
                },
            )
            if not created:
                obj.save()
            return True, created
        except Exception as e:
            return False, e

    def import_rules_from_tag(self, tag, slug, idmap):
        """
        Takes the YAML construction of a tag and imports it. Also needs an idmap for name yaml name -> DB name conversions
        Returns a tuple:
            Bool                Did we operated successfully?
            Int/Exception       How many new objects we created if we succeeded
                                Otherwise, the exception if we failed.
            List                A list of strings of the names of rules we added
        """
        rules = set()
        try:
            updates = 0
            applied_tag = odyseescraper.models.Tag.objects.filter(slug=slug).first()
            # Add rules for lines in the description that are just the slug
            rulename = (
                f"IMPORT - {tag.get('name')} - Description contains slug - {slug}"
            )
            rules.add(rulename)
            obj, created = odyseescraper.models.TaggingRule.objects.update_or_create(
                name=rulename,
                defaults={
                    "description_regex": f"^{slug}$",
                    "tag": applied_tag,
                },
            )
            if created:
                self.stdout.write(
                    " ".join(
                        [
                            self.style.SUCCESS("[RULE]"),
                            f"{str(applied_tag)} - Slug match in description",
                        ]
                    )
                )
                updates += 1
            # And one for the name
            rulename = f"IMPORT - {tag.get('name')} - Description contains name - {tag.get('name')}"
            rules.add(rulename)
            obj, created = odyseescraper.models.TaggingRule.objects.update_or_create(
                name=rulename,
                defaults={
                    "description_regex": f"^{tag.get('name')}$",
                    "tag": applied_tag,
                },
            )
            if created:
                self.stdout.write(
                    " ".join(
                        [
                            self.style.SUCCESS("[RULE]"),
                            f"{str(applied_tag)} - Name match in description",
                        ]
                    )
                )
                updates += 1
            # Iterate over exclusive rules
            for rule, ruledata in tag.get("rules", {}).items():
                rulename = f"IMPORT - {tag.get('name')} - {rule}"
                rules.add(rulename)
                obj, created = (
                    odyseescraper.models.TaggingRule.objects.update_or_create(
                        name=rulename,
                        defaults={
                            "title_regex": ruledata.get("title_regex", ""),
                            "description_regex": ruledata.get("description_regex", ""),
                            "channel_regex": ruledata.get("channel_regex", ""),
                            "tag": applied_tag,
                        },
                    )
                )
                if created:
                    self.stdout.write(
                        " ".join(
                            [
                                self.style.SUCCESS("[RULE]"),
                                f"{str(applied_tag)} - {rule}",
                            ]
                        )
                    )
                    updates += 1
            # Then fix up lbry tags
            for lbry_tag in tag.get("lbry_tags", []):
                rulename = f"IMPORT - {tag.get('name')} - lbry-tag {lbry_tag}"
                rules.add(rulename)
                obj, created = (
                    odyseescraper.models.TaggingRule.objects.update_or_create(
                        name=rulename,
                        defaults={
                            "title_regex": "",
                            "description_regex": r"^LBRY Tags:.*\s"
                            + lbry_tag
                            + r"\s*(;.*)?$",
                            "channel_regex": "",
                            "tag": applied_tag,
                        },
                    )
                )
                if created:
                    self.stdout.write(
                        " ".join(
                            [
                                self.style.SUCCESS("[LBRY]"),
                                f"{str(applied_tag)} - lbry-tag {lbry_tag}",
                            ]
                        )
                    )
                    updates += 1
            # Additional rules for license text
            for license in tag.get("licenses", []):
                rulename = f"IMPORT - {tag.get('name')} - lbry-tag {license}"
                rules.add(rulename)
                obj, created = (
                    odyseescraper.models.TaggingRule.objects.update_or_create(
                        name=rulename,
                        defaults={
                            "title_regex": "",
                            "license_regex": license,
                            "description_regex": "",
                            "channel_regex": "",
                            "tag": applied_tag,
                        },
                    )
                )
                if created:
                    self.stdout.write(
                        " ".join(
                            [
                                self.style.SUCCESS("[LICENSE]"),
                                f"{str(applied_tag)} - license-text {license}",
                            ]
                        )
                    )
                    updates += 1
            # Then fix up implies directives
            for impliedtag in tag.get("implies", []):
                required_tag = odyseescraper.models.Tag.objects.filter(
                    slug=slug
                ).first()
                implied_tag = odyseescraper.models.Tag.objects.filter(
                    slug=impliedtag
                ).first()
                rulename = f"IMPORT - {tag.get('name')} -> {str(implied_tag)}"
                rules.add(rulename)
                obj, created = (
                    odyseescraper.models.TaggingRule.objects.update_or_create(
                        name=rulename,
                        defaults={
                            "required_tag": required_tag,
                            "tag": implied_tag,
                        },
                    )
                )
                if created:
                    self.stdout.write(
                        " ".join(
                            [
                                self.style.SUCCESS("[IMPL]"),
                                f"{str(required_tag)} -> {str(implied_tag)}",
                            ]
                        )
                    )
                    updates += 1
            return True, updates, rules
        except Exception as e:
            return False, e, set()

    def handle(self, *args, **options):
        updates = 0
        failures = []
        with open(options["file"]) as stream:
            try:
                tagfile = yaml.safe_load(stream)
                self.stdout.write("Importing tags...")
                idmap = {}
                categorymap = {}
                rulelist = set()
                # First pass builds up our categories
                for category, categorydata in tagfile.items():
                    category_obj, created = (
                        odyseescraper.models.TagCategory.objects.update_or_create(
                            name=categorydata.get("name", category),
                            defaults={
                                "color": categorydata.get("color", ""),
                                "description": categorydata.get(
                                    "description", "No description for this category"
                                ),
                                "useforweighting": categorydata.get(
                                    "use_for_weighting", True
                                ),
                            },
                        )
                    )
                    categorymap[category] = category_obj
                    if created:
                        self.stdout.write(
                            " ".join(
                                [self.style.SUCCESS("[CATEGORY]"), f"{str(category)}"]
                            )
                        )
                        updates += 1
                # Next pass iterates over all the categories and builds up tags
                for category, categorydata in tagfile.items():
                    category_obj = categorymap[category]
                    for tag, tagdata in categorydata.get("tags", {}).items():
                        idmap[tag] = tagdata.get("name")
                        success, created = self.import_tag(
                            tag=tagdata, slug=tag, category=category_obj
                        )
                        if not success:
                            self.stdout.write(
                                " ".join(
                                    [
                                        self.style.ERROR("[ERROR]"),
                                        f"{str(tag)}: {created}",
                                    ]
                                )
                            )
                            failures.append({"tag": tag, "error": created})
                        elif created:
                            self.stdout.write(
                                " ".join([self.style.SUCCESS("[TAG]"), f"{str(tag)}"])
                            )
                            updates += 1
                        elif int(options["verbosity"]) > 1:
                            self.stdout.write(
                                " ".join(
                                    [
                                        self.style.SUCCESS("[OK]"),
                                        f"Already have tag: {str(tag)}",
                                    ]
                                )
                            )
                # Next, pull in rules
                self.stdout.write("Importing rules and implies...")
                for category, categorydata in tagfile.items():
                    category_obj = categorymap[category]
                    for tag, tagdata in categorydata.get("tags", {}).items():
                        success, created, rulenames = self.import_rules_from_tag(
                            tag=tagdata, slug=tag, idmap=idmap
                        )
                        rulelist.update(rulenames)
                        if not success:
                            self.stdout.write(
                                " ".join(
                                    [
                                        self.style.ERROR("[ERROR]"),
                                        f"Rules for {str(tag)}: {created}",
                                    ]
                                )
                            )
                            failures.append({"tag": tag, "error": created})
                        elif created > 0:
                            updates += created
                        elif int(options["verbosity"]) > 1:
                            self.stdout.write(
                                " ".join(
                                    [
                                        self.style.SUCCESS("[OK]"),
                                        f"Already have all rules for tag: {str(tag)}",
                                    ]
                                )
                            )
                # Lastly, we're going to make a pass to remove all rules
                # starting with IMPORT that aren't currently in the list
                self.stdout.write("Cleaning up removed rules...")
                rules = odyseescraper.models.TaggingRule.objects.exclude(
                    name__in=rulelist
                ).filter(name__istartswith="IMPORT")
                for rule in rules:
                    self.stdout.write(
                        " ".join(
                            [
                                self.style.SUCCESS("[DELETE]"),
                                f"Cleaning up removed rule: {rule}",
                            ]
                        )
                    )
                    rule.delete()
            except yaml.YAMLError as exc:
                print(exc)
        if failures:
            self.stdout.write(
                self.style.ERROR("Errors occurred while importing tagfile:")
            )
            for error in failures:
                self.stdout.write(self.style.ERROR(f'{error["tag"]}: {error["error"]}'))
            if updates > 0:
                self.stdout.write(
                    self.style.WARNING(f"Made {updates} changes despite this")
                )
        else:
            if updates > 0:
                self.stdout.write(self.style.SUCCESS(f"Made {updates} changes"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"No new tags or rules added, some may have been updated"
                    )
                )
