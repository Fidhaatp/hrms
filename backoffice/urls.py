from django.urls import path

from core import profile_views as pv

from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", pv.backoffice_profile, name="profile"),
    path("profile/photo/", pv.backoffice_profile_photo, name="profile_picture_update"),
    path("leave/", views.leave_list, name="leave_list"),
    path("leave/add/", views.leave_add, name="leave_add"),
    path("pending-verifications/", views.pending_verifications, name="pending_verifications"),
    path("procedure-reviews/", views.procedure_reviews, name="procedure_reviews"),
    path("pending-leads/", views.pending_leads, name="pending_leads"),
    path("team/", views.team, name="team"),
    path("leads/", views.all_leads, name="all_leads"),
    path("leads/legacy/", views.lead_list, name="lead_list"),
    path("leads/<int:pk>/verify/", views.lead_verify, name="lead_verify"),
    path("leads/<int:pk>/reject/", views.lead_reject, name="lead_reject"),
    path("procedure-steps/<int:step_id>/review/", views.procedure_review, name="procedure_review"),
    path("leads/<int:pk>/open-case/", views.lead_open_case, name="lead_open_case"),
    path("cases/", views.cases, name="cases"),
    path("cases/<int:pk>/", views.case_detail, name="case_detail"),
    path("cases/<int:pk>/update/", views.case_update, name="case_update"),
    path("reports/", views.reports, name="reports"),
    path("reports/download/", views.reports_download, name="reports_download"),
]
