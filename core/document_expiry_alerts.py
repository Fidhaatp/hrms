"""Alerts when team onboarding documents expire within one week."""

from datetime import timedelta

from django.utils import timezone

from backoffice.models import BackOffice
from branch.models import Branch, BranchManager
from core.models import TeamMemberDocuments, UserProfile
from finance.models import Finance
from followup.models import FollowUp
from marketing.models import Marketing
from staff.models import Staff

DOCUMENT_EXPIRY_ALERT_DAYS = 7

EXPIRY_FIELDS = (
    ("passport_expiry", "passport_image", "Passport"),
    ("emirates_id_expiry", "emirates_id_image", "Emirates ID"),
    ("insurance_expiry", "insurance_image", "Insurance"),
    ("labour_card_expiry", "labour_card_image", "Labour card"),
    ("labour_contract_expiry", "labour_contract_image", "Labour contract"),
)

BRANCH_MEMBER_MODELS = (Staff, FollowUp, BackOffice, Finance, Marketing)


def _today():
    return timezone.localdate()


def _employee_name(user):
    return user.get_full_name() or user.get_username()


def _user_branch(user):
    for attr in (
        "staff_profile",
        "followup_profile",
        "backoffice_profile",
        "finance_profile",
        "marketing_profile",
        "branch_manager_profile",
    ):
        profile = getattr(user, attr, None)
        if not profile:
            continue
        branch = getattr(profile, "branch", None)
        if branch:
            return branch
    return None


def _branch_user_ids(branch):
    if not branch:
        return []
    user_ids = set()
    for model in BRANCH_MEMBER_MODELS:
        user_ids.update(
            model.objects.filter(branch=branch, is_active=True).values_list("user_id", flat=True)
        )
    user_ids.update(
        BranchManager.objects.filter(branch=branch, is_active=True).values_list("user_id", flat=True)
    )
    return list(user_ids)


def _alert_message(alert, *, for_self=False):
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

    doc = alert["document_label"]
    if for_self:
        return f"Your {doc} {timing}."
    if alert.get("branch_name") and alert["branch_name"] != "—":
        return f"{alert['employee_name']} ({alert['branch_name']}) — {doc} {timing}."
    return f"{alert['employee_name']} — {doc} {timing}."


def _build_alerts(docs_qs):
    today = _today()
    warn_until = today + timedelta(days=DOCUMENT_EXPIRY_ALERT_DAYS)
    alerts = []

    for docs in docs_qs.select_related("user"):
        user = docs.user
        branch = _user_branch(user)
        employee_name = _employee_name(user)

        for expiry_field, file_field, label in EXPIRY_FIELDS:
            expiry = getattr(docs, expiry_field, None)
            file_value = getattr(docs, file_field, None)
            if not expiry or not file_value:
                continue
            if expiry > warn_until:
                continue

            days_left = (expiry - today).days
            alert = {
                "document_label": label,
                "expiry_date": expiry,
                "days_left": days_left,
                "days_ago": abs(days_left) if days_left < 0 else 0,
                "employee_name": employee_name,
                "employee_username": user.get_username(),
                "branch_name": branch.name if branch else "—",
                "branch_id": branch.pk if branch else None,
                "user_id": user.pk,
                "is_expired": days_left < 0,
            }
            alert["message"] = _alert_message(alert)
            alerts.append(alert)

    alerts.sort(key=lambda row: (row["days_left"], row["expiry_date"], row["employee_name"]))
    return alerts


def document_expiry_alerts_for_user(user):
    try:
        docs = user.team_documents
    except TeamMemberDocuments.DoesNotExist:
        return []
    alerts = _build_alerts(TeamMemberDocuments.objects.filter(pk=docs.pk))
    for alert in alerts:
        alert["message"] = _alert_message(alert, for_self=True)
    return alerts


def document_expiry_alerts_for_branch(branch):
    if not branch:
        return []
    user_ids = _branch_user_ids(branch)
    if not user_ids:
        return []
    return _build_alerts(TeamMemberDocuments.objects.filter(user_id__in=user_ids))


def document_expiry_alerts_for_hr():
    return _build_alerts(TeamMemberDocuments.objects.all())


def document_expiry_alerts_for_request(user):
    if user.is_superuser:
        return document_expiry_alerts_for_hr()

    profile = getattr(user, "profile", None)
    if not profile:
        return []

    if profile.user_type == UserProfile.UserType.HR:
        return document_expiry_alerts_for_hr()

    return []
