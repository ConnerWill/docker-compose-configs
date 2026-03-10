import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from odyseescraper.odysee import wait_for_component
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Command(BaseCommand):
    help = "Waits for LBRY to start its wallet up"

    def handle(self, *args, **options):
        wait_for_component("wallet")
