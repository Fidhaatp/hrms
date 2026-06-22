"""Shared module page renderer and context builders."""

from django.db.models import Count, Sum
from django.urls import reverse

from core.dashboard_metrics import (
    awards_dashboard,
    finance_dashboard,
    hr_dashboard,
    marketing_dashboard,
    operations_dashboard,
    organization_analytics,
)
from core.models import (
    Announcement,
    AttendanceRecord,
    ClientCase,
    EmployeeIncentive,
    EmployeeTarget,
    Lead,
    LeaveRequest,
    MarketingCampaign,
    PaymentRequest,
    UserProfile,
)
from core.portal import render_portal_page
from core.roles import WORKFLOWS
from staff.models import Staff


def render_module(
    request,
    user_type,
    *,
    page_title,
    active_nav,
    module_title,
    module_intro="",
    workflow_steps=None,
    quick_links=None,
    stats=None,
    extra_rows=None,
    extra_table_headers=None,
):
    return render_portal_page(
        request,
        user_type,
        "portal/modules/standard.html",
        page_title,
        active_nav=active_nav,
        module_title=module_title,
        module_intro=module_intro,
        workflow_steps=workflow_steps or [],
        quick_links=quick_links or [],
        stats=stats or [],
        extra_rows=extra_rows or [],
        extra_table_headers=extra_table_headers or [],
    )


def quick_link(label, url_name, icon="bi-link-45deg", url_kwargs=None):
    return {
        "label": label,
        "url": reverse(url_name, kwargs=url_kwargs or {}),
        "icon": icon,
    }


def _stats_from_dict(data):
    return [{"label": k, "value": v} for k, v in data.items()]


def admin_dashboard_context():
    from branch.models import Branch

    hr = hr_dashboard()
    ops = operations_dashboard()
    awards = awards_dashboard()
    revenue = (
        EmployeeTarget.objects.aggregate(total=Sum("achieved_amount"))["total"] or 0
    )
    return {
        "metrics": {
            "employees": UserProfile.objects.count(),
            "branches": Branch.active.count(),
            "revenue": revenue,
            "collections": revenue,
            "pending_cases": ops["pending_cases"],
            "completed_cases": ops["completed_cases"],
            "leave_pending_hr": hr["leave_pending_hr"],
            "attendance_today": hr["attendance_today"],
        },
        "awards": awards,
        "operations": ops,
    }


def finance_module_stats():
    m = finance_dashboard()
    return _stats_from_dict(
        {
            "Payroll ready": m["payroll_ready"],
            "Incentives (month)": m["incentive_total"],
            "Collections": m["collections_total"],
        }
    )


def marketing_module_stats():
    m = marketing_dashboard()
    return _stats_from_dict(
        {
            "Active campaigns": m["active_campaigns"],
            "Leads this month": m["leads_this_month"],
        }
    )


def branch_staff_rows(branch):
    if not branch:
        return []
    return Staff.objects.filter(branch=branch, is_active=True).select_related("user")[:50]


def cases_for_branch(branch):
    qs = ClientCase.objects.select_related("lead", "assigned_to")
    if branch:
        qs = qs.filter(branch=branch)
    return qs.order_by("-updated_at")[:50]


def cases_for_backoffice():
    return ClientCase.objects.select_related("lead", "branch", "assigned_to").order_by("-updated_at")[:100]


def lead_pipeline_steps():
    return ["New Lead", "Contacted", "Interested", "Meeting", "Converted"]


def client_journey_steps():
    return WORKFLOWS["client_processing"]["steps"]


def hr_workflow_steps():
    return WORKFLOWS["leave_approval"]["steps"]


def payroll_workflow_steps():
    return WORKFLOWS["salary_approval"]["steps"]


def case_workflow_steps():
    return backoffice_case_processing_steps()


def backoffice_case_processing_steps():
    """Actual back-office work after sale (visa, admission, general services)."""
    return [
        "Documents verified",
        "Application created",
        "File submitted",
        "Submitted online",
        "Tracking response",
        "Customer updated",
        "Completed",
    ]


def followup_doc_steps():
    return [
        "Passport copy",
        "Certificates",
        "Photos",
        "Hand to back office",
    ]
