from django.shortcuts import redirect
from django.urls import reverse


def redirect_user_after_login(user):
    """Send user to the dashboard for their role."""
    profile = getattr(user, "profile", None)
    if profile:
        url_name = profile.get_dashboard_url_name()
        return redirect(url_name)
    return redirect("hr:dashboard")
