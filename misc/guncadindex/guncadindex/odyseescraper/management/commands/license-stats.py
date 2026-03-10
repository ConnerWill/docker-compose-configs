from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from odyseescraper.models import OdyseeRelease, TaggingRule


class Command(BaseCommand):  # pragma: no cover
    help = "Shows outstanding unhandled license fields"

    def handle(self, *args, **options):
        license_rules = TaggingRule.objects.exclude(license_regex="").values_list(
            "id", flat=True
        )
        license_releases = OdyseeRelease.objects.exclude(license="None")
        unhandled_releases = license_releases.exclude(
            tag_rules__in=license_rules
        ).distinct()
        if unhandled_releases.count() > 0:
            license_stats = (
                unhandled_releases.values("license")
                .annotate(count=Count("id"))
                .order_by("-count")
            )

            total_count = unhandled_releases.count()
            self.stdout.write(f"{license_releases.count()} releases with licenses")
            self.stdout.write(f"{total_count} with unhandled license strings")

            for entry in license_stats:
                self.stdout.write(f"{entry['count']:5}  \"{entry['license']}\"")
        else:
            self.stdout.write("All known licenses have associated TaggingRules")
