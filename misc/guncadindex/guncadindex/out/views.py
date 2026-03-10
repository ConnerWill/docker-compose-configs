from urllib.parse import unquote, urlparse

from django.core import signing
from django.http import HttpResponseRedirect
from django.views.generic import RedirectView, TemplateView
from out import utils
from prometheus_client import Counter

DISCLAIMER_COOKIE_AGE = 60 * 60 * 24 * 7
DISCLAIMER_COOKIE_NAME = "guncad_outbound_disclaimer"

DISCLAIMER_URL_AGE = 60 * 60 * 24 * 7

outbound_request_counter = Counter(
    "guncadindex_outbound_requests",
    "Total number of outbound link hits, categorized by domain",
    ["destination"],
)


class OutRedirect(HttpResponseRedirect):
    allowed_schemes = ["http", "https", "lbry"]


class OutRedirectView(TemplateView):
    template_name = "out_warning.html"

    def has_valid_disclaimer(self, request):
        raw = request.COOKIES.get(DISCLAIMER_COOKIE_NAME)
        if not raw:
            return False
        try:
            signing.loads(
                raw,
                max_age=DISCLAIMER_COOKIE_AGE,
                salt="guncad-outbound-disclaimer",
            )
            return True
        except signing.BadSignature:
            return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hostname = urlparse(self.target_url).hostname
        shown_length = int(len(hostname) / 2)
        context["target_url"] = hostname[: shown_length - 1] + (
            "*" * (len(hostname) - shown_length)
        )
        context["cookie_age"] = DISCLAIMER_COOKIE_AGE
        return context

    def dispatch(self, request, *args, **kwargs):
        self.target_url = utils.retrieve_outbound_url(request.GET.get("t"))
        host = urlparse(self.target_url).hostname or None
        if not self.target_url:
            # If they visit this page with no param, redirect to root
            # This can also happen if an invalid URL blob is supplied
            return OutRedirect("/")
        blocked_region_action = getattr(request, "blocked_region_action", 0)
        if blocked_region_action > 0:
            # Just in case a Cuck winds up here, we should NOT serve them
            # the redirected link under ANY circumstance
            return OutRedirect("/")
        traffic_classifier = getattr(request, "traffic_classifier", "")
        if not traffic_classifier.startswith("bot"):
            outbound_request_counter.labels(destination=host).inc()
        if self.has_valid_disclaimer(request):
            # If the user's accepted the disclaimer recently, just send
            # them where they wanna go
            return OutRedirect(self.target_url)
        # Render the template
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = OutRedirect(self.target_url)
        signed = signing.dumps(
            {"accepted": True},
            salt="guncad-outbound-disclaimer",
        )
        response.set_cookie(
            DISCLAIMER_COOKIE_NAME,
            signed,
            max_age=DISCLAIMER_COOKIE_AGE,
            secure=request.is_secure(),
            httponly=True,
            samesite="Lax",
        )
        return response
