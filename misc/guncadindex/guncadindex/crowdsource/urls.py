from django.urls import include, path

from . import views

urlpatterns = [
    path("release/<slug:pk>", views.TagVoteView.as_view(), name="votetag"),
    path("report/<slug:object_id>", views.ReportView.as_view(), name="votereport"),
]
