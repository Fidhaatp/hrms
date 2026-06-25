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

@login_required
def portal_notifications_view(request):
    is_hr = getattr(request.user, "is_superuser", False)
    profile = getattr(request.user, "profile", None)
    
    if profile and profile.user_type == UserProfile.UserType.HR:
        is_hr = True

    if not profile and not is_hr:
        return redirect("core:home")

    if is_hr:
        from hr.views import _render_page
        return _render_page(
            request,
            "core/notifications_content.html",
            "Notifications",
            "notifications",
        )
    
    branch_staff = []
    if profile.user_type == UserProfile.UserType.BRANCH:
        from staff.models import Staff
        manager = getattr(request.user, "branch_manager_profile", None)
        if manager and manager.branch:
            branch_staff = Staff.objects.filter(branch=manager.branch).select_related("user")

    from core.portal import render_portal_page
    return render_portal_page(
        request,
        profile.user_type,
        "core/notifications_content.html",
        "Notifications",
        active_nav="notifications",
        branch_staff=branch_staff,
    )

@login_required
@require_http_methods(["POST"])
def assign_renewal_staff(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.user_type != UserProfile.UserType.BRANCH:
        messages.error(request, "Only Branch Managers can assign renewals.")
        return redirect("core:notifications")
        
    lead_id = request.POST.get("lead_id")
    staff_id = request.POST.get("staff_id")
    
    from core.models import Lead
    from django.contrib.auth import get_user_model
    User = get_user_model()
    from django.shortcuts import get_object_or_404
    
    manager = getattr(request.user, "branch_manager_profile", None)
    if not manager or not manager.branch:
        return redirect("core:notifications")
        
    lead = get_object_or_404(Lead, pk=lead_id, branch=manager.branch)
    
    if staff_id:
        staff_user = get_object_or_404(User, pk=staff_id)
        # Ensure the staff is actually in this branch
        if not getattr(staff_user, "staff_profile", None) or staff_user.staff_profile.branch != manager.branch:
            messages.error(request, "Selected staff is not in your branch.")
            return redirect("core:notifications")
        lead.renewal_assigned_to = staff_user
        messages.success(request, f"Renewal assigned to {staff_user.get_full_name() or staff_user.username}.")
    else:
        lead.renewal_assigned_to = None
        messages.success(request, "Renewal assignment removed.")
        
    lead.save()
    return redirect("core:notifications")
