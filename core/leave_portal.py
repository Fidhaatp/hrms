from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from core.leave_forms import LeaveRequestForm
from core.leave_utils import all_leave_summaries, leave_summary as yearly_leave_summary
from core.models import LeaveRequest, UserProfile
from core.portal import portal_role_required, render_portal_page

LEAVE_LIST_URL = {
    UserProfile.UserType.STAFF: "staff:leave_list",
    UserProfile.UserType.FOLLOWUP: "followup:leave_list",
    UserProfile.UserType.BACKOFFICE: "backoffice:leave_list",
}

LEAVE_ADD_URL = {
    UserProfile.UserType.STAFF: "staff:leave_add",
    UserProfile.UserType.FOLLOWUP: "followup:leave_add",
    UserProfile.UserType.BACKOFFICE: "backoffice:leave_add",
}


def _leave_page_context(request, user_type, **extra):
    balances = all_leave_summaries(request.user)
    defaults = {
        "leave_requests": LeaveRequest.objects.filter(user=request.user).select_related(
            "leave_category", "leave_type"
        ),
        "leave_balances": balances,
        "leave_summary": yearly_leave_summary(request.user),
        "leave_form": LeaveRequestForm(user=request.user),
        "show_leave_modal": False,
        "leave_list_url_name": LEAVE_LIST_URL[user_type],
        "leave_add_url_name": LEAVE_ADD_URL[user_type],
    }
    defaults.update(extra)
    return defaults


def leave_list_view(user_type):
    @portal_role_required(user_type)
    def view(request):
        return render_portal_page(
            request,
            user_type,
            "portal/leave/list.html",
            "Leave Requests",
            active_nav="leave",
            **_leave_page_context(request, user_type),
        )

    return view


def leave_add_view(user_type):
    @portal_role_required(user_type)
    @require_http_methods(["POST"])
    def view(request):
        form = LeaveRequestForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect(LEAVE_LIST_URL[user_type])

        return render_portal_page(
            request,
            user_type,
            "portal/leave/list.html",
            "Leave Requests",
            active_nav="leave",
            **_leave_page_context(request, user_type, leave_form=form, show_leave_modal=True),
        )

    return view
