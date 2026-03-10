from crowdsource.models import TagSuggestion
from django.core.management.base import BaseCommand
from django.db.models import Count, F, Window
from django.db.models.functions import PercentRank


class Command(BaseCommand):  # pragma: no cover
    help = "Display some of the highest-suggested TagSuggestions. Suggestions must have at least 3 occurrences to be displayed."

    def add_arguments(self, parser):
        parser.add_argument(
            "percent",
            type=int,
            nargs="?",
            default=10,
            help="Show the top N percent of suggested tags (default: 10)",
        )

    def handle(self, *args, **options):
        n = options["percent"]
        totalcount = TagSuggestion.objects.count()
        uniquecount = TagSuggestion.objects.values("tag").distinct().count()
        qs = (
            TagSuggestion.objects.values("tag")
            .annotate(count=Count("id"))
            .filter(count__gte=3)
            .annotate(
                percentile=Window(expression=PercentRank(), order_by=F("count").desc())
            )
            .filter(percentile__lte=n / 100)
            .order_by("-count")
        )
        self.stdout.write(f"{'Tag':<30} {'Count':>8} {'Percentile':>12}")
        self.stdout.write("-" * 52)
        for suggestion in qs:
            tag = suggestion.get("tag")
            count = suggestion.get("count")
            percentile = suggestion.get("percentile") * 100
            self.stdout.write(f"{tag:<30} {count:>8} {percentile:>11.3f}%")
        self.stdout.write("-" * 52)
        self.stdout.write(
            f"{totalcount} records, {uniquecount} suggestions, {qs.count()} displayed here"
        )
