"""Shared avatar / display helpers for all portal user types."""


def get_initials(display_name):
    name = (display_name or "").replace("_", " ").replace(".", " ").strip()
    parts = [p for p in name.split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return (name[:2] if len(name) >= 2 else name[:1] or "?").upper()


def get_avatar_context(user):
    """Build template context for profile avatar (HR, branch, staff, follow-up, etc.)."""
    if not user or not user.is_authenticated:
        return {
            "display_name": "Guest",
            "initials": "?",
            "avatar_url": None,
        }

    profile = getattr(user, "profile", None)
    display_name = user.get_full_name() or user.get_username()

    role_profile = (
        getattr(user, "hr_profile", None)
        or getattr(user, "branch_manager_profile", None)
        or getattr(user, "staff_profile", None)
        or getattr(user, "followup_profile", None)
        or getattr(user, "backoffice_profile", None)
    )
    if role_profile and hasattr(role_profile, "display_name"):
        display_name = role_profile.display_name

    avatar_url = None
    if profile and profile.profile_picture:
        avatar_url = profile.profile_picture.url

    return {
        "display_name": display_name,
        "initials": get_initials(display_name),
        "avatar_url": avatar_url,
    }
