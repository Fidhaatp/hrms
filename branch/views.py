from core.branch_target_utils import (
    branch_active_staff,
    branch_target_summary,
    save_branch_staff_targets,
)
from core.branch_target_utils import branch_target_summary
from core.dashboard_metrics import branch_dashboard
from core.lead_portal import branch_all_leads_list_view, branch_lead_history_view
from core.lead_calendar import branch_expiry_leads_queryset, service_expiry_calendar_view
from core.models import UserProfile
from core.portal import portal_role_required, render_portal_page
from core.portal_pages import branch_staff_rows
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from followup.models import FollowUp

from .reports import (
    REPORT_CHOICES,
    build_branch_report_rows,
    parse_report_dates,
    parse_report_type,
    branch_report_download_response,
)

all_leads = branch_all_leads_list_view()
lead_history = branch_lead_history_view()
calendar = service_expiry_calendar_view(
    UserProfile.UserType.BRANCH,
    branch_expiry_leads_queryset,
    "branch:calendar",
)


def _manager_branch(request):
    manager = getattr(request.user, "branch_manager_profile", None)
    return manager.branch if manager else None


@portal_role_required(UserProfile.UserType.BRANCH)
def index(request):
    branch_manager = getattr(request.user, "branch_manager_profile", None)
    branch = branch_manager.branch if branch_manager else None
    metrics = branch_dashboard(branch)
    target_summary = branch_target_summary(branch)
    return render_portal_page(
        request,
        UserProfile.UserType.BRANCH,
        "branch/dashboard.html",
        "Dashboard",
        branch_manager=branch_manager,
        branch=branch,
        metrics=metrics,
        target_summary=target_summary,
        recent_leads=metrics.get("recent_leads", []),
        dashboard_charts_json=metrics.get("charts_json", "{}"),
        chart_subtitle=metrics.get("chart_subtitle", ""),
    )


@portal_role_required(UserProfile.UserType.BRANCH)
@require_http_methods(["GET", "POST"])
def staff(request):
    branch = _manager_branch(request)
    target_summary = branch_target_summary(branch)
    show_target_modal = request.GET.get("assign_targets") == "1"

    if request.method == "POST" and branch:
        staff_amounts = {}
        for member in branch_active_staff(branch):
            staff_amounts[member.pk] = request.POST.get(f"staff_target_{member.pk}", "0")
        try:
            save_branch_staff_targets(
                branch,
                request.user,
                request.POST.get("branch_target_amount", "0"),
                staff_amounts,
            )
            messages.success(request, "Branch target split saved for staff.")
            return redirect("branch:staff")
        except ValueError as exc:
            messages.error(request, str(exc))
            show_target_modal = True

    return render_portal_page(
        request,
        UserProfile.UserType.BRANCH,
        "branch/staff.html",
        "Staff",
        active_nav="staff",
        branch=branch,
        staff_members=branch_staff_rows(branch),
        target_summary=target_summary,
        show_target_modal=show_target_modal,
    )


@portal_role_required(UserProfile.UserType.BRANCH)
def followup_team(request):
    branch = _manager_branch(request)
    members = (
        FollowUp.objects.filter(branch=branch, is_active=True).select_related("user").order_by("user__first_name")
        if branch
        else FollowUp.objects.none()
    )
    return render_portal_page(
        request,
        UserProfile.UserType.BRANCH,
        "branch/followup.html",
        "Follow-up team",
        active_nav="followup",
        branch=branch,
        followup_members=members,
    )


@portal_role_required(UserProfile.UserType.BRANCH)
def reports(request):
    branch = _manager_branch(request)
    date_from, date_to = parse_report_dates(request)
    report_type = parse_report_type(request)
    lead_rows, case_rows = build_branch_report_rows(branch, report_type, date_from, date_to)
    return render_portal_page(
        request,
        UserProfile.UserType.BRANCH,
        "branch/reports.html",
        "Reports",
        active_nav="reports",
        branch=branch,
        report_type=report_type,
        report_choices=REPORT_CHOICES,
        date_from=date_from,
        date_to=date_to,
        lead_rows=lead_rows,
        case_rows=case_rows,
    )


@portal_role_required(UserProfile.UserType.BRANCH)
def reports_download(request):
    branch = _manager_branch(request)
    date_from, date_to = parse_report_dates(request)
    report_type = parse_report_type(request)
    return branch_report_download_response(branch, report_type, date_from, date_to)
