"""TAKHLEES HRMS role hierarchy, dashboard specs, and workflow definitions."""

from core.models import UserProfile


ROLE_HIERARCHY = [
    {
        "level": 1,
        "key": "admin",
        "title": "Admin",
        "user_type": UserProfile.UserType.ADMIN,
        "responsibilities": [
            "Full system control",
            "Branches and employees",
            "Permissions",
            "HR management",
            "Organization dashboards",
        ],
        "portal": "/admin-portal/",
    },
    {
        "level": 2,
        "key": "hr_manager",
        "title": "HR Manager",
        "user_type": UserProfile.UserType.HR,
        "responsibilities": [
            "Employee profiles",
            "Leave approval",
            "Visa and insurance tracking",
            "Salary approval",
            "Announcements",
        ],
        "portal": "/hr/",
    },
    {
        "level": 2,
        "key": "finance_manager",
        "title": "Finance Manager",
        "user_type": UserProfile.UserType.FINANCE,
        "responsibilities": [
            "Payroll",
            "Incentives",
            "Collections",
            "Financial communication",
        ],
        "portal": "/finance/",
    },
    {
        "level": 2,
        "key": "marketing_manager",
        "title": "Marketing Manager",
        "user_type": UserProfile.UserType.MARKETING,
        "responsibilities": [
            "Campaigns",
            "Posters and videos",
            "Marketing announcements",
        ],
        "portal": "/marketing/",
    },
    {
        "level": 3,
        "key": "branch_manager",
        "title": "Branch Manager",
        "user_type": UserProfile.UserType.BRANCH,
        "responsibilities": [
            "Staff supervision",
            "First-level approvals",
            "Communication bridge",
            "Performance monitoring",
        ],
        "portal": "/branch/",
    },
    {
        "level": 4,
        "key": "branch_accountant",
        "title": "Branch Accountant",
        "user_type": UserProfile.UserType.BRANCH_ACCOUNTANT,
        "responsibilities": [
            "Collections",
            "Invoices",
            "Financial reports",
        ],
        "portal": "/accountant/",
    },
    {
        "level": 4,
        "key": "branch_staff",
        "title": "Branch Staff",
        "user_type": UserProfile.UserType.STAFF,
        "responsibilities": [
            "Sales",
            "Add leads",
        ],
        "portal": "/staff/",
    },
    {
        "level": 5,
        "key": "followup_staff",
        "title": "Follow Up Staff",
        "user_type": UserProfile.UserType.FOLLOWUP,
        "responsibilities": [
            "Document collection",
            "Client communication",
            "Case updates",
        ],
        "portal": "/followup/",
    },
    {
        "level": 6,
        "key": "backoffice_staff",
        "title": "Back Office Staff",
        "user_type": UserProfile.UserType.BACKOFFICE,
        "responsibilities": [
            "Case processing",
            "Completion updates",
        ],
        "portal": "/backoffice/",
    },
]


DASHBOARD_METRICS = {
    "employee": ["Attendance Details", "Targets", "Incentives", "Leave Balance"],
    "branch": ["Revenue", "Collections", "Conversion Rate", "Ranking"],
    "hr": ["Visa Expiry", "Insurance Expiry", "Contracts", "Employee Attendance"],
    "operations": ["Pending Cases", "Completed Cases"],
    "awards": ["Employee of Month", "Branch of Month"],
}


WORKFLOWS = {
    "leave_approval": {
        "title": "Leave Approval",
        "steps": ["Employee", "Branch Manager", "HR", "Approved"],
    },
    "salary_approval": {
        "title": "Salary Approval",
        "steps": ["Attendance + Incentive", "HR", "Finance", "Payroll"],
    },
    "client_processing": {
        "title": "Client Processing",
        "steps": [
            "Branch Staff (sale)",
            "Follow Up (documents)",
            "Back Office (case processing)",
            "Completed",
        ],
    },
    "case_processing": {
        "title": "Back Office Case Processing",
        "steps": [
            "Verify documents",
            "Create application",
            "Submit file",
            "Submit online",
            "Track response",
            "Update customer",
            "Complete case",
        ],
    },
    "recruitment": {
        "title": "Recruitment",
        "steps": ["Branch Request", "HR", "Interview", "Joining"],
    },
    "salary_increment": {
        "title": "Salary Increment",
        "steps": ["Manager", "HR", "Admin", "Update"],
    },
}


def role_level_for(user_type):
    for role in ROLE_HIERARCHY:
        if role["user_type"] == user_type:
            return role["level"]
    return None


def role_title_for(user_type):
    for role in ROLE_HIERARCHY:
        if role["user_type"] == user_type:
            return role["title"]
    return user_type
