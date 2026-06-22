from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.auth_utils import redirect_user_after_login
from core.forms import ProfilePictureForm

from core.auth_utils import redirect_user_after_login
from core.models import UserProfile
from core.portal_modules import ADMIN_META, ADMIN_NAV
from core.portal_pages import admin_dashboard_context, quick_link
from core.profile_page import build_portal_profile_context
from core.profile_utils import get_avatar_context
from core.roles import WORKFLOWS


def _admin_context(user, **extra):
    avatar = get_avatar_context(user)
    profile = getattr(user, "profile", None)
    return {
        "portal_display_name": avatar["display_name"],
        "portal_initials": avatar["initials"],
        "portal_avatar_url": avatar["avatar_url"],
        "portal_role": ADMIN_META["role_label"],
        "portal_nav": ADMIN_NAV,
        "portal_home_url_name": ADMIN_META["home_url_name"],
        "portal_brand_sub": ADMIN_META["brand_sub"],
        "portal_profile_url_name": profile.get_profile_url_name() if profile else "admin_portal:profile",
        **extra,
    }


def admin_required(view_func):
    @login_required(login_url="core:login")
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not profile or profile.user_type != UserProfile.UserType.ADMIN:
            return redirect_user_after_login(request.user)
        return view_func(request, *args, **kwargs)

    return _wrapped


def _render(request, template, title, active_nav="dashboard", **extra):
    return render(
        request,
        "admin_portal/base.html",
        {
            "page_title": title,
            "content_template": template,
            "active_nav": active_nav,
            **_admin_context(request.user, **extra),
        },
    )


@admin_required
def dashboard(request):
    ctx = admin_dashboard_context()
    return _render(
        request,
        "admin_portal/dashboard.html",
        "Dashboard",
        metrics=ctx["metrics"],
        awards=ctx["awards"],
        operations=ctx["operations"],
    )


@admin_required
def employees(request):
    return _render(
        request,
        "admin_portal/module.html",
        "Employee Management",
        active_nav="employees",
        module_title="Employee Management",
        module_intro="Add, edit, assign roles, and transfer employees across branches.",
        workflow_steps=["Add Employee", "Assign Role", "Assign Branch", "Transfer"],
        quick_links=[
            quick_link("All staff", "hr:staff_list", "bi-people-fill"),
            quick_link("Org database", "hr:org_database", "bi-database-fill"),
            quick_link("HR portal", "hr:dashboard", "bi-briefcase-fill"),
        ],
    )


@admin_required
def branches(request):
    return _render(
        request,
        "admin_portal/module.html",
        "Branch Management",
        active_nav="branches",
        module_title="Branch Management",
        module_intro="Create branches, set targets, and monitor branch performance.",
        quick_links=[
            quick_link("Manage branches", "hr:branches", "bi-building-fill"),
            quick_link("Branch managers", "hr:branch_managers", "bi-person-badge-fill"),
            quick_link("Analytics", "hr:analytics", "bi-bar-chart-fill"),
        ],
    )


@admin_required
def roles(request):
    return _render(
        request,
        "admin_portal/module.html",
        "Users & Roles",
        active_nav="roles",
        module_title="Users & Role Management",
        module_intro="Manage portal users: Admin, HR, Finance, Marketing, Branch teams.",
        quick_links=[
            quick_link("Staff team", "hr:staff_list", "bi-person-fill"),
            quick_link("Follow-up team", "hr:followup_list", "bi-telephone-fill"),
            quick_link("Back office team", "hr:backoffice_list", "bi-clipboard-check-fill"),
            quick_link("Org database", "hr:org_database", "bi-diagram-3-fill"),
        ],
    )


@admin_required
def reports(request):
    return _render(
        request,
        "admin_portal/module.html",
        "Reports",
        active_nav="reports",
        module_title="Organization Reports",
        module_intro="Revenue, attendance, incentives, and CRM reports.",
        quick_links=[
            quick_link("Analytics", "hr:analytics", "bi-graph-up"),
            quick_link("All leads", "hr:leads", "bi-funnel-fill"),
            quick_link("Leave requests", "hr:leave_requests", "bi-calendar-week"),
        ],
    )


@admin_required
def workflows(request):
    return _render(
        request,
        "admin_portal/module.html",
        "Workflows",
        active_nav="workflows",
        module_title="System Workflows",
        module_intro="CRM, HR, payroll, and recruitment workflows across all portals.",
        workflow_steps=WORKFLOWS["client_processing"]["steps"],
        quick_links=[quick_link("Workflow board", "hr:workflows", "bi-diagram-2-fill")],
    )


@admin_required
def settings(request):
    return _render(
        request,
        "admin_portal/module.html",
        "Settings",
        active_nav="settings",
        module_title="Settings & Policies",
        module_intro="Permissions, HR policies, salary structures, and lead configuration.",
        quick_links=[
            quick_link("Lead sources", "hr:lead_sources", "bi-signpost-split"),
            quick_link("Lead statuses", "hr:lead_statuses", "bi-flag"),
            quick_link("Leave categories", "hr:leave_categories", "bi-calendar-range"),
            quick_link("Compliance", "hr:compliance", "bi-shield-check"),
        ],
    )


@admin_required
def django_admin(request):
    return redirect("/admin/")


@admin_required
def profile(request):
    return _render(
        request,
        "portal/pages/profile.html",
        "My Profile",
        active_nav="profile",
        **build_portal_profile_context(request.user),
    )


@admin_required
@require_http_methods(["POST"])
def profile_picture_update(request):
    profile_obj = getattr(request.user, "profile", None)
    if not profile_obj:
        messages.error(request, "Profile not found.")
        return redirect("admin_portal:profile")

    form = ProfilePictureForm(request.POST, request.FILES, instance=profile_obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile picture updated.")
    else:
        messages.error(request, "Could not update profile picture. Please use a valid image file.")
    return redirect("admin_portal:profile")
