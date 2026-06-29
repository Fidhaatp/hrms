import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import calendar

from django.db import transaction
from django.utils import timezone

from branch.models import BranchMonthlyTarget
from core.models import EmployeeTarget
from staff.models import Staff


def current_target_period():
    today = timezone.localdate()
    return today.month, today.year


def _money(value):
    return Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _int_target(value):
    """Whole-number target for leads (no decimal pace on dashboards)."""
    return int(_money(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def staff_target_breakdown(target_amount, achieved_amount, today=None):
    """Split a monthly target into daily/weekly pace for staff dashboards."""
    today = today or timezone.localdate()
    monthly_target = Decimal(target_amount or 0)
    achieved = Decimal(achieved_amount or 0)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    day_of_month = today.day
    days_remaining = max(days_in_month - day_of_month, 0)

    daily_target = _int_target(monthly_target / Decimal("25")) if monthly_target else 0
    weekly_target = _int_target(daily_target * 6) if monthly_target else 0
    enquiry_target = math.ceil(float(monthly_target) / 50.0) / 2 if monthly_target else 0
    
    weeks_in_month = max(1, (days_in_month + 6) // 7)
    week_index = (day_of_month - 1) // 7 + 1
    week_start_day = (week_index - 1) * 7 + 1
    week_end_day = min(week_index * 7, days_in_month)

    expected_by_today = min(_int_target(daily_target * day_of_month), _int_target(monthly_target))
    remaining = max(_int_target(monthly_target - achieved), 0)
    daily_needed = _int_target(remaining / days_remaining) if days_remaining else remaining
    weekly_needed = _int_target(daily_needed * min(7, days_remaining)) if days_remaining else remaining

    if monthly_target:
        achievement_percent = round(float(achieved) / float(monthly_target) * 100, 1)
    else:
        achievement_percent = 0

    return {
        "period_label": today.strftime("%B %Y"),
        "monthly_target": _int_target(monthly_target),
        "achieved_amount": _int_target(achieved),
        "remaining_amount": remaining,
        "daily_target": daily_target,
        "weekly_target": weekly_target,
        "enquiry_target": int(enquiry_target) if enquiry_target.is_integer() else enquiry_target,
        "daily_needed": daily_needed,
        "weekly_needed": weekly_needed,
        "expected_by_today": expected_by_today,
        "days_in_month": days_in_month,
        "day_of_month": day_of_month,
        "days_remaining": days_remaining,
        "week_index": week_index,
        "weeks_in_month": weeks_in_month,
        "week_start_day": week_start_day,
        "week_end_day": week_end_day,
        "achievement_percent": achievement_percent,
        "on_track": achieved >= expected_by_today if monthly_target else True,
    }


def branch_active_staff(branch):
    if not branch:
        return Staff.objects.none()
    return Staff.objects.filter(branch=branch, is_active=True).select_related("user").order_by(
        "user__first_name",
        "user__last_name",
        "user__username",
    )


def get_branch_monthly_target(branch, month, year):
    if not branch:
        return None
    return BranchMonthlyTarget.objects.filter(
        branch=branch,
        period_month=month,
        period_year=year,
    ).first()


def staff_target_map(branch, month, year):
    if not branch:
        return {}
    rows = EmployeeTarget.objects.filter(
        user__staff_profile__branch=branch,
        user__staff_profile__is_active=True,
        period_month=month,
        period_year=year,
    ).select_related("user")
    return {row.user_id: row for row in rows}


def branch_staff_target_rows(branch, month=None, year=None):
    if month is None or year is None:
        month, year = current_target_period()
    targets = staff_target_map(branch, month, year)
    rows = []
    for member in branch_active_staff(branch):
        target = targets.get(member.user_id)
        target_amount = target.target_amount if target else Decimal("0")
        daily_target = _int_target(target_amount / Decimal("25")) if target_amount else 0
        weekly_target = _int_target(daily_target * 6) if target_amount else 0
        enquiry_target = math.ceil(float(target_amount) / 50.0) / 2 if target_amount else 0
        enquiry_target = int(enquiry_target) if enquiry_target.is_integer() else enquiry_target
        rows.append(
            {
                "staff": member,
                "target_amount": target_amount,
                "daily_target": daily_target,
                "weekly_target": weekly_target,
                "enquiry_target": enquiry_target,
                "achieved_amount": target.achieved_amount if target else Decimal("0"),
                "achievement_percent": target.achievement_percent if target else 0,
            }
        )
    return rows


def branch_target_summary(branch, month=None, year=None):
    if month is None or year is None:
        month, year = current_target_period()
    branch_target = get_branch_monthly_target(branch, month, year)
    staff_rows = branch_staff_target_rows(branch, month, year)
    assigned_total = sum((row["target_amount"] for row in staff_rows), Decimal("0"))
    achieved_total = sum((row["achieved_amount"] for row in staff_rows), Decimal("0"))
    branch_amount = branch_target.target_amount if branch_target else Decimal("0")
    remaining = branch_amount - assigned_total
    if remaining < 0:
        remaining = Decimal("0")
    breakdown = staff_target_breakdown(branch_amount, achieved_total)
    assigned_percent = (
        round(float(assigned_total) / float(branch_amount) * 100, 1) if branch_amount else 0
    )
    achieved_percent = breakdown["achievement_percent"]
    return {
        "period_month": month,
        "period_year": year,
        "period_label": breakdown["period_label"],
        "branch_target_amount": branch_amount,
        "branch_enquiry_target": breakdown["enquiry_target"],
        "assigned_total": assigned_total,
        "remaining": remaining,
        "achieved_total": achieved_total,
        "assigned_percent": assigned_percent,
        "achieved_percent": achieved_percent,
        "breakdown": breakdown,
        "staff_rows": staff_rows,
        "staff_count": len(staff_rows),
    }


def _parse_decimal(value):
    text = (value or "").strip()
    if not text:
        return Decimal("0")
    try:
        amount = Decimal(text)
    except (InvalidOperation, TypeError):
        raise ValueError("Enter valid target amounts.")
    if amount < 0:
        raise ValueError("Target amounts cannot be negative.")
    return amount


def save_branch_staff_targets(branch, manager_user, branch_target_amount, staff_amounts):
    """
    Save branch monthly target and per-staff splits.
    staff_amounts: dict of {staff_pk: Decimal}
    """
    month, year = current_target_period()
    staff_members = {
        member.pk: member
        for member in branch_active_staff(branch)
    }
    if not staff_members:
        raise ValueError("No active staff in this branch.")

    branch_target_amount = _parse_decimal(branch_target_amount)
    parsed_staff_amounts = {}
    for staff_pk, raw_amount in staff_amounts.items():
        staff_pk = int(staff_pk)
        if staff_pk not in staff_members:
            raise ValueError("Invalid staff member for this branch.")
        parsed_staff_amounts[staff_pk] = _parse_decimal(raw_amount)

    assigned_total = sum(parsed_staff_amounts.values(), Decimal("0"))
    if assigned_total > branch_target_amount:
        raise ValueError(
            f"Staff targets total ({assigned_total}) cannot exceed the branch target ({branch_target_amount})."
        )

    with transaction.atomic():
        branch_target, _created = BranchMonthlyTarget.objects.update_or_create(
            branch=branch,
            period_month=month,
            period_year=year,
            defaults={
                "target_amount": branch_target_amount,
                "assigned_by": manager_user,
            },
        )
        for staff_pk, member in staff_members.items():
            amount = parsed_staff_amounts.get(staff_pk, Decimal("0"))
            EmployeeTarget.objects.update_or_create(
                user=member.user,
                period_month=month,
                period_year=year,
                defaults={"target_amount": amount},
            )
    return branch_target
