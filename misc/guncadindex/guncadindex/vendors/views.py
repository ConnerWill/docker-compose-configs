from agegate.mixins import AgeGateRequiredMixin
from django.views.generic import ListView

from .models import Vendor


class AllVendorsView(AgeGateRequiredMixin, ListView):
    model = Vendor
    context_object_name = "items"
    template_name = "all_vendors.html"
    queryset = Vendor.objects.visible().order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hide_vendors"] = True
        return context
