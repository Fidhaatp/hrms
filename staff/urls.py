from django.urls import path

from core import profile_views as pv

from . import views

app_name = "staff"

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", pv.staff_profile, name="profile"),
    path("profile/photo/", pv.staff_profile_photo, name="profile_picture_update"),
    path("leave/", views.leave_list, name="leave_list"),
    path("leave/add/", views.leave_add, name="leave_add"),
    path("leads/", views.lead_list, name="lead_list"),
    path("leads/search/", views.lead_search, name="lead_search"),
    path("leads/<int:pk>/contact/", views.lead_contact, name="lead_contact"),
    path("leads/add/", views.lead_add, name="lead_add"),
    path("leads/<int:pk>/edit/", views.lead_edit, name="lead_edit"),
    path("leads/<int:pk>/update/", views.lead_update, name="lead_update"),
    path("leads/<int:pk>/status/", views.lead_status, name="lead_status"),
    path("leads/<int:pk>/start-renewal/", views.lead_start_renewal, name="lead_start_renewal"),
    path("calendar/", views.calendar, name="calendar"),
    path("pipeline/", views.pipeline, name="pipeline"),
    path("targets/", views.targets, name="targets"),
]
