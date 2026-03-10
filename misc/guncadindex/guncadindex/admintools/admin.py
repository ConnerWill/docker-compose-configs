from django.contrib import admin

from .models import AdminNavbarLink, AdminSiteBanner


@admin.register(AdminSiteBanner)
class AdminSiteBannerAdmin(admin.ModelAdmin):
    list_display = ["id", "priority", "text", "visible", "color"]
    search_fields = ["text"]
    readonly_fields = ["id"]
    ordering = ["-visible", "-priority", "id"]


@admin.register(AdminNavbarLink)
class AdminNavbarLinkAdmin(admin.ModelAdmin):
    list_display = ["id", "priority", "text", "visible", "newtab", "link"]
    search_fields = ["text", "link"]
    readonly_fields = ["id"]
    ordering = ["-visible", "-priority", "id"]
