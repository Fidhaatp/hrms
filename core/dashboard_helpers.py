from datetime import timedelta

from django.utils import timezone

from core.lead_utils import converted_leads_filter
from core.models import Lead


def _today():
    return timezone.localdate()


def _month_start():
    today = _today()
    return today.replace(day=1)


def organization_lead_stats():
    month_start = _month_start()
    week_start = _today() - timedelta(days=7)
    total = Lead.objects.count()
    month_new = Lead.objects.filter(created_at__date__gte=month_start).count()
    week_new = Lead.objects.filter(created_at__date__gte=week_start).count()
    converted = Lead.objects.filter(**converted_leads_filter()).count()
    pending_backoffice = Lead.objects.filter(
        backoffice_status=Lead.BackofficeStatus.PENDING
    ).count()
    in_progress = Lead.objects.filter(
        backoffice_status=Lead.BackofficeStatus.VERIFIED,
        pipeline_stage__in=[Lead.PipelineStage.FOLLOWUP, Lead.PipelineStage.SUBMITTED],
    ).count()
    rate = round(converted / total * 100, 1) if total else 0
    return {
        "total": total,
        "month_new": month_new,
        "week_new": week_new,
        "converted": converted,
        "conversion_rate": rate,
        "pending_backoffice": pending_backoffice,
        "in_progress": in_progress,
    }


def lead_dashboard_rows(queryset, limit=8):
    rows = []
    for lead in queryset.select_related("branch", "followup_status", "created_by")[:limit]:
        status_name = lead.followup_status.name if lead.followup_status else "New"
        rows.append(
            {
                "id": lead.display_id,
                "name": lead.name,
                "company": lead.branch.name if lead.branch else "—",
                "badge": lead.team_status_badge,
                "status": status_name,
                "followup": lead.updated_at.strftime("%d %b %Y"),
                "initials": lead.initials,
            }
        )
    return rows


def followup_dashboard_metrics(user=None):
    from core.dashboard_metrics import followup_dashboard_metrics as _metrics

    return _metrics(user)