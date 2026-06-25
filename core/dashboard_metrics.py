"""Organization-wide dashboard metric calculations."""

import json
from calendar import month_abbr
from datetime import date, timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.timesince import timesince

from branch.models import BranchMonthlyTarget
from core.branch_target_utils import staff_target_breakdown
from core.lead_utils import (
    backoffice_pending_leads_queryset,
    converted_leads_filter,
    followup_active_leads_queryset,
    followup_sent_leads_queryset,
    followup_team_leads_queryset,
)
from core.models import (
    Announcement,
    AttendanceRecord,
    Award,
    EmployeeCompliance,
    EmployeeIncentive,
    EmployeeTarget,
    Lead,
    LeadRoadmapEntry,
    LeaveRequest,
    RecruitmentRequest,
    UserProfile,
)
from staff.models import Staff


def _today():
    return timezone.localdate()


def _month_start():
    today = _today()
    return date(today.year, today.month, 1)


def employee_dashboard(user):
    today = _today()
    month_start = _month_start()
    attendance_today = AttendanceRecord.objects.filter(user=user, date=today).first()
    month_attendance = AttendanceRecord.objects.filter(user=user, date__gte=month_start)
    target = EmployeeTarget.objects.filter(
        user=user, period_month=today.month, period_year=today.year
    ).first()
    incentive_total = (
        EmployeeIncentive.objects.filter(user=user, month=today.month, year=today.year).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )
    from core.leave_utils import leave_summary

    summary = leave_summary(user)
    announcements = Announcement.objects.filter(is_active=True).count()
    target_amount = target.target_amount if target else 0
    achieved_amount = target.achieved_amount if target else 0
    target_breakdown = staff_target_breakdown(target_amount, achieved_amount, today)
    return {
        "attendance_status": attendance_today.get_status_display() if attendance_today else "Not marked",
        "attendance_present_days": month_attendance.filter(status=AttendanceRecord.Status.PRESENT).count(),
        "target_amount": target_amount,
        "achieved_amount": achieved_amount,
        "achievement_percent": target.achievement_percent if target else 0,
        "target_breakdown": target_breakdown,
        "incentive_total": incentive_total,
        "leave_remaining": summary["remaining"],
        "leave_used": summary["used"],
        "leave_entitlement": summary["entitlement"],
        "announcements_count": announcements,
    }


def _six_month_lead_chart(queryset, date_field="created_at"):
    month_start = _month_start()
    six_month_start = _month_shift(month_start, 5)
    lead_counts = {
        row["month"].strftime("%Y-%m"): row["count"]
        for row in queryset.filter(**{f"{date_field}__date__gte": six_month_start})
        .annotate(month=TruncMonth(date_field))
        .values("month")
        .annotate(count=Count("id"))
    }
    monthly_labels = []
    monthly_leads = []
    cursor = six_month_start
    for _ in range(6):
        key = f"{cursor.year}-{cursor.month:02d}"
        monthly_labels.append(f"{month_abbr[cursor.month]} {cursor.year}")
        monthly_leads.append(lead_counts.get(key, 0))
        cursor = _next_month(cursor)
    subtitle = f"{monthly_labels[0]} – {monthly_labels[-1]}" if monthly_labels else ""
    return monthly_labels, monthly_leads, subtitle


def branch_dashboard(branch):
    empty = {
        "team_count": 0,
        "leads_total": 0,
        "leads_all_time": 0,
        "leads_converted": 0,
        "conversion_rate": 0,
        "at_followup": 0,
        "revenue": 0,
        "collections": 0,
        "branch_target": 0,
        "staff_target_total": 0,
        "ranking": "—",
        "recent_leads": [],
        "charts": {},
        "charts_json": json.dumps({}),
        "chart_subtitle": "",
    }
    if not branch:
        return empty
    month_start = _month_start()
    staff_qs = Staff.objects.filter(branch=branch, is_active=True)
    all_leads = Lead.objects.filter(branch=branch)
    month_leads = all_leads.filter(created_at__date__gte=month_start)
    total = month_leads.count()
    converted = month_leads.filter(**converted_leads_filter()).count()
    rate = round(converted / total * 100, 1) if total else 0
    targets = EmployeeTarget.objects.filter(
        user__staff_profile__branch=branch,
        period_month=_today().month,
        period_year=_today().year,
    ).aggregate(revenue=Sum("achieved_amount"), target=Sum("target_amount"))
    branch_target = BranchMonthlyTarget.objects.filter(
        branch=branch,
        period_month=_today().month,
        period_year=_today().year,
    ).first()
    monthly_labels, monthly_leads, subtitle = _six_month_lead_chart(all_leads)
    charts = {
        "monthly": {
            "labels": monthly_labels,
            "leads": monthly_leads,
            "revenue": [0] * len(monthly_labels),
            "subtitle": subtitle,
        },
        "sources": {"labels": ["No leads yet"], "values": [0]},
    }
    recent_leads = list(
        all_leads.select_related("service", "followup_status", "source").order_by("-created_at")[:8]
    )
    return {
        "team_count": staff_qs.count(),
        "leads_total": total,
        "leads_all_time": all_leads.count(),
        "leads_converted": converted,
        "conversion_rate": rate,
        "at_followup": all_leads.filter(
            sent_to_followup_at__isnull=False,
            sent_to_backoffice_at__isnull=True,
        ).exclude(backoffice_status=Lead.BackofficeStatus.REJECTED).count(),
        "revenue": targets["revenue"] or 0,
        "collections": targets["revenue"] or 0,
        "branch_target": branch_target.target_amount if branch_target else 0,
        "staff_target_total": targets["target"] or 0,
        "ranking": 1,
        "recent_leads": recent_leads,
        "charts": charts,
        "charts_json": json.dumps(charts),
        "chart_subtitle": subtitle,
    }


def _pct_change(current, previous):
    if not previous:
        return None
    return round((current - previous) / previous * 100)


def _month_shift(d, months_back):
    year, month = d.year, d.month - months_back
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return date(year, month, 1)


def _next_month(d):
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


def _activity_entry_meta(entry):
    title_lower = entry.title.lower()
    if "convert" in title_lower or "won" in title_lower:
        icon, tone = "trophy", "amber"
    elif "call" in title_lower or "follow" in title_lower:
        icon, tone = "telephone", "blue"
    elif "email" in title_lower or "sent" in title_lower:
        icon, tone = "envelope", "green"
    elif "lead" in title_lower or "added" in title_lower:
        icon, tone = "person-plus", "violet"
    else:
        icon, tone = "flag", "blue"

    company = entry.lead.company
    text = f"{entry.title} — {entry.lead.name}"
    if company:
        text = f"{entry.title} — {entry.lead.name} ({company})"
    return {
        "text": text,
        "note": entry.note,
        "created_at": entry.created_at,
        "time_ago": f"{timesince(entry.created_at)} ago",
        "icon": icon,
        "tone": tone,
    }


def hr_dashboard_leads():
    today = _today()
    month_start = _month_start()
    prev_month_start = _month_shift(month_start, 1)
    prev_month_end = month_start - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    prev_week_start = week_start - timedelta(days=7)

    total = Lead.objects.count()
    total_this_month = Lead.objects.filter(created_at__date__gte=month_start).count()
    total_prev_month = Lead.objects.filter(
        created_at__date__gte=prev_month_start,
        created_at__date__lte=prev_month_end,
    ).count()
    new_week = Lead.objects.filter(created_at__date__gte=week_start).count()
    new_prev_week = Lead.objects.filter(
        created_at__date__gte=prev_week_start,
        created_at__date__lt=week_start,
    ).count()
    converted = Lead.objects.filter(**converted_leads_filter()).count()
    conversion_rate = round(converted / total * 100, 1) if total else 0
    in_progress = (
        Lead.objects.filter(backoffice_status=Lead.BackofficeStatus.VERIFIED)
        .exclude(**converted_leads_filter())
        .count()
    )
    followup_due_today = Lead.objects.filter(
        next_followup_date=today,
        backoffice_status=Lead.BackofficeStatus.VERIFIED,
    ).count()

    six_month_start = _month_shift(month_start, 5)
    lead_counts = {
        row["month"].strftime("%Y-%m"): row["count"]
        for row in Lead.objects.filter(created_at__date__gte=six_month_start)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
    }
    revenue_by_month = {}
    for row in EmployeeTarget.objects.filter(
        Q(period_year__gt=six_month_start.year)
        | Q(period_year=six_month_start.year, period_month__gte=six_month_start.month)
    ).values("period_year", "period_month").annotate(revenue=Sum("achieved_amount")):
        key = f"{row['period_year']}-{row['period_month']:02d}"
        revenue_by_month[key] = float(row["revenue"] or 0)

    monthly_labels = []
    monthly_leads = []
    monthly_revenue = []
    cursor = six_month_start
    for _ in range(6):
        key = f"{cursor.year}-{cursor.month:02d}"
        monthly_labels.append(f"{month_abbr[cursor.month]} {cursor.year}")
        monthly_leads.append(lead_counts.get(key, 0))
        monthly_revenue.append(round(revenue_by_month.get(key, 0) / 100000, 1))
        cursor = _next_month(cursor)

    source_rows = (
        Lead.objects.values("source__name").annotate(count=Count("id")).order_by("-count")[:8]
    )
    source_labels = [row["source__name"] or "Unknown" for row in source_rows]
    source_values = [row["count"] for row in source_rows]
    if not source_labels:
        source_labels = ["No leads yet"]
        source_values = [0]

    recent_leads = Lead.objects.select_related(
        "source", "followup_status", "branch", "created_by"
    ).order_by("-created_at")[:5]
    recent_activity = [
        _activity_entry_meta(entry)
        for entry in LeadRoadmapEntry.objects.select_related("lead", "created_by").order_by(
            "-created_at"
        )[:6]
    ]

    charts = {
        "monthly": {
            "labels": monthly_labels,
            "leads": monthly_leads,
            "revenue": monthly_revenue,
            "subtitle": f"{monthly_labels[0]} – {monthly_labels[-1]}" if monthly_labels else "",
        },
        "sources": {
            "labels": source_labels,
            "values": source_values,
        },
    }

    return {
        "stats": {
            "total": total,
            "total_this_month": total_this_month,
            "total_trend": _pct_change(total_this_month, total_prev_month),
            "new_week": new_week,
            "new_week_trend": _pct_change(new_week, new_prev_week),
            "converted": converted,
            "conversion_rate": conversion_rate,
            "in_progress": in_progress,
            "followup_due_today": followup_due_today,
        },
        "charts": charts,
        "charts_json": json.dumps(charts),
        "recent_leads": recent_leads,
        "recent_activity": recent_activity,
    }


def hr_dashboard():
    today = _today()
    soon = today + timedelta(days=30)
    compliance_qs = EmployeeCompliance.objects.select_related("user")
    return {
        "visa_expiring_soon": compliance_qs.filter(
            visa_expiry__isnull=False, visa_expiry__lte=soon, visa_expiry__gte=today
        ).count(),
        "insurance_expiring_soon": compliance_qs.filter(
            insurance_expiry__isnull=False,
            insurance_expiry__lte=soon,
            insurance_expiry__gte=today,
        ).count(),
        "contracts_expiring_soon": compliance_qs.filter(
            contract_end__isnull=False, contract_end__lte=soon, contract_end__gte=today
        ).count(),
        "attendance_today": AttendanceRecord.objects.filter(
            date=today, status=AttendanceRecord.Status.PRESENT
        ).count(),
        "leave_pending_hr": LeaveRequest.objects.filter(
            workflow_stage=LeaveRequest.WorkflowStage.PENDING_HR
        ).count(),
        "recruitment_open": RecruitmentRequest.objects.exclude(
            status=RecruitmentRequest.Status.CLOSED
        ).count(),
        "users_total": UserProfile.objects.count(),
    }


def case_operations_metrics():
    from core.models import ClientCase

    stages = ClientCase.ProcessingStage
    return {
        "in_progress": ClientCase.objects.exclude(status=stages.COMPLETED).count(),
        "submitted": ClientCase.objects.filter(status=stages.PORTALS_UPLOADED).count(),
        "completed": ClientCase.objects.filter(status=stages.COMPLETED).count(),
        "opened": ClientCase.objects.filter(status=stages.OPENED).count(),
    }


def operations_dashboard():
    from core.models import ClientCase

    pending_leads = backoffice_pending_leads_queryset().count()
    followup_active = Lead.objects.filter(
        backoffice_status=Lead.BackofficeStatus.VERIFIED,
        pipeline_stage__in=[Lead.PipelineStage.FOLLOWUP, Lead.PipelineStage.SUBMITTED],
    ).count()
    case_metrics = case_operations_metrics()
    active_cases = case_metrics["in_progress"]
    completed_cases = case_metrics["completed"]
    return {
        "pending_cases": pending_leads + active_cases,
        "completed_cases": completed_cases,
        "pending_backoffice": pending_leads,
        "active_followup": followup_active,
        "active_client_cases": active_cases,
    }


def finance_dashboard():
    today = _today()
    incentive_total = (
        EmployeeIncentive.objects.filter(month=today.month, year=today.year).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )
    targets = EmployeeTarget.objects.filter(
        period_month=today.month, period_year=today.year
    ).aggregate(total=Sum("achieved_amount"))
    return {
        "payroll_ready": LeaveRequest.objects.filter(
            workflow_stage=LeaveRequest.WorkflowStage.APPROVED,
            status=LeaveRequest.Status.APPROVED,
        ).count(),
        "incentive_total": incentive_total,
        "collections_total": targets["total"] or 0,
    }


def marketing_dashboard():
    return {
        "active_campaigns": Announcement.objects.filter(is_active=True).count(),
        "leads_this_month": Lead.objects.filter(created_at__date__gte=_month_start()).count(),
    }


def followup_dashboard_metrics(user=None):
    """Lead pipeline stats and charts for the follow-up team (all branches)."""
    today = _today()
    week_start = today - timedelta(days=today.weekday())
    team_qs = followup_team_leads_queryset()
    pending_qs = followup_active_leads_queryset()

    active_count = team_qs.count()
    new_this_week = team_qs.filter(sent_to_followup_at__date__gte=week_start).count()
    due_today = team_qs.filter(next_followup_date=today).count()
    approved_this_week = Lead.objects.filter(
        sent_to_backoffice_at__date__gte=week_start,
    ).count()

    monthly_labels, monthly_leads, subtitle = _six_month_lead_chart(
        team_qs, date_field="sent_to_followup_at"
    )
    source_rows = (
        team_qs.values("source__name").annotate(count=Count("id")).order_by("-count")[:8]
    )
    source_labels = [row["source__name"] or "Unknown" for row in source_rows]
    source_values = [row["count"] for row in source_rows]
    if not source_labels:
        source_labels = ["No active leads"]
        source_values = [0]

    charts = {
        "monthly": {
            "labels": monthly_labels,
            "leads": monthly_leads,
            "revenue": [0] * len(monthly_labels),
            "subtitle": subtitle,
        },
        "sources": {"labels": source_labels, "values": source_values},
    }
    recent_leads = list(
        team_qs.select_related("branch", "service", "staff_status", "followup_status", "source").order_by(
            "-sent_to_followup_at"
        )[:8]
    )
    recent_activity = [
        _activity_entry_meta(entry)
        for entry in LeadRoadmapEntry.objects.filter(lead__in=team_qs)
        .select_related("lead", "created_by")
        .order_by("-created_at")[:6]
    ]

    return {
        "stats": {
            "active_queue": active_count,
            "pending_action": pending_qs.count(),
            "new_this_week": new_this_week,
            "due_today": due_today,
            "approved_this_week": approved_this_week,
        },
        "charts": charts,
        "charts_json": json.dumps(charts),
        "recent_leads": recent_leads,
        "recent_activity": recent_activity,
    }


def staff_dashboard_metrics(user):
    """Lead pipeline stats and charts for a staff member's own submissions."""
    month_start = _month_start()
    prev_month_start = _month_shift(month_start, 1)
    prev_month_end = month_start - timedelta(days=1)
    base = Lead.objects.filter(Q(created_by=user) | Q(renewal_assigned_to=user, renewal_handled=False))

    total = base.count()
    this_month = base.filter(created_at__date__gte=month_start).count()
    prev_month = base.filter(
        created_at__date__gte=prev_month_start,
        created_at__date__lte=prev_month_end,
    ).count()

    in_progress = base.filter(sent_to_followup_at__isnull=True).count()
    needs_documents = base.filter(
        sent_to_followup_at__isnull=True,
        service_documents_zip="",
    ).count()
    at_followup = base.filter(
        sent_to_followup_at__isnull=False,
        sent_to_backoffice_at__isnull=True,
    ).count()
    at_backoffice = base.filter(sent_to_backoffice_at__isnull=False).exclude(
        backoffice_status=Lead.BackofficeStatus.REJECTED
    ).count()
    rejected = base.filter(backoffice_status=Lead.BackofficeStatus.REJECTED).count()

    six_month_start = _month_shift(month_start, 5)
    lead_counts = {
        row["month"].strftime("%Y-%m"): row["count"]
        for row in base.filter(created_at__date__gte=six_month_start)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
    }
    monthly_labels = []
    monthly_leads = []
    cursor = six_month_start
    for _ in range(6):
        key = f"{cursor.year}-{cursor.month:02d}"
        monthly_labels.append(f"{month_abbr[cursor.month]} {cursor.year}")
        monthly_leads.append(lead_counts.get(key, 0))
        cursor = _next_month(cursor)

    source_rows = (
        base.values("source__name").annotate(count=Count("id")).order_by("-count")[:8]
    )
    source_labels = [row["source__name"] or "Unknown" for row in source_rows]
    source_values = [row["count"] for row in source_rows]
    if not source_labels:
        source_labels = ["No leads yet"]
        source_values = [0]

    recent_leads = base.select_related("service", "staff_status", "followup_status", "source").order_by(
        "-created_at"
    )[:8]
    action_leads = base.filter(
        sent_to_followup_at__isnull=True,
        service_documents_zip="",
    ).order_by("-created_at")[:5]
    recent_activity = [
        _activity_entry_meta(entry)
        for entry in LeadRoadmapEntry.objects.filter(lead__created_by=user)
        .select_related("lead", "created_by")
        .order_by("-created_at")[:6]
    ]

    charts = {
        "monthly": {
            "labels": monthly_labels,
            "leads": monthly_leads,
            "revenue": [0] * len(monthly_labels),
            "subtitle": f"{monthly_labels[0]} – {monthly_labels[-1]}" if monthly_labels else "",
        },
        "sources": {
            "labels": source_labels,
            "values": source_values,
        },
    }

    return {
        "stats": {
            "total": total,
            "this_month": this_month,
            "month_trend": _pct_change(this_month, prev_month),
            "in_progress": in_progress,
            "needs_documents": needs_documents,
            "at_followup": at_followup,
            "at_backoffice": at_backoffice,
            "rejected": rejected,
        },
        "charts": charts,
        "charts_json": json.dumps(charts),
        "recent_leads": recent_leads,
        "action_leads": action_leads,
        "recent_activity": recent_activity,
    }


def awards_dashboard():
    today = _today()
    employee_award = Award.objects.filter(
        award_type=Award.AwardType.EMPLOYEE_OF_MONTH,
        month=today.month,
        year=today.year,
    ).select_related("winner_user").first()
    branch_award = Award.objects.filter(
        award_type=Award.AwardType.BRANCH_OF_MONTH,
        month=today.month,
        year=today.year,
    ).select_related("winner_branch").first()
    return {
        "employee_of_month": employee_award,
        "branch_of_month": branch_award,
    }


def organization_analytics():
    user_counts = UserProfile.objects.values("user_type").annotate(total=Count("id"))
    user_map = {row["user_type"]: row["total"] for row in user_counts}
    leave_counts = LeaveRequest.objects.values("workflow_stage").annotate(total=Count("id"))
    leave_map = {row["workflow_stage"]: row["total"] for row in leave_counts}
    ops = operations_dashboard()
    return {
        "users": user_map,
        "leave_workflow": leave_map,
        "operations": ops,
        "awards": awards_dashboard(),
    }
