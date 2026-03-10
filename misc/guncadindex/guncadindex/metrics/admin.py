from django.contrib import admin

from .models import TrafficClassifier


# Register your models here.
@admin.register(TrafficClassifier)
class TrafficClassifierAdmin(admin.ModelAdmin):
    list_display = ["description", "priority", "id", "kind", "pattern", "value"]
    search_fields = ["description", "pattern", "value", "priority"]
    ordering = ["-priority", "-id"]
    list_filter = ["kind"]
