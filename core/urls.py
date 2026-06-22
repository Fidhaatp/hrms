from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "core"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="core:login", permanent=False), name="home"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("post-login/", views.post_login, name="post_login"),
    path("register/", views.register_portal, name="register_portal"),
]
