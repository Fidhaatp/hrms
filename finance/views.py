from django.db.models import Sum

from core.dashboard_metrics import finance_dashboard
from core.models import ApprovalStatus, EmployeeIncentive, LeaveRequest, PaymentRequest, UserProfile
from core.portal import portal_role_required, render_portal_page
from core.portal_pages import finance_module_stats, payroll_workflow_steps, quick_link, render_module


@portal_role_required(UserProfile.UserType.FINANCE)
def index(request):
    return render_portal_page(
        request,
        UserProfile.UserType.FINANCE,
        "finance/dashboard.html",
        "Dashboard",
        metrics=finance_dashboard(),
    )


@portal_role_required(UserProfile.UserType.FINANCE)
def payroll(request):
    approved = LeaveRequest.objects.filter(
        workflow_stage=LeaveRequest.WorkflowStage.APPROVED,
        status=LeaveRequest.Status.APPROVED,
    ).count()
    return render_module(
        request,
        UserProfile.UserType.FINANCE,
        page_title="Payroll",
        active_nav="payroll",
        module_title="Payroll",
        module_intro="Salary processing, overtime, and payroll completion after HR verification.",
        workflow_steps=payroll_workflow_steps(),
        stats=[{"label": "Ready for payroll", "value": approved}],
        quick_links=[
            quick_link("HR leave approvals", "hr:leave_requests", "bi-calendar-check"),
            quick_link("HR portal", "hr:dashboard", "bi-briefcase"),
        ],
    )


@portal_role_required(UserProfile.UserType.FINANCE)
def incentives(request):
    total = EmployeeIncentive.objects.aggregate(t=Sum("amount"))["t"] or 0
    return render_module(
        request,
        UserProfile.UserType.FINANCE,
        page_title="Incentives",
        active_nav="incentives",
        module_title="Incentives",
        module_intro="Verify and process branch staff incentives.",
        stats=[{"label": "Total incentives", "value": total}],
    )


@portal_role_required(UserProfile.UserType.FINANCE)
def collections(request):
    pending = PaymentRequest.objects.filter(status=ApprovalStatus.PENDING).count()
    return render_module(
        request,
        UserProfile.UserType.FINANCE,
        page_title="Collections",
        active_nav="collections",
        module_title="Collections",
        module_intro="Customer payments, due tracking, and collection reports.",
        stats=[{"label": "Pending payments", "value": pending}],
        quick_links=[quick_link("HR approvals", "hr:approvals", "bi-check2-square")],
    )


@portal_role_required(UserProfile.UserType.FINANCE)
def expenses(request):
    return render_module(
        request,
        UserProfile.UserType.FINANCE,
        page_title="Expenses",
        active_nav="expenses",
        module_title="Expenses",
        module_intro="Branch expenses and vendor payments.",
    )


@portal_role_required(UserProfile.UserType.FINANCE)
def reports(request):
    m = finance_dashboard()
    return render_module(
        request,
        UserProfile.UserType.FINANCE,
        page_title="Reports",
        active_nav="reports",
        module_title="Financial Reports",
        module_intro="Revenue, profit, and collection reports.",
        stats=finance_module_stats(),
        quick_links=[quick_link("HR analytics", "hr:analytics", "bi-bar-chart-fill")],
    )
