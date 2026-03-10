import random
from collections import defaultdict
from datetime import timedelta

from crowdsource.models import Report, TagVote
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.db.models import Count, F, Func, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView
from odyseescraper.models import OdyseeRelease, Tag
from odyseescraper.views import OdyseeReleaseListView


# Staff tooling views
class ToolsLandingView(UserPassesTestMixin, TemplateView):
    template_name = "tools_landing.html"

    def test_func(self):
        return self.request.user.is_staff


class ToolsCSSTestView(TemplateView):
    template_name = "tools_csstest.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["test_release"] = (
            OdyseeRelease.objects.filter(release_state__gt=0).order_by("?").first()
        )
        context["tests_grid"] = {"elements": range(4)}
        context["tests_header"] = {
            "tags": ["h1", "h2", "h3"],
            "classes": ["", "huge", "underline"],
        }
        context["tests_image"] = {
            "images": [
                "test/image-horizontal.webp",
                "test/image-vertical.webp",
                "test/image-animated.gif",
            ],
            "classes": ["", "circle"],
            "sizes": ["", 64, 128],
            "dimensions": ["width", "height"],
        }
        return context


class ToolsVoteView(UserPassesTestMixin, ListView):
    model = TagVote
    context_object_name = "items"
    paginate_by = 20
    template_name = "tools_votes.html"

    def get_queryset(self):
        aggregated = (
            TagVote.objects.values("release", "tag")
            .annotate(total_score=Sum("value"))
            .annotate(absolute_score=Func(F("total_score"), function="ABS"))
            .order_by("-absolute_score", "release", "tag__name")
        )
        release_ids = {entry["release"] for entry in aggregated}
        tag_ids = {entry["tag"] for entry in aggregated}
        releases = OdyseeRelease.objects.in_bulk(release_ids)
        tags = Tag.objects.in_bulk(tag_ids)

        results = []
        for entry in aggregated:
            results.append(
                {
                    "release": releases.get(entry["release"]),
                    "tag": tags.get(entry["tag"]),
                    "total_score": entry["total_score"],
                    "absolute_score": entry["absolute_score"],
                }
            )
        return results

    def test_func(self):
        return self.request.user.is_staff and self.request.user.has_perm(
            "odyseescraper.change_odyseerelease"
        )

    def post(self, request, *args, **kwargs):
        release = get_object_or_404(OdyseeRelease, id=request.POST.get("release", ""))
        tag = get_object_or_404(Tag, id=request.POST.get("tag", ""))
        action = request.POST.get("action", "")
        decision = request.POST.get("decision", "")
        if decision == "accept":
            if action == "add":
                # Add tag by adding to manual and removing from the blacklist
                release.blacklisted_tags.remove(tag)
                release.manual_tags.add(tag)
                messages.success(
                    request, f"Added tag {tag.name} to release {release.name}"
                )
            elif action == "remove":
                # Blacklist tag by adding to blacklist list and removing from manual
                release.blacklisted_tags.add(tag)
                release.manual_tags.remove(tag)
                messages.success(
                    request, f"Removed tag {tag.name} from release {release.name}"
                )
            else:
                # Just clear out the votes
                messages.success(
                    request,
                    f"Cleared neutral votes for {tag.name} from release {release.name}",
                )
            votes = TagVote.objects.filter(release=release).filter(tag=tag).delete()
        elif decision == "reject":
            messages.success(
                request, f"Dismissed votes for {tag.name} on {release.name}"
            )
            votes = TagVote.objects.filter(release=release).filter(tag=tag).delete()
        else:
            messages.error(
                request,
                f"Unsupported decision type: {decision} - {tag.name} on {release.name}",
            )
        cache.delete("most_recent_updates")
        return redirect(reverse("tools-votes"))


class ReportView(UserPassesTestMixin, ListView):
    model = Report
    context_object_name = "items"
    paginate_by = 20
    template_name = "tools_reports.html"

    def get_queryset(self):
        """
        Aggregate reports by release, with counts per reason.
        Returns a list of dicts:
        [
            {
                "release": <OdyseeRelease>,
                "reason_counts": {0: 3, 1: 2, 4: 1},  # reason_index -> count
                "total_count": 6,
            },
            ...
        ]
        Sorted by total_count descending.
        """
        aggregated = (
            Report.objects.values("release", "reason_index")
            .annotate(count=Count("id"))
            .order_by("release", "reason_index")
        )

        release_ids = {entry["release"] for entry in aggregated}
        releases = OdyseeRelease.objects.in_bulk(release_ids)

        release_dict = defaultdict(lambda: {"reason_counts": {}, "total_count": 0})

        for entry in aggregated:
            release_id = entry["release"]
            reason_index = entry["reason_index"]
            count = entry["count"]

            release_entry = release_dict[release_id]
            release_entry["release"] = releases.get(release_id)
            release_entry["reason_counts"][reason_index] = {
                "label": Report.REPORT_REASONS[reason_index],
                "count": count,
            }
            release_entry["total_count"] += count

        # convert to a list and sort by total_count descending
        results = sorted(release_dict.values(), key=lambda x: -x["total_count"])

        return results

    def test_func(self):
        return self.request.user.is_staff and self.request.user.has_perm(
            "odyseescraper.change_odyseerelease"
        )

    def post(self, request, *args, **kwargs):
        release = get_object_or_404(OdyseeRelease, id=request.POST.get("release", ""))
        decision = request.POST.get("decision", "")

        if decision == "takedown":
            messages.success(request, f"Release {release.name} has been delisted")
            release.hidden = True
            release.save()
            Report.objects.filter(release=release).delete()
        elif decision == "ignore":
            Report.objects.filter(release=release).delete()
            messages.success(request, f"Reports for {release.name} have been ignored")
        else:
            messages.error(
                request, f"Unsupported decision: {decision} on {release.name}"
            )
        cache.delete("most_recent_updates")
        return redirect(reverse("tools-reports"))
