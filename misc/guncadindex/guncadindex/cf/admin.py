from django.contrib import admin

from .models import Cuck


# Register your models here.
@admin.register(Cuck)
class CuckAdmin(admin.ModelAdmin):
    list_display = ["region", "action", "disabled", "visible", "valid_after", "reason"]
    search_fields = ["region", "reason"]
    ordering = ["-disabled", "-region"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate_visible()

    def visible(self, obj):
        return obj.visible

    visible.admin_order_field = "visible"
    visible.short_description = "Visible"
    visible.boolean = True
