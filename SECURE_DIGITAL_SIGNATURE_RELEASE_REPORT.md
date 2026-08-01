# Final Release Report

1. **Application Name**: Secure Digital Signature Workflow
2. **Technical Name**: `secure_digital_signature`
3. **Version**: 18.0.1.0.1 (2026-07-15: added the MTO publisher icon and set `web_icon` on the root menu so the app switcher shows the branded icon, not just the Apps Store listing - see `CHANGELOG.md`)
4. **Price**: 30.0
5. **Currency**: EUR
6. **License**: OPL-1
7. **Dependencies**: `base`, `mail`, `portal`, `web` (standard Odoo Community modules only; no other paid or custom app required)
8. **Models Created**: `digital.signature.request`, `digital.signature.document`, `digital.signature.signer`, `digital.signature.field`, `digital.signature.event`, `digital.signature.template`, `digital.signature.template.field`, `digital.signature.verification`
9. **Views Created**: Request form/list/search (with an inline signer list and a "Fields" popup for per-signer field placement), Template form/list, Audit Trail list/search, 2 public QWeb portal templates (signing page, verification page), backend menus.
10. **Security Groups**: **User** (`group_signature_user`, implies `base.group_user`) and **Manager** (`group_signature_manager`, implies User, auto-granted to `base.user_admin`).
11. **Record Rules**: Ownership (`created_by_uid = uid`) + manager-sees-all + multi-company on `digital.signature.request` and all 4 of its child models (document/signer/field/event); a multi-company rule on `digital.signature.template`.
12. **Portal Routes**: `/sign/<token>` (+ `/submit`, `/reject`, `/download/<original|final>`), `/sign/verify/<verification_token>` - all `auth='public'`, looked up strictly by random token, never by database id.
13. **Reports**: None via Odoo's QWeb report engine - the Final Signed PDF and Completion Certificate are generated programmatically (PyPDF2 + reportlab) and stored as `digital.signature.document` records, downloadable like any other attachment.
14. **Cron Jobs**: `Digital Signature: Expire Overdue Requests` (hourly), `Digital Signature: Send Reminders` (daily).
15. **Automated Tests**: 21 tests across `test_digital_signature_request.py` (sequential/parallel completion, required-field enforcement, rejection revokes all tokens, signed-token reuse prevention, field-definition lock after send, original-document lock after draft, cancel revokes tokens, expiry cron), `test_digital_signature_security.py` (ownership isolation, manager sees all, cross-user write denial, immutable audit trail even for admin), `test_portal_signing.py` (`HttpCase` - valid/invalid token, id-guessing prevention, verification page for both found/not-found/valid states).
16. **Test Results**: `0 failed, 0 error(s) of 21 tests`, verified on the working tree, after every fix, and again on a fresh extraction of the final shipped ZIP into an independent addons path with its own database - all three runs clean.
17. **Known Limitations**:
    - Field placement is done via page number + X/Y/width/height percentages in a list/popup, not a drag-and-drop visual PDF designer.
    - No claim of legal/regulatory certification (eIDAS, ESIGN Act, etc.) - explicitly disclaimed in the manifest, README and store listing as an internal workflow and audit tool.
    - No `wkhtmltopdf` is installed in this development environment, but this app does not need it: the signed PDF and certificate are generated directly with PyPDF2/reportlab, verified to work correctly (real hashes, real field burn-in, a real scannable QR code) by rendering the actual generated demo files with `pdftoppm` during this build and visually inspecting them.
18. **Community Compatibility**: Full - no Enterprise-only feature is used.
19. **Enterprise Compatibility**: Fully compatible.
20. **External Python Dependencies**: **None.** `PyPDF2` and `reportlab` are already core Odoo dependencies (`odoo/requirements.txt`); no new package was added.
21. **Store Assets**: `static/description/index.html`, `README.md`, `USER_GUIDE.md`, `INSTALLATION.md`, `SUPPORT.md`, `LICENSE`, `CHANGELOG.md`, 7 real screenshots captured from the running demo database (including a genuine rendered completion certificate with a scannable QR code). `banner.png`/`icon.png`/`cover.png` are intentionally not included, per the project owner's standing decision for this session - to be supplied separately.
22. **ZIP File Path**: `marketplace_addons/dist/secure_digital_signature_18.0.zip` (66 files, ~772 KB, module folder at the archive root, no `__pycache__`/`.pyc`/`.DS_Store`/database dumps; rebuilt 2026-07-15 with the MTO icon and `web_icon` fix).
23. **Installation Command**:
    ```bash
    ./odoo-bin -d yourdb -i secure_digital_signature --stop-after-init
    ```
24. **Upgrade Command**:
    ```bash
    ./odoo-bin -d yourdb -u secure_digital_signature --stop-after-init
    ```
25. **Release Checklist**:
    - [x] Clean install on an empty database (no parse errors, no missing external IDs)
    - [x] Module upgrade (`-u`) on top of an existing install
    - [x] Full automated test suite passing (21/21), including on the final extracted ZIP
    - [x] Clean uninstall verified on a test database
    - [x] Manual verification in a real browser: request builder, sequential signer activation, public signing page (real signature-pad canvas), field placement popup, audit trail, public verification page
    - [x] The actual generated final PDF and completion certificate were downloaded and rendered to images (`pdftoppm`) and visually confirmed correct - real field burn-in, a real SHA-256 hash pair, and a real scannable QR code
    - [x] Two real bugs found and fixed during manual QA: (1) the field-lock guard exempted `env.su`, which meant it silently did nothing in the exact context (superuser) most tests run in - tightened to have no exception, since the app's own code never needs one; (2) the per-signer field-placement sub-form was defined but structurally unreachable because the parent signer list used `editable="bottom"` (inline edit always wins over the popup form) - added an explicit "Fields" button with a dedicated action/view so the feature is actually usable
    - [x] `ir.model.access.csv` and record rules reviewed for least privilege (a user can create/manage their own requests but never see another user's; the public controller never accepts a database id, only random tokens)
    - [x] Price set to 30.0 EUR, license OPL-1, `application: True`, `installable: True`
    - [x] Arabic translation (`i18n/ar.po`, 72 curated high-visibility strings) imported and verified to load without error
    - [ ] `banner.png` / `icon.png` / `cover.png` - pending, to be supplied outside this session
    - [ ] Full 100% Arabic translation coverage - 33% achieved for this string set; a follow-up pass is recommended before the actual store upload if full coverage is required

**This module is functionally complete and test-verified against the real, final shipped ZIP**, including hands-on inspection of the actual generated PDF artifacts (not just database state).
