import random

from agegate.mixins import AgeGateRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from odyseescraper.models import OdyseeRelease, Tag, TagCategory

from .models import Report, TagVote


class TagVoteView(AgeGateRequiredMixin, DetailView):
    model = OdyseeRelease
    template_name = "vote_tag.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        release = self.get_object()
        context["unapplied_tags"] = (
            Tag.objects.prefetch_related("category")
            .all()
            .exclude(id__in=release.tags.values_list("id", flat=True))
            .order_by("category__name", "name")
        )
        context["applied_tags"] = release.tags.all().order_by("category__name", "name")
        return context

    def cast_vote(self, release, voter, tag, vote):
        obj, created = TagVote.objects.update_or_create(
            voter=voter,
            release=release,
            tag=Tag.objects.get(id=tag),
            defaults={"value": vote},
        )
        pass

    def post(self, request, *args, **kwargs):
        release = self.get_object()
        # This DEBUG check here is so that, on your local, you can cast
        # multiple votes without doing any funny business
        if settings.DEBUG:
            voter = hash(random.random())
        else:
            voter = hash(request.META["REMOTE_ADDR"])
        for tag in request.POST.getlist("add", []):
            self.cast_vote(
                release=release, voter=voter, tag=tag, vote=TagVote.Operation.UPVOTE
            )
        for tag in request.POST.getlist("del", []):
            self.cast_vote(
                release=release, voter=voter, tag=tag, vote=TagVote.Operation.DOWNVOTE
            )

        messages.success(
            request, f"Your votes for {release.name[:30]} were submitted successfully"
        )
        return redirect(reverse("detail", kwargs={"pk": release.id}))


class ReportView(AgeGateRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, object_id):
        release = get_object_or_404(OdyseeRelease, id=object_id)
        voter = hash(random.random() if settings.DEBUG else request.META["REMOTE_ADDR"])

        # Data validation
        try:
            reason_index = int(request.POST.get("reason_index"))
            if not 0 <= reason_index < len(Report.REPORT_REASONS):
                raise ValueError
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Invalid reason selected.")

        # Create the thing
        Report.objects.create(
            release=release,
            voter=voter,
            reason_index=reason_index,
        )

        messages.success(request, f"Your report for {release.name[:30]} was filed")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
