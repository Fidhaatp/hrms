from core.document_expiry_alerts import document_expiry_alerts_for_request
from core.models import UserProfile


def _split_document_expiry_alerts(alerts):
    expired = [row for row in alerts if row.get("is_expired")]
    expiring_soon = [row for row in alerts if not row.get("is_expired")]
    return expired, expiring_soon


def portal_notifications(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {
            "document_expiry_alerts": [],
            "document_expiry_expired_alerts": [],
            "document_expiry_soon_alerts": [],
            "document_expiry_alert_count": 0,
            "document_expiry_expired_count": 0,
            "document_expiry_soon_count": 0,
            "document_expiry_alert_days": 7,
            
            "lead_expiry_alerts": [],
            "lead_expiry_expired_alerts": [],
            "lead_expiry_soon_alerts": [],
            "lead_expiry_alert_count": 0,
            "lead_expiry_expired_count": 0,
            "lead_expiry_soon_count": 0,
            "lead_expiry_alert_days": 7,
            
            "total_notification_count": 0,
        }

    alerts = document_expiry_alerts_for_request(request.user)
    expired, expiring_soon = _split_document_expiry_alerts(alerts)
    from core.document_expiry_alerts import DOCUMENT_EXPIRY_ALERT_DAYS
    
    from core.lead_expiry_alerts import lead_expiry_alerts_for_request, LEAD_EXPIRY_ALERT_DAYS
    lead_alerts = lead_expiry_alerts_for_request(request.user)
    lead_expired = [row for row in lead_alerts if row.get("is_expired")]
    lead_expiring_soon = [row for row in lead_alerts if not row.get("is_expired")]

    return {
        "document_expiry_alerts": alerts,
        "document_expiry_expired_alerts": expired,
        "document_expiry_soon_alerts": expiring_soon,
        "document_expiry_alert_count": len(alerts),
        "document_expiry_expired_count": len(expired),
        "document_expiry_soon_count": len(expiring_soon),
        "document_expiry_alert_days": DOCUMENT_EXPIRY_ALERT_DAYS,
        
        "lead_expiry_alerts": lead_alerts,
        "lead_expiry_expired_alerts": lead_expired,
        "lead_expiry_soon_alerts": lead_expiring_soon,
        "lead_expiry_alert_count": len(lead_alerts),
        "lead_expiry_expired_count": len(lead_expired),
        "lead_expiry_soon_count": len(lead_expiring_soon),
        "lead_expiry_alert_days": LEAD_EXPIRY_ALERT_DAYS,
        
        "total_notification_count": len(alerts) + len(lead_alerts),
    }


def followup_portal_sidebar(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"followup_leads_queue_count": 0}

    profile = getattr(request.user, "profile", None)
    if not profile or profile.user_type != UserProfile.UserType.FOLLOWUP:
        return {"followup_leads_queue_count": 0}

    from core.lead_utils import followup_queue_leads_count

    return {"followup_leads_queue_count": followup_queue_leads_count()}


def backoffice_portal_sidebar(request):
    defaults = {
        "backoffice_pending_verifications_count": 0,
        "backoffice_team_pending_leads_count": 0,
        "backoffice_procedure_review_count": 0,
    }
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return defaults

    profile = getattr(request.user, "profile", None)
    if not profile or profile.user_type != UserProfile.UserType.BACKOFFICE:
        return defaults

    from core.backoffice_utils import (
        backoffice_in_progress_leads_queryset,
        backoffice_pending_leads_for_user,
        backoffice_procedure_review_leads_count,
        user_is_backoffice_head,
    )

    if user_is_backoffice_head(request.user):
        defaults["backoffice_pending_verifications_count"] = backoffice_pending_leads_for_user(
            request.user
        ).count()
    else:
        defaults["backoffice_team_pending_leads_count"] = backoffice_in_progress_leads_queryset(
            request.user
        ).count()
        defaults["backoffice_procedure_review_count"] = backoffice_procedure_review_leads_count()

    return defaults
