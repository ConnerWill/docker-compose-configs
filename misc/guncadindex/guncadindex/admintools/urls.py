from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.ToolsLandingView.as_view(), name="tools"),
    path("votes", views.ToolsVoteView.as_view(), name="tools-votes"),
    path("reports", views.ReportView.as_view(), name="tools-reports"),
    path("csstest", views.ToolsCSSTestView.as_view(), name="tools-csstest"),
]
