from datetime import date

from core.models import LeaveCategory, LeaveRequest, LeaveType


def count_leave_days(start_date, end_date):
    return (end_date - start_date).days + 1


def get_active_leave_categories():
    return LeaveCategory.objects.filter(is_active=True).order_by("name")


def get_active_leave_types():
    return LeaveType.objects.filter(is_active=True).order_by("name")


def get_yearly_leave_category():
    category, _ = LeaveCategory.objects.get_or_create(
        code=LeaveCategory.YEARLY_CODE,
        defaults={
            "name": "Yearly Leave",
            "description": "Annual leave entitlement — one month (30 days) per calendar year.",
            "days_per_year": 30,
            "is_active": True,
        },
    )
    return category


def used_leave_days(user, leave_category, year=None):
    """Days booked against a category (pending + approved) in a calendar year."""
    year = year or date.today().year
    total = 0
    qs = LeaveRequest.objects.filter(
        user=user,
        leave_category=leave_category,
        status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
    )
    for request in qs:
        total += request.days_in_year(year)
    return total


def leave_balance(user, leave_category, year=None):
    year = year or date.today().year
    entitlement = leave_category.days_per_year
    used = used_leave_days(user, leave_category, year)
    return max(entitlement - used, 0)


def leave_summary_for_category(user, leave_category, year=None):
    year = year or date.today().year
    used = used_leave_days(user, leave_category, year)
    entitlement = leave_category.days_per_year
    return {
        "leave_category": leave_category,
        "year": year,
        "entitlement": entitlement,
        "used": used,
        "remaining": max(entitlement - used, 0),
    }


def all_leave_summaries(user, year=None):
    year = year or date.today().year
    return [
        leave_summary_for_category(user, category, year)
        for category in get_active_leave_categories()
    ]


def leave_summary(user, year=None):
    """Yearly category balance (main entitlement)."""
    return leave_summary_for_category(user, get_yearly_leave_category(), year)


def team_leave_requests_queryset():
    from core.models import UserProfile

    return (
        LeaveRequest.objects.filter(
            user__profile__user_type__in=[
                UserProfile.UserType.STAFF,
                UserProfile.UserType.FOLLOWUP,
                UserProfile.UserType.BACKOFFICE,
            ]
        )
        .select_related("user", "leave_category", "leave_type", "user__profile")
        .order_by("-created_at")
    )


def hr_pending_leave_requests_queryset():
    return team_leave_requests_queryset().filter(
        workflow_stage=LeaveRequest.WorkflowStage.PENDING_HR
    )


def hr_actionable_leave_requests_queryset():
    """Leave requests HR can approve or reject (including branch-manager queue)."""
    return team_leave_requests_queryset().filter(
        workflow_stage__in=[
            LeaveRequest.WorkflowStage.PENDING_HR,
            LeaveRequest.WorkflowStage.PENDING_MANAGER,
        ]
    )


def branch_pending_leave_requests_queryset(branch):
    return team_leave_requests_queryset().filter(
        workflow_stage=LeaveRequest.WorkflowStage.PENDING_MANAGER,
        user__staff_profile__branch=branch,
    )
