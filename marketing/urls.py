from django.urls import path

from core import profile_views as pv

from . import views

app_name = "marketing"

urlpatterns = [
    path("", views.index, name="index"),
    path("profile/", pv.marketing_profile, name="profile"),
    path("profile/photo/", pv.marketing_profile_photo, name="profile_picture_update"),
    path("campaigns/", views.campaigns, name="campaigns"),
    path("creatives/", views.creatives, name="creatives"),
    path("leads/", views.leads, name="leads"),
    path("announcements/", views.announcements, name="announcements"),
]
