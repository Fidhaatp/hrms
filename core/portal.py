from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.auth_utils import redirect_user_after_login
from core.backoffice_utils import (
    backoffice_accessible_leads_queryset,
    backoffice_cases_queryset_for_user,
    backoffice_head_required,
    backoffice_pending_leads_for_user,
    get_backoffice_portal_nav,
    user_is_backoffice_head,
)
from core.models import UserProfile
from core.portal_modules import PORTAL_META, PORTAL_NAV
from core.profile_page import build_portal_profile_context
from core.profile_utils import get_avatar_context


def portal_user_context(user, role_label):
    avatar = get_avatar_context(user)
    profile = getattr(user, "profile", None)
    return {
        "portal_display_name": avatar["display_name"],
        "portal_initials": avatar["initials"],
        "portal_avatar_url": avatar["avatar_url"],
        "portal_role": role_label,
        "portal_profile_url_name": profile.get_profile_url_name() if profile else None,
    }


def render_portal_page(request, user_type, content_template, page_title, active_nav="dashboard", **extra):
    meta = PORTAL_META[user_type]
    portal_nav = PORTAL_NAV[user_type]
    role_label = meta["role_label"]
    if user_type == UserProfile.UserType.BACKOFFICE:
        portal_nav = get_backoffice_portal_nav(request.user)
        role_label = "Back Office Head" if user_is_backoffice_head(request.user) else meta["role_label"]
    context = {
        "page_title": page_title,
        "content_template": content_template,
        "active_nav": active_nav,
        "portal_nav": portal_nav,
        "portal_home_url_name": meta["home_url_name"],
        "portal_brand_sub": meta["brand_sub"],
        "is_backoffice_head": user_type == UserProfile.UserType.BACKOFFICE and user_is_backoffice_head(request.user),
        **portal_user_context(request.user, role_label),
        **extra,
    }
    return render(request, "portal/base.html", context)


def portal_role_required(user_type):
    """Only allow users with the given portal role."""

    def decorator(view_func):
        @login_required(login_url="core:login")
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            if not profile or profile.user_type != user_type:
                return redirect_user_after_login(request.user)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def portal_roles_required(*user_types):
    """Allow any of the given portal roles."""

    def decorator(view_func):
        @login_required(login_url="core:login")
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            if not profile or profile.user_type not in user_types:
                return redirect_user_after_login(request.user)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
