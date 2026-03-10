from django.conf import settings
from django.core.cache import cache

from .models import Report, TagSuggestion, TagVote


def crowdsource(request):
    pending_votes = cache.get_or_set(
        "crowdsource_pending_votes", TagVote.objects.count, 30
    )
    pending_reports = cache.get_or_set(
        "crowdsource_pending_reports", Report.objects.count, 30
    )
    report_reasons = enumerate(Report.REPORT_REASONS)
    return {
        "crowdsource_pending_votes": pending_votes,
        "crowdsource_pending_reports": pending_reports,
        "crowdsource_report_reasons": report_reasons,
    }
