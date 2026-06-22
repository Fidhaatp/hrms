from core.dashboard_metrics import employee_dashboard, staff_dashboard_metrics
from core.leave_portal import leave_add_view, leave_list_view
from core.leave_utils import all_leave_summaries, leave_summary
from core.lead_portal import (
    staff_lead_add_view,
    staff_lead_edit_view,
    staff_lead_list_view,
    staff_lead_status_view,
    staff_lead_update_view,
)
from core.lead_calendar import (
    branch_expiry_leads_queryset,
    followup_expiry_leads_queryset,
    service_expiry_calendar_view,
    staff_expiry_leads_queryset,
)
from core.models import EmployeeTarget, LeaveRequest, UserProfile
from core.portal import portal_role_required, render_portal_page
from core.portal_pages import lead_pipeline_steps, render_module
from django.utils import timezone

leave_list = leave_list_view(UserProfile.UserType.STAFF)
leave_add = leave_add_view(UserProfile.UserType.STAFF)
lead_list = staff_lead_list_view()
lead_add = staff_lead_add_view()
lead_edit = staff_lead_edit_view()
lead_update = staff_lead_update_view()
lead_status = staff_lead_status_view()
calendar = service_expiry_calendar_view(
    UserProfile.UserType.STAFF,
    staff_expiry_leads_queryset,
    "staff:calendar",
)


@portal_role_required(UserProfile.UserType.STAFF)
def index(request):
    staff_profile = getattr(request.user, "staff_profile", None)
    balances = all_leave_summaries(request.user)
    summary = next(
        (b for b in balances if b["leave_category"].code == "yearly"),
        leave_summary(request.user),
    )
    pending_leave = LeaveRequest.objects.filter(
        user=request.user,
        status=LeaveRequest.Status.PENDING,
    ).count()
    lead_dashboard = staff_dashboard_metrics(request.user)
    return render_portal_page(
        request,
        UserProfile.UserType.STAFF,
        "staff/dashboard.html",
        "Dashboard",
        staff_profile=staff_profile,
        lead_stats=lead_dashboard["stats"],
        recent_leads=lead_dashboard["recent_leads"],
        action_leads=lead_dashboard["action_leads"],
        recent_activity=lead_dashboard["recent_activity"],
        dashboard_charts_json=lead_dashboard["charts_json"],
        chart_subtitle=lead_dashboard["charts"]["monthly"].get("subtitle", ""),
        leave_summary=summary,
        pending_leave_count=pending_leave,
        metrics=employee_dashboard(request.user),
    )


@portal_role_required(UserProfile.UserType.STAFF)
def pipeline(request):
    return render_module(
        request,
        UserProfile.UserType.STAFF,
        page_title="Sales Pipeline",
        active_nav="pipeline",
        module_title="Sales Pipeline",
        module_intro="Track leads from new contact through conversion, then handover to Follow-up team.",
        workflow_steps=lead_pipeline_steps() + ["Handover → Follow Up"],
    )


@portal_role_required(UserProfile.UserType.STAFF)
def targets(request):
    today = timezone.localdate()
    target = EmployeeTarget.objects.filter(
        user=request.user,
        period_month=today.month,
        period_year=today.year,
    ).first()
    metrics = employee_dashboard(request.user)
    target_breakdown = metrics["target_breakdown"]
    return render_portal_page(
        request,
        UserProfile.UserType.STAFF,
        "staff/targets.html",
        "Targets",
        active_nav="targets",
        target_breakdown=target_breakdown,
        metrics=metrics,
    )
