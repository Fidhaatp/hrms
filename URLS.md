# TAKHLEES HRMS — URL Reference

**Base URL (local dev):** `http://127.0.0.1:8000`

Run server: `python manage.py runserver` (from `hrms/` folder)

---

## Quick index

| Section | Base path |
|---------|-----------|
| [Core / Auth](#core--auth) | `/` |
| [Django Admin](#django-admin) | `/admin/` |
| [HR Portal](#hr-portal) | `/hr/` |
| [Staff Portal](#staff-portal) | `/staff/` |
| [Follow-up Portal](#follow-up-portal) | `/followup/` |
| [Back Office Portal](#back-office-portal) | `/backoffice/` |
| [Branch Portal](#branch-portal) | `/branch/` |
| [Finance Portal](#finance-portal) | `/finance/` |
| [Marketing Portal](#marketing-portal) | `/marketing/` |
| [Accountant Portal](#accountant-portal) | `/accountant/` |
| [Static & Media](#static--media) | `/static/`, `/media/` |

---

## Core / Auth

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/` | `core:home` | GET | Redirects to login |
| `http://127.0.0.1:8000/login/` | `core:login` | GET, POST | Sign in (all roles) |
| `http://127.0.0.1:8000/logout/` | `core:logout` | GET | Sign out |
| `http://127.0.0.1:8000/post-login/` | `core:post_login` | GET | Role-based redirect after login |
| `http://127.0.0.1:8000/register/` | `core:register_portal` | GET | Registration hub (portal links) |

---

## Django Admin

| URL | Method | Description |
|-----|--------|-------------|
| `http://127.0.0.1:8000/admin/` | GET | Django admin (users, compliance, attendance, etc.) |

---

## HR Portal

**Base:** `http://127.0.0.1:8000/hr/`  
**Role:** HR Manager, Admin  
**URL namespace:** `hr:`

### Dashboard & overview

| URL | Name | Method | Description |
|-----|------|--------|-------------|

| `http://127.0.0.1:8000/hr/` | `hr:dashboard` | GET | HR dashboard (metrics, leads overview) |
| `http://127.0.0.1:8000/hr/analytics/` | `hr:analytics` | GET | Organization-wide analytics |
| `http://127.0.0.1:8000/hr/workflows/` | `hr:workflows` | GET | Role hierarchy & workflow reference |
| `http://127.0.0.1:8000/hr/org-database/` | `hr:org_database` | GET | Centralized staff & branch database |
| `http://127.0.0.1:8000/hr/approvals/` | `hr:approvals` | GET | Approval hub (leave summary) |

### Leads

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/hr/leads/` | `hr:leads` | GET | All leads (organization view) |

### Branches

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/hr/branches/` | `hr:branches` | GET | List branches |
| `http://127.0.0.1:8000/hr/branches/add/` | `hr:branch_add` | POST | Add branch (+ optional manager) |
| `http://127.0.0.1:8000/hr/branches/<id>/edit/` | `hr:branch_edit` | POST | Edit branch |
| `http://127.0.0.1:8000/hr/branches/<id>/deactivate/` | `hr:branch_deactivate` | POST | Deactivate branch |
| `http://127.0.0.1:8000/hr/branches/<id>/reactivate/` | `hr:branch_reactivate` | POST | Reactivate branch |

### Branch managers

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/hr/branch-managers/` | `hr:branch_managers` | GET | List branch managers |
| `http://127.0.0.1:8000/hr/branches/managers/add/` | `hr:branch_manager_add` | POST | Add branch manager |
| `http://127.0.0.1:8000/hr/branch-managers/<id>/deactivate/` | `hr:branch_manager_deactivate` | POST | Deactivate manager |
| `http://127.0.0.1:8000/hr/branch-managers/<id>/reactivate/` | `hr:branch_manager_reactivate` | POST | Reactivate manager |

### Team management

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/hr/staff/` | `hr:staff_list` | GET | Staff team list |
| `http://127.0.0.1:8000/hr/staff/add/` | `hr:staff_add` | POST | Create staff account |
| `http://127.0.0.1:8000/hr/staff/<id>/deactivate/` | `hr:staff_deactivate` | POST | Deactivate staff |
| `http://127.0.0.1:8000/hr/staff/<id>/reactivate/` | `hr:staff_reactivate` | POST | Reactivate staff |
| `http://127.0.0.1:8000/hr/followup/` | `hr:followup_list` | GET | Follow-up team list |
| `http://127.0.0.1:8000/hr/followup/add/` | `hr:followup_add` | POST | Create follow-up account |
| `http://127.0.0.1:8000/hr/followup/<id>/deactivate/` | `hr:followup_deactivate` | POST | Deactivate follow-up |
| `http://127.0.0.1:8000/hr/followup/<id>/reactivate/` | `hr:followup_reactivate` | POST | Reactivate follow-up |
| `http://127.0.0.1:8000/hr/backoffice/` | `hr:backoffice_list` | GET | Back office team list |
| `http://127.0.0.1:8000/hr/backoffice/add/` | `hr:backoffice_add` | POST | Create back office account |
| `http://127.0.0.1:8000/hr/backoffice/<id>/deactivate/` | `hr:backoffice_deactivate` | POST | Deactivate back office |
| `http://127.0.0.1:8000/hr/backoffice/<id>/reactivate/` | `hr:backoffice_reactivate` | POST | Reactivate back office |

### Leave management

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/hr/leave-requests/` | `hr:leave_requests` | GET | View & approve leave (HR step) |
| `http://127.0.0.1:8000/hr/leave-requests/<id>/approve/` | `hr:leave_approve` | POST | HR approve leave |
| `http://127.0.0.1:8000/hr/leave-requests/<id>/reject/` | `hr:leave_reject` | POST | HR reject leave |
| `http://127.0.0.1:8000/hr/leave-categories/` | `hr:leave_categories` | GET | Leave categories (entitlements) |
| `http://127.0.0.1:8000/hr/leave-categories/add/` | `hr:leave_category_add` | POST | Add leave category |
| `http://127.0.0.1:8000/hr/leave-types/` | `hr:leave_types` | GET | Leave types (sick, casual, …) |
| `http://127.0.0.1:8000/hr/leave-types/add/` | `hr:leave_type_add` | POST | Add leave type |

### HR operations

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/hr/compliance/` | `hr:compliance` | GET | Visa, insurance, contract tracking |
| `http://127.0.0.1:8000/hr/recruitment/` | `hr:recruitment` | GET | Recruitment requests |

### Approvals (API actions)

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/hr/approvals/salary-increment/<id>/decide/` | `hr:salary_increment_decide` | POST | Approve/reject salary increment |
| `http://127.0.0.1:8000/hr/approvals/rejoining/<id>/decide/` | `hr:rejoining_decide` | POST | Approve/reject rejoining |
| `http://127.0.0.1:8000/hr/approvals/payment/<id>/decide/` | `hr:payment_decide` | POST | Approve/reject payment request |

### HR account

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/hr/account/register/` | `hr:register` | GET, POST | HR self-registration |
| `http://127.0.0.1:8000/hr/profile/` | `hr:profile` | GET | HR profile |
| `http://127.0.0.1:8000/hr/profile/photo/` | `hr:profile_picture_update` | POST | Update profile photo |

---

## Staff Portal

**Base:** `http://127.0.0.1:8000/staff/`  
**Role:** Branch Staff  
**URL namespace:** `staff:`

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/staff/` | `staff:index` | GET | Staff dashboard |
| `http://127.0.0.1:8000/staff/leave/` | `staff:leave_list` | GET | My leave requests & balance |
| `http://127.0.0.1:8000/staff/leave/add/` | `staff:leave_add` | POST | Submit leave request |
| `http://127.0.0.1:8000/staff/leads/` | `staff:lead_list` | GET | My leads list |
| `http://127.0.0.1:8000/staff/leads/add/` | `staff:lead_add` | POST | Add lead (auto sent to follow-up) |

---

## Follow-up Portal

**Base:** `http://127.0.0.1:8000/followup/`  
**Role:** Follow Up Staff  
**URL namespace:** `followup:`

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/followup/` | `followup:index` | GET | Follow-up dashboard |
| `http://127.0.0.1:8000/followup/leave/` | `followup:leave_list` | GET | My leave requests |
| `http://127.0.0.1:8000/followup/leave/add/` | `followup:leave_add` | POST | Submit leave request |
| `http://127.0.0.1:8000/followup/leads/` | `followup:lead_list` | GET | Verified leads to work |
| `http://127.0.0.1:8000/followup/leads/<id>/update/` | `followup:lead_update` | POST | Update lead status / branch / roadmap |

---

## Back Office Portal

**Base:** `http://127.0.0.1:8000/backoffice/`  
**Role:** Back Office Staff  
**URL namespace:** `backoffice:`

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/backoffice/` | `backoffice:index` | GET | Back office dashboard |
| `http://127.0.0.1:8000/backoffice/leave/` | `backoffice:leave_list` | GET | My leave requests |
| `http://127.0.0.1:8000/backoffice/leave/add/` | `backoffice:leave_add` | POST | Submit leave request |
| `http://127.0.0.1:8000/backoffice/leads/` | `backoffice:lead_list` | GET | Lead verification queue |
| `http://127.0.0.1:8000/backoffice/leads/<id>/verify/` | `backoffice:lead_verify` | POST | Mark lead as correct |
| `http://127.0.0.1:8000/backoffice/leads/<id>/reject/` | `backoffice:lead_reject` | POST | Mark lead as not correct |

---

## Branch Portal

**Base:** `http://127.0.0.1:8000/branch/`  
**Role:** Branch Manager  
**URL namespace:** `branch:`

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/branch/` | `branch:index` | GET | Branch dashboard |
| `http://127.0.0.1:8000/branch/leads/` | `branch:lead_list` | GET | Branch lead roadmap |
| `http://127.0.0.1:8000/branch/leave-approvals/` | `branch:leave_approvals` | GET | Pending leave (manager step) |
| `http://127.0.0.1:8000/branch/leave-approvals/<id>/approve/` | `branch:leave_approve` | POST | Approve leave → forward to HR |
| `http://127.0.0.1:8000/branch/leave-approvals/<id>/reject/` | `branch:leave_reject` | POST | Reject leave request |

---

## Finance Portal

**Base:** `http://127.0.0.1:8000/finance/`  
**Role:** Finance Manager  
**URL namespace:** `finance:`

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/finance/` | `finance:index` | GET | Finance dashboard (payroll, incentives, collections) |

---

## Marketing Portal

**Base:** `http://127.0.0.1:8000/marketing/`  
**Role:** Marketing Manager  
**URL namespace:** `marketing:`

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/marketing/` | `marketing:index` | GET | Marketing dashboard (campaigns, leads) |

---

## Accountant Portal

**Base:** `http://127.0.0.1:8000/accountant/`  
**Role:** Branch Accountant  
**URL namespace:** `accountant:`

| URL | Name | Method | Description |
|-----|------|--------|-------------|
| `http://127.0.0.1:8000/accountant/` | `accountant:index` | GET | Branch accountant dashboard |

---

## Static & Media

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/static/...` | CSS, JS, images (theme, logo) |
| `http://127.0.0.1:8000/media/...` | Uploaded files (profile pictures, etc.) |
| `http://127.0.0.1:8000/sitemap.xml` | Sitemap |
| `http://127.0.0.1:8000/robots.txt` | Robots file |

---

## Login redirect by role

After login at `/login/`, users are sent to their portal:

| Role | Redirect URL |
|------|--------------|
| Admin / HR Manager | `http://127.0.0.1:8000/hr/` |
| Finance Manager | `http://127.0.0.1:8000/finance/` |
| Marketing Manager | `http://127.0.0.1:8000/marketing/` |
| Branch Manager | `http://127.0.0.1:8000/branch/` |
| Branch Accountant | `http://127.0.0.1:8000/accountant/` |
| Branch Staff | `http://127.0.0.1:8000/staff/` |
| Follow Up Staff | `http://127.0.0.1:8000/followup/` |
| Back Office Staff | `http://127.0.0.1:8000/backoffice/` |

---

## Workflow URL map

| Workflow step | URL |
|---------------|-----|
| Staff adds lead (→ follow-up) | `POST /staff/leads/add/` |
| Back office verifies | `POST /backoffice/leads/<id>/verify/` |
| Follow-up updates lead | `POST /followup/leads/<id>/update/` |
| Branch views roadmap | `GET /branch/leads/` |
| Employee requests leave | `POST /staff/leave/add/` (or followup/backoffice) |
| Branch manager approves leave | `POST /branch/leave-approvals/<id>/approve/` |
| HR final leave approval | `POST /hr/leave-requests/<id>/approve/` |

---

## URL count summary

| App | Routes |
|-----|--------|
| Core | 5 |
| Admin | 1 |
| HR | 42 |
| Staff | 5 |
| Follow-up | 5 |
| Back Office | 6 |
| Branch | 6 |
| Finance | 1 |
| Marketing | 1 |
| Accountant | 1 |
| **Total (app routes)** | **73** |

---

*See also: [TAKHLEES_SYSTEM.md](TAKHLEES_SYSTEM.md) · [PROJECT_STATUS.md](PROJECT_STATUS.md)*
