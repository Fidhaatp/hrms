"""Service expiry calendar for staff, follow-up, and branch portals."""

import json
from datetime import date

from core.lead_monitoring import branch_leads_queryset
from core.lead_utils import followup_team_leads_queryset
from core.models import Lead
from core.portal import portal_role_required, render_portal_page


def _clamp_month(year: int, month: int) -> tuple[int, int]:
    if month < 1:
        return year - 1, 12
    if month > 12:
        return year + 1, 1
    return year, month


def _build_all_events_by_date(leads_qs) -> dict[str, list[dict]]:
    events_by_date: dict[str, list[dict]] = {}
    leads = (
        leads_qs.select_related("service", "branch", "created_by", "created_by__profile")
        .order_by("service_expire_date", "name")
    )
    for lead in leads:
        iso = lead.service_expire_date.isoformat()
        events_by_date.setdefault(iso, []).append(
            {
                "id": lead.display_id,
                "name": lead.name,
                "phone": lead.phone or "",
                "service": lead.service.name if lead.service_id else "—",
                "branch": lead.branch.name if lead.branch_id else "—",
                "staff": lead.created_by.get_full_name() or lead.created_by.username,
            }
        )
    return events_by_date


def build_service_expiry_calendar_context(request, leads_qs):
    today = date.today()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
    except (TypeError, ValueError):
        year, month = today.year, today.month
    year, month = _clamp_month(year, month)

    all_events = _build_all_events_by_date(leads_qs)
    selected = request.GET.get("date", "")
    selected_events = all_events.get(selected, []) if selected else []

    month_count = sum(
        len(events)
        for iso, events in all_events.items()
        if iso.startswith(f"{year:04d}-{month:02d}-")
    )

    return {
        "calendar_year": year,
        "calendar_month": month,
        "calendar_month_name": date(year, month, 1).strftime("%B %Y"),
        "calendar_all_events_json": json.dumps(all_events),
        "calendar_event_count": month_count,
        "calendar_selected_date": selected,
        "calendar_selected_events": selected_events,
    }


def service_expiry_calendar_view(user_type, leads_qs_fn, calendar_url_name):
    @portal_role_required(user_type)
    def view(request):
        ctx = build_service_expiry_calendar_context(request, leads_qs_fn(request))
        ctx["calendar_url_name"] = calendar_url_name
        return render_portal_page(
            request,
            user_type,
            "portal/calendar/service_expiry.html",
            "Service expiry calendar",
            active_nav="calendar",
            **ctx,
        )

    return view


def staff_expiry_leads_queryset(request):
    return Lead.objects.filter(created_by=request.user).exclude(service_expire_date__isnull=True)


def followup_expiry_leads_queryset(request):
    return followup_team_leads_queryset().exclude(service_expire_date__isnull=True)


def branch_expiry_leads_queryset(request):
    manager = getattr(request.user, "branch_manager_profile", None)
    branch = manager.branch if manager else None
    return branch_leads_queryset(branch).exclude(service_expire_date__isnull=True)
