from django.contrib import admin

from .models import Report, TagSuggestion, TagVote


@admin.register(TagVote)
class TagVoteAdmin(admin.ModelAdmin):
    list_display = ["release__name", "tag__name", "value", "voter", "id"]
    search_fields = ["release__name", "tag__name", "value", "voter", "id"]
    ordering = ["release__name", "tag__name", "value"]


@admin.register(TagSuggestion)
class TagSuggestionAdmin(admin.ModelAdmin):
    list_display = ["tag", "release__name", "source", "created"]
    search_fields = ["tag", "release__name"]
    ordering = ["tag"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["release__name", "reason_label", "voter"]
    search_fields = ["release__name", "voter"]
    ordering = ["release__name"]
