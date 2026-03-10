from urllib.parse import urlparse

from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from .utils import (
    AGE_GATE_COOKIE_AGE,
    AGE_GATE_COOKIE_NAME,
    generate_age_gate_cookie,
    has_valid_disclaimer,
)


@method_decorator(never_cache, name="dispatch")
@method_decorator(ensure_csrf_cookie, name="dispatch")
class AgeGateView(TemplateView):
    template_name = "age_gate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cookie_age"] = AGE_GATE_COOKIE_AGE
        return context

    def post(self, request, *args, **kwargs):
        next_url = request.GET.get("next", "/")
        try:
            next_url_parsed = urlparse(next_url)
            if (
                next_url_parsed.scheme
                or next_url_parsed.netloc
                or not next_url_parsed.path.startswith("/")
            ):
                next_url = "/"
        except:
            next_url = "/"
        response = redirect(next_url)
        signed = generate_age_gate_cookie()
        response.set_cookie(
            AGE_GATE_COOKIE_NAME,
            signed,
            max_age=AGE_GATE_COOKIE_AGE,
            secure=request.is_secure(),
            httponly=True,
            samesite="Lax",
        )
        return response
