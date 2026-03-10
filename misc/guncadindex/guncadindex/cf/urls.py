from django.urls import path

from .views import CuckStateView

urlpatterns = [
    path("cuck", CuckStateView.as_view(), name="cuck"),
]
