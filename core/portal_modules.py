"""Navigation and module metadata for all role portals."""

from core.models import UserProfile

_NAV = lambda items: items  # noqa: E731 — clarity for large lists


ADMIN_NAV = _NAV(
    [
        {"nav_key": "dashboard", "label": "Dashboard", "icon": "bi-grid-1x2-fill", "url_name": "admin_portal:dashboard"},
        {"nav_key": "employees", "label": "Employees", "icon": "bi-people-fill", "url_name": "admin_portal:employees"},
        {"nav_key": "branches", "label": "Branches", "icon": "bi-building-fill", "url_name": "admin_portal:branches"},
        {"nav_key": "roles", "label": "Users & Roles", "icon": "bi-shield-lock-fill", "url_name": "admin_portal:roles"},
        {"nav_key": "reports", "label": "Reports", "icon": "bi-bar-chart-fill", "url_name": "admin_portal:reports"},
        {"nav_key": "workflows", "label": "Workflows", "icon": "bi-diagram-2-fill", "url_name": "admin_portal:workflows"},
        {"nav_key": "settings", "label": "Settings", "icon": "bi-gear-fill", "url_name": "admin_portal:settings"},
        {"nav_key": "django_admin", "label": "System Admin", "icon": "bi-database-fill", "url_name": "admin_portal:django_admin"},
        {"nav_key": "profile", "label": "My Profile", "icon": "bi-person-circle", "url_name": "admin_portal:profile"},
    ]
)

FINANCE_NAV = _NAV(
    [
        {"nav_key": "dashboard", "label": "Dashboard", "icon": "bi-grid-1x2-fill", "url_name": "finance:index"},
        {"nav_key": "payroll", "label": "Payroll", "icon": "bi-cash-stack", "url_name": "finance:payroll"},
        {"nav_key": "incentives", "label": "Incentives", "icon": "bi-trophy-fill", "url_name": "finance:incentives"},
        {"nav_key": "collections", "label": "Collections", "icon": "bi-wallet2", "url_name": "finance:collections"},
        {"nav_key": "expenses", "label": "Expenses", "icon": "bi-receipt", "url_name": "finance:expenses"},
        {"nav_key": "reports", "label": "Reports", "icon": "bi-bar-chart-fill", "url_name": "finance:reports"},
        {"nav_key": "profile", "label": "My Profile", "icon": "bi-person-circle", "url_name": "finance:profile"},
    ]
)

MARKETING_NAV = _NAV(
    [
        {"nav_key": "dashboard", "label": "Dashboard", "icon": "bi-grid-1x2-fill", "url_name": "marketing:index"},
        {"nav_key": "campaigns", "label": "Campaigns", "icon": "bi-megaphone-fill", "url_name": "marketing:campaigns"},
        {"nav_key": "creatives", "label": "Creatives", "icon": "bi-palette-fill", "url_name": "marketing:creatives"},
        {"nav_key": "leads", "label": "Lead Generation", "icon": "bi-funnel-fill", "url_name": "marketing:leads"},
        {"nav_key": "announcements", "label": "Announcements", "icon": "bi-bell-fill", "url_name": "marketing:announcements"},
        {"nav_key": "profile", "label": "My Profile", "icon": "bi-person-circle", "url_name": "marketing:profile"},
    ]
)

BRANCH_NAV = _NAV(
    [
        {"nav_key": "dashboard", "label": "Dashboard", "icon": "bi-grid-1x2-fill", "url_name": "branch:index"},
        {"nav_key": "all_leads", "label": "All leads", "icon": "bi-people-fill", "url_name": "branch:all_leads"},
        {
            "nav_key": "lead_history",
            "label": "Lead tracking history",
            "icon": "bi-clock-history",
            "url_name": "branch:lead_history",
        },
        {"nav_key": "calendar", "label": "Expiry calendar", "icon": "bi-calendar3", "url_name": "branch:calendar"},
        {"nav_key": "staff", "label": "Staff", "icon": "bi-person-badge-fill", "url_name": "branch:staff"},
        {"nav_key": "followup", "label": "Follow-up", "icon": "bi-telephone-fill", "url_name": "branch:followup"},
        {"nav_key": "reports", "label": "Reports", "icon": "bi-bar-chart-fill", "url_name": "branch:reports"},
        {"nav_key": "profile", "label": "My Profile", "icon": "bi-person-circle", "url_name": "branch:profile"},
    ]
)

ACCOUNTANT_NAV = _NAV(
    [
        {"nav_key": "dashboard", "label": "Dashboard", "icon": "bi-grid-1x2-fill", "url_name": "accountant:index"},
        {"nav_key": "collections", "label": "Collections", "icon": "bi-wallet2", "url_name": "accountant:collections"},
        {"nav_key": "invoices", "label": "Invoices", "icon": "bi-file-earmark-text-fill", "url_name": "accountant:invoices"},
        {"nav_key": "reports", "label": "Branch Reports", "icon": "bi-bar-chart-fill", "url_name": "accountant:reports"},
        {"nav_key": "finance_comm", "label": "Finance Comm.", "icon": "bi-send-fill", "url_name": "accountant:finance_comm"},
        {"nav_key": "profile", "label": "My Profile", "icon": "bi-person-circle", "url_name": "accountant:profile"},
    ]
)

STAFF_NAV = _NAV(
    [
        {"nav_key": "dashboard", "label": "Dashboard", "icon": "bi-grid-1x2-fill", "url_name": "staff:index"},
        {"nav_key": "leads", "label": "Leads", "icon": "bi-person-plus-fill", "url_name": "staff:lead_list"},
        {"nav_key": "calendar", "label": "Expiry calendar", "icon": "bi-calendar3", "url_name": "staff:calendar"},
        {"nav_key": "pipeline", "label": "Sales Pipeline", "icon": "bi-funnel-fill", "url_name": "staff:pipeline"},
        {"nav_key": "targets", "label": "Targets", "icon": "bi-bullseye", "url_name": "staff:targets"},
        {"nav_key": "leave", "label": "Leave", "icon": "bi-calendar2-week-fill", "url_name": "staff:leave_list"},
        {"nav_key": "profile", "label": "My Profile", "icon": "bi-person-circle", "url_name": "staff:profile"},
    ]
)

FOLLOWUP_NAV = _NAV(
    [
        {"nav_key": "dashboard", "label": "Dashboard", "icon": "bi-grid-1x2-fill", "url_name": "followup:index"},
        {"nav_key": "leads", "label": "Follow-up Leads", "icon": "bi-telephone-fill", "url_name": "followup:lead_list"},
        {"nav_key": "all_leads", "label": "Leads", "icon": "bi-people-fill", "url_name": "followup:all_leads"},
        {"nav_key": "calendar", "label": "Expiry calendar", "icon": "bi-calendar3", "url_name": "followup:calendar"},
        {"nav_key": "leave", "label": "Leave", "icon": "bi-calendar2-week-fill", "url_name": "followup:leave_list"},
        {"nav_key": "profile", "label": "My Profile", "icon": "bi-person-circle", "url_name": "followup:profile"},
    ]
)

BACKOFFICE_NAV = _NAV(
    [
        {"nav_key": "dashboard", "label": "Dashboard", "icon": "bi-grid-1x2-fill", "url_name": "backoffice:index"},
        {"nav_key": "pending", "label": "Pending Verifications", "icon": "bi-hourglass-split", "url_name": "backoffice:pending_verifications"},
        {"nav_key": "team", "label": "Team", "icon": "bi-person-badge-fill", "url_name": "backoffice:team"},
        {"nav_key": "procedures", "label": "Procedure review", "icon": "bi-list-check", "url_name": "backoffice:procedure_reviews"},
        {"nav_key": "pending_leads", "label": "Pending leads", "icon": "bi-hourglass-split", "url_name": "backoffice:pending_leads"},
        {"nav_key": "all_leads", "label": "Leads", "icon": "bi-people-fill", "url_name": "backoffice:all_leads"},
        {"nav_key": "reports", "label": "Reports", "icon": "bi-bar-chart-fill", "url_name": "backoffice:reports"},
        {"nav_key": "leave", "label": "Leave", "icon": "bi-calendar2-week-fill", "url_name": "backoffice:leave_list"},
        {"nav_key": "profile", "label": "My Profile", "icon": "bi-person-circle", "url_name": "backoffice:profile"},
    ]
)

PORTAL_NAV = {
    UserProfile.UserType.STAFF: STAFF_NAV,
    UserProfile.UserType.FOLLOWUP: FOLLOWUP_NAV,
    UserProfile.UserType.BACKOFFICE: BACKOFFICE_NAV,
    UserProfile.UserType.BRANCH: BRANCH_NAV,
    UserProfile.UserType.FINANCE: FINANCE_NAV,
    UserProfile.UserType.MARKETING: MARKETING_NAV,
    UserProfile.UserType.BRANCH_ACCOUNTANT: ACCOUNTANT_NAV,
}

PORTAL_META = {
    UserProfile.UserType.STAFF: {
        "role_label": "Branch Staff",
        "brand_sub": "CRM Sales Portal",
        "home_url_name": "staff:index",
    },
    UserProfile.UserType.FOLLOWUP: {
        "role_label": "Follow Up Staff",
        "brand_sub": "Follow-up Portal",
        "home_url_name": "followup:index",
    },
    UserProfile.UserType.BACKOFFICE: {
        "role_label": "Back Office Staff",
        "brand_sub": "Operations Portal",
        "home_url_name": "backoffice:index",
    },
    UserProfile.UserType.BRANCH: {
        "role_label": "Branch Manager",
        "brand_sub": "Branch Manager Portal",
        "home_url_name": "branch:index",
    },
    UserProfile.UserType.FINANCE: {
        "role_label": "Finance Manager",
        "brand_sub": "Finance Portal",
        "home_url_name": "finance:index",
    },
    UserProfile.UserType.MARKETING: {
        "role_label": "Marketing Manager",
        "brand_sub": "Marketing Portal",
        "home_url_name": "marketing:index",
    },
    UserProfile.UserType.BRANCH_ACCOUNTANT: {
        "role_label": "Branch Accountant",
        "brand_sub": "Branch Accountant Portal",
        "home_url_name": "accountant:index",
    },
}

ADMIN_META = {
    "role_label": "System Admin",
    "brand_sub": "Admin Portal",
    "home_url_name": "admin_portal:dashboard",
}
