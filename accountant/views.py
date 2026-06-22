from core.dashboard_metrics import branch_dashboard
from core.models import ApprovalStatus, PaymentRequest, UserProfile
from core.portal import portal_role_required, render_portal_page
from core.portal_pages import quick_link, render_module


def _accountant_branch(user):
    profile = getattr(user, "branch_accountant_profile", None)
    if profile:
        return profile.branch
    staff = getattr(user, "staff_profile", None)
    return staff.branch if staff else None


@portal_role_required(UserProfile.UserType.BRANCH_ACCOUNTANT)
def index(request):
    branch = _accountant_branch(request.user)
    return render_portal_page(
        request,
        UserProfile.UserType.BRANCH_ACCOUNTANT,
        "accountant/dashboard.html",
        "Dashboard",
        branch=branch,
        metrics=branch_dashboard(branch),
    )


@portal_role_required(UserProfile.UserType.BRANCH_ACCOUNTANT)
def collections(request):
    branch = _accountant_branch(request.user)
    return render_module(
        request,
        UserProfile.UserType.BRANCH_ACCOUNTANT,
        page_title="Collections",
        active_nav="collections",
        module_title="Collections",
        module_intro=f"Customer payments and receipts for {branch.name if branch else 'your branch'}.",
        quick_links=[quick_link("Finance portal", "finance:collections", "bi-wallet2")],
    )


@portal_role_required(UserProfile.UserType.BRANCH_ACCOUNTANT)
def invoices(request):
    return render_module(
        request,
        UserProfile.UserType.BRANCH_ACCOUNTANT,
        page_title="Invoices",
        active_nav="invoices",
        module_title="Invoices",
        module_intro="Create invoices and track invoice status.",
    )


@portal_role_required(UserProfile.UserType.BRANCH_ACCOUNTANT)
def reports(request):
    branch = _accountant_branch(request.user)
    m = branch_dashboard(branch)
    return render_module(
        request,
        UserProfile.UserType.BRANCH_ACCOUNTANT,
        page_title="Branch Reports",
        active_nav="reports",
        module_title="Branch Reports",
        module_intro="Revenue and collections for your branch.",
        stats=[
            {"label": "Revenue", "value": m["revenue"]},
            {"label": "Collections", "value": m["collections"]},
            {"label": "Conversion %", "value": m["conversion_rate"]},
        ],
    )


@portal_role_required(UserProfile.UserType.BRANCH_ACCOUNTANT)
def finance_comm(request):
    pending = PaymentRequest.objects.filter(status=ApprovalStatus.PENDING).count()
    return render_module(
        request,
        UserProfile.UserType.BRANCH_ACCOUNTANT,
        page_title="Finance Communication",
        active_nav="finance_comm",
        module_title="Finance Communication",
        module_intro="Submit reports and payment requests to the Finance Manager.",
        stats=[{"label": "Pending payment requests", "value": pending}],
        quick_links=[quick_link("Finance collections", "finance:collections", "bi-send-fill")],
    )
