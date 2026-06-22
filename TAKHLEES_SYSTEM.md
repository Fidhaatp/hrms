# TAKHLEES HRMS — System Architecture

**Version:** June 2026  
**Stack:** Django 6 · SQLite (dev) · Bootstrap 5 · TAKHLEES brand theme

This document describes the **role-based organization system**, **dashboard metrics**, and **approval workflows** implemented in TAKHLEES HRMS.

---

## 1. Role hierarchy

| Level | Role | Portal URL | Main responsibilities |
|------:|------|------------|------------------------|
| 1 | **Admin** | `/admin-portal/` | Full system control, users, branches, reports, settings |
| 2 | **HR Manager** | `/hr/` | Employee profiles, leave, recruitment, compliance, approvals |
| 2 | **Finance Manager** | `/finance/` | Payroll, incentives, collections, expenses, reports |
| 2 | **Marketing Manager** | `/marketing/` | Campaigns, creatives, lead generation, announcements |
| 3 | **Branch Manager** | `/branch/` | Staff, leads, cases, leave approvals, performance |
| 4 | **Branch Accountant** | `/accountant/` | Collections, invoices, branch reports, finance comm. |
| 4 | **Branch Staff** | `/staff/` | Leads, sales pipeline, targets, leave |
| 5 | **Follow Up Staff** | `/followup/` | Customer follow-up, documents, cases, notes |
| 6 | **Back Office Staff** | `/backoffice/` | Lead verification, case processing |

### Role mapping in code

Defined in `core/roles.py` and `UserProfile.UserType` in `core/models.py`.

| Spec role | `user_type` value |
|-----------|-------------------|
| Admin | `admin` |
| HR Manager | `hr` |
| Finance Manager | `finance` |
| Marketing Manager | `marketing` |
| Branch Manager | `branch` |
| Branch Accountant | `branch_accountant` |
| Branch Staff | `staff` |
| Follow Up Staff | `followup` |
| Back Office Staff | `backoffice` |

---

## 2. Dashboard metrics

Each portal dashboard shows metrics aligned with the organization spec.

### Employee dashboard (`/staff/`)

| Metric | Source |
|--------|--------|
| Attendance details | `AttendanceRecord` |
| Targets | `EmployeeTarget` (monthly achievement %) |
| Incentives | `EmployeeIncentive` (month total) |
| Leave balance | `LeaveCategory` + `LeaveRequest` |

### Branch dashboard (`/branch/`)

| Metric | Source |
|--------|--------|
| Revenue | `EmployeeTarget.achieved_amount` (branch staff) |
| Collections | Same as revenue (monthly) |
| Conversion rate | Leads converted / total (branch, this month) |
| Ranking | Branch performance rank |

### HR dashboard (`/hr/`)

| Metric | Source |
|--------|--------|
| Visa expiry (30 days) | `EmployeeCompliance.visa_expiry` |
| Insurance expiry (30 days) | `EmployeeCompliance.insurance_expiry` |
| Contracts expiring | `EmployeeCompliance.contract_end` |
| Employee attendance | `AttendanceRecord` (present today) |
| Leave pending HR | `LeaveRequest` at `pending_hr` stage |

### Operations dashboard (Back office / Follow-up)

| Metric | Source |
|--------|--------|
| Pending cases | Leads pending back office + active follow-up |
| Completed cases | Converted leads |

### Finance dashboard (`/finance/`)

| Metric | Source |
|--------|--------|
| Payroll ready | Approved leave count |
| Incentives | Monthly incentive total |
| Collections | Monthly achieved targets |

### Marketing dashboard (`/marketing/`)

| Metric | Source |
|--------|--------|
| Active campaigns | Active `Announcement` count |
| Leads this month | `Lead` count |

### Awards

| Metric | Model |
|--------|-------|
| Employee of the Month | `Award` (type: `employee_of_month`) |
| Branch of the Month | `Award` (type: `branch_of_month`) |

Metrics are calculated in `core/dashboard_metrics.py`.

---

## 3. Workflows

### 3.1 Leave approval

```
Employee → Branch Manager → HR → Approved
```

**Implementation:**

1. Employee submits leave from Staff / Follow-up / Back Office portal.
2. If staff has a **branch** assigned → `workflow_stage = pending_manager`.
3. Branch Manager approves at `/branch/leave-approvals/` → `pending_hr`.
4. HR approves at `/hr/leave-requests/` → `approved`.
5. Either step can **reject** → `rejected`.

**Model:** `LeaveRequest.workflow_stage`  
**Values:** `pending_manager` · `pending_hr` · `approved` · `rejected`

### 3.2 Salary approval

```
Attendance + Incentive → HR → Finance → Payroll
```

**Implementation:** Finance dashboard shows payroll-ready counts and incentive totals. Full payroll processing is planned; data models: `AttendanceRecord`, `EmployeeIncentive`.

### 3.3 Client processing (leads & cases)

```
Branch Staff (sale) → Follow Up (documents) → Back Office (case processing) → Completed
```

**Example (educational consultancy):**

1. **Branch staff** — customer pays; lead created (`/staff/leads/`).
2. **Follow-up** — collect passport, certificates, photos; upload files on **Leads**. Set status to **Converted** → automatically sends to branch roadmap + opens back office case (no manual handoff checkboxes).
3. **Back office** — case processing (`/backoffice/cases/<id>/`): verify documents, create application, submit file, submit online, track response, update customer, complete case.

**Lead verification:** Back office still verifies leads from non-staff sources (`/backoffice/leads/`).

**Case stages:** `opened` → `documents_verified` → `application_created` → `applied_universities` → `portals_uploaded` → `tracking_responses` → `customer_updated` → `completed`

**Models:** `Lead`, `LeadRoadmapEntry`

### 3.4 Recruitment

```
Branch Request → HR → Interview → Joining
```

**Implementation:** `RecruitmentRequest` model with status flow. HR views at `/hr/recruitment/`.

**Statuses:** `branch_request` → `hr_review` → `interview` → `joining` → `closed`

### 3.5 Salary increment

```
Manager → HR → Admin → Update
```

**Implementation:** Documented workflow; model `SalaryIncrementRequest` exists for future UI. HR Approvals page focuses on leave workflow.

---

## 4. HR portal modules

| Module | URL | Purpose |
|--------|-----|---------|
| Dashboard | `/hr/` | HR metrics + leads overview |
| Workflows | `/hr/workflows/` | Role hierarchy & workflow reference |
| Compliance | `/hr/compliance/` | Visa, insurance, contract tracking |
| Recruitment | `/hr/recruitment/` | Branch hiring requests |
| Org Database | `/hr/org-database/` | Centralized staff & branch directory |
| Approvals | `/hr/approvals/` | Leave approval hub |
| Analytics | `/hr/analytics/` | Organization-wide reporting |
| Leave Requests | `/hr/leave-requests/` | HR final leave approval |

---

## 5. Data models (new)

| Model | App | Purpose |
|-------|-----|---------|
| `EmployeeCompliance` | core | Visa, insurance, contract dates |
| `AttendanceRecord` | core | Daily attendance |
| `EmployeeTarget` | core | Monthly sales/target tracking |
| `EmployeeIncentive` | core | Monthly incentives |
| `Announcement` | core | Organization announcements |
| `Award` | core | Employee/Branch of the month |
| `RecruitmentRequest` | core | Hiring workflow |
| `Staff.branch` | staff | Link branch staff to branch for leave routing |

---

## 6. How to run

```bash
cd hrms
source ../venv/bin/activate   # if using venv
python manage.py migrate
python manage.py runserver
```

- **Login:** http://127.0.0.1:8000/login/
- **HR register:** http://127.0.0.1:8000/hr/account/register/
- **Admin data entry:** http://127.0.0.1:8000/admin/ (compliance, attendance, targets, awards)

---

## 7. Creating users by role

| Role | How to create |
|------|----------------|
| HR / Admin | Self-register at `/hr/account/register/` (set `user_type=hr` or `admin` in admin) |
| Branch Staff | HR → Staff (assign branch for leave routing) |
| Branch Manager | HR → Branch Managers |
| Follow-up / Back Office | HR → respective team pages |
| Finance / Marketing / Accountant | Django admin → UserProfile with `finance`, `marketing`, or `branch_accountant` |

---

## 8. File reference

| Purpose | Path |
|---------|------|
| Role & workflow definitions | `core/roles.py` |
| Dashboard calculations | `core/dashboard_metrics.py` |
| Leave workflow helpers | `core/leave_utils.py` |
| Branch leave approvals | `branch/views.py` |
| HR pages | `hr/views.py`, `hr/urls.py` |
| System doc (this file) | `TAKHLEES_SYSTEM.md` |
| **All URL paths** | **`URLS.md`** |
| Project status | `PROJECT_STATUS.md` |

---

## 9. Portal modules (navigation)

Each role portal has a **sidebar** with modules. Live data pages link to existing workflows; module pages show metrics, workflow steps, and quick links.

### Portal 1 — Admin (`/admin-portal/`)

| Module | Path |
|--------|------|
| Dashboard | `/admin-portal/` |
| Employees | `/admin-portal/employees/` |
| Branches | `/admin-portal/branches/` |
| Users & Roles | `/admin-portal/roles/` |
| Reports | `/admin-portal/reports/` |
| Workflows | `/admin-portal/workflows/` |
| Settings | `/admin-portal/settings/` |
| System Admin (Django) | `/admin/` |

### Portal 2 — HR Manager (`/hr/`)

Dashboard, leads, branches, teams (staff / follow-up / back office), leave (requests, categories, types), lead sources/statuses, org database, approvals, analytics, compliance, recruitment, workflows, profile.

### Portal 3 — Finance (`/finance/`)

| Module | Path |
|--------|------|
| Dashboard | `/finance/` |
| Payroll | `/finance/payroll/` |
| Incentives | `/finance/incentives/` |
| Collections | `/finance/collections/` |
| Expenses | `/finance/expenses/` |
| Reports | `/finance/reports/` |

### Portal 4 — Marketing (`/marketing/`)

| Module | Path |
|--------|------|
| Dashboard | `/marketing/` |
| Campaigns | `/marketing/campaigns/` |
| Creatives | `/marketing/creatives/` |
| Lead Generation | `/marketing/leads/` |
| Announcements | `/marketing/announcements/` |

### Portal 5 — Branch Manager (`/branch/`)

| Module | Path |
|--------|------|
| Dashboard | `/branch/` |
| Staff | `/branch/staff/` |
| Lead Monitoring | `/branch/leads/` |
| Cases | `/branch/cases/` |
| Leave Approvals | `/branch/leave-approvals/` |
| Performance | `/branch/performance/` |
| Communication | `/branch/communication/` |

### Portal 6 — Branch Accountant (`/accountant/`)

| Module | Path |
|--------|------|
| Dashboard | `/accountant/` |
| Collections | `/accountant/collections/` |
| Invoices | `/accountant/invoices/` |
| Branch Reports | `/accountant/reports/` |
| Finance Comm. | `/accountant/finance-communication/` |

### Portal 7 — Branch Staff (`/staff/`)

| Module | Path |
|--------|------|
| Dashboard | `/staff/` |
| Leads | `/staff/leads/` |
| Sales Pipeline | `/staff/pipeline/` |
| Targets | `/staff/targets/` |
| Leave | `/staff/leave/` |

### Portal 8 — Follow Up (`/followup/`)

| Module | Path |
|--------|------|
| Dashboard | `/followup/` |
| Customer Follow-up | `/followup/leads/` |
| Documents | `/followup/documents/` |
| Case Status | `/followup/cases/` |
| Notes & History | `/followup/notes/` |
| Leave | `/followup/leave/` |

### Portal 9 — Back Office (`/backoffice/`)

| Module | Path |
|--------|------|
| Dashboard | `/backoffice/` |
| Lead Verification | `/backoffice/leads/` |
| Case Processing | `/backoffice/cases/` |
| Reports | `/backoffice/reports/` |
| Leave | `/backoffice/leave/` |

### CRM + case journey (all portals)

```
Lead (Staff, branch saved) → Follow up → Documents → Back office case → Completed
```

`ClientCase` model tracks: Received → Under Process → Submitted → Approved → Completed. Created when follow-up sends lead to branch roadmap.

---

## 10. Next development steps

1. Branch Manager recruitment request form (submit to HR)
2. Finance payroll run (full salary processing UI)
3. Marketing campaign add/edit forms
4. Case status update forms (follow-up / back office)
5. Attendance check-in from employee portal
6. Employee Self Service & Customer portals (future)
7. Strict `hr` role guards on all `/hr/` URLs

---

*TAKHLEES HRMS — multi-portal human resource & operations management.*
