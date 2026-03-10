from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from django.utils import timezone
from prometheus_client import Counter

from .models import Cuck, CuckAction
from .views import CuckStateView

BLOCKED_REGIONS = {"CA", "NJ", "NY"}
BLOCKED_METHODS = {"GET", "POST"}

cuck_counter = Counter(
    "guncadindex_geoblocked_requests",
    "Total number of requests geoblocked",
    ["region", "action"],
)
geo_counter = Counter(
    "guncadindex_requests_by_region",
    "Total number of requests, sorted by location",
    ["region", "country"],
)


class CloudflareRegionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        region = request.headers.get("CF-Region-Code", "XX").upper()
        country = request.headers.get("CF-IPCountry", "XX").upper()
        if region and country:
            geo_counter.labels(region=region, country=country).inc()

        return self.get_response(request)


class CuckStateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if (
            path.startswith(getattr(settings, "STATIC_URL", "/static"))
            or path.startswith(getattr(settings, "MEDIA_URL", "/media"))
            or path.startswith("/admin")
        ):
            return self.get_response(request)

        rules = cache.get_or_set("cucks:v2", self.load_rules, 60)
        result = self.classify(request, rules)

        # Block states by forcing a specific view to render
        if result:
            request.blocked_region = result.region
            request.blocked_region_reason = result.reason
            request.blocked_region_action = result.action
            if result.action == CuckAction.BLOCK:
                response = CuckStateView.as_view()(request)
                response.render()
                response["Cache-Control"] = "no-store"
                response["Retry-After"] = "86400"
                # Bump metrics
                cuck_counter.labels(region=result.region, action="block").inc()
                return response
            elif result.action == CuckAction.RESTRICT_ACCESS_HEAVY:
                cuck_counter.labels(
                    region=result.region, action="restrict-access-heavy"
                ).inc()
        else:
            request.blocked_region_action = 0  # No action

        return self.get_response(request)

    def load_rules(self):
        return list(Cuck.objects.visible().order_by("-region"))

    def classify(self, request, rules):
        region = request.headers.get("CF-Region-Code", "UNKNOWN")
        is_bot = request.headers.get("CF-Client-Bot", "").lower() == "true"

        for rule in rules:
            if (
                region.lower() == rule.region.lower()
                and not is_bot
                and request.method in BLOCKED_METHODS
            ):
                return rule

        return None


class CloudflareTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.headers.get("CF-Timezone")

        if tzname:
            try:
                timezone.activate(ZoneInfo(tzname))
            except Exception:
                timezone.deactivate()
        else:
            timezone.deactivate()

        return self.get_response(request)
