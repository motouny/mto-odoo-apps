# Final Release Report

1. **Application Name**: Employee & Client Self-Service Portal
2. **Technical Name**: `employee_client_self_service_portal`
3. **Version**: 18.0.3.0.1 (extension of an existing 18.0.2.0.0 app - see `EMPLOYEE_CLIENT_PORTAL_AUDIT.md` for the pre-existing state). `18.0.3.0.1` (2026-07-15) adds the MTO publisher icon and fixes the app-switcher icon: `static/description/icon.png` alone does not make Odoo's home menu show a branded icon - the root `<menuitem>` needs an explicit `web_icon="employee_client_self_service_portal,static/description/icon.png"` attribute, which was missing. See `CHANGELOG.md`.
4. **Price**: 49.0
5. **Currency**: EUR
6. **License**: OPL-1
7. **Dependencies**: `portal`, `hr`, `hr_holidays`, `hr_attendance`, `project`, `mail` (all standard Odoo Community modules; unchanged from the pre-existing app - no new dependency was added)
8. **Models Created** (this extension; the pre-existing `hr.employee`/`project.project`/`portal.wizard.user` extensions and `employee.portal.task` were already present and untouched): `ess.request.type`, `ess.request.team`, `ess.request`, `ess.request.comment`, `ess.request.status.history`, `ess.portal.notification`
9. **Views Created**: Backend list/form/search/pivot/graph for `ess.request`; list views for request types and teams; a new backend menu ("Employee & Client Requests"); 4 new portal templates (My Requests, New Request, Request Detail, Notifications) plus additive `inherit_id` xpath extensions to the existing home tiles and breadcrumbs (no existing template was rewritten, only extended)
10. **Security Groups**: 2 new - **Client** (`group_ess_client`, implies `base.group_portal`) for true external self-service, and **Request Manager** (`group_ess_request_manager`, implies `base.group_user`, auto-granted to `base.user_admin`) for internal triage staff. The pre-existing design decision to keep employees and the project-scoped Portal Manager on plain `base.group_portal` was preserved unchanged.
11. **Record Rules**: Multi-company + ownership rules on all 6 new models (`ess_request_security.xml`); the pre-existing `ir.rule` set for `hr.leave`, `hr.leave.allocation`, `hr.attendance`, `employee.portal.task` and `project.task` was left untouched.
12. **Portal Routes** (new): `/my/requests` (+`/new`, `/new/submit`, `/<id>`, `/<id>/comment`, `/<id>/cancel`, `/<id>/rate`), `/my/notifications`. All existing routes from the pre-existing app are unchanged except two small, deliberate fixes (see Upgrade Plan item 6 in the audit): the multi-company scoping of `_get_managed_projects()`/`_get_managed_employees()`, and replacing a silent `except: pass` on tampered team-approval requests with a visible error message.
13. **Reports**: Pivot and graph views on `ess.request` (by type/status); Overdue and My Tickets saved filters.
14. **Cron Jobs**: None added (the pre-existing daily assignment-reminder cron is unchanged).
15. **Automated Tests**: This app had **zero automated tests before this session** (a gap noted during the audit). Added 3 test modules / 19 test methods: `test_ess_request.py` (workflow, status history, rating, immutability), `test_ess_request_security.py` (unauthorized approval, cross-employee/cross-client visibility, impersonation attempt, manager visibility), `test_portal_requests.py` (`HttpCase` - login requirement, cross-employee IDOR check on the portal detail route).
16. **Test Results**: `0 failed, 0 error(s) of 19 tests`, verified three times: (1) on the working source tree, (2) after every subsequent fix, (3) on a fresh extraction of the final shipped ZIP into an independent addons path with its own test database - all three runs clean.
17. **Known Limitations**:
    - Group visits / multi-request bulk actions are out of scope; each `ess.request` is a single request.
    - The client and request-manager groups are new; the pre-existing Portal Manager role was intentionally left as-is rather than merged into the new request system, to avoid changing behavior real deployments may already depend on.
    - As with the base app, no `wkhtmltopdf` is installed in this development environment, so this extension does not add any new PDF reports (it uses pivot/graph views instead, which do not require it).
    - The Arabic translation covers 171 of 288 translatable strings (59%) - up from 110/115 (95.7%) before, since ~170 new strings were introduced by the request system; the highest-visibility UI strings (menus, states, fields, buttons) are translated, some longer help texts are not.
18. **Community Compatibility**: Full - no Enterprise-only feature is used.
19. **Enterprise Compatibility**: Fully compatible.
20. **External Python Dependencies**: None (unchanged).
21. **Store Assets**: `static/description/index.html` (rewritten to cover the request system and new roles), `README.md` (extended), `USER_GUIDE.md`, `INSTALLATION.md`, `SUPPORT.md`, `LICENSE`, `CHANGELOG.md` (all four newly added - only `README.md` pre-existed), 8 real screenshots captured from the running demo database, replacing the previous set which had a numbering gap (`04_*.png` never existed) and one unused file (`02_time_off.png` wasn't referenced by the old `index.html`). `banner.png`/`icon.png`/`mto_lockup.png` were already present and are unchanged/reused.
22. **ZIP File Path**: `marketplace_addons/dist/employee_client_self_service_portal_18.0.zip` (77 files, ~1.2 MB, module folder at the archive root, no `__pycache__`/`.pyc`/`.DS_Store`/database dumps).
23. **Installation Command**:
    ```bash
    ./odoo-bin -d yourdb -i employee_client_self_service_portal --stop-after-init
    ```
24. **Upgrade Command**:
    ```bash
    ./odoo-bin -d yourdb -u employee_client_self_service_portal --stop-after-init
    ```
25. **Release Checklist**:
    - [x] Audit of the pre-existing app completed first (`EMPLOYEE_CLIENT_PORTAL_AUDIT.md`), extension plan derived from it
    - [x] No existing model, view, route or record rule was deleted or behaviorally changed except two explicitly-documented bug fixes
    - [x] Clean install on an empty database (no parse errors, no missing external IDs)
    - [x] Module upgrade (`-u`) on top of an existing install
    - [x] Full automated test suite passing (19/19), including on the final extracted ZIP
    - [x] Clean uninstall verified on a test database
    - [x] Manual verification in a real browser: employee dashboard, Portal Manager team/approvals/assignments, client self-service request list and detail, backend staff triage queue, cross-ownership IDOR checks (client cannot open another employee's or client's request by guessing the URL)
    - [x] Two real bugs found and fixed during manual QA: (1) a naive multi-company domain (`company_id in company_ids`) silently hid company-independent projects that used to be visible - fixed to `'|', company_id = False, company_id in company_ids`; (2) demo data for the pre-existing Portal Manager / Team Tasks features never existed, so those screens were always empty in a fresh demo install - added minimal demo wiring
    - [x] `ir.model.access.csv` and record rules reviewed for least privilege (a Client cannot create a request on another client's behalf even with `create` ACL granted, enforced by `ir.rule`, not just the controller)
    - [x] Price/license/author metadata preserved from the existing paid listing (€49/OPL-1/MTO)
    - [x] Arabic translation extended and re-imported; previously-flagged untranslated strings (Portal Manager, Portal Project, both help texts) are now translated
    - [ ] PDF report rendering - N/A for this extension (no new PDF reports were added)
    - [ ] Full 100% Arabic translation coverage - 59% achieved for this larger string set; recommend a follow-up pass before store upload if full coverage is required

**This extension is functionally complete and test-verified against the real, final shipped ZIP.** It is additive by design: every pre-existing feature was audited first and left working exactly as before, except two explicitly-documented and tested bug fixes.
