from django.contrib import admin, messages

from .models import SearchToken


# Register your models here.
@admin.register(SearchToken)
class SearchTokenAdmin(admin.ModelAdmin):
    list_display = ["token", "disabled", "popularity", "added"]
    search_fields = ["token"]
    readonly_fields = ["added"]
    ordering = ["token"]
