# Employee & Client Self-Service Portal — Audit Report

Audited path: `marketplace_addons/employee_client_self_service_portal`
Audit date: 2026-07-13. Current manifest: v18.0.2.0.0, €49/OPL-1, depends on
`portal, hr, hr_holidays, hr_attendance, project, mail`.

## 1. Current Features

- **Employee self-service** (`base.group_portal`, keyed off `request.env.user.employee_id`):
  - My Profile — edit private contact/emergency/education fields only (whitelisted).
  - My Time Off — view balances, submit new leave, cancel own pending leave.
  - My Attendances — check in/out (JSON toggle), monthly history.
  - My Tasks — read-only list of `project.task` the user is assigned to.
  - My Assignments — accept/update lightweight `employee.portal.task` records assigned by the Portal Manager; daily email reminder cron for unfinished ones.
- **Client-side Portal Manager** (still `base.group_portal`, scoped via `project.project.portal_manager_id`):
  - My Team — card grid of a managed project's employees with today's status (present/on leave/on permission/absent).
  - Team approvals — first-stage approval/refusal of managed employees' leave (two-stage validation alongside internal HR).
  - Team Tasks — assign/track lightweight tasks for managed employees.
- Branding follows the installing company's name/logo automatically.
- Daily cron (`ir_cron_assignment_reminder`) emails employees with pending assignment tasks.
- English + Arabic (95.7% translated, 5 strings still English — see §9).

## 2. Current Models

| Model | Type | Purpose |
|---|---|---|
| `hr.employee` (extended) | existing | + `project_id` (Portal Project), + `action_grant_portal_access()` |
| `project.project` (extended) | existing | + `portal_manager_id` (the portal user who oversees this project's employees) |
| `portal.wizard.user` (extended) | existing (Transient) | auto-links a newly granted portal user to any unlinked employee sharing the same contact |
| `employee.portal.task` | new | lightweight task assigned by a Portal Manager to an employee: `employee_id`, `project_id` (related), `assigned_by_id`, `name`, `description`, `deadline`, `state` (new/accepted/in_progress/done), `status_note`, `last_update_date`; `_cron_send_reminders()` |

No `company_id` field exists on `employee.portal.task`, and no multi-company scoping exists anywhere in the module (see §5).

## 3. Current Controllers

Single controller class `EmployeeSelfPortal(CustomerPortal)` in `controllers/portal.py`, 21 routes, all `auth='user'` (none `auth='public'`). Every mutating route derives its owning record server-side (`_get_portal_employee()`, `_document_check_access()`, `_get_team_leave()`, `_get_own_task()`) before calling `.sudo()` — see §7 for the one pattern worth flagging.

## 4. Current Portal Routes

`/my`, `/my/dashboard`, `/my/profile` (+`/update`), `/my/time-off` (+`/new`, `/new/submit`, `/<id>`, `/<id>/cancel`), `/my/attendances` (+`/toggle` JSON), `/my/tasks`, `/my/team`, `/my/team/approvals` (+`/<id>/approve`, `/<id>/refuse`), `/my/team/tasks` (+`/new`, `/new/submit`), `/my/assignments` (+`/<id>/accept`, `/<id>/update`).

## 5. Security Risks

1. **No multi-company boundary.** Grep for `company_id` across the module returns only 3 hits (an allocation-data filter, a demo data record, and a mail-template `email_from` expression). None of `_get_managed_projects`, `_get_managed_employees`, `_team_status`, or the dashboard/team/approvals/team-tasks routes filter by `request.env.company`. In a multi-company install, a Portal Manager's visibility is bounded only by which `project.project` records have their `portal_manager_id` pointed at them — an administrator who links a manager to a project in a different company would leak that company's employee names, statuses and leave data to the portal user. This is an administrative-configuration reliance today, not an exploitable bug in isolation, but it is a real gap for a paid multi-company-marketed app.
2. **Cron runs as `base.user_root`** (fully privileged, standard for `ir.cron`) and iterates all pending tasks company-wide with no company filter — consistent with finding #1, not a new issue, but compounds it once multi-company scoping is added elsewhere.
3. **Silent failure on tampered approve/refuse requests.** `/my/team/approvals/<id>/approve|refuse` swallow `AccessError`/`MissingError`/`UserError` with a bare `pass` and redirect as if nothing happened. Not a security hole (the ownership check still blocks the action), but it means a tampering attempt produces no audit trail and no user-visible feedback — worth upgrading to at least a flash message, and ideally a logged warning.
4. **No rate limiting / brute-force protection** on any POST route (framework-level gap, same as almost every Odoo portal controller — noting it because the parent spec asks for it, not because this module is unusual).

## 6. Missing Access Rules

None found for models this module defines. `employee.portal.task` has its ACL row and matching `ir.rule`. `project.task` correctly relies on the base `project` module's own `base.group_portal` ACL, narrowed here only by an additional `ir.rule`. No gaps identified in `ir.model.access.csv` or the `ir.rule` set as they exist today.

## 7. IDOR Risks

Every ownership-defining field on every mutating route is derived server-side from the logged-in user — **with one exception worth flagging explicitly**: `/my/team/tasks/new/submit` reads `employee_id` from the POST body (`controllers/portal.py:441`) rather than deriving it. It **is** validated against `self._get_managed_employees().ids` before use (line 442), so it is not currently exploitable — but it is the single place in the codebase where a foreign key flows from an HTTP field into a `create()` call, and is the highest-risk-by-pattern spot to re-check on any future edit. No other IDOR vector was found: leave cancel/approve/refuse and task accept/update all re-verify ownership from a server-derived record before mutating, independent of the `ir.rule` layer (defense in depth).

No attachment/download routes exist in this module at all, so there is no attachment-ownership surface to audit here (the separate `employee_client_self_service_portal_payroll` add-on, out of scope for this audit, is where payslip downloads would live).

## 8. Missing Features

Against the full target feature list for this app category, the following are **not yet implemented** and are the subject of this extension:

- A general-purpose employee/client request system (leave already exists, but permission requests, attendance-correction requests, overtime requests, letter/certificate requests, data-change requests, equipment/custody requests, and internal-support requests do not).
- Request status history / audit trail as a first-class, queryable model (today only `mail.thread`-style chatter would provide this, and none of the current models even inherit `mail.thread`).
- Any client-company-facing features at all — the current "Portal Manager" is explicitly an *internal-project* oversight role for a single named portal user, not a client/company-scoped self-service area with its own contacts, projects, contracts, or assets visibility.
- Notifications as a queryable in-portal model (today, only outbound email exists — no "Notifications" page in the portal).
- Reports (Requests by Status/Type/Employee, Average Resolution Time, etc.) — none exist.
- Rating/CSAT on request closure.
- Document upload/download for employees (no attachment surface at all currently).

## 9. UI Problems

- `static/description/index.html` references `01_dashboard.png`, `05_my_team.png`, `06_approvals.png`, `03_assignments.png` but **not** `02_time_off.png`, which exists in the screenshots folder unused. There is also a numbering gap — no `04_*.png` was ever produced. Store listing should be regenerated with the current, consistent screenshot set once new features land.
- 5 translatable strings remain untranslated in `i18n/ar.po` (the assignment-reminder email body, one portal template's terms, and two field help texts) — 95.7% complete, not 100%.
- Silent failure UX on tampered team-approval requests (see §5.3) — a legitimate user who double-clicks after a leave was already processed by someone else gets no feedback, just a redirect.

## 10. Store Readiness

The existing app is well-built: clean ownership checks, whitelisted mass-assignment surfaces, correctly scoped `ir.rule`s, no attachment surface to worry about, and a git history showing active maintenance (including a self-corrected manifest-duplication bug). It is **not yet store-ready as a category-leading "Employee & Client Self-Service Portal"** because the "Client" half of the name is currently just an internal-project-manager view, not a true external-client self-service area, and because it has no general request system, no reports, and an incomplete store listing. The extension below closes the highest-value gaps without touching the parts that already work correctly.

## 11. Upgrade Plan

1. Add a generic, independent request system (`ess.request.type`, `ess.request`, `ess.request.comment`, `ess.request.status.history`, `ess.portal.notification`) covering the highest-value request types (leave stays on the existing `hr.leave` flow; new: permission, attendance correction, overtime, letter/certificate, data change, equipment/custody, internal support), with its own state machine, sequence, attachments, and mail notifications — additive, does not touch the existing leave/attendance/task code paths.
2. Add `company_id` to every new model and add explicit multi-company filtering to the existing `_get_managed_projects`/`_get_managed_employees` helpers (backward-compatible: single-company installs are unaffected).
3. Add a minimal true client-facing area (client company info, contacts, and a "create service request" flow reusing the new `ess.request` system) gated by a **new**, explicitly client-scoped group rather than overloading `base.group_portal` further — additive, does not change the existing Portal Manager role.
4. Add an in-portal Notifications page backed by `ess.portal.notification`.
5. Add basic reports (Requests by Status/Type/Employee/Client, Overdue Requests).
6. Fix the two UI problems in §9 (screenshot set, remaining translations) and replace the silent `pass` in the approve/refuse routes with a proper flash message.
7. Re-package with updated demo data, a refreshed `index.html`, and a new release report — keep the price/license/author metadata as already set (€49/OPL-1/MTO) unless the user asks otherwise.
