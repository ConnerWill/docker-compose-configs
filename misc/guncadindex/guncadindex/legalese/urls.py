from django.urls import include, path

from . import views

urlpatterns = [
    path("legal", views.LegaleseTermsView.as_view(), name="legal"),
]
