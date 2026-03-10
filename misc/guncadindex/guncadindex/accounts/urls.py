from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

urlpatterns = [
    path("login/", LoginView.as_view(template_name="admin/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="landing"), name="logout"),
]
