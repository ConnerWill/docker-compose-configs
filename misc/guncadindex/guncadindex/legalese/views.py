from django.shortcuts import render
from django.views.generic import TemplateView


class LegaleseTermsView(TemplateView):
    template_name = "termsofuse.html"
