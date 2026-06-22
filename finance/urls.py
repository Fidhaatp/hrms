from django.urls import path

from core import profile_views as pv

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", pv.finance_profile, name="profile"),
    path("profile/photo/", pv.finance_profile_photo, name="profile_picture_update"),
    path("payroll/", views.payroll, name="payroll"),
    path("incentives/", views.incentives, name="incentives"),
    path("collections/", views.collections, name="collections"),
    path("expenses/", views.expenses, name="expenses"),
    path("reports/", views.reports, name="reports"),
]
