# Final Release Report

1. **Application Name**: Saudi Government Fixed Asset Management (MOF Compliant)
2. **Technical Name**: `sa_gov_fixed_assets`
3. **Version**: 18.0.1.1.0 (2026-07-23: added barcode-type choice (QR/Code128) and an RFID Tag ID field on `sa.gov.asset.tag`, plus a Quick Scan wizard for fast barcode/QR/RFID-based physical verification — see item 13a)
4. **Price**: 30.0
5. **Currency**: EUR
6. **License**: OPL-1
7. **Dependencies**: `base`, `mail`, `web` (all standard Odoo Community modules; no Enterprise-only module, no other paid or custom app required — deliberately does not depend on Enterprise's `account_asset`, ships its own asset/depreciation models instead)
8. **Models Created**: `sa.gov.asset.classification` (1,636-row static MOF classification/coding table), `sa.gov.asset` (main asset register), `sa.gov.asset.type.detail`, `sa.gov.asset.depreciation.line`, `sa.gov.asset.tag`, `sa.gov.asset.verification` + `sa.gov.asset.verification.line`, `sa.gov.asset.verification.populate.wizard` (+ `res.company`/`res.config.settings` extensions for the large-entity threshold and MOF entity name/code)
9. **Views Created**: List/kanban/form/search for `sa.gov.asset`; list/form/search for the classification table; list/form for tags; list/form for verification campaigns with an editable line grid; a populate wizard; a `res.config.settings` panel; app menus
10. **Security Groups**: Asset User (read + verification data entry), Asset Officer (create/edit assets), Asset Manager (capitalize/dispose/transfer, classification overrides), Administrator (implies Manager, auto-assigned to `base.user_admin`)
11. **Record Rules**: Multi-company rules on `sa.gov.asset`, `sa.gov.asset.verification`, `sa.gov.asset.depreciation.line`, `sa.gov.asset.tag`
12. **Reports**: Asset Register (سجل الأصول), Classification & Coding Sheet, Physical Count Sheet, Asset Tag Label (QR or Code128, picked per tag) — all QWeb, `binding_type: report` on the relevant models
13. **Automated Tests**: 11 test methods in `tests/test_sa_gov_asset.py` — capitalization-threshold determination (land/NA, above/below threshold, large-entity override), manual override, MOF asset code generation, depreciation schedule generation and math (including a regression test that posting a depreciation line correctly updates `book_value`/`accumulated_depreciation`), useful-life range validation, disposal-method guard, and 3 Quick Scan tests (marks an existing line found, auto-creates a line for an asset not yet on the campaign, handles an unknown scanned code without crashing)
13a. **Barcode / RFID / Quick Scan (added 2026-07-23)**: `sa.gov.asset.tag` now has a `barcode_type` choice (QR or Code128 — the guide, p.37, accepts either) and an `rfid_tag_id` (EPC) field; the tag label report prints whichever type is chosen and shows the RFID ID if set. A new `sa.gov.asset.verification.quick.scan.wizard` ("Quick Scan (Barcode / QR / RFID)" button on an in-progress campaign) accepts a scanned code, looks it up against asset code / tag number / RFID ID, marks the matching campaign line found (or creates one if the asset wasn't already on the campaign), and stays open for the next scan — verified live in the browser with a real RFID-style code, both the match and the "unknown code" path. Note on scope: this reads whatever a handheld scanner/RFID reader *emits as text* (the standard keyboard-wedge/HID mode nearly all commercial handheld RFID readers support) — it is not a driver-level integration with specific RFID reader hardware/SDKs, which is outside what an Odoo addon can do on its own.
14. **Test Results**: `0 failed, 0 error(s)` of the module's own test suite, run both scoped (`--test-tags /sa_gov_fixed_assets`) and as part of the full unfiltered Odoo core `--test-enable` suite (`base`, `mail`, `web` and all their dependents). The unfiltered run surfaced and led to fixing one real bug (see Known Limitations/Fixes below); all other failures observed in that run (`base.tests.test_configmanager`, `phone_validation` geocoding tests, `base`/`web` `test_reports` PDF-generation tests) are pre-existing environment limitations (no internet access for phone geocoding data, no `wkhtmltopdf` binary installed) unrelated to this module — confirmed by grepping the log for the module name, not assumed.
15. **Fixed during QA (pre-release)**:
    - An uncommented always-invisible field (`verification_id` on the "Add Assets to Campaign" wizard view) failed Odoo core's `base.tests.test_views.TestInvisibleField` convention check; fixed by adding an explanatory XML comment.
    - `sa.gov.asset._compute_depreciation_totals`'s `@api.depends` was missing `depreciation_line_ids.state`, so posting a depreciation line didn't recompute `book_value`/`accumulated_depreciation` on the parent asset. Found while capturing real screenshots for the store listing (the ambulance demo asset's book value didn't reflect posted depreciation). Fixed, with a regression assertion added to the test suite.
16. **Community Compatibility**: Full — installs and runs on Odoo 18 Community with only `base`/`mail`/`web`.
17. **Enterprise Compatibility**: Fully compatible; no Enterprise-only feature is used or required.
18. **External Python Dependencies**: None. QR codes use Odoo's own built-in `/report/barcode/QR/<value>` route (no external library).
19. **Data**: `data/sa.gov.asset.classification.csv` — the full official MOF classification/coding table (1,636 rows: 31 main groups, sub-groups, asset types, each combined with its accounting classification, capitalization threshold and useful-life range), extracted from the Ministry of Finance's official Excel annex and the guide's narrative methodology (see the approved plan file for provenance detail). `data/demo_data.xml` — 3 base demo assets exercising both the capitalized and non-capitalized paths.
20. **Store Assets**: `static/description/index.html` (Arabic-first marketing copy, RTL), `static/description/banner.png` (1280×720, MTO brand + a real running-app screenshot in a browser-chrome mockup), `static/description/icon.png` (MTO brand icon, `web_icon` set on the root menu), `static/description/mto_lockup.png`, 7 real screenshots in `static/description/screenshots/` captured from an actually-running instance with enriched demo data (a capitalized vehicle with posted depreciation, a 1-SAR heritage asset, a non-capitalized furniture item, an in-progress verification campaign with a flagged discrepancy) — none are mockups or placeholders.
21. **ZIP File Path**: `marketplace_addons/dist/sa_gov_fixed_assets_18.0.zip` (55 files, ~1.9 MB, module folder at the archive root, no `__pycache__`/`.pyc`/`.DS_Store`)
22. **Installation Command**:
    ```bash
    ./odoo-bin -d yourdb -i sa_gov_fixed_assets --stop-after-init
    ```
23. **Upgrade Command**:
    ```bash
    ./odoo-bin -d yourdb -u sa_gov_fixed_assets --stop-after-init
    ```
24. **Release Checklist**:
    - [x] Clean install on an empty database (no parse errors, no missing external IDs, all 1,636 classification rows load)
    - [x] Module upgrade (`-u`) on top of an existing install
    - [x] Clean uninstall verified (`button_immediate_uninstall`), then reinstalled cleanly
    - [x] Full automated test suite passing (11/11 methods), both scoped and inside the unfiltered core suite
    - [x] Quick Scan (barcode/QR/RFID) verified live in a real browser session, including the "unknown code" path
    - [x] Manual verification in a real browser: list/kanban/form views, the مرسملة/غير مرسملة determination for multiple asset families (land, IT equipment, furniture, vehicle, heritage), MOF asset code generation, depreciation schedule + posting, a physical verification campaign with a discrepancy, all 3 printable reports via the HTML-report-route workaround (no `wkhtmltopdf` in this dev environment)
    - [x] `ir.model.access.csv` and record rules reviewed for least privilege (4-tier group hierarchy, base User group is read-only + verification data entry)
    - [x] Price set to 30.0 EUR, license OPL-1, `application: True`, `installable: True`
    - [x] Real screenshots and a real banner captured/composited from the running app (not placeholders), per house convention
    - [ ] Arabic i18n `.po` translation file — not yet built; most user-facing data (classification names, demo content) is already bilingual/Arabic, but UI field labels are English-only in code
    - [ ] PDF (as opposed to HTML-preview) report rendering — not verifiable in this environment (no `wkhtmltopdf`); recommend one manual check before the actual store upload
    - [ ] Full componentization, fair-value revaluation wizards, impairment workflow — explicitly deferred to v2, documented in the plan file

**This module is functionally complete, real-screenshot-verified, and packaged**, but is not yet 100% store-upload-ready: the `i18n/ar.po` file is still outstanding, and PDF report rendering should get one manual pass on an environment with `wkhtmltopdf` installed before the actual store upload. See `/Users/mohamedtouny/.claude/plans/majestic-skipping-pudding.md` for full architecture detail and the documented v2 scope.
