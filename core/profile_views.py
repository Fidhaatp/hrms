"""Reusable My Profile views for every portal."""

from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from core.auth_utils import redirect_user_after_login
from core.forms import ProfilePictureForm
from core.models import UserProfile
from core.portal import portal_role_required, render_portal_page
from core.profile_page import build_portal_profile_context


def _profile_redirect(user):
    profile = getattr(user, "profile", None)
    if profile:
        from django.urls import reverse

        return redirect(reverse(profile.get_profile_url_name()))
    return redirect_user_after_login(user)


def profile_view(user_type):
    @portal_role_required(user_type)
    def view(request):
        return render_portal_page(
            request,
            user_type,
            "portal/pages/profile.html",
            "My Profile",
            active_nav="profile",
            **build_portal_profile_context(request.user),
        )

    return view


def profile_picture_update_view(user_type):
    @portal_role_required(user_type)
    @require_http_methods(["POST"])
    def view(request):
        profile = getattr(request.user, "profile", None)
        if not profile:
            messages.error(request, "Profile not found.")
            return _profile_redirect(request.user)

        form = ProfilePictureForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile picture updated.")
        else:
            messages.error(request, "Could not update profile picture. Please use a valid image file.")
        return _profile_redirect(request.user)

    return view


# Named views for URL imports
staff_profile = profile_view(UserProfile.UserType.STAFF)
staff_profile_photo = profile_picture_update_view(UserProfile.UserType.STAFF)

followup_profile = profile_view(UserProfile.UserType.FOLLOWUP)
followup_profile_photo = profile_picture_update_view(UserProfile.UserType.FOLLOWUP)

backoffice_profile = profile_view(UserProfile.UserType.BACKOFFICE)
backoffice_profile_photo = profile_picture_update_view(UserProfile.UserType.BACKOFFICE)

branch_profile = profile_view(UserProfile.UserType.BRANCH)
branch_profile_photo = profile_picture_update_view(UserProfile.UserType.BRANCH)

finance_profile = profile_view(UserProfile.UserType.FINANCE)
finance_profile_photo = profile_picture_update_view(UserProfile.UserType.FINANCE)

marketing_profile = profile_view(UserProfile.UserType.MARKETING)
marketing_profile_photo = profile_picture_update_view(UserProfile.UserType.MARKETING)

accountant_profile = profile_view(UserProfile.UserType.BRANCH_ACCOUNTANT)
accountant_profile_photo = profile_picture_update_view(UserProfile.UserType.BRANCH_ACCOUNTANT)
