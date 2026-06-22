from core.models import Lead, LeadLostReasonType, LeadSource, LeadService, LeadStatus


def get_creator_branch(user):
    """Branch of the staff member who created the lead."""
    staff = getattr(user, "staff_profile", None)
    if staff and staff.branch_id:
        return staff.branch
    return None


def get_active_lead_sources():
    return LeadSource.objects.filter(is_active=True).order_by("sort_order", "name")


def get_active_lead_services():
    return LeadService.objects.filter(is_active=True).order_by("sort_order", "name")


def get_active_lead_statuses():
    return LeadStatus.objects.filter(is_active=True).order_by("sort_order", "name")


def get_staff_lead_statuses():
    """Statuses staff may set before handoff (excludes follow-up Approved, etc.)."""
    return get_active_lead_statuses().filter(sends_to_backoffice=False)


def get_followup_lead_statuses():
    """Statuses follow-up may set after staff converted the lead."""
    return get_active_lead_statuses().filter(sends_to_followup=False)


def get_active_lost_reason_types():
    return LeadLostReasonType.objects.filter(is_active=True).order_by("sort_order", "name")


def is_staff_lost_status(status):
    return bool(status and status.code == LeadStatus.LOST_CODE)


def staff_status_to_stage(status):
    """Map staff LeadStatus code to Lead.StaffStage."""
    from core.models import Lead

    mapping = {
        LeadStatus.NEW_CODE: Lead.StaffStage.NEW,
        LeadStatus.CONTACTED_CODE: Lead.StaffStage.CONTACTED,
        LeadStatus.QUALIFIED_CODE: Lead.StaffStage.QUALIFIED,
        LeadStatus.CONVERTED_CODE: Lead.StaffStage.CONVERTED,
        LeadStatus.LOST_CODE: Lead.StaffStage.LOST,
    }
    if status and status.code in mapping:
        return mapping[status.code]
    return None


def get_default_lead_status():
    status = LeadStatus.objects.filter(is_default=True, is_active=True).order_by("sort_order").first()
    if status:
        return status
    status, _ = LeadStatus.objects.get_or_create(
        code=LeadStatus.NEW_CODE,
        defaults={
            "name": "New",
            "badge_style": LeadStatus.BadgeStyle.ACTIVE,
            "is_default": True,
            "sort_order": 0,
        },
    )
    return status


def get_lead_status_by_code(code):
    return LeadStatus.objects.get(code=code, is_active=True)


def get_followup_queue_default_status():
    """Initial follow-up team status when staff sends a converted lead."""
    status = LeadStatus.objects.filter(code=LeadStatus.NEW_CODE, is_active=True).order_by(
        "sort_order"
    ).first()
    return status or get_default_lead_status()


def converted_leads_filter():
    return {"followup_status__counts_as_converted": True}


def followup_status_is_converted(status):
    """True when follow-up marks the customer as converted (sale complete)."""
    return bool(status and status.counts_as_converted)


def followup_status_sends_to_backoffice(status):
    """True when follow-up approves the lead for back office processing."""
    return bool(status and status.sends_to_backoffice)


def followup_team_leads_queryset():
    """All staff-converted leads for the follow-up portal — every branch, never removed on status change."""
    return Lead.objects.filter(
        sent_to_followup_at__isnull=False,
        staff_stage=Lead.StaffStage.CONVERTED,
    ).exclude(backoffice_status=Lead.BackofficeStatus.REJECTED)


def followup_sent_leads_queryset():
    """Alias for follow-up team lead list."""
    return followup_team_leads_queryset()


def followup_active_leads_queryset():
    """Staff-converted leads awaiting follow-up action (not yet sent to back office)."""
    return followup_team_leads_queryset().filter(sent_to_backoffice_at__isnull=True)


def followup_queue_leads_count():
    """Follow-up leads with ongoing procedures (same queue as the Follow-up Leads page)."""
    return filter_leads_procedure_in_progress(followup_team_leads_queryset()).count()


def backoffice_pending_leads_queryset():
    """Follow-up approved leads waiting for back office — all branches."""
    return Lead.objects.filter(
        backoffice_status=Lead.BackofficeStatus.PENDING,
        sent_to_backoffice_at__isnull=False,
    )


def backoffice_all_leads_queryset():
    """All leads follow-up approved to back office — all branches."""
    return Lead.objects.filter(sent_to_backoffice_at__isnull=False)


def filter_leads_procedure_completed(queryset):
    """Leads where every active service procedure step is approved."""
    from core.backoffice_utils import filter_backoffice_procedure_completed

    return filter_backoffice_procedure_completed(queryset)


def filter_leads_procedure_in_progress(queryset):
    """Leads with procedures still ongoing (or service has no procedures)."""
    from django.db.models import F, Q

    from core.backoffice_utils import annotate_backoffice_procedure_progress

    qs = annotate_backoffice_procedure_progress(queryset)
    return qs.filter(
        Q(_required_procedure_count=0) | Q(_required_procedure_count__gt=F("_approved_procedure_count"))
    )


def apply_converted_lead_handoff(lead, user, *, note=""):
    """
    When follow-up sets status to Converted:
    - Send lead to branch roadmap (branch manager & accountant)
    - Open back office case processing automatically
    """
    from core.case_utils import ensure_client_case

    if not lead.branch_id:
        return False, None, "This lead has no branch — staff must add it from a branch first."

    lead.pipeline_stage = Lead.PipelineStage.BRANCH
    lead.staff_stage = Lead.StaffStage.CONVERTED
    lead.handover_status = Lead.HandoverStatus.HANDED_OVER
    case, created = ensure_client_case(lead, user)
    roadmap_note = note or "Customer converted — branch roadmap and back office case processing started automatically."
    lead.roadmap_entries.create(
        created_by=user,
        title=f"Converted → {lead.branch.name} & back office",
        note=roadmap_note,
    )
    msg = f"Sent to {lead.branch.name} roadmap"
    if created:
        msg += f" and opened case {case.case_ref} for back office."
    else:
        msg += f"; case {case.case_ref} is active for back office."
    return True, case, msg
