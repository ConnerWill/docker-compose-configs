from django.urls import path

from .views import OutRedirectView

urlpatterns = [
    path("", OutRedirectView.as_view(), name="out"),
]
