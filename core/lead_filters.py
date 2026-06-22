"""Status and search filters for portal lead list pages."""

from urllib.parse import urlencode

from django.db.models import Q

from core.lead_utils import get_followup_lead_statuses, get_staff_lead_statuses
from core.models import Lead

FILTER_ALL = "all"
FILTER_NONE = "none"


def parse_lead_list_filters(request):
    return {
        "q": (request.GET.get("q") or "").strip(),
        "staff_status": (request.GET.get("staff_status") or FILTER_ALL).strip(),
        "followup_status": (request.GET.get("followup_status") or FILTER_ALL).strip(),
        "backoffice_status": (request.GET.get("backoffice_status") or FILTER_ALL).strip(),
    }


def lead_filter_query_string(filters, *, exclude_page=False):
    data = {}
    if filters.get("q"):
        data["q"] = filters["q"]
    for key in ("staff_status", "followup_status", "backoffice_status"):
        value = filters.get(key, FILTER_ALL)
        if value and value not in (FILTER_ALL, ""):
            data[key] = value
    if not exclude_page:
        page = filters.get("page")
        if page and str(page) != "1":
            data["page"] = page
    return urlencode(data)


def apply_lead_list_filters(queryset, filters):
    q = filters.get("q", "")
    if q:
        q_filter = (
            Q(name__icontains=q)
            | Q(phone__icontains=q)
            | Q(email__icontains=q)
            | Q(company__icontains=q)
            | Q(takhlees_id__icontains=q)
            | Q(created_by__username__icontains=q)
            | Q(created_by__first_name__icontains=q)
            | Q(created_by__last_name__icontains=q)
        )
        if q.upper().startswith("L-"):
            try:
                q_filter |= Q(pk=int(q[2:].lstrip("0") or "0"))
            except ValueError:
                pass
        queryset = queryset.filter(q_filter)

    staff_status = filters.get("staff_status", FILTER_ALL)
    if staff_status and staff_status != FILTER_ALL:
        queryset = queryset.filter(staff_status_id=staff_status)

    followup_status = filters.get("followup_status", FILTER_ALL)
    if followup_status == FILTER_NONE:
        queryset = queryset.filter(followup_status__isnull=True)
    elif followup_status and followup_status != FILTER_ALL:
        queryset = queryset.filter(followup_status_id=followup_status)

    backoffice_status = filters.get("backoffice_status", FILTER_ALL)
    if backoffice_status and backoffice_status != FILTER_ALL:
        queryset = queryset.filter(backoffice_status=backoffice_status)

    return queryset


def lead_filter_context(
    filters,
    *,
    show_staff=False,
    show_followup=False,
    show_backoffice=False,
):
    return {
        "lead_filters": filters,
        "pagination_query": lead_filter_query_string(filters, exclude_page=True),
        "filter_staff_statuses": list(get_staff_lead_statuses()) if show_staff else [],
        "filter_followup_statuses": list(get_followup_lead_statuses()) if show_followup else [],
        "filter_backoffice_statuses": list(Lead.BackofficeStatus.choices) if show_backoffice else [],
        "show_staff_status_filter": show_staff,
        "show_followup_status_filter": show_followup,
        "show_backoffice_status_filter": show_backoffice,
    }


def filters_are_active(filters):
    if filters.get("q"):
        return True
    for key in ("staff_status", "followup_status", "backoffice_status"):
        value = filters.get(key, FILTER_ALL)
        if value and value not in (FILTER_ALL, ""):
            return True
    return False
