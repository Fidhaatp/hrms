from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from branch.models import Branch, BranchManager
from core.auth_utils import redirect_user_after_login
from core.forms import ProfilePictureForm
from core.profile_page import build_portal_profile_context
from core.profile_utils import get_avatar_context
from backoffice.models import BackOffice
from followup.models import FollowUp
from finance.models import Finance
from marketing.models import Marketing
from hr.forms import (
    BackOfficeForm,
    BackOfficeProfileEditForm,
    BranchForm,
    BranchManagerEditForm,
    BranchManagerForm,
    FinanceForm,
    FollowUpForm,
    HRRegistrationForm,
    MarketingForm,
    OrgTeamProfileEditForm,
    StaffForm,
    StaffProfileEditForm,
    TeamProfileEditForm,
)
from core.dashboard_metrics import (
    awards_dashboard,
    hr_dashboard,
    hr_dashboard_leads,
    operations_dashboard,
    organization_analytics,
)
from core.lead_forms import LeadServiceForm, LeadSourceForm, LeadStatusForm
from core.lead_utils import converted_leads_filter
from core.leave_forms import LeaveCategoryForm, LeaveTypeForm
from core.countries import COUNTRY_NAMES
from core.models import (
    ApprovalStatus,
    EmployeeCompliance,
    LeaveCategory,
    LeaveRequest,
    LeaveType,
    PaymentRequest,
    RecruitmentRequest,
    RejoiningRequest,
    SalaryIncrementRequest,
    UserProfile,
)
from hr.nav import hr_nav_sections
from staff.models import Staff


def _hr_user_context(user):
    hr = getattr(user, "hr_profile", None)
    avatar = get_avatar_context(user)
    profile = getattr(user, "profile", None)
    return {
        "hr_profile": hr,
        "hr_display_name": avatar["display_name"],
        "hr_initials": avatar["initials"],
        "hr_avatar_url": avatar["avatar_url"],
        "hr_role": "HR",
        "portal_profile_url_name": profile.get_profile_url_name() if profile else "hr:profile",
    }


def _render_page(request, content_template, page_title, active_nav, **extra):
    context = {
        "page_title": page_title,
        "content_template": content_template,
        "active_nav": active_nav,
        "hr_nav_sections": hr_nav_sections(),
        "portal_home_url_name": "hr:dashboard",
        **_hr_user_context(request.user),
        **extra,
    }
    return render(request, "hr/base.html", context)


def _profile_url():
    return reverse("hr:profile")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def profile_picture_update(request):
    profile = getattr(request.user, "profile", None)
    if not profile:
        messages.error(request, "Profile not found.")
        return redirect(_profile_url())

    form = ProfilePictureForm(request.POST, request.FILES, instance=profile)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile picture updated.")
    else:
        messages.error(request, "Could not update profile picture. Please use a valid image file.")
    return redirect(_profile_url())


@login_required(login_url="core:login")
def profile(request):
    return _render_page(
        request,
        "portal/pages/profile.html",
        "My Profile",
        "profile",
        **build_portal_profile_context(request.user),
    )


@login_required(login_url="core:login")
def dashboard(request):
    lead_dashboard = hr_dashboard_leads()
    return _render_page(
        request,
        "hr/dashboard.html",
        "Dashboard",
        "dashboard",
        metrics=hr_dashboard(),
        lead_stats=lead_dashboard["stats"],
        dashboard_charts_json=lead_dashboard["charts_json"],
        chart_subtitle=lead_dashboard["charts"]["monthly"].get("subtitle", ""),
        recent_leads=lead_dashboard["recent_leads"],
        recent_activity=lead_dashboard["recent_activity"],
        awards=awards_dashboard(),
        operations=operations_dashboard(),
    )


@login_required(login_url="core:login")
def leads(request):
    from core.lead_filters import (
        apply_lead_list_filters,
        filters_are_active,
        lead_filter_context,
        parse_lead_list_filters,
    )
    from core.models import Lead

    filters = parse_lead_list_filters(request)
    queryset = apply_lead_list_filters(
        Lead.objects.select_related(
            "created_by",
            "branch",
            "backoffice_checked_by",
            "followup_assigned_to",
            "source",
            "staff_status",
            "followup_status",
            "created_by__staff_profile__branch",
        ),
        filters,
    )
    return _render_page(
        request,
        "hr/pages/leads.html",
        "Lead Management",
        "leads",
        leads=queryset[:500],
        filters_active=filters_are_active(filters),
        **lead_filter_context(filters, show_staff=True, show_followup=True, show_backoffice=True),
    )


def _branches_queryset():
    return Branch.objects.prefetch_related(
        Prefetch(
            "managers",
            queryset=BranchManager.objects.select_related("user").order_by("-is_active", "user__username"),
        )
    ).order_by("-is_deleted", "-created_at")


def _branch_page_context(**extra):
    defaults = {
        "branches": _branches_queryset(),
        "add_form": BranchForm(),
        "manager_form": BranchManagerForm(prefix="mgr", hide_branch=True),
        "standalone_manager_form": BranchManagerForm(branch_required=True),
        "edit_form": None,
        "edit_branch": None,
        "show_add_modal": False,
        "show_edit_modal": False,
        "show_manager_modal": False,
        "add_manager_checked": False,
        "country_choices": COUNTRY_NAMES,
    }
    defaults.update(extra)
    return defaults


def _branch_managers_queryset():
    return BranchManager.objects.select_related("user", "user__team_documents", "branch").order_by(
        "-is_active", "-created_at"
    )


def _active_branches():
    return Branch.active.all().order_by("name")


def _branch_manager_page_context(**extra):
    defaults = {
        "branch_managers": _branch_managers_queryset(),
        "standalone_manager_form": BranchManagerForm(branch_required=True),
        "show_manager_modal": False,
        "active_branches": _active_branches(),
        "edit_manager": None,
        "manager_edit_form": None,
        "show_manager_edit_modal": False,
    }
    defaults.update(extra)
    return defaults


@login_required(login_url="core:login")
def branch_managers(request):
    return _render_page(
        request,
        "hr/pages/branch_managers.html",
        "Branch Managers",
        "branch_managers",
        **_branch_manager_page_context(),
    )


@login_required(login_url="core:login")
def branches(request):
    return _render_page(
        request,
        "hr/pages/branches.html",
        "Branches",
        "branches",
        **_branch_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def branch_add(request):
    branch_form = BranchForm(request.POST)
    add_manager = request.POST.get("add_manager") == "on"
    manager_form = (
        BranchManagerForm(request.POST, request.FILES, prefix="mgr", hide_branch=True)
        if add_manager
        else None
    )

    branch_valid = branch_form.is_valid()
    manager_valid = manager_form.is_valid() if manager_form else True

    if branch_valid and manager_valid:
        with transaction.atomic():
            branch = branch_form.save()
            if manager_form:
                manager_form.save(branch=branch)
                messages.success(
                    request,
                    f'Branch "{branch.name}" and manager "{manager_form.cleaned_data["username"]}" created.',
                )
            else:
                messages.success(request, f'Branch "{branch.name}" added successfully.')
        return redirect("hr:branches")

    return _render_page(
        request,
        "hr/pages/branches.html",
        "Branches",
        "branches",
        **_branch_page_context(
            add_form=branch_form,
            manager_form=manager_form or BranchManagerForm(prefix="mgr", hide_branch=True),
            show_add_modal=True,
            add_manager_checked=add_manager,
        ),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def branch_manager_add(request):
    form = BranchManagerForm(request.POST, request.FILES, branch_required=True)
    if form.is_valid():
        manager = form.save()
        messages.success(
            request,
            f'Branch manager "{manager.username}" added to "{manager.branch.name}".',
        )
        return redirect("hr:branch_managers")

    return _render_page(
        request,
        "hr/pages/branch_managers.html",
        "Branch Managers",
        "branch_managers",
        **_branch_manager_page_context(standalone_manager_form=form, show_manager_modal=True),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def branch_edit(request, pk):
    branch = get_object_or_404(Branch.active, pk=pk)
    form = BranchForm(request.POST, instance=branch)
    if form.is_valid():
        form.save()
        messages.success(request, f'Branch "{form.instance.name}" updated successfully.')
        return redirect("hr:branches")

    return _render_page(
        request,
        "hr/pages/branches.html",
        "Branches",
        "branches",
        **_branch_page_context(edit_form=form, edit_branch=branch, show_edit_modal=True),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def branch_deactivate(request, pk):
    branch = get_object_or_404(Branch.active, pk=pk)
    name = branch.name
    branch.deactivate()
    for manager in branch.managers.filter(is_active=True):
        manager.deactivate()
    messages.success(request, f'Branch "{name}" has been deactivated.')
    return redirect("hr:branches")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def branch_reactivate(request, pk):
    branch = get_object_or_404(Branch.objects.filter(is_deleted=True), pk=pk)
    name = branch.name
    branch.reactivate()
    messages.success(request, f'Branch "{name}" has been activated.')
    return redirect("hr:branches")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def branch_manager_edit(request, pk):
    manager = get_object_or_404(
        BranchManager.objects.select_related("user", "branch"),
        pk=pk,
        branch__is_deleted=False,
    )
    form = BranchManagerEditForm(manager, request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, f'Branch manager "{manager.username}" updated successfully.')
        return redirect("hr:branch_managers")

    return _render_page(
        request,
        "hr/pages/branch_managers.html",
        "Branch Managers",
        "branch_managers",
        **_branch_manager_page_context(
            manager_edit_form=form,
            edit_manager=manager,
            show_manager_edit_modal=True,
        ),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def branch_manager_deactivate(request, pk):
    manager = get_object_or_404(BranchManager, pk=pk, is_active=True, branch__is_deleted=False)
    name = manager.username
    manager.deactivate()
    messages.success(request, f'Branch manager "{name}" has been deactivated.')
    return redirect("hr:branch_managers")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def branch_manager_reactivate(request, pk):
    manager = get_object_or_404(BranchManager, pk=pk, is_active=False)
    try:
        manager.reactivate()
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("hr:branch_managers")
    messages.success(request, f'Branch manager "{manager.username}" has been activated.')
    return redirect("hr:branch_managers")


def _staff_queryset():
    return Staff.objects.select_related("user", "user__team_documents", "branch").order_by("-is_active", "-created_at")


def _staff_page_context(**extra):
    defaults = {
        "staff_members": _staff_queryset(),
        "staff_form": StaffForm(),
        "show_staff_modal": False,
        "active_branches": _active_branches(),
        "edit_staff": None,
        "staff_edit_form": None,
        "show_staff_edit_modal": False,
    }
    defaults.update(extra)
    return defaults


@login_required(login_url="core:login")
def staff_list(request):
    return _render_page(
        request,
        "hr/pages/staff.html",
        "Staff",
        "staff",
        **_staff_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def staff_add(request):
    form = StaffForm(request.POST, request.FILES)
    if form.is_valid():
        member = form.save()
        messages.success(request, f'Staff profile "{member.username}" created successfully.')
        return redirect("hr:staff_list")

    return _render_page(
        request,
        "hr/pages/staff.html",
        "Staff",
        "staff",
        **_staff_page_context(staff_form=form, show_staff_modal=True),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def staff_edit(request, pk):
    member = get_object_or_404(Staff.objects.select_related("user", "branch"), pk=pk)
    form = StaffProfileEditForm(member, request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, f'Staff "{member.username}" updated successfully.')
        return redirect("hr:staff_list")

    return _render_page(
        request,
        "hr/pages/staff.html",
        "Staff",
        "staff",
        **_staff_page_context(
            staff_edit_form=form,
            edit_staff=member,
            show_staff_edit_modal=True,
        ),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def staff_deactivate(request, pk):
    member = get_object_or_404(Staff, pk=pk, is_active=True)
    name = member.username
    member.deactivate()
    messages.success(request, f'Staff "{name}" has been deactivated.')
    return redirect("hr:staff_list")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def staff_reactivate(request, pk):
    member = get_object_or_404(Staff, pk=pk, is_active=False)
    member.reactivate()
    messages.success(request, f'Staff "{member.username}" has been activated.')
    return redirect("hr:staff_list")


def _followup_queryset():
    return FollowUp.objects.select_related("user", "user__team_documents", "branch").order_by("-is_active", "-created_at")


def _followup_page_context(**extra):
    defaults = {
        "team_members": _followup_queryset(),
        "team_form": FollowUpForm(),
        "show_team_modal": False,
        "active_branches": _active_branches(),
        "edit_member": None,
        "team_edit_form": None,
        "show_team_edit_modal": False,
    }
    defaults.update(extra)
    return defaults


@login_required(login_url="core:login")
def followup_list(request):
    return _render_page(
        request,
        "hr/pages/followup.html",
        "Follow-up Team",
        "followup",
        **_followup_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def followup_add(request):
    form = FollowUpForm(request.POST, request.FILES)
    if form.is_valid():
        member = form.save()
        messages.success(request, f'Follow-up profile "{member.username}" created successfully.')
        return redirect("hr:followup_list")

    return _render_page(
        request,
        "hr/pages/followup.html",
        "Follow-up Team",
        "followup",
        **_followup_page_context(team_form=form, show_team_modal=True),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def followup_edit(request, pk):
    member = get_object_or_404(FollowUp.objects.select_related("user", "branch"), pk=pk)
    form = TeamProfileEditForm(member, request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, f'Follow-up member "{member.username}" updated successfully.')
        return redirect("hr:followup_list")

    return _render_page(
        request,
        "hr/pages/followup.html",
        "Follow-up Team",
        "followup",
        **_followup_page_context(
            team_edit_form=form,
            edit_member=member,
            show_team_edit_modal=True,
        ),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def followup_deactivate(request, pk):
    member = get_object_or_404(FollowUp, pk=pk, is_active=True)
    name = member.username
    member.deactivate()
    messages.success(request, f'Follow-up member "{name}" has been deactivated.')
    return redirect("hr:followup_list")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def followup_reactivate(request, pk):
    member = get_object_or_404(FollowUp, pk=pk, is_active=False)
    member.reactivate()
    messages.success(request, f'Follow-up member "{member.username}" has been activated.')
    return redirect("hr:followup_list")


def _backoffice_queryset():
    return BackOffice.objects.select_related("user", "user__team_documents", "branch").order_by("-is_active", "-created_at")


def _backoffice_page_context(**extra):
    defaults = {
        "team_members": _backoffice_queryset(),
        "team_form": BackOfficeForm(),
        "show_team_modal": False,
        "active_branches": _active_branches(),
        "edit_member": None,
        "team_edit_form": None,
        "show_team_edit_modal": False,
    }
    defaults.update(extra)
    return defaults


@login_required(login_url="core:login")
def backoffice_list(request):
    return _render_page(
        request,
        "hr/pages/backoffice.html",
        "Back Office Team",
        "backoffice",
        **_backoffice_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def backoffice_add(request):
    form = BackOfficeForm(request.POST, request.FILES)
    if form.is_valid():
        member = form.save()
        messages.success(request, f'Back office profile "{member.username}" created successfully.')
        return redirect("hr:backoffice_list")

    return _render_page(
        request,
        "hr/pages/backoffice.html",
        "Back Office Team",
        "backoffice",
        **_backoffice_page_context(team_form=form, show_team_modal=True),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def backoffice_edit(request, pk):
    member = get_object_or_404(BackOffice.objects.select_related("user", "branch"), pk=pk)
    form = BackOfficeProfileEditForm(member, request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, f'Back office member "{member.username}" updated successfully.')
        return redirect("hr:backoffice_list")

    return _render_page(
        request,
        "hr/pages/backoffice.html",
        "Back Office Team",
        "backoffice",
        **_backoffice_page_context(
            team_edit_form=form,
            edit_member=member,
            show_team_edit_modal=True,
        ),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def backoffice_deactivate(request, pk):
    member = get_object_or_404(BackOffice, pk=pk, is_active=True)
    name = member.username
    member.deactivate()
    messages.success(request, f'Back office member "{name}" has been deactivated.')
    return redirect("hr:backoffice_list")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def backoffice_reactivate(request, pk):
    member = get_object_or_404(BackOffice, pk=pk, is_active=False)
    member.reactivate()
    messages.success(request, f'Back office member "{member.username}" has been activated.')
    return redirect("hr:backoffice_list")


def _finance_queryset():
    return Finance.objects.select_related("user", "user__team_documents", "branch").order_by("-is_active", "-created_at")


def _finance_page_context(**extra):
    defaults = {
        "team_members": _finance_queryset(),
        "team_form": FinanceForm(),
        "show_team_modal": False,
        "edit_member": None,
        "team_edit_form": None,
        "show_team_edit_modal": False,
    }
    defaults.update(extra)
    return defaults


@login_required(login_url="core:login")
def finance_list(request):
    return _render_page(
        request,
        "hr/pages/finance.html",
        "Finance Team",
        "finance",
        **_finance_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def finance_add(request):
    form = FinanceForm(request.POST, request.FILES)
    if form.is_valid():
        member = form.save()
        messages.success(request, f'Finance profile "{member.username}" created successfully.')
        return redirect("hr:finance_list")

    return _render_page(
        request,
        "hr/pages/finance.html",
        "Finance Team",
        "finance",
        **_finance_page_context(team_form=form, show_team_modal=True),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def finance_edit(request, pk):
    member = get_object_or_404(Finance.objects.select_related("user"), pk=pk)
    form = OrgTeamProfileEditForm(member, request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, f'Finance member "{member.username}" updated successfully.')
        return redirect("hr:finance_list")

    return _render_page(
        request,
        "hr/pages/finance.html",
        "Finance Team",
        "finance",
        **_finance_page_context(
            team_edit_form=form,
            edit_member=member,
            show_team_edit_modal=True,
        ),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def finance_deactivate(request, pk):
    member = get_object_or_404(Finance, pk=pk, is_active=True)
    name = member.username
    member.deactivate()
    messages.success(request, f'Finance member "{name}" has been deactivated.')
    return redirect("hr:finance_list")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def finance_reactivate(request, pk):
    member = get_object_or_404(Finance, pk=pk, is_active=False)
    member.reactivate()
    messages.success(request, f'Finance member "{member.username}" has been activated.')
    return redirect("hr:finance_list")


def _marketing_queryset():
    return Marketing.objects.select_related("user", "user__team_documents", "branch").order_by("-is_active", "-created_at")


def _marketing_page_context(**extra):
    defaults = {
        "team_members": _marketing_queryset(),
        "team_form": MarketingForm(),
        "show_team_modal": False,
        "edit_member": None,
        "team_edit_form": None,
        "show_team_edit_modal": False,
    }
    defaults.update(extra)
    return defaults


@login_required(login_url="core:login")
def marketing_list(request):
    return _render_page(
        request,
        "hr/pages/marketing.html",
        "Marketing Team",
        "marketing",
        **_marketing_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def marketing_add(request):
    form = MarketingForm(request.POST, request.FILES)
    if form.is_valid():
        member = form.save()
        messages.success(request, f'Marketing profile "{member.username}" created successfully.')
        return redirect("hr:marketing_list")

    return _render_page(
        request,
        "hr/pages/marketing.html",
        "Marketing Team",
        "marketing",
        **_marketing_page_context(team_form=form, show_team_modal=True),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def marketing_edit(request, pk):
    member = get_object_or_404(Marketing.objects.select_related("user"), pk=pk)
    form = OrgTeamProfileEditForm(member, request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, f'Marketing member "{member.username}" updated successfully.')
        return redirect("hr:marketing_list")

    return _render_page(
        request,
        "hr/pages/marketing.html",
        "Marketing Team",
        "marketing",
        **_marketing_page_context(
            team_edit_form=form,
            edit_member=member,
            show_team_edit_modal=True,
        ),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def marketing_deactivate(request, pk):
    member = get_object_or_404(Marketing, pk=pk, is_active=True)
    name = member.username
    member.deactivate()
    messages.success(request, f'Marketing member "{name}" has been deactivated.')
    return redirect("hr:marketing_list")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def marketing_reactivate(request, pk):
    member = get_object_or_404(Marketing, pk=pk, is_active=False)
    member.reactivate()
    messages.success(request, f'Marketing member "{member.username}" has been activated.')
    return redirect("hr:marketing_list")


def _leave_requests_queryset(status_filter=None):
    qs = team_leave_requests_queryset()
    if status_filter and status_filter != "all":
        qs = qs.filter(status=status_filter)
    return qs


def _leave_requests_page_context(**extra):
    status_filter = extra.pop("status_filter", "all")
    qs = team_leave_requests_queryset()
    if status_filter and status_filter != "all":
        qs = qs.filter(status=status_filter)
    defaults = {
        "leave_requests": qs,
        "status_filter": status_filter,
        "pending_count": hr_actionable_leave_requests_queryset().count(),
    }
    defaults.update(extra)
    return defaults


def _leave_categories_page_context(**extra):
    defaults = {
        "leave_categories": LeaveCategory.objects.order_by("name"),
        "leave_category_form": LeaveCategoryForm(),
        "show_leave_category_modal": False,
    }
    defaults.update(extra)
    return defaults


def _leave_types_page_context(**extra):
    defaults = {
        "leave_types": LeaveType.objects.order_by("name"),
        "leave_type_form": LeaveTypeForm(),
        "show_leave_type_modal": False,
    }
    defaults.update(extra)
    return defaults


def _lead_sources_page_context(**extra):
    from core.models import LeadSource

    defaults = {
        "lead_sources": LeadSource.objects.order_by("sort_order", "name"),
        "lead_source_form": LeadSourceForm(),
        "show_lead_source_modal": False,
    }
    defaults.update(extra)
    return defaults


def _lead_statuses_page_context(**extra):
    from core.models import LeadStatus

    defaults = {
        "lead_statuses": LeadStatus.objects.order_by("sort_order", "name"),
        "lead_status_form": LeadStatusForm(),
        "show_lead_status_modal": False,
    }
    defaults.update(extra)
    return defaults


def _lead_services_page_context(**extra):
    from core.models import LeadService

    defaults = {
        "lead_services": LeadService.objects.order_by("sort_order", "name"),
        "lead_service_form": LeadServiceForm(),
        "show_lead_service_modal": False,
    }
    defaults.update(extra)
    return defaults


@login_required(login_url="core:login")
def leave_requests(request):
    status_filter = request.GET.get("status", "all")
    return _render_page(
        request,
        "hr/pages/leave_requests.html",
        "Leave Requests",
        "leave_requests",
        **_leave_requests_page_context(status_filter=status_filter),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def leave_approve(request, pk):
    leave_req = get_object_or_404(LeaveRequest, pk=pk)
    if leave_req.user.profile.user_type not in (
        UserProfile.UserType.STAFF,
        UserProfile.UserType.FOLLOWUP,
        UserProfile.UserType.BACKOFFICE,
    ):
        messages.error(request, "This leave request cannot be managed here.")
        return redirect("hr:leave_requests")
    if leave_req.workflow_stage not in (
        LeaveRequest.WorkflowStage.PENDING_HR,
        LeaveRequest.WorkflowStage.PENDING_MANAGER,
    ):
        messages.error(request, "This leave request is no longer pending.")
        return redirect("hr:leave_requests")
    leave_req.approve_by_hr(request.user, request.POST.get("hr_note", ""))
    messages.success(
        request,
        f'Approved {leave_req.leave_type.name} ({leave_req.leave_category.name}) for '
        f'{leave_req.user.get_username()} ({leave_req.start_date} – {leave_req.end_date}).',
    )
    return redirect("hr:leave_requests")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def leave_reject(request, pk):
    leave_req = get_object_or_404(LeaveRequest, pk=pk)
    if leave_req.user.profile.user_type not in (
        UserProfile.UserType.STAFF,
        UserProfile.UserType.FOLLOWUP,
        UserProfile.UserType.BACKOFFICE,
    ):
        messages.error(request, "This leave request cannot be managed here.")
        return redirect("hr:leave_requests")
    if leave_req.workflow_stage in (
        LeaveRequest.WorkflowStage.PENDING_HR,
        LeaveRequest.WorkflowStage.PENDING_MANAGER,
    ):
        leave_req.reject_by_hr(request.user, request.POST.get("hr_note", ""))
    else:
        messages.error(request, "This leave request is no longer pending.")
        return redirect("hr:leave_requests")
    messages.success(
        request,
        f'Rejected leave request for {leave_req.user.get_username()}.',
    )
    return redirect("hr:leave_requests")


@login_required(login_url="core:login")
def leave_categories(request):
    return _render_page(
        request,
        "hr/pages/leave_categories.html",
        "Leave Categories",
        "leave_categories",
        **_leave_categories_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def leave_category_add(request):
    form = LeaveCategoryForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f'Leave category "{form.cleaned_data["name"]}" added.')
        return redirect("hr:leave_categories")

    return _render_page(
        request,
        "hr/pages/leave_categories.html",
        "Leave Categories",
        "leave_categories",
        **_leave_categories_page_context(leave_category_form=form, show_leave_category_modal=True),
    )


@login_required(login_url="core:login")
def leave_types(request):
    return _render_page(
        request,
        "hr/pages/leave_types.html",
        "Leave Types",
        "leave_types",
        **_leave_types_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def leave_type_add(request):
    form = LeaveTypeForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f'Leave type "{form.cleaned_data["name"]}" added.')
        return redirect("hr:leave_types")

    return _render_page(
        request,
        "hr/pages/leave_types.html",
        "Leave Types",
        "leave_types",
        **_leave_types_page_context(leave_type_form=form, show_leave_type_modal=True),
    )


@login_required(login_url="core:login")
def lead_sources(request):
    return _render_page(
        request,
        "hr/pages/lead_sources.html",
        "Lead Sources",
        "lead_sources",
        **_lead_sources_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def lead_source_add(request):
    form = LeadSourceForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f'Lead source "{form.cleaned_data["name"]}" added.')
        return redirect("hr:lead_sources")

    return _render_page(
        request,
        "hr/pages/lead_sources.html",
        "Lead Sources",
        "lead_sources",
        **_lead_sources_page_context(lead_source_form=form, show_lead_source_modal=True),
    )


@login_required(login_url="core:login")
def lead_statuses(request):
    return _render_page(
        request,
        "hr/pages/lead_statuses.html",
        "Lead Statuses",
        "lead_statuses",
        **_lead_statuses_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def lead_status_add(request):
    form = LeadStatusForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f'Lead status "{form.cleaned_data["name"]}" added.')
        return redirect("hr:lead_statuses")

    return _render_page(
        request,
        "hr/pages/lead_statuses.html",
        "Lead Statuses",
        "lead_statuses",
        **_lead_statuses_page_context(lead_status_form=form, show_lead_status_modal=True),
    )


@login_required(login_url="core:login")
def lead_services(request):
    return _render_page(
        request,
        "hr/pages/lead_services.html",
        "Lead Services",
        "lead_services",
        **_lead_services_page_context(),
    )


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def lead_service_add(request):
    form = LeadServiceForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, f'Lead service "{form.cleaned_data["name"]}" added.')
        return redirect("hr:lead_services")

    return _render_page(
        request,
        "hr/pages/lead_services.html",
        "Lead Services",
        "lead_services",
        **_lead_services_page_context(lead_service_form=form, show_lead_service_modal=True),
    )


@login_required(login_url="core:login")
def org_database(request):
    return _render_page(
        request,
        "hr/pages/org_database.html",
        "Organization Database",
        "org_database",
        staff_members=Staff.objects.select_related("user", "branch").order_by("-is_active", "-created_at"),
        followup_members=FollowUp.objects.select_related("user", "branch").order_by("-is_active", "-created_at"),
        backoffice_members=BackOffice.objects.select_related("user", "branch").order_by("-is_active", "-created_at"),
        branch_managers=BranchManager.objects.select_related("user", "branch").order_by("-is_active", "-created_at"),
        finance_members=Finance.objects.select_related("user").order_by("-is_active", "-created_at"),
        marketing_members=Marketing.objects.select_related("user").order_by("-is_active", "-created_at"),
        branches=Branch.objects.order_by("-is_deleted", "-created_at"),
    )


def _approval_dashboard_context():
    leave_qs = hr_pending_leave_requests_queryset()
    return {
        "leave_requests": leave_qs[:15],
        "approval_pending_counts": {
            "leave": leave_qs.count(),
            "increment": 0,
            "rejoining": 0,
            "payment": 0,
        },
    }


@login_required(login_url="core:login")
def approvals(request):
    return _render_page(
        request,
        "hr/pages/approvals.html",
        "Approvals",
        "approvals",
        **_approval_dashboard_context(),
    )


def _update_hr_decision(request_obj, item, approved_message, rejected_message):
    decision = request_obj.POST.get("decision", "").lower()
    note = request_obj.POST.get("hr_note", "").strip()
    if decision not in {"approve", "reject"}:
        messages.error(request_obj, "Invalid decision.")
        return False
    item.status = ApprovalStatus.APPROVED if decision == "approve" else ApprovalStatus.REJECTED
    item.hr_note = note
    item.reviewed_by = request_obj.user
    item.reviewed_at = timezone.now()
    item.save(update_fields=["status", "hr_note", "reviewed_by", "reviewed_at", "updated_at"])
    messages.success(request_obj, approved_message if decision == "approve" else rejected_message)
    return True


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def salary_increment_decide(request, pk):
    req = get_object_or_404(SalaryIncrementRequest, pk=pk)
    _update_hr_decision(
        request,
        req,
        f"Salary increment approved for {req.user.get_username()}.",
        f"Salary increment rejected for {req.user.get_username()}.",
    )
    return redirect("hr:approvals")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def rejoining_decide(request, pk):
    req = get_object_or_404(RejoiningRequest, pk=pk)
    _update_hr_decision(
        request,
        req,
        f"Rejoining request approved for {req.user.get_username()}.",
        f"Rejoining request rejected for {req.user.get_username()}.",
    )
    return redirect("hr:approvals")


@login_required(login_url="core:login")
@require_http_methods(["POST"])
def payment_decide(request, pk):
    req = get_object_or_404(PaymentRequest, pk=pk)
    _update_hr_decision(
        request,
        req,
        f"Payment request approved for {req.user.get_username()}.",
        f"Payment request rejected for {req.user.get_username()}.",
    )
    return redirect("hr:approvals")


@login_required(login_url="core:login")
def analytics(request):
    return _render_page(
        request,
        "hr/pages/analytics.html",
        "Organization Analytics",
        "analytics",
        metrics=organization_analytics(),
    )


@login_required(login_url="core:login")
def compliance(request):
    return _render_page(
        request,
        "hr/pages/compliance.html",
        "Compliance Tracking",
        "compliance",
        compliance_records=EmployeeCompliance.objects.select_related("user").order_by("visa_expiry"),
    )


@login_required(login_url="core:login")
def recruitment(request):
    return _render_page(
        request,
        "hr/pages/recruitment.html",
        "Recruitment",
        "recruitment",
        requests=RecruitmentRequest.objects.select_related("branch", "requested_by").order_by("-created_at"),
    )


@login_required(login_url="core:login")
def workflows(request):
    from core.roles import DASHBOARD_METRICS, ROLE_HIERARCHY, WORKFLOWS

    return _render_page(
        request,
        "hr/pages/workflows.html",
        "System Workflows",
        "workflows",
        roles=ROLE_HIERARCHY,
        workflows=WORKFLOWS,
        dashboard_metrics=DASHBOARD_METRICS,
    )


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect_user_after_login(request.user)

    form = HRRegistrationForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "HR account created successfully. Welcome!")
        return redirect("hr:dashboard")

    return render(
        request,
        "hr/account/registration.html",
        {"form": form},
    )
