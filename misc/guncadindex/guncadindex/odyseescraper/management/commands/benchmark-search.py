import logging
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandParser
from odyseescraper.models import OdyseeRelease

logger = logging.getLogger("benchmark-search")
logger.setLevel(logging.INFO)


class Command(BaseCommand):  # pragma: no cover
    help = "Benchmark search efficacy with incremental exact-name queries"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "num_queries",
            type=int,
            help="Number of benchmark queries to run",
        )
        parser.add_argument(
            "--top-k",
            type=int,
            default=5,
            help="How many top search results to consider a hit",
        )

    def handle(self, *args, **options):
        self.run_benchmark(
            options["num_queries"],
            options["top_k"],
        )

    def run_benchmark(self, num_queries: int, top_k: int) -> None:
        releases = self._get_random_releases(num_queries)

        rows = []
        char_counts = []
        percent_counts = []

        for release in releases:
            name = (release.name or "").strip()
            if not name:
                continue

            name_len = len(name)
            found = False

            for i in range(1, name_len + 1):
                query = name[:i]

                results = OdyseeRelease.objects.search(query).values_list(
                    "id", flat=True
                )[:top_k]

                if release.id in results:
                    pct = i / name_len
                    char_counts.append(i)
                    percent_counts.append(pct)

                    rows.append(
                        {
                            "id": release.id,
                            "name": name,
                            "chars": i,
                            "pct": pct,
                            "status": "OK",
                        }
                    )

                    logger.info(
                        "SUCCESS id=%s chars=%d (%.1f%%)",
                        release.id,
                        i,
                        100 * pct,
                    )
                    found = True
                    break

            if not found:
                rows.append(
                    {
                        "id": release.id,
                        "name": name,
                        "chars": None,
                        "pct": None,
                        "status": "FAIL",
                    }
                )

                logger.info(
                    "FAILURE id=%s len=%d name=%r",
                    release.id,
                    name_len,
                    name,
                )

        self._dump_results(rows, char_counts, percent_counts, num_queries)

    def _get_random_releases(self, n: int):
        return list(
            OdyseeRelease.objects.visible()
            .exclude(name__isnull=True)
            .exclude(name__exact="")
            .order_by("?")[:n]
        )

    def _percentile(self, data, pct: float):
        if not data:
            return None
        data = sorted(data)
        idx = int(len(data) * pct)
        return data[min(idx, len(data) - 1)]

    def _dump_results(self, rows, char_counts, percent_counts, total):
        logger.info("")
        logger.info("=== SEARCH BENCHMARK RESULTS ===")
        logger.info("Total samples: %d", total)
        logger.info("Successes: %d", len(char_counts))
        logger.info("Failures: %d", total - len(char_counts))
        logger.info("")

        # Sort: successes by pct asc, failures last
        rows = sorted(
            rows,
            key=lambda r: (
                r["pct"] is None,
                r["pct"] if r["pct"] is not None else 1.0,
            ),
        )

        logger.info(
            "| ID                                       | Rslt | Chars | % Used | Name |"
        )
        logger.info(
            "|------------------------------------------|------|-------|--------|------|"
        )

        for r in rows:
            if r["pct"] is None:
                logger.info(
                    "| %s | FAIL |   —   |   —    | %s |",
                    r["id"],
                    r["name"],
                )
            else:
                logger.info(
                    "| %s | OK   | %5d | %6.1f%% | %s |",
                    r["id"],
                    r["chars"],
                    100 * r["pct"],
                    r["name"],
                )

        p50_chars = self._percentile(char_counts, 0.50)
        p95_chars = self._percentile(char_counts, 0.95)
        p50_pct = self._percentile(percent_counts, 0.50)
        p95_pct = self._percentile(percent_counts, 0.95)
        fail_pct = (total - len(char_counts)) / len(char_counts)

        logger.info("")
        logger.info("=== SUMMARY STATS ===")
        logger.info(
            "Failure rate: %.1f%%",
            fail_pct,
        )
        if p50_chars is not None:
            logger.info(
                "p50: %d chars (%.1f%% of name)",
                p50_chars,
                100 * p50_pct,
            )
            logger.info(
                "p95: %d chars (%.1f%% of name)",
                p95_chars,
                100 * p95_pct,
            )
        else:
            logger.info("No successful samples to compute percentiles")
