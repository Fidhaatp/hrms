"""Branch lead monitoring — filters, search, and timeline steps."""

from datetime import datetime, timedelta

from django.db.models import Prefetch, Q
from django.utils import timezone

from core.lead_filters import apply_lead_list_filters, parse_lead_list_filters
from core.models import Lead, LeadProcedureStep, LeadRoadmapEntry, UserProfile

TEAM_ROLE_LABELS = {
    UserProfile.UserType.STAFF: "Staff",
    UserProfile.UserType.FOLLOWUP: "Follow-up",
    UserProfile.UserType.BACKOFFICE: "Back office",
    UserProfile.UserType.BRANCH: "Branch manager",
    UserProfile.UserType.HR: "HR",
}

STEP_TONES = ("green", "teal", "slate", "gold", "emerald")
BRANCH_LEADS_PER_PAGE = 15


def parse_monitoring_params(request, *, default_period="all"):
    period = (request.GET.get("period") or default_period).strip().lower()
    if period not in ("today", "yesterday", "week", "month", "year", "custom", "all"):
        period = "week"
    query = (request.GET.get("q") or "").strip()
    date_from_raw = (request.GET.get("date_from") or "").strip()
    date_to_raw = (request.GET.get("date_to") or "").strip()
    date_from = _parse_date(date_from_raw)
    date_to = _parse_date(date_to_raw)
    status_filters = parse_lead_list_filters(request)
    return {
        "period": period,
        "q": query,
        "date_from": date_from,
        "date_to": date_to,
        "date_from_raw": date_from_raw,
        "date_to_raw": date_to_raw,
        **status_filters,
    }


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _period_range(period, date_from=None, date_to=None):
    today = timezone.localdate()
    if period == "all":
        return None, None
    if period == "today":
        return today, today
    if period == "yesterday":
        day = today - timedelta(days=1)
        return day, day
    if period == "week":
        return today - timedelta(days=today.weekday()), today
    if period == "month":
        return today.replace(day=1), today
    if period == "year":
        return today.replace(month=1, day=1), today
    if period == "custom" and date_from and date_to:
        return min(date_from, date_to), max(date_from, date_to)
    if period == "custom" and date_from:
        return date_from, date_from
    return today - timedelta(days=today.weekday()), today


def branch_leads_queryset(branch):
    """All leads belonging to a branch."""
    if not branch:
        return Lead.objects.none()
    return (
        Lead.objects.filter(branch=branch)
        .select_related(
            "created_by",
            "created_by__profile",
            "followup_assigned_to",
            "followup_assigned_to__profile",
            "staff_status",
            "followup_status",
            "backoffice_checked_by",
            "backoffice_checked_by__profile",
            "source",
            "service",
        )
        .prefetch_related(
            Prefetch(
                "roadmap_entries",
                queryset=LeadRoadmapEntry.objects.select_related(
                    "created_by",
                    "created_by__profile",
                ).order_by("created_at"),
            ),
            Prefetch(
                "procedure_steps",
                queryset=LeadProcedureStep.objects.select_related("procedure", "reviewed_by"),
            ),
            "service__procedures",
        )
        .order_by("-updated_at", "-created_at")
    )


def branch_monitoring_queryset(branch, params):
    if not branch:
        return Lead.objects.none()

    qs = branch_leads_queryset(branch)

    query = params.get("q")
    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(company__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
            | Q(takhlees_id__icontains=query)
            | Q(passport_no__icontains=query)
            | Q(created_by__username__icontains=query)
            | Q(created_by__first_name__icontains=query)
            | Q(created_by__last_name__icontains=query)
        )

    start, end = _period_range(
        params.get("period", "week"),
        params.get("date_from"),
        params.get("date_to"),
    )
    if start and end:
        qs = qs.filter(
            Q(created_at__date__gte=start, created_at__date__lte=end)
            | Q(roadmap_entries__created_at__date__gte=start, roadmap_entries__created_at__date__lte=end)
            | Q(updated_at__date__gte=start, updated_at__date__lte=end)
        ).distinct()

    return apply_lead_list_filters(qs, params)


def _user_team_label(user):
    if not user:
        return ""
    profile = getattr(user, "profile", None)
    if not profile:
        return ""
    return TEAM_ROLE_LABELS.get(profile.user_type, profile.get_user_type_display())


def _actor_payload(user):
    if not user:
        return {
            "staff": "System",
            "staff_username": "",
            "team": "",
        }
    return {
        "staff": user.get_full_name() or user.get_username(),
        "staff_username": user.get_username(),
        "team": _user_team_label(user),
    }


def _roadmap_text(lead):
    parts = []
    for entry in lead.roadmap_entries.all():
        parts.append(entry.title or "")
        parts.append(entry.note or "")
    return " ".join(parts).lower()


def _skip_synthetic_event(roadmap_text, keywords):
    return any(keyword in roadmap_text for keyword in keywords)


def _is_duplicate_lead_added(entry, lead):
    title = (entry.title or "").lower()
    if title not in ("follow up", "lead added", "lead registered"):
        return False
    delta = abs((entry.created_at - lead.created_at).total_seconds())
    return delta < 120


def _followup_actor(lead):
    if lead.followup_assigned_to_id:
        return lead.followup_assigned_to
    for entry in reversed(list(lead.roadmap_entries.all())):
        user = entry.created_by
        if user and _user_team_label(user) == "Follow-up":
            return user
    return None


def _roadmap_entry_for_keywords(lead, *keywords):
    for entry in reversed(list(lead.roadmap_entries.all())):
        text = f"{entry.title} {entry.note}".lower()
        if all(keyword in text for keyword in keywords):
            return entry
    return None


def _status_for_roadmap_entry(entry):
    title = entry.title or ""
    title_lower = title.lower()
    note = entry.note or ""
    note_lower = note.lower()

    if "not correct" in title_lower or "reject" in title_lower:
        return "Rejected"
    if "back office verified" in title_lower:
        return "Verified"
    if "approved" in title_lower and "back office" in title_lower:
        return "Approved"
    if title_lower.startswith("status:"):
        return title.split(":", 1)[1].strip()
    if title_lower.startswith("follow-up:"):
        return title.split(":", 1)[1].strip()
    if "converted" in title_lower:
        return "Converted"
    if "zip checked" in title_lower or "zip verified" in title_lower:
        return "Documents checked"
    if "lead details updated" in title_lower:
        return "Details updated"
    if title_lower in ("follow up", "lead added", "lead registered"):
        return "New"
    if "handed over" in title_lower or "handover" in title_lower:
        return "Handed over"
    if "sent to follow-up" in note_lower:
        if "(" in note and ")" in note:
            return note.rsplit("(", 1)[-1].rstrip(").")
        return "Sent to follow-up"
    if "status to " in note_lower:
        return note.split("status to ", 1)[1].strip().rstrip(".")
    return "Updated"


def _event_from_roadmap(entry):
    actor = _actor_payload(entry.created_by)
    return {
        "title": entry.title,
        "staff": actor["staff"],
        "staff_username": actor["staff_username"],
        "team": actor["team"],
        "status": _status_for_roadmap_entry(entry),
        "note": entry.note or "",
        "at": entry.created_at,
    }


def lead_timeline_steps(lead):
    """Full lead history — roadmap entries plus pipeline milestones."""
    events = []
    creator = lead.created_by
    creator_actor = _actor_payload(creator)
    events.append(
        {
            "title": "Lead added",
            "staff": creator_actor["staff"],
            "staff_username": creator_actor["staff_username"],
            "team": creator_actor["team"] or "Staff",
            "status": "New",
            "note": f"Staff added lead · {lead.branch.name if lead.branch else '—'}",
            "at": lead.created_at,
        }
    )

    for entry in lead.roadmap_entries.all():
        if _is_duplicate_lead_added(entry, lead):
            continue
        events.append(_event_from_roadmap(entry))

    roadmap_text = _roadmap_text(lead)

    if lead.sent_to_followup_at and not _skip_synthetic_event(
        roadmap_text, ("sent to follow-up", "sent to follow up", "follow-up team")
    ):
        actor = _actor_payload(lead.created_by)
        events.append(
            {
                "title": "Sent to follow-up team",
                "staff": actor["staff"],
                "staff_username": actor["staff_username"],
                "team": actor["team"] or "Staff",
                "status": "Converted",
                "note": "Staff sent lead to follow-up team.",
                "at": lead.sent_to_followup_at,
            }
        )

    if lead.sent_to_backoffice_at and not _skip_synthetic_event(
        roadmap_text, ("approved → back office", "approved -> back office")
    ):
        entry = _roadmap_entry_for_keywords(lead, "approved", "back office")
        actor = _actor_payload(entry.created_by if entry else _followup_actor(lead))
        events.append(
            {
                "title": "Follow-up approved → Back office",
                "staff": actor["staff"],
                "staff_username": actor["staff_username"],
                "team": actor["team"] or "Follow-up",
                "status": "Approved",
                "note": (
                    entry.note
                    if entry and entry.note
                    else "Follow-up approved lead for back office verification."
                ),
                "at": lead.sent_to_backoffice_at,
            }
        )

    if lead.backoffice_checked_at and not _skip_synthetic_event(
        roadmap_text, ("back office verified", "back office — not correct")
    ):
        rejected = lead.backoffice_status == Lead.BackofficeStatus.REJECTED
        entry = _roadmap_entry_for_keywords(
            lead, "back office", "not correct" if rejected else "verified"
        )
        actor = _actor_payload(entry.created_by if entry else lead.backoffice_checked_by)
        events.append(
            {
                "title": "Back office: Not correct" if rejected else "Back office: Verified",
                "staff": actor["staff"],
                "staff_username": actor["staff_username"],
                "team": actor["team"] or "Back office",
                "status": "Rejected" if rejected else "Verified",
                "note": (
                    entry.note
                    if entry and entry.note
                    else (lead.backoffice_notes or "Back office completed verification.")
                ),
                "at": lead.backoffice_checked_at,
            }
        )

    if lead.handed_over_at and not _skip_synthetic_event(roadmap_text, ("handed over", "handover")):
        actor = _actor_payload(_followup_actor(lead) or lead.created_by)
        events.append(
            {
                "title": "Handed over to branch",
                "staff": actor["staff"],
                "staff_username": actor["staff_username"],
                "team": actor["team"],
                "status": lead.get_staff_stage_display(),
                "note": lead.handover_note or "Customer converted — branch roadmap started.",
                "at": lead.handed_over_at,
            }
        )

    events.sort(key=lambda item: item["at"])
    for index, step in enumerate(events):
        step["tone"] = STEP_TONES[index % len(STEP_TONES)]
    return events


def monitoring_lead_cards(leads):
    return [
        {
            "lead": lead,
            "steps": lead_timeline_steps(lead),
            "stage_label": _branch_stage_label(lead),
            "milestones": lead_pipeline_milestones(lead),
        }
        for lead in leads
    ]


def lead_pipeline_milestones(lead):
    """Checkpoints shown in branch lead tracking history table."""
    return {
        "added": bool(lead.created_at),
        "documents": bool(lead.service_documents_zip),
        "followup": bool(lead.sent_to_followup_at),
        "followup_approved": bool(lead.sent_to_backoffice_at),
        "backoffice_verified": lead.backoffice_status == Lead.BackofficeStatus.VERIFIED
        and bool(lead.backoffice_checked_at),
        "backoffice_rejected": lead.backoffice_status == Lead.BackofficeStatus.REJECTED,
    }


def _branch_stage_label(lead):
    if lead.backoffice_status == Lead.BackofficeStatus.REJECTED:
        return "Rejected by back office"
    if lead.pipeline_stage == Lead.PipelineStage.BRANCH:
        return "At branch"
    if lead.sent_to_backoffice_at:
        if lead.backoffice_status == Lead.BackofficeStatus.VERIFIED:
            return "Back office verified"
        return "Back office review"
    if lead.sent_to_followup_at:
        return "With follow-up"
    return "With staff"
