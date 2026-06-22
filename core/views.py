from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.auth_utils import redirect_user_after_login
from core.forms import LoginForm
from core.models import UserProfile


def custom_400(request, exception):
    return render(
        request,
        "400.html",
        {
            "error_code": 400,
            "error_title": "Bad Request",
            "error_message": "The request could not be understood by the server.",
        },
        status=400,
    )


def custom_403(request, exception):
    return render(
        request,
        "403.html",
        {
            "error_code": 403,
            "error_title": "Access Denied",
            "error_message": "You do not have permission to access this page.", 
        },
        status=403,
    )


def custom_404(request, exception):
    return render(
        request,
        "404.html",
        {
            "error_code": 404,
            "error_title": "Page Not Found",
            "error_message": "The page you are looking for does not exist.",
        },
        status=404,
    )


def custom_500(request):
    return render(
        request,
        "500.html",
        {
            "error_code": 500,
            "error_title": "Server Error",
            "error_message": "Something went wrong on our side. Please try again later.",
        },
        status=500,
    )


@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.user.is_authenticated:
        return redirect_user_after_login(request.user)

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
        return redirect_user_after_login(user)

    return render(request, "core/login.html", {"form": form})


@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("core:login")


@login_required
def post_login(request):
    return redirect_user_after_login(request.user)


def register_portal(request):
    """Common page — links to each app's registration."""
    registration_options = [
        {
            "title": "HR Registration",
            "description": "Human resources staff — manage employees, leave, and payroll.",
            "icon": "bi-person-badge-fill",
            "color": "#E01E26",
            "url_name": "hr:register",
            "available": True,
        },
        {
            "title": "Staff",
            "description": "Staff accounts are created by HR from the portal.",
            "icon": "bi-people-fill",
            "color": "#00843D",
            "url_name": "hr:staff_list",
            "available": True,
        },
        {
            "title": "Back Office",
            "description": "Back office accounts are created by HR from the portal.",
            "icon": "bi-building-fill",
            "color": "#1a1a1a",
            "url_name": "hr:backoffice_list",
            "available": True,
        },
        {
            "title": "Branch",
            "description": "Branch managers are created by HR.",
            "icon": "bi-geo-alt-fill",
            "color": "#E01E26",
            "url_name": "branch:index",
            "available": True,
        },
        {
            "title": "Follow-up",
            "description": "Follow-up team accounts are created by HR from the portal.",
            "icon": "bi-telephone-fill",
            "color": "#00843D",
            "url_name": "hr:followup_list",
            "available": True,
        },
    ]
    return render(
        request,
        "core/register_portal.html",
        {"registration_options": registration_options},
    )
