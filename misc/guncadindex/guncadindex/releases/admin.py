from django.contrib import admin

from .models import (
    Channel,
    ChannelDownloadMethod,
    ChannelThumbnail,
    DownloadMethod,
    Release,
    ReleaseDownloadMethod,
    ReleaseThumbnail,
)


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "hidden",
        "name",
        "release_state",
        "discovered",
        "updated",
    ]
    list_filter = [
        "hidden",
        "release_state",
    ]
    readonly_fields = ["discovered", "released", "updated"]
    search_fields = ["name", "description"]
    ordering = ["-discovered"]


@admin.register(ReleaseThumbnail)
class ReleaseThumbnailAdmin(admin.ModelAdmin):
    list_display = ["release", "id", "updated", "origin", "color"]
    readonly_fields = ["id", "updated", "color"]
    search_fields = ["origin"]
    ordering = ["-updated"]


@admin.register(ReleaseDownloadMethod)
class ReleaseDownloadMethodAdmin(admin.ModelAdmin):
    list_display = ["release", "id", "origin", "link"]
    list_filter = ["origin"]
    search_fields = ["release__name", "release__description"]
    ordering = ["release", "origin"]


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "hidden",
        "name",
        "release_state",
        "discovered",
    ]
    list_filter = [
        "hidden",
        "release_state",
    ]
    readonly_fields = ["discovered"]
    search_fields = ["name", "description"]
    ordering = ["-discovered"]


@admin.register(ChannelThumbnail)
class ChannelThumbnailAdmin(admin.ModelAdmin):
    list_display = ["release", "id", "updated", "origin"]
    readonly_fields = ["id", "updated"]
    search_fields = ["origin"]
    ordering = ["-updated"]


@admin.register(ChannelDownloadMethod)
class ChannelDownloadMethodAdmin(admin.ModelAdmin):
    list_display = ["channel", "id", "origin", "link"]
    list_filter = ["origin"]
    search_fields = ["channel__name", "channel__description"]
    ordering = ["channel", "origin"]
