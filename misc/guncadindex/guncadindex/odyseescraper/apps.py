import threading
import time

from django.apps import AppConfig


class OdyseescraperConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "odyseescraper"

    def ready(self):
        import odyseescraper.signals
