from core.backoffice_utils import (
    backoffice_accessible_leads_queryset,
    backoffice_completed_leads_queryset,
    backoffice_head_required,
    backoffice_in_progress_leads_queryset,
    backoffice_pending_leads_for_user,
    backoffice_pending_procedure_count,
    backoffice_recent_procedure_leads,
    backoffice_team_members_queryset,
    user_is_backoffice_head,
)
from core.case_portal import (
    backoffice_case_detail_view,
    backoffice_case_update_view,
    backoffice_cases_list_view,
    recent_cases_for_dashboard,
)
from core.dashboard_metrics import case_operations_metrics
from core.leave_portal import leave_add_view, leave_list_view
from core.lead_documents import backoffice_open_case_view
from core.lead_portal import (
    backoffice_all_leads_list_view,
    backoffice_lead_reject_view,
    backoffice_lead_verify_view,
    backoffice_pending_list_view,
    backoffice_procedure_pending_list_view,
    backoffice_procedure_review_view,
    backoffice_team_pending_leads_list_view,
)
from core.lead_utils import backoffice_pending_leads_queryset
from core.models import UserProfile
from core.portal import portal_role_required, render_portal_page

from .reports import (
    REPORT_CHOICES,
    build_report_rows,
    parse_report_dates,
    parse_report_type,
    report_download_response,
)

leave_list = leave_list_view(UserProfile.UserType.BACKOFFICE)
leave_add = leave_add_view(UserProfile.UserType.BACKOFFICE)
pending_verifications = backoffice_pending_list_view()
procedure_reviews = backoffice_procedure_pending_list_view()
pending_leads = backoffice_team_pending_leads_list_view()
all_leads = backoffice_all_leads_list_view()
lead_list = pending_verifications
lead_verify = backoffice_lead_verify_view()
lead_reject = backoffice_lead_reject_view()
procedure_review = backoffice_procedure_review_view()
lead_open_case = backoffice_open_case_view()
cases = backoffice_cases_list_view()
case_detail = backoffice_case_detail_view()
case_update = backoffice_case_update_view()


@portal_role_required(UserProfile.UserType.BACKOFFICE)
def index(request):
    backoffice_profile = getattr(request.user, "backoffice_profile", None)
    pending_leads = backoffice_pending_leads_for_user(request.user).count()
    if user_is_backoffice_head(request.user):
        all_approved_leads_count = backoffice_accessible_leads_queryset(request.user).count()
    else:
        all_approved_leads_count = backoffice_completed_leads_queryset(request.user).count()
    recent_pending_leads = []
    recent_procedure_leads = []
    pending_procedure_count = 0
    pending_in_progress_count = 0
    if user_is_backoffice_head(request.user):
        recent_pending_leads = list(
            backoffice_pending_leads_for_user(request.user)
            .select_related("branch", "created_by", "followup_status", "service")
            .order_by("-sent_to_backoffice_at")[:8]
        )
    else:
        pending_procedure_count = backoffice_pending_procedure_count()
        pending_in_progress_count = backoffice_in_progress_leads_queryset(request.user).count()
        recent_procedure_leads = list(backoffice_recent_procedure_leads())
    case_metrics = case_operations_metrics()
    return render_portal_page(
        request,
        UserProfile.UserType.BACKOFFICE,
        "backoffice/dashboard.html",
        "Dashboard",
        backoffice_profile=backoffice_profile,
        pending_leads_count=pending_leads,
        all_approved_leads_count=all_approved_leads_count,
        recent_pending_leads=recent_pending_leads,
        pending_procedure_count=pending_procedure_count,
        pending_in_progress_count=pending_in_progress_count,
        recent_procedure_leads=recent_procedure_leads,
        is_backoffice_head=user_is_backoffice_head(request.user),
        case_metrics=case_metrics,
        recent_cases=recent_cases_for_dashboard(request.user),
    )


@portal_role_required(UserProfile.UserType.BACKOFFICE)
@backoffice_head_required()
def team(request):
    members = backoffice_team_members_queryset()
    active_count = members.filter(is_active=True).count()
    return render_portal_page(
        request,
        UserProfile.UserType.BACKOFFICE,
        "backoffice/team.html",
        "Back office team",
        active_nav="team",
        team_members=members,
        team_active_count=active_count,
        team_total_count=members.count(),
    )


@portal_role_required(UserProfile.UserType.BACKOFFICE)
def reports(request):
    date_from, date_to = parse_report_dates(request)
    report_type = parse_report_type(request)
    lead_rows, case_rows = build_report_rows(report_type, date_from, date_to)
    return render_portal_page(
        request,
        UserProfile.UserType.BACKOFFICE,
        "backoffice/reports.html",
        "Reports",
        active_nav="reports",
        report_type=report_type,
        report_choices=REPORT_CHOICES,
        date_from=date_from,
        date_to=date_to,
        lead_rows=lead_rows,
        case_rows=case_rows,
    )


@portal_role_required(UserProfile.UserType.BACKOFFICE)
def reports_download(request):
    date_from, date_to = parse_report_dates(request)
    report_type = parse_report_type(request)
    return report_download_response(report_type, date_from, date_to)
