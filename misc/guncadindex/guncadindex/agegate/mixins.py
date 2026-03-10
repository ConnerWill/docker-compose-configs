from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .utils import AGE_GATE_COOKIE_NAME, has_valid_disclaimer


class AgeGateRequiredMixin:
    """
    Requires age verification for human traffic.
    Hard depends on metrics.middleware.RequestMiddleware
    """

    age_cookie_name = AGE_GATE_COOKIE_NAME
    age_cookie_value = "1"
    age_gate_url = reverse_lazy("agegate")

    def is_human(self, request):
        """
        Returns if we think a user is human enough to see the disclaimer
        """
        classifier = getattr(request, "traffic_classifier", "")
        return any(
            classifier.startswith(prefix)
            for prefix in (
                "human",
                "bot_norefer",
            )
        )

    def dispatch(self, request, *args, **kwargs):
        is_human = self.is_human(request)
        has_disclaimer = has_valid_disclaimer(request)
        if not is_human or has_disclaimer or request.method in ("HEAD", "OPTIONS"):
            return super().dispatch(request, *args, **kwargs)

        next_url = request.get_full_path()
        # We don't sanitize here -- the AgeGateView will do that
        return HttpResponseRedirect(f"{self.age_gate_url}?next={next_url}")
