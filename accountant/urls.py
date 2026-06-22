from django.urls import path

from core import profile_views as pv

from . import views

app_name = "accountant"

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", pv.accountant_profile, name="profile"),
    path("profile/photo/", pv.accountant_profile_photo, name="profile_picture_update"),
    path("collections/", views.collections, name="collections"),
    path("invoices/", views.invoices, name="invoices"),
    path("reports/", views.reports, name="reports"),
    path("finance-communication/", views.finance_comm, name="finance_comm"),
]
