"""Back office head vs team permissions."""

from functools import wraps

from django.contrib import messages
from django.db.models import Count, F, Q
from django.shortcuts import redirect

from backoffice.models import BackOffice
from core.models import Lead


def get_backoffice_profile(user):
    return getattr(user, "backoffice_profile", None)


def user_is_backoffice_head(user):
    profile = get_backoffice_profile(user)
    return bool(profile and profile.is_active and profile.is_backoffice_head)


def backoffice_head_required():
    """Require an active back office head (use inside @portal_role_required BACKOFFICE views)."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not user_is_backoffice_head(request.user):
                messages.error(request, "Only the back office head can access this page.")
                return redirect("backoffice:index")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def backoffice_team_only_required():
    """Active back office team member — not the head."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            profile = get_backoffice_profile(request.user)
            if not profile or not profile.is_active:
                messages.error(request, "Back office profile not found.")
                return redirect("backoffice:index")
            if user_is_backoffice_head(request.user):
                messages.error(request, "Procedure review is for back office team members only.")
                return redirect("backoffice:index")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def backoffice_accessible_leads_queryset(user):
    """Head sees all back-office leads; team sees only head-approved (verified) leads."""
    from core.lead_utils import backoffice_all_leads_queryset

    qs = backoffice_all_leads_queryset()
    if user_is_backoffice_head(user):
        return qs
    return qs.filter(backoffice_status=Lead.BackofficeStatus.VERIFIED)


def annotate_backoffice_procedure_progress(queryset):
    from core.models import LeadProcedureStep

    return queryset.annotate(
        _required_procedure_count=Count(
            "service__procedures",
            filter=Q(service__procedures__is_active=True),
            distinct=True,
        ),
        _approved_procedure_count=Count(
            "procedure_steps",
            filter=Q(
                procedure_steps__status=LeadProcedureStep.Status.APPROVED,
                procedure_steps__procedure__is_active=True,
            ),
            distinct=True,
        ),
    )


def filter_backoffice_procedure_completed(queryset):
    """Leads where every active service procedure step is approved."""
    return annotate_backoffice_procedure_progress(queryset).filter(
        _required_procedure_count__gt=0,
        _required_procedure_count=F("_approved_procedure_count"),
    )


def filter_backoffice_procedure_in_progress(queryset):
    """Head-approved leads with procedures not fully done — excluding the review queue."""
    from core.models import LeadProcedureStep

    qs = annotate_backoffice_procedure_progress(queryset).filter(
        Q(_required_procedure_count=0)
        | Q(_required_procedure_count__gt=F("_approved_procedure_count")),
    )
    review_lead_ids = LeadProcedureStep.objects.filter(
        status=LeadProcedureStep.Status.PENDING,
        lead__backoffice_status=Lead.BackofficeStatus.VERIFIED,
        lead__sent_to_backoffice_at__isnull=False,
    ).values_list("lead_id", flat=True)
    return qs.exclude(pk__in=review_lead_ids)


def backoffice_completed_leads_queryset(user):
    return filter_backoffice_procedure_completed(backoffice_accessible_leads_queryset(user))


def backoffice_in_progress_leads_queryset(user):
    return filter_backoffice_procedure_in_progress(
        backoffice_accessible_leads_queryset(user).filter(
            backoffice_status=Lead.BackofficeStatus.VERIFIED,
        )
    )


def backoffice_pending_leads_for_user(user):
    """Pending approve/reject queue — head only."""
    from core.lead_utils import backoffice_pending_leads_queryset

    if not user_is_backoffice_head(user):
        return Lead.objects.none()
    return backoffice_pending_leads_queryset()


def backoffice_cases_queryset_for_user(user):
    from core.models import ClientCase

    qs = ClientCase.objects.all()
    if user_is_backoffice_head(user):
        return qs
    profile = get_backoffice_profile(user)
    if profile and profile.branch_id:
        return qs.filter(branch_id=profile.branch_id)
    return ClientCase.objects.none()


def backoffice_team_members_queryset():
    return BackOffice.objects.select_related("user", "user__profile", "branch").order_by(
        "-is_active", "-is_backoffice_head", "branch__name", "user__username"
    )


def backoffice_pending_procedure_count():
    """Procedure steps waiting for team review on head-approved leads."""
    from core.models import LeadProcedureStep

    return LeadProcedureStep.objects.filter(
        status=LeadProcedureStep.Status.PENDING,
        lead__backoffice_status=Lead.BackofficeStatus.VERIFIED,
        lead__sent_to_backoffice_at__isnull=False,
    ).count()


def backoffice_procedure_review_leads_count():
    """Head-approved leads with at least one procedure step awaiting team review."""
    from core.models import LeadProcedureStep

    return (
        LeadProcedureStep.objects.filter(
            status=LeadProcedureStep.Status.PENDING,
            lead__backoffice_status=Lead.BackofficeStatus.VERIFIED,
            lead__sent_to_backoffice_at__isnull=False,
        )
        .values("lead_id")
        .distinct()
        .count()
    )


def backoffice_recent_procedure_leads(limit=8):
    """Distinct leads with pending procedure steps for dashboard."""
    from core.models import LeadProcedureStep

    lead_ids = (
        LeadProcedureStep.objects.filter(
            status=LeadProcedureStep.Status.PENDING,
            lead__backoffice_status=Lead.BackofficeStatus.VERIFIED,
            lead__sent_to_backoffice_at__isnull=False,
        )
        .values_list("lead_id", flat=True)
        .distinct()[:limit]
    )
    return (
        Lead.objects.filter(pk__in=lead_ids)
        .select_related("branch", "service", "created_by")
        .order_by("-updated_at")
    )


def get_backoffice_portal_nav(user):
    from core.portal_modules import BACKOFFICE_NAV

    head_only = {"pending", "team"}
    team_only = {"procedures", "pending_leads"}
    nav = []
    for item in BACKOFFICE_NAV:
        if item["nav_key"] in head_only and not user_is_backoffice_head(user):
            continue
        if item["nav_key"] in team_only and user_is_backoffice_head(user):
            continue
        nav.append(item)
    return nav
