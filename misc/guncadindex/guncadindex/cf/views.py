from django.http import HttpResponse
from django.views.generic import TemplateView


class CuckStateView(TemplateView):
    template_name = "cuck.html"
    status_code = 451

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["region"] = getattr(self.request, "blocked_region", "NOTBLOCKED")
        ctx["reason"] = getattr(
            self.request,
            "blocked_region_reason",
            "This request was not blocked by geofiltering. If you see this message, it is in error.\n\nPlease contact the site administrator.",
        )
        return ctx

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault("status", self.status_code)
        return super().render_to_response(context, **response_kwargs)
