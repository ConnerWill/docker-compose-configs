from django.contrib import admin, messages
from django.db.models import Count

from .models import (
    FaqEntry,
    OdyseeChannel,
    OdyseeChannelThumbnail,
    OdyseeRelease,
    OdyseeReleaseLemmy,
    OdyseeReleaseSimilar,
    OdyseeReleaseThumbnail,
    ReleaseState,
    Tag,
    TagCategory,
    TaggingRule,
)


# Register your models here.
@admin.register(OdyseeChannel)
class OdyseeChannelAdmin(admin.ModelAdmin):
    list_display = [
        "handle",
        "name",
        "release_count",
        "dupe_count",
        "default_release_state",
        "disabled",
        "lbry_only",
        "discovered",
    ]
    readonly_fields = ["id", "claimid"]
    search_fields = ["name", "description", "handle", "claimid"]
    ordering = ["-discovered"]
    list_filter = ["disabled", "lbry_only", "default_release_state"]
    actions = [
        "null_releases",
        "verify_releases",
        "unverify_releases",
        "dangerous_releases",
        "delete_releases",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate_common()

    def release_count(self, obj):
        return obj.release_count

    release_count.admin_order_field = "release_count"
    release_count.short_description = "Releases"

    def dupe_count(self, obj):
        return obj.dupe_count

    dupe_count.admin_order_field = "dupe_count"
    dupe_count.short_description = "Duplicates"

    @admin.action(description="Set default release state to inherited by channel")
    def null_releases(self, request, queryset):
        queryset.update(default_release_state=None)

    @admin.action(description="Set default release state to VERIFIED")
    def verify_releases(self, request, queryset):
        queryset.update(default_release_state=ReleaseState.VERIFIED)

    @admin.action(description="Set default release state to RELEASED")
    def unverify_releases(self, request, queryset):
        queryset.update(default_release_state=ReleaseState.RELEASED)

    @admin.action(description="Set default release state to DANGEROUS")
    def dangerous_releases(self, request, queryset):
        queryset.update(default_release_state=ReleaseState.DANGEROUS)

    @admin.action(description="Nuke and disable selected channels")
    def delete_releases(self, request, queryset):
        if not request.user.has_perm("yourapp.delete_odyseerelease"):
            self.message_user(
                request,
                "You do not have permission to delete releases.",
                level=messages.ERROR,
            )
        else:
            total_deleted = 0
            for channel in queryset:
                deleted_count, _ = OdyseeRelease.objects.filter(
                    channel=channel
                ).delete()
                total_deleted += deleted_count
                channel.disabled = True
                channel.save()
            self.message_user(
                request,
                f"Deleted {total_deleted} releases from {queryset.count()} channel(s) and disabled them.",
                level=messages.SUCCESS,
            )


@admin.register(FaqEntry)
class FaqEntryAdmin(admin.ModelAdmin):
    list_display = ["id", "question"]
    search_fields = ["question", "answer"]
    ordering = ["id"]


@admin.register(OdyseeReleaseThumbnail)
class OdyseeReleaseThumbnailAdmin(admin.ModelAdmin):
    list_display = ["release", "id", "updated", "needs_updated", "origin"]
    readonly_fields = ["id", "color", "release", "updated", "needs_updated"]
    search_fields = ["id", "origin"]
    ordering = ["-updated"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate_needs_updated()

    def needs_updated(self, obj):
        return obj.needs_updated

    needs_updated.admin_order_field = "needs_updated"
    needs_updated.short_description = "Needs Updated"
    needs_updated.boolean = True


@admin.register(OdyseeReleaseSimilar)
class OdyseeReleaseSimilarAdmin(admin.ModelAdmin):
    list_display = ["release", "id", "updated", "needs_updated"]
    readonly_fields = ["id", "release", "similar", "updated", "needs_updated"]
    ordering = ["-updated"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate_needs_updated()

    def needs_updated(self, obj):
        return obj.needs_updated

    needs_updated.admin_order_field = "needs_updated"
    needs_updated.short_description = "Needs Updated"
    needs_updated.boolean = True


@admin.register(OdyseeReleaseLemmy)
class OdyseeReleaseLemmyAdmin(admin.ModelAdmin):
    list_display = ["release", "id", "updated", "needs_updated"]
    readonly_fields = ["id", "release", "updated", "needs_updated"]
    ordering = ["-updated"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate_needs_updated()

    def needs_updated(self, obj):
        return obj.needs_updated

    needs_updated.admin_order_field = "needs_updated"
    needs_updated.short_description = "Needs Updated"
    needs_updated.boolean = True


@admin.register(OdyseeChannelThumbnail)
class OdyseeChannelThumbnailAdmin(admin.ModelAdmin):
    list_display = ["release", "id", "updated", "needs_updated", "origin"]
    readonly_fields = ["id", "color", "release", "updated", "needs_updated"]
    search_fields = ["id", "origin"]
    ordering = ["-updated"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate_needs_updated()

    def needs_updated(self, obj):
        return obj.needs_updated

    needs_updated.admin_order_field = "needs_updated"
    needs_updated.short_description = "Needs Updated"
    needs_updated.boolean = True


@admin.register(OdyseeRelease)
class OdyseeReleaseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "channel",
        "released",
        "license",
        "release_state",
        "hidden",
        "abandoned",
        "lbry_only",
    ]
    readonly_fields = [
        "name",
        "description",
        "id",
        "abandoned",
        "duplicate",
        "channel",
        "sd_hash",
        "sha384sum",
        "discovered",
        "released",
        "last_updated",
        "size",
        "slug",
        "thumbnail",
        "thumbnail_manager",
        "ai_tags",
        "tag_rules",
        "odysee_views",
        "odysee_likes",
        "odysee_dislikes",
        "lbry_effective_amount",
        "lbry_support_amount",
        "lbry_reposts",
        "popularity",
    ]
    search_fields = [
        "name",
        "license",
        "description",
        "id",
        "url",
        "channel__name",
        "sha384sum",
        "shortlink",
    ]
    ordering = ["-released"]
    list_filter = [
        "channel",
        "license",
        "tags",
        "released",
        "hidden",
        "abandoned",
        "lbry_only",
        "release_state",
    ]
    actions = [
        "verify_releases",
        "unverify_releases",
        "dangerous_releases",
        "unset_verify_releases",
        "save_all_releases",
    ]

    def get_tags(self, obj):
        return ", ".join([str(tag) for tag in obj.tags.all()])

    get_tags.short_description = "Tags"

    @admin.action(description="Set release state to VERIFIED")
    def verify_releases(self, request, queryset):
        queryset.update(release_state=ReleaseState.VERIFIED)

    @admin.action(description="Set release state to RELEASED")
    def unverify_releases(self, request, queryset):
        queryset.update(release_state=ReleaseState.RELEASED)

    @admin.action(description="Set release state to DANGEROUS")
    def dangerous_releases(self, request, queryset):
        queryset.update(release_state=ReleaseState.DANGEROUS)

    @admin.action(description="Set release state to inherited by channel")
    def unset_verify_releases(self, request, queryset):
        queryset.update(release_state=None)

    @admin.action(description="Re-save releases, cleaning up stale data")
    def save_all_releases(self, request, queryset):
        for release in queryset:
            release.save()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "category__name",
        "description",
        "custom_color",
        "text_color",
        "id",
    ]
    search_fields = ["name", "slug", "description"]
    ordering = ["name"]


@admin.register(TagCategory)
class TagCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "color", "useforweighting", "id"]
    search_fields = ["name", "description"]
    ordering = ["name"]
    list_filter = ["useforweighting"]


@admin.register(TaggingRule)
class TaggingRuleAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "tag",
        "release_count",
        "id",
    ]
    search_fields = ["name", "tag__name", "required_tag__name"]
    ordering = ["name"]
    list_filter = ["tag", "required_tag"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(release_count=Count("releases"))

    def release_count(self, obj):
        return obj.release_count

    release_count.admin_order_field = "release_count"
    release_count.short_description = "Releases"
