from django.urls import path

from core import profile_views as pv

from . import views

app_name = "branch"

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", pv.branch_profile, name="profile"),
    path("profile/photo/", pv.branch_profile_photo, name="profile_picture_update"),
    path("all-leads/", views.all_leads, name="all_leads"),
    path("lead-history/", views.lead_history, name="lead_history"),
    path("calendar/", views.calendar, name="calendar"),
    path("staff/", views.staff, name="staff"),
    path("followup/", views.followup_team, name="followup"),
    path("reports/", views.reports, name="reports"),
    path("reports/download/", views.reports_download, name="reports_download"),
    # Legacy redirects
    path("leads/", views.lead_history, name="lead_list"),
]
