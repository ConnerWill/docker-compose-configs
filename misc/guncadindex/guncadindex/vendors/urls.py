from django.urls import include, path

from . import views

urlpatterns = [
    path("all", views.AllVendorsView.as_view(), name="allvendors"),
]
