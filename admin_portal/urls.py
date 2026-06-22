from django.urls import path

from . import views

app_name = "admin_portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("employees/", views.employees, name="employees"),
    path("branches/", views.branches, name="branches"),
    path("roles/", views.roles, name="roles"),
    path("reports/", views.reports, name="reports"),
    path("workflows/", views.workflows, name="workflows"),
    path("settings/", views.settings, name="settings"),
    path("system-admin/", views.django_admin, name="django_admin"),
    path("profile/", views.profile, name="profile"),
    path("profile/photo/", views.profile_picture_update, name="profile_picture_update"),
]
