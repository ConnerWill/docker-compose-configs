import json
import os
import re
import time
from itertools import chain

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone
from odyseescraper import odysee
from odyseescraper.models import OdyseeRelease


class Command(BaseCommand):
    help = "Updates the popularity of all releases"

    def handle(self, *args, **options):
        for release in OdyseeRelease.objects.all():
            release.update_popularity()
            release.save()
