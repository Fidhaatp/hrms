from core.dashboard_metrics import followup_dashboard_metrics, operations_dashboard
from core.leave_portal import leave_add_view, leave_list_view
from core.leave_utils import all_leave_summaries, leave_summary
from core.lead_documents import followup_lead_document_upload_view
from core.lead_portal import (
    followup_all_leads_list_view,
    followup_lead_check_docs_view,
    followup_lead_expire_date_view,
    followup_lead_list_view,
    followup_lead_procedure_submit_view,
    followup_lead_status_view,
    followup_lead_update_view,
)
from core.lead_calendar import followup_expiry_leads_queryset, service_expiry_calendar_view
from core.models import LeaveRequest, UserProfile
from core.portal import portal_role_required, render_portal_page

leave_list = leave_list_view(UserProfile.UserType.FOLLOWUP)
leave_add = leave_add_view(UserProfile.UserType.FOLLOWUP)
lead_list = followup_lead_list_view()
all_leads = followup_all_leads_list_view()
lead_update = followup_lead_update_view()
lead_check_docs = followup_lead_check_docs_view()
lead_expire_date = followup_lead_expire_date_view()
lead_status = followup_lead_status_view()
lead_procedure_submit = followup_lead_procedure_submit_view()
lead_document_upload = followup_lead_document_upload_view()
calendar = service_expiry_calendar_view(
    UserProfile.UserType.FOLLOWUP,
    followup_expiry_leads_queryset,
    "followup:calendar",
)


@portal_role_required(UserProfile.UserType.FOLLOWUP)
def index(request):
    followup_profile = getattr(request.user, "followup_profile", None)
    balances = all_leave_summaries(request.user)
    summary = next(
        (b for b in balances if b["leave_category"].code == "yearly"),
        leave_summary(request.user),
    )
    pending_leave = LeaveRequest.objects.filter(
        user=request.user,
        status=LeaveRequest.Status.PENDING,
    ).count()
    lead_dashboard = followup_dashboard_metrics(request.user)
    return render_portal_page(
        request,
        UserProfile.UserType.FOLLOWUP,
        "followup/dashboard.html",
        "Dashboard",
        followup_profile=followup_profile,
        lead_stats=lead_dashboard["stats"],
        recent_leads=lead_dashboard["recent_leads"],
        recent_activity=lead_dashboard["recent_activity"],
        dashboard_charts_json=lead_dashboard["charts_json"],
        chart_subtitle=lead_dashboard["charts"]["monthly"].get("subtitle", ""),
        leave_summary=summary,
        pending_leave_count=pending_leave,
        operations=operations_dashboard(),
    )
