"""Grouped sidebar navigation for the HR portal (workflow order)."""

HR_NAV_SECTIONS = [
    {
        "label": "Overview",
        "items": [
            {
                "nav_key": "dashboard",
                "label": "Dashboard",
                "icon": "bi-grid-1x2-fill",
                "url_name": "hr:dashboard",
            },
            {
                "nav_key": "notifications",
                "label": "Notifications",
                "icon": "bi-bell-fill",
                "url_name": "core:notifications",
            },
        ],
    },
    {
        "step": 1,
        "label": "Organization setup",
        "items": [
            {
                "nav_key": "branches",
                "label": "Branches",
                "icon": "bi-building",
                "url_name": "hr:branches",
            },
            {
                "nav_key": "branch_managers",
                "label": "Branch managers",
                "icon": "bi-person-badge-fill",
                "url_name": "hr:branch_managers",
            },
            {
                "nav_key": "org_database",
                "label": "Org database",
                "icon": "bi-diagram-3-fill",
                "url_name": "hr:org_database",
            },
        ],
    },
    {
        "step": 2,
        "label": "Team accounts",
        "items": [
            {
                "nav_key": "staff",
                "label": "Staff",
                "icon": "bi-people-fill",
                "url_name": "hr:staff_list",
            },
            {
                "nav_key": "followup",
                "label": "Follow-up team",
                "icon": "bi-telephone-fill",
                "url_name": "hr:followup_list",
            },
            {
                "nav_key": "backoffice",
                "label": "Back office",
                "icon": "bi-building-fill",
                "url_name": "hr:backoffice_list",
            },
            {
                "nav_key": "finance",
                "label": "Finance team",
                "icon": "bi-cash-stack",
                "url_name": "hr:finance_list",
            },
            {
                "nav_key": "marketing",
                "label": "Marketing team",
                "icon": "bi-megaphone-fill",
                "url_name": "hr:marketing_list",
            },
        ],
    },
    {
        "step": 3,
        "label": "Leave management",
        "items": [
            {
                "nav_key": "leave_categories",
                "label": "Leave categories",
                "icon": "bi-calendar-range-fill",
                "url_name": "hr:leave_categories",
            },
            {
                "nav_key": "leave_types",
                "label": "Leave types",
                "icon": "bi-tags-fill",
                "url_name": "hr:leave_types",
            },
            {
                "nav_key": "leave_requests",
                "label": "Leave requests",
                "icon": "bi-calendar2-week-fill",
                "url_name": "hr:leave_requests",
            },
        ],
    },
    {
        "step": 4,
        "label": "Leads & CRM",
        "items": [
            {
                "nav_key": "leads",
                "label": "All leads",
                "icon": "bi-funnel-fill",
                "url_name": "hr:leads",
            },
            {
                "nav_key": "lead_sources",
                "label": "Lead sources",
                "icon": "bi-signpost-split-fill",
                "url_name": "hr:lead_sources",
            },
            {
                "nav_key": "lead_services",
                "label": "Lead services",
                "icon": "bi-briefcase-fill",
                "url_name": "hr:lead_services",
            },
            {
                "nav_key": "lead_statuses",
                "label": "Lead statuses",
                "icon": "bi-flag-fill",
                "url_name": "hr:lead_statuses",
            },
        ],
    },
    {
        "step": 5,
        "label": "HR operations",
        "items": [
            {
                "nav_key": "approvals",
                "label": "Approvals",
                "icon": "bi-check2-square",
                "url_name": "hr:approvals",
            },
            {
                "nav_key": "compliance",
                "label": "Compliance",
                "icon": "bi-shield-check",
                "url_name": "hr:compliance",
            },
            {
                "nav_key": "recruitment",
                "label": "Recruitment",
                "icon": "bi-person-plus-fill",
                "url_name": "hr:recruitment",
            },
            {
                "nav_key": "workflows",
                "label": "Workflows",
                "icon": "bi-diagram-2-fill",
                "url_name": "hr:workflows",
            },
        ],
    },
    {
        "label": "Insights",
        "items": [
            {
                "nav_key": "analytics",
                "label": "Analytics",
                "icon": "bi-bar-chart-line-fill",
                "url_name": "hr:analytics",
            },
        ],
    },
    {
        "label": "Account",
        "items": [
            {
                "nav_key": "profile",
                "label": "My profile",
                "icon": "bi-person-circle",
                "url_name": "hr:profile",
            },
        ],
    },
]


def hr_nav_sections():
    return HR_NAV_SECTIONS
