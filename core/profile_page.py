"""Shared My Profile page data for all portals."""

from core.forms import ProfilePictureForm
from core.models import UserProfile
from core.profile_utils import get_avatar_context

ROLE_PROFILE_ATTR = {
    UserProfile.UserType.HR: "hr_profile",
    UserProfile.UserType.STAFF: "staff_profile",
    UserProfile.UserType.FOLLOWUP: "followup_profile",
    UserProfile.UserType.BACKOFFICE: "backoffice_profile",
    UserProfile.UserType.BRANCH: "branch_manager_profile",
    UserProfile.UserType.FINANCE: "finance_profile",
    UserProfile.UserType.MARKETING: "marketing_profile",
    UserProfile.UserType.BRANCH_ACCOUNTANT: "branch_accountant_profile",
}


def _role_profile(user, user_type):
    attr = ROLE_PROFILE_ATTR.get(user_type)
    return getattr(user, attr, None) if attr else None


def _username_for(user, role_profile):
    if role_profile:
        if hasattr(role_profile, "login_username"):
            return role_profile.login_username
        if hasattr(role_profile, "username"):
            return role_profile.username
    return user.get_username()


def build_portal_profile_context(user):
    user_profile = getattr(user, "profile", None)
    avatar = get_avatar_context(user)
    role_profile = _role_profile(user, user_profile.user_type) if user_profile else None

    branch_name = None
    if role_profile and getattr(role_profile, "branch", None):
        branch_name = role_profile.branch.name

    phone = ""
    if role_profile and getattr(role_profile, "phone", None):
        phone = role_profile.phone
    elif user_profile and user_profile.phone:
        phone = user_profile.phone

    created_at = None
    updated_at = None
    if role_profile:
        created_at = getattr(role_profile, "created_at", None)
        updated_at = getattr(role_profile, "updated_at", None)
    if user_profile:
        created_at = created_at or user_profile.created_at
        updated_at = updated_at or user_profile.updated_at

    is_active = user.is_active
    if role_profile and hasattr(role_profile, "is_active"):
        is_active = role_profile.is_active

    role_label = user_profile.get_user_type_display() if user_profile else "User"
    photo_url_name = None
    if user_profile:
        photo_url_name = user_profile.get_profile_url_name().replace(":profile", ":profile_picture_update")

    return {
        "profile_details": {
            "username": _username_for(user, role_profile),
            "display_name": avatar["display_name"],
            "email": user.email or "",
            "phone": phone or "—",
            "join_date": getattr(role_profile, "join_date", None),
            "date_of_birth": getattr(role_profile, "date_of_birth", None),
            "branch_name": branch_name,
            "role_label": role_label,
            "created_at": created_at,
            "updated_at": updated_at,
            "is_active": is_active,
        },
        "has_role_profile": bool(role_profile or user_profile),
        "profile_picture_form": ProfilePictureForm(instance=user_profile) if user_profile else None,
        "profile_photo_url_name": photo_url_name,
    }
