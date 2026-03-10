import time
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django_redis import get_redis_connection


class Command(BaseCommand):
    help = "Dump unique visitor data from Redis"

    def handle(self, *args, **options):
        r = get_redis_connection("default")
        now = time.time()
        entries = r.zrevrangebyscore("uniq:visitors", "+inf", 0, withscores=True)

        if not entries:
            self.stdout.write("No visitors found.")
            return

        for user_id, ts in entries:
            age = now - ts
            bin_label = self.get_bin_label(age)
            stamp = datetime.fromtimestamp(ts).isoformat()
            self.stdout.write(f"[{bin_label:10}] {stamp}  {user_id.decode()}")

    def get_bin_label(self, age):
        if age <= 86400:
            return "daily"
        elif age <= 86400 * 7:
            return "weekly"
        elif age <= 86400 * 30:
            return "monthly"
        else:
            return "old"
