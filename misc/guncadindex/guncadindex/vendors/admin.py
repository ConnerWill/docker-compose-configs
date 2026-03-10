from django.contrib import admin
from django.core.cache import cache

from . import utils
from .models import Vendor


# Register your models here.
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        "slug",
        "name",
        "homepage",
        "disabled",
        "visible",
        "footer",
        "should_markup",
    ]
    search_fields = ["slug", "name", "description"]
    ordering = ["slug"]
    actions = ["enable_vendors", "disable_vendors"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate_visible()

    def visible(self, obj):
        return obj.visible

    visible.admin_order_field = "visible"
    visible.short_description = "Visible"
    visible.boolean = True

    @admin.action(description="Enable selected vendors")
    def enable_vendors(self, request, queryset):
        queryset.update(disabled=False)
        utils.clear_caches()

    @admin.action(description="Disable selected vendors")
    def disable_vendors(self, request, queryset):
        queryset.update(disabled=True)
        utils.clear_caches()
