"""Branch manager reports — scoped to the manager's branch."""

import csv
from datetime import date
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


def branch_leads_report_queryset(branch, date_from, date_to):
    if not branch:
        return Lead.objects.none()
    return (
        Lead.objects.filter(
            branch=branch,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .select_related("created_by", "followup_status", "service", "backoffice_checked_by")
        .order_by("-created_at")
    )


def branch_cases_report_queryset(branch, date_from, date_to):
    if not branch:
        return ClientCase.objects.none()
    return (
        ClientCase.objects.filter(
            branch=branch,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        .select_related("lead")
        .order_by("-created_at")
    )


def build_branch_report_rows(branch, report_type, date_from, date_to):
    lead_rows = []
    case_rows = []
    if report_type in (REPORT_LEADS, REPORT_ALL):
        for lead in branch_leads_report_queryset(branch, date_from, date_to):
            lead_rows.append(
                {
                    "id": lead.display_id,
                    "name": lead.name,
                    "phone": lead.phone,
                    "service": lead.service.name if lead.service_id else "",
                    "staff": lead.created_by.get_username(),
                    "status": lead.followup_status.name if lead.followup_status_id else "",
                    "followup_sent": lead.sent_to_followup_at.strftime("%d %b %Y") if lead.sent_to_followup_at else "",
                    "bo_approved": lead.sent_to_backoffice_at.strftime("%d %b %Y") if lead.sent_to_backoffice_at else "",
                    "backoffice": lead.get_backoffice_status_display(),
                    "added": lead.created_at.strftime("%d %b %Y"),
                }
            )
    if report_type in (REPORT_CASES, REPORT_ALL):
        for case in branch_cases_report_queryset(branch, date_from, date_to):
            case_rows.append(
                {
                    "ref": case.case_ref,
                    "client": case.client_name,
                    "lead": case.lead.display_id if case.lead_id else "",
                    "service": case.get_service_type_display(),
                    "status": case.get_status_display(),
                    "created": case.created_at.strftime("%d %b %Y"),
                }
            )
    return lead_rows, case_rows


def branch_report_download_response(branch, report_type, date_from, date_to):
    lead_rows, case_rows = build_branch_report_rows(branch, report_type, date_from, date_to)
    buffer = StringIO()
    writer = csv.writer(buffer)
    branch_slug = (branch.name if branch else "branch").replace(" ", "-").lower()
    if report_type == REPORT_LEADS:
        writer.writerow(
            ["Lead ID", "Name", "Phone", "Service", "Staff", "Status", "Follow-up sent", "BO approved", "Back office", "Added"]
        )
        for row in lead_rows:
            writer.writerow(
                [
                    row["id"],
                    row["name"],
                    row["phone"],
                    row["service"],
                    row["staff"],
                    row["status"],
                    row["followup_sent"],
                    row["bo_approved"],
                    row["backoffice"],
                    row["added"],
                ]
            )
        filename = f"{branch_slug}-leads-{date_from}-to-{date_to}.csv"
    elif report_type == REPORT_CASES:
        writer.writerow(["Case ref", "Client", "Lead", "Service", "Status", "Created"])
        for row in case_rows:
            writer.writerow([row["ref"], row["client"], row["lead"], row["service"], row["status"], row["created"]])
        filename = f"{branch_slug}-cases-{date_from}-to-{date_to}.csv"
    else:
        writer.writerow(["Type", "Ref", "Name", "Status", "Date"])
        for row in lead_rows:
            writer.writerow(["Lead", row["id"], row["name"], row["backoffice"], row["added"]])
        for row in case_rows:
            writer.writerow(["Case", row["ref"], row["client"], row["status"], row["created"]])
        filename = f"{branch_slug}-report-{date_from}-to-{date_to}.csv"
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
