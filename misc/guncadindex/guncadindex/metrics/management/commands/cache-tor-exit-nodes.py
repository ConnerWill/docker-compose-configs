import ipaddress
import logging

import requests
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

TOR_EXIT_CACHE_KEY = "tor_exit_ips"
TOR_EXIT_TTL = 3600 * 6  # 6hrs
TOR_EXIT_URL = "https://check.torproject.org/cgi-bin/TorBulkExitList.py"

logger = logging.getLogger("cache-tor-exit-nodes")
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Fetch and cache the current Tor exit node list."

    def handle(self, *args, **options):
        try:
            logger.info(f"Fetching Tor exit list from {TOR_EXIT_URL}…")
            resp = requests.get(TOR_EXIT_URL, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            raise CommandError(f"Failed to fetch Tor exit list: {e}")

        exits = set()
        for line in resp.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                exits.add(ipaddress.ip_address(line))
            except ValueError:
                self.stderr.write(f"Skipping invalid line: {line}")

        cache.set(TOR_EXIT_CACHE_KEY, exits, TOR_EXIT_TTL)
        logger.info(
            self.style.SUCCESS(f"Cached {len(exits)} Tor exit IPs for {TOR_EXIT_TTL}s")
        )
