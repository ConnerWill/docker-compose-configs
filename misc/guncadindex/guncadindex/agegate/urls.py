from django.urls import path

from .views import AgeGateView

urlpatterns = [
    path("", AgeGateView.as_view(), name="agegate"),
]
