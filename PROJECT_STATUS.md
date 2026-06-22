# TAKHLEES HRMS — Project Status

**Last updated:** May 2026  
**Stack:** Django 6 · SQLite (dev) · Bootstrap 5 · DataTables · Chart.js · SweetAlert2  
**Project path:** `hrms/` (run server from here: `python manage.py runserver`)

---

## Overview

Multi-role Human Resource & Lead Management System. Each user type has its own portal after login. HR manages organization setup; operational teams (staff, back office, follow-up, branch) use dedicated dashboards.

---

## User roles & login redirect

| Role | Portal URL | Created by |
|------|------------|------------|
| HR | `/hr/` | Self-registration (`/hr/account/register/`) |
| Staff | `/staff/` | HR → Staff |
| Back Office | `/backoffice/` | HR → Back Office |
| Follow-up | `/followup/` | HR → Follow-up |
| Branch Manager | `/branch/` | HR → Branch Managers |

**Auth:** `/login/` · **Register hub:** `/register/` (links to HR portal or team list pages)

---

## Implemented features

### HR portal (`/hr/`)

| Feature | URL | Status |
|---------|-----|--------|
| Dashboard (charts, sample lead widgets) | `/hr/` | Done |
| All leads (database) | `/hr/leads/` | Done |
| Branches (add, edit, soft delete) | `/hr/branches/` | Done |
| Branch managers | `/hr/branch-managers/` | Done |
| Staff team | `/hr/staff/` | Done |
| Follow-up team | `/hr/followup/` | Done |
| Back office team | `/hr/backoffice/` | Done |
| HR profile & photo | `/hr/profile/` | Done |
| Leave requests (approve/reject) | `/hr/leave-requests/` | Done |
| Leave categories (days/year) | `/hr/leave-categories/` | Done |
| Leave types (sick, casual, …) | `/hr/leave-types/` | Done |
| HR self-registration | `/hr/account/register/` | Done |

### Staff portal (`/staff/`)

| Feature | URL | Status |
|---------|-----|--------|
| Dashboard | `/staff/` | Done |
| Add & view own leads | `/staff/leads/` | Done |
| Leave requests | `/staff/leave/` | Done |

### Back office portal (`/backoffice/`)

| Feature | URL | Status |
|---------|-----|--------|
| Dashboard | `/backoffice/` | Done |
| Verify leads (correct / not correct) | `/backoffice/leads/` | Done |
| Leave requests | `/backoffice/leave/` | Done |

### Follow-up portal (`/followup/`)

| Feature | URL | Status |
|---------|-----|--------|
| Dashboard | `/followup/` | Done |
| Work verified leads, status, branch, roadmap | `/followup/leads/` | Done |
| Leave requests | `/followup/leave/` | Done |

### Branch portal (`/branch/`)

| Feature | URL | Status |
|---------|-----|--------|
| Dashboard | `/branch/` | Done |
| Lead roadmap (timeline) | `/branch/leads/` | Done |

---

## Lead pipeline (implemented)

```
Staff adds lead
       ↓
Back office:  ✓ Correct  →  Follow-up team
              ✗ Not correct  →  Staff sees "Not correct"
       ↓
Follow-up: status, roadmap notes, assign branch, "Send to branch"
       ↓
Branch: full roadmap timeline for leads at their branch
```

**Models:** `Lead`, `LeadRoadmapEntry` (`core` app)

| Field / concept | Description |
|-----------------|-------------|
| `backoffice_status` | `pending` · `verified` · `rejected` |
| `followup_status` | `new` · `contacted` · `qualified` · `converted` · `lost` |
| `pipeline_stage` | `submitted` · `followup` · `branch` |
| Roadmap | Auto + manual entries on verify, reject, follow-up updates |

---

## Leave system (implemented)

Two separate concepts:

| Concept | Model | Purpose | Managed by |
|---------|--------|---------|------------|
| **Leave category** | `LeaveCategory` | Days per year (e.g. Yearly = 30) | HR → Leave Categories |
| **Leave type** | `LeaveType` | Sick, Casual, etc. (no day count) | HR → Leave Types |

**Request flow:** Staff / Follow-up / Back office submit → balance checked per **category** → HR approves or rejects.

**Defaults (seeded):**

- **Category:** Yearly Leave — 30 days/year  
- **Types:** Sick Leave, Casual Leave (classification only; HR can add more)  

---

## Data models (by app)

### `core`

- `UserProfile` — role, phone, profile picture  
- `LeaveCategory`, `LeaveType`, `LeaveRequest`  
- `Lead`, `LeadRoadmapEntry`  

### `hr`

- `Hr` — HR profile linked to `User`  

### `staff` / `followup` / `backoffice`

- `Staff` / `FollowUp` / `BackOffice` — team profiles (`user`, phone, dates, `is_active`)

### `branch`

- `Branch` — soft delete (`is_deleted`)  
- `BranchManager` — linked to branch, deactivate disables login  

---

## Project structure

```
hrms/
├── manage.py
├── hrms/                 # settings, urls, wsgi
├── core/                 # auth, profiles, leave, leads
├── hr/                   # HR views, forms, urls
├── staff/
├── followup/
├── backoffice/
├── branch/
├── templates/
│   ├── core/             # login, register hub
│   ├── hr/               # HR portal
│   └── portal/           # shared layout for team portals
├── static/hr/            # css, js (shared UI)
└── db.sqlite3            # dev database
```

---

## Migrations (core)

| Migration | Description |
|-----------|-------------|
| 0001–0003 | Initial, UserProfile, profile picture |
| 0004 | Leave system |
| 0005 | Sick/casual seed (legacy; superseded by 0006) |
| 0006 | Split LeaveCategory vs LeaveType |
| 0007 | LeaveRequest → leave_category FK fix |
| 0008 | Lead pipeline |

Run: `python manage.py migrate`

---

## Not implemented / partial

| Area | Notes |
|------|--------|
| HR lead add/edit | HR views all leads; add lead modal on HR page is demo-only |
| Lead export | Button on HR leads page — UI only |
| Email notifications | None |
| Branch manager self-register | HR creates accounts only |
| Role-based permission beyond login redirect | URLs not hidden between roles; decorator checks per portal |
| Production deploy | DEBUG/settings, static via web server not configured in repo |
| Automated tests | Minimal / none |
| API / mobile | None |

---

## How to run locally

```bash
cd hrms
python3 -m venv venv          # if needed
source venv/bin/activate
pip install -r requirements.txt   # if requirements.txt exists
python manage.py migrate
python manage.py runserver
```

Open: http://127.0.0.1:8000/login/

Create HR via `/hr/account/register/`, then add teams from HR sidebar.

---

## Key files reference

| Purpose | Path |
|---------|------|
| Settings | `hrms/settings.py` |
| Root URLs | `hrms/urls.py` |
| Lead workflow views | `core/lead_portal.py` |
| Leave workflow views | `core/leave_portal.py` |
| Portal layout | `templates/portal/base.html` |
| HR layout | `templates/hr/base.html` |
| Shared UI JS | `static/hr/js/app.js` |
| TAKHLEES theme | `static/hr/css/takhlees-theme.css` |
| Logo | `static/hr/images/takhlees-logo.png` |

---

## UI / branding (TAKHLEES)

- **Colors:** Red `#E01E26` (primary actions), Green `#00843D` (success / verified), Black sidebar, white content.
- **Logo** on login, register hub, HR registration, and all sidebars.
- **Help banners** on lead workflow pages (staff, back office, follow-up, branch).

---

## System documentation

Full architecture, roles, workflows, and dashboards: **`TAKHLEES_SYSTEM.md`**

---

The project is a **working multi-portal HRMS** with:

- Full **HR administration** (branches, teams, leave, leads overview)  
- **Team portals** with login and role-specific dashboards  
- **Lead pipeline** across staff → back office → follow-up → branch  
- **Leave management** with categories, types, balances, and HR approval  

Next logical steps: HR lead creation UI, email alerts, tests, production settings, and tightening access control on HR-only routes.
