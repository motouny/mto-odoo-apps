# Final Release Report

1. **Application Name**: Smart Visitor Management
2. **Technical Name**: `smart_visitor_management`
3. **Version**: 18.0.1.0.3 (2026-07-29: Visitor Badge now prints on its own compact card paper format instead of the company default A4/Letter, skips the one-time company document-layout wizard, and no longer overflows the QR code/badge number past the card border; added `visitor.department` master data linked to Hosts and Visits - see `CHANGELOG.md`)
4. **Price**: 30.0
5. **Currency**: EUR
6. **License**: OPL-1
7. **Dependencies**: `base`, `mail`, `portal`, `web` (all standard Odoo Community modules; no other paid or custom app required)
8. **Models Created**: `visitor.location`, `visitor.gate`, `visitor.host`, `visitor.guest`, `visitor.vehicle`, `visitor.blacklist`, `visitor.badge.template`, `visitor.checkpoint.log`, `visitor.visit` (+ `res.company`/`res.config.settings` extensions)
9. **Views Created**: List/form/kanban/calendar/search for `visitor.visit`; list/form for guests, locations, gates, hosts, blacklist, badge templates; read-only list for the checkpoint scan log; a client-action Check-In Kiosk view; a `res.config.settings` panel; a public QWeb portal template; app menus.
10. **Security Groups**: Visitor User, Host Employee, Receptionist, Security Officer, Auditor, Visitor Manager (implies Receptionist + Security Officer), Administrator (implies Visitor Manager, auto-assigned to `base.user_admin`).
11. **Record Rules**: Multi-company rules on `visitor.visit`, `visitor.location`, `visitor.gate`, `visitor.host`, `visitor.blacklist`, `visitor.badge.template`, `visitor.checkpoint.log`; a Host-only-sees-own-visits rule; a full-company-access rule for Receptionist/Security/Auditor/Manager.
12. **Portal Routes**:
    - `GET/POST /visitor/invitation/<token>` and `/visitor/invitation/<token>/submit` - public, token-only lookup (never by id), CSRF-protected form submission.
    - `POST /visitor/kiosk/scan` (JSON, `auth=user`, restricted to Manager/Receptionist/Security groups) - QR/manual check-in and check-out.
13. **Reports**: Visitor Badge (PDF, with embedded QR via Odoo's built-in `/report/barcode` route), Vehicle Permit (PDF).
14. **Cron Jobs**: `Visitor Management: Expire Overdue Visits` (hourly) - moves approved/scheduled/pending visits whose end time has passed to *Expired* and revokes their QR token.
15. **Automated Tests**: 28 Python tests across `test_visitor_visit.py` (workflow, QR reuse/expiry prevention, blacklist blocking, immutable scan log), `test_security.py` (unauthorized approval, cross-host visibility, multi-company isolation, security-officer write restriction), `test_portal.py` (`HttpCase` - public page access, 404 on invalid/id-guessed token, CSRF-protected submission).
16. **Test Results**: `0 failed, 0 error(s) of 28 tests` on a clean install against PostgreSQL, run standalone (module installed alone, no other MTO app), combined with the other two MTO apps in the same database (no XML-ID/route/model collisions), and via Odoo core's own `base.tests.test_reports` suite (2026-07-15 re-verification), which is what actually surfaced and confirmed the report fix in `18.0.1.0.1` below - not the module's own test suite.
17. **Known Limitations**:
    - Group visits share a single QR token per visit rather than one token per accompanying guest.
    - The "Scheduled" vs "Approved" state distinction is time-derived at approval time, not a separately triggered transition.
    - No automated test exercises PDF generation itself, since this development environment has no `wkhtmltopdf` binary installed; the QWeb report templates were verified to load without error at module install, and the HTML preview of both the badge and vehicle permit reports (same templates, no PDF conversion step) was verified in a real browser, including the embedded QR image and a populated vehicle table.
    - Visitor badge design is functional/plain, not a graphically designed badge template.
    - **Fixed in 18.0.1.0.1 (2026-07-15)**: the Vehicle Permit report used `t-field` directly on `<td>` elements, which Odoo's QWeb engine rejects at render time (`AssertionError: QWeb widgets do not work correctly on 'td' elements`). This passed module install and the module's own tests undetected - it only surfaced when running Odoo core's `base.tests.test_reports` suite, which actually renders every registered report's HTML. Fields are now wrapped in `<span>` inside each `<td>`. See `smart_visitor_management/CHANGELOG.md`.
18. **Community Compatibility**: Full - installs and runs on Odoo 18 Community with only `base`/`mail`/`portal`/`web`.
19. **Enterprise Compatibility**: Fully compatible; no Enterprise-only feature is used or required.
20. **External Python Dependencies**: None beyond what Odoo 18 already requires (`qrcode`, used internally by Odoo's own barcode report route, not a new dependency added by this module).
21. **Store Assets**: `static/description/index.html`, `README.md`, `USER_GUIDE.md`, `INSTALLATION.md`, `CHANGELOG.md`, 8 real screenshots captured from the running demo database (`static/description/screenshots/01`-`08`, including a new Departments screenshot and a refreshed Visitor Badge screenshot showing the fixed compact card). `icon.png` (MTO brand kit "M" mark), `banner.png` and `cover.png` are present under `static/description/` and declared via the manifest `images` key.
22. **ZIP File Path**: `marketplace_addons/dist/smart_visitor_management_18.0.zip` (80 files, ~1.2 MB, module folder at the archive root, no `__pycache__`/`.pyc`/`.DS_Store`/database dumps; rebuilt 2026-07-29 with the `18.0.1.0.3` badge print fix, Departments feature, the Arabic translation fix for the renamed Department field, and refreshed store screenshots/icon/banner/cover. Verified by installing the zip itself - not just the source folder - into a throwaway Community-only database.)
23. **Installation Command**:
    ```bash
    ./odoo-bin -d yourdb -i smart_visitor_management --stop-after-init
    ```
24. **Upgrade Command**:
    ```bash
    ./odoo-bin -d yourdb -u smart_visitor_management --stop-after-init
    ```
25. **Release Checklist**:
    - [x] Clean install on an empty database (no parse errors, no missing external IDs)
    - [x] Module upgrade (`-u`) on top of an existing install
    - [x] Full automated test suite passing (22/22)
    - [x] Clean uninstall verified on a test database
    - [x] Manual verification in a real browser: backend CRUD, kiosk QR scanner (Owl component), public tokenized guest registration page, Arabic/RTL rendering, mobile layout
    - [x] A real bug found and fixed during manual QA (kanban view crashed on mobile because `guest_id`/`host_id`/`visit_start` were used in the card template without being declared as kanban fields)
    - [x] `ir.model.access.csv` and record rules reviewed for least privilege (Security Officer has no direct `write` ACL; check-in/out only works through a narrowly-scoped server method)
    - [x] Price set to 30.0 EUR, license OPL-1, `application: True`, `installable: True`
    - [x] Arabic translation (`i18n/ar.po`, 92 curated high-visibility strings) imported and verified live in a real Arabic/RTL session
    - [ ] `banner.png` / `icon.png` / `cover.png` - pending, to be supplied outside this session
    - [ ] PDF (as opposed to HTML-preview) report rendering - not verifiable in this environment (no `wkhtmltopdf`); recommend one manual check before the actual store upload

**This module is functionally complete and test-verified, but is not yet 100% store-upload-ready**: the three store graphics are still outstanding by design, and PDF report rendering should get one manual pass on an environment with `wkhtmltopdf` installed before the final upload.
