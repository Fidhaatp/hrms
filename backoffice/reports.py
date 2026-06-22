"""Back office reports — date filters and CSV export."""

import csv
from datetime import date, timedelta
from io import StringIO

from django.http import HttpResponse
from django.utils import timezone

from core.models import ClientCase, Lead


REPORT_LEADS = "leads"
REPORT_CASES = "cases"
REPORT_ALL = "all"

REPORT_CHOICES = (
    (REPORT_LEADS, "Leads"),
    (REPORT_CASES, "Cases"),
    (REPORT_ALL, "All"),
)


def parse_report_dates(request):
    today = timezone.localdate()
    default_from = today.replace(day=1)
    date_from_raw = request.GET.get("date_from") or default_from.isoformat()
    date_to_raw = request.GET.get("date_to") or today.isoformat()
    try:
        date_from = date.fromisoformat(date_from_raw)
        date_to = date.fromisoformat(date_to_raw)
    except ValueError:
        date_from, date_to = default_from, today
    if date_from > date_to:
        date_from, date_to = date_to, date_from
    return date_from, date_to


def parse_report_type(request):
    report_type = request.GET.get("report", REPORT_LEADS)
    if report_type not in dict(REPORT_CHOICES):
        report_type = REPORT_LEADS
    return report_type


def leads_report_queryset(date_from, date_to):
    return (
        Lead.objects.filter(
            sent_to_backoffice_at__isnull=False,
            sent_to_backoffice_at__date__gte=date_from,
            sent_to_backoffice_at__date__lte=date_to,
        )
        .select_related("branch", "created_by", "followup_status", "service", "backoffice_checked_by")
        .order_by("-sent_to_backoffice_at")
    )


def cases_report_queryset(date_from, date_to):
    return (
        ClientCase.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .select_related("lead", "branch")
        .order_by("-created_at")
    )


def build_report_rows(report_type, date_from, date_to):
    lead_rows = []
    case_rows = []
    if report_type in (REPORT_LEADS, REPORT_ALL):
        for lead in leads_report_queryset(date_from, date_to):
            lead_rows.append(
                {
                    "id": lead.display_id,
                    "name": lead.name,
                    "phone": lead.phone,
                    "service": lead.service.name if lead.service_id else "",
                    "branch": lead.branch.name if lead.branch_id else "",
                    "staff": lead.created_by.get_username() if lead.created_by_id else "",
                    "followup_status": lead.followup_status.name if lead.followup_status_id else "",
                    "backoffice_status": lead.get_backoffice_status_display(),
                    "approved_at": lead.sent_to_backoffice_at.strftime("%d %b %Y %H:%M") if lead.sent_to_backoffice_at else "",
                    "checked_at": lead.backoffice_checked_at.strftime("%d %b %Y %H:%M") if lead.backoffice_checked_at else "",
                    "checked_by": lead.backoffice_checked_by.get_username() if lead.backoffice_checked_by_id else "",
                }
            )
    if report_type in (REPORT_CASES, REPORT_ALL):
        for case in cases_report_queryset(date_from, date_to):
            case_rows.append(
                {
                    "ref": case.case_ref,
                    "client": case.client_name,
                    "branch": case.branch.name if case.branch_id else "",
                    "lead": case.lead.display_id if case.lead_id else "",
                    "service": case.get_service_type_display(),
                    "status": case.get_status_display(),
                    "created": case.created_at.strftime("%d %b %Y"),
                }
            )
    return lead_rows, case_rows


def report_download_response(report_type, date_from, date_to):
    lead_rows, case_rows = build_report_rows(report_type, date_from, date_to)
    buffer = StringIO()
    writer = csv.writer(buffer)

    if report_type == REPORT_LEADS:
        writer.writerow(
            ["Lead ID", "Name", "Phone", "Service", "Branch", "Staff", "Follow-up status", "Back office", "Approved", "Checked", "Checked by"]
        )
        for row in lead_rows:
            writer.writerow(
                [
                    row["id"], row["name"], row["phone"], row["service"], row["branch"],
                    row["staff"], row["followup_status"], row["backoffice_status"],
                    row["approved_at"], row["checked_at"], row["checked_by"],
                ]
            )
        filename = f"backoffice-leads-{date_from}-to-{date_to}.csv"
    elif report_type == REPORT_CASES:
        writer.writerow(["Case ref", "Client", "Branch", "Lead", "Service", "Status", "Created"])
        for row in case_rows:
            writer.writerow(
                [row["ref"], row["client"], row["branch"], row["lead"], row["service"], row["status"], row["created"]]
            )
        filename = f"backoffice-cases-{date_from}-to-{date_to}.csv"
    else:
        writer.writerow(["Section", "ID", "Name", "Branch", "Status", "Date"])
        for row in lead_rows:
            writer.writerow(["Lead", row["id"], row["name"], row["branch"], row["backoffice_status"], row["approved_at"]])
        for row in case_rows:
            writer.writerow(["Case", row["ref"], row["client"], row["branch"], row["status"], row["created"]])
        filename = f"backoffice-report-{date_from}-to-{date_to}.csv"

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
