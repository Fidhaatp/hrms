from django.urls import path

from core import profile_views as pv

from . import views

app_name = "followup"

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", pv.followup_profile, name="profile"),
    path("profile/photo/", pv.followup_profile_photo, name="profile_picture_update"),
    path("leave/", views.leave_list, name="leave_list"),
    path("leave/add/", views.leave_add, name="leave_add"),
    path("leads/", views.lead_list, name="lead_list"),
    path("all-leads/", views.all_leads, name="all_leads"),
    path("leads/<int:pk>/update/", views.lead_update, name="lead_update"),
    path("leads/<int:pk>/check-docs/", views.lead_check_docs, name="lead_check_docs"),
    path("leads/<int:pk>/status/", views.lead_status, name="lead_status"),
    path("leads/<int:pk>/expire-date/", views.lead_expire_date, name="lead_expire_date"),
    path("leads/<int:pk>/procedure/", views.lead_procedure_submit, name="lead_procedure_submit"),
    path("leads/<int:pk>/upload-document/", views.lead_document_upload, name="lead_document_upload"),
    path("calendar/", views.calendar, name="calendar"),
]
