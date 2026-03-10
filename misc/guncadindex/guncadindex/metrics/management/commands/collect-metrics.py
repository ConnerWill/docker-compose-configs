import time

from django.core.management.base import BaseCommand
from metrics.metrics import collect_metrics


class Command(BaseCommand):
    help = "Collect Prometheus metrics on a loop forever"

    def handle(self, *args, **options):
        self.stdout.write("Starting metrics collection loop...")
        try:
            while True:
                collect_metrics()
                time.sleep(15)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Interrupt received"))
