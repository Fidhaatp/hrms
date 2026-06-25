"""Alerts when a lead's service expires within one week."""

from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from core.models import Lead, UserProfile

LEAD_EXPIRY_ALERT_DAYS = 7

def _today():
    return timezone.localdate()

def _alert_message(alert):
    expiry_text = alert["expiry_date"].strftime("%d %b %Y")
    days_left = alert["days_left"]
    if days_left < 0:
        timing = f"expired on {expiry_text}"
    elif days_left == 0:
        timing = f"expires today ({expiry_text})"
    elif days_left == 1:
        timing = f"expires tomorrow ({expiry_text})"
    else:
        timing = f"expires in {days_left} days ({expiry_text})"

    return f"Lead {alert['lead_name']} ({alert['lead_display_id']}) service {timing}."

def _build_alerts(leads_qs):
    today = _today()
    warn_until = today + timedelta(days=LEAD_EXPIRY_ALERT_DAYS)
    alerts = []

    # Only check leads that have an expiry date and are not completely lost/archived.
    # We'll just filter for service_expire_date <= warn_until
    # We might also want to filter out leads that are already renewed, but for now we'll just check the date.
    leads = leads_qs.filter(
        service_expire_date__isnull=False,
        service_expire_date__lte=warn_until,
        renewal_handled=False
    ).select_related("branch", "service")

    for lead in leads:
        expiry = lead.service_expire_date
        days_left = (expiry - today).days

        alert = {
            "lead_name": lead.name,
            "lead_display_id": lead.display_id,
            "lead_id": lead.pk,
            "expiry_date": expiry,
            "days_left": days_left,
            "days_ago": abs(days_left) if days_left < 0 else 0,
            "is_expired": days_left < 0,
            "assigned_to_id": lead.renewal_assigned_to_id,
            "assigned_to_name": lead.renewal_assigned_to.get_full_name() or lead.renewal_assigned_to.username if lead.renewal_assigned_to else None,
        }
        alert["message"] = _alert_message(alert)
        alerts.append(alert)

    alerts.sort(key=lambda row: (row["days_left"], row["expiry_date"], row["lead_name"]))
    return alerts


def lead_expiry_alerts_for_request(user):
    if user.is_superuser:
        return []

    profile = getattr(user, "profile", None)
    if not profile:
        return []

    if profile.user_type == UserProfile.UserType.HR:
        return []

    # Branch Staff & Managers see leads in their branch
    if profile.user_type in (UserProfile.UserType.BRANCH, UserProfile.UserType.STAFF):
        # We need the user's branch
        if profile.user_type == UserProfile.UserType.BRANCH:
            manager = getattr(user, "branch_manager_profile", None)
            branch = manager.branch if manager else None
        else:
            staff = getattr(user, "staff_profile", None)
            branch = staff.branch if staff else None
            
        if not branch:
            return []
        
        if profile.user_type == UserProfile.UserType.STAFF:
            return _build_alerts(Lead.objects.filter(branch=branch).filter(
                Q(renewal_assigned_to=user) | 
                (Q(renewal_assigned_to__isnull=True) & Q(created_by=user))
            ))
        else:
            return _build_alerts(Lead.objects.filter(branch=branch))

    # Follow-up team sees leads assigned to them or all followup leads
    if profile.user_type == UserProfile.UserType.FOLLOWUP:
        from core.lead_portal import followup_team_leads_queryset
        qs = followup_team_leads_queryset()
        # To avoid spam, only show leads assigned to this user, OR if unassigned, show to all?
        # Let's show leads that have followup_assigned_to=user OR followup_assigned_to__isnull=True
        return _build_alerts(qs.filter(
            Q(followup_assigned_to=user) | Q(followup_assigned_to__isnull=True)
        ))

    return []
