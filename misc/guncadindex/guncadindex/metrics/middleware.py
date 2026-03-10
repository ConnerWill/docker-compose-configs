import hashlib
import time
from datetime import datetime
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django_redis import get_redis_connection
from metrics.models import TrafficClassifier
from prometheus_client import Counter
from user_agents import parse

request_counter = Counter(
    "guncadindex_requests", "Total number of requests, categorized", ["audience_type"]
)
request_by_referer_counter = Counter(
    "guncadindex_requests_by_referer",
    "Total number of requests, categorized by referer website",
    ["referer"],
)


class VisitorMiddleware:
    """
    Classifies a request, using Redis, based on whether we've seen this visitor or not before
    """

    WINDOW_SECONDS = {
        "daily": 86400,
        "weekly": 86400 * 7,
        "monthly": 86400 * 30,
    }

    def __init__(self, get_response):
        self.get_response = get_response
        self.redis: Redis = get_redis_connection("default")

    def __call__(self, request):
        traffic_classifier = request.traffic_classifier
        user_id = self.get_user_fingerprint(request)

        # If the user's a bot, bail early *and* remove them from historical
        # metrics.
        if traffic_classifier.startswith("bot"):
            self.redis.zrem("uniq:visitors", user_id)
            return self.get_response(request)

        request.traffic_user_id = user_id[:8]
        now = time.time()

        #
        # Using zadd here adds the visitor to a set with a score set to the
        # current timestamp. We're later going to use this score to filter when
        # we collect metrics.
        #
        # Note that this means these entries don't expire and must be manually
        # pruned later on.
        #
        self.redis.zadd("uniq:visitors", {user_id: now})

        # TODO: If this gets too expensive, move it to the cronjob
        # (metrics/metrics.py) so it's outside of the request flow.
        # But that shouldn't happen for a while
        max_window = max(self.WINDOW_SECONDS.values())
        self.redis.zremrangebyscore("uniq:visitors", 0, now - max_window)

        return self.get_response(request)

    def get_user_fingerprint(self, request):
        ip = request.META.get(
            "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")
        )
        ua = request.META.get("HTTP_USER_AGENT", "")
        secret = settings.SECRET_KEY
        raw = f"{ip}|{ua}|{secret}"
        return hashlib.sha256(raw.encode()).hexdigest()


class RefererMiddleware:
    """
    Bins requests by their referer header
    """

    MAX_REFERERS = 30
    _seen_referers = set()

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_by_referer_counter.labels(referer=self.get_referer(request)).inc()
        return self.get_response(request)

    def get_referer(self, request):
        referer = request.META.get("HTTP_REFERER", "none").lower()
        host = urlparse(referer).hostname or None
        # If the referer field is null, pass that info through
        if not host:
            return "none"
        # Else, if we know the guy, let 'im through
        if host in self._seen_referers:
            return host
        # Otherwise, if we have room in the list, let 'im through
        if len(self._seen_referers) < self.MAX_REFERERS:
            self._seen_referers.add(host)
            return host
        # We're full
        return "other"


class RequestMiddleware:
    """
    Uses traffic classifier DB objects (cached, ofc) to determine what kind of traffic the request is.
    Used to filter bots and the like from Real Human Beans.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        classifier_rules = cache.get_or_set("traffic_classifiers", self.load_rules, 60)

        audience = self.classify(request, classifier_rules)
        request_counter.labels(audience_type=audience).inc()
        request.traffic_classifier = audience

        return self.get_response(request)

    def load_rules(self):
        return list(
            TrafficClassifier.objects.order_by("-priority", "-id").values(
                "kind", "priority", "pattern", "value"
            )
        )

    def match_rule(self, pattern, match):
        p = pattern.lower()
        m = match.lower()
        if p == ":empty:":
            return not m
        else:
            return p in m

    def classify(self, request, rules):

        exit_nodes = cache.get("tor_exit_ips") or set()

        targets = {
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "host": request.META.get("HTTP_HOST", ""),
            "xff": request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip(),
            "referrer": request.META.get("HTTP_REFERER", ""),
            "path": request.path,
        }

        if targets.get("xff") in exit_nodes:
            return "onion_exit"

        for rule in rules:
            kind = rule["kind"]
            pattern = rule["pattern"]
            value = rule["value"]

            target = targets.get(kind) or ""
            if self.match_rule(pattern, target):
                return value

        try:
            ua_parsed = parse(targets.get("user_agent"))
            if ua_parsed.is_bot:
                return "bot"
            return "human"
        except Exception as e:
            return "human"
