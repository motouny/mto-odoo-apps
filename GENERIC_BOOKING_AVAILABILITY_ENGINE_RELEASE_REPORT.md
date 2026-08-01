# Final Release Report

1. **Application Name**: Generic Booking & Availability Engine
2. **Technical Name**: `generic_booking_availability_engine`
3. **Version**: 18.0.1.0.0
4. **Price**: 30.0
5. **Currency**: EUR
6. **License**: OPL-1
7. **Dependencies**: `base`, `mail`, `portal`, `product`, `sale` (all standard Odoo Community modules; no Enterprise-only module, no other paid or custom app required)
8. **Models Created**: `booking.resource.category`, `booking.resource`, `booking.availability`, `booking.pricing.rule`, `booking.cancellation.policy` + `booking.cancellation.policy.line`, `booking.order` + `booking.order.line`, `booking.availability.generator` (transient wizard)
9. **Views Created**: List/kanban/form/search for resources, categories, pricing rules, cancellation policies; list/form/calendar for availability; list/kanban/form/search for booking orders with a guarded status-bar workflow; a bulk-availability-generator wizard; portal templates (My Bookings card, list, detail); app menus
10. **Security Groups**: Booking Operator (creates/manages bookings, read-only on resource configuration), Booking Manager (full configuration access, auto-assigned to `base.user_admin`). Portal customers are granted access directly through Odoo's standard `base.group_portal` (see item 15 — no custom portal group)
11. **Record Rules**: Multi-company rules on `booking.resource` and `booking.order`; portal-own-records rules on `booking.order`/`booking.order.line` scoped to `base.group_portal` via `partner_id child_of` the logged-in partner
12. **Reports**: Booking Voucher (QWeb, `binding_type: report` on `booking.order`)
13. **Automated Tests**: 8 test methods in `tests/test_booking_order.py` — sequence assignment, pricing-rule resolution by priority/date-range, the capacity guard blocking an overbooking attempt, the full draft→paid→pending-supplier-confirmation→confirmed→completed workflow, an invalid-transition guard, cancellation refund-percentage calculation (both a full-refund and a partial-refund case against the cancellation policy), and the max-quantity-per-booking constraint
14. **Test Results**: `0 failed, 0 error(s)` of the module's own test suite, run both scoped (`--test-tags /generic_booking_availability_engine`) and as part of the full unfiltered Odoo core `--test-enable` suite (3765 tests across every installed Community + Enterprise module). The unfiltered run showed `20 failed, 5 error(s)` overall — grepped the full log line-by-line and confirmed every one of them is a pre-existing environment limitation unrelated to this module: no `wkhtmltopdf` binary installed (PDF-conversion tests in `base`/`account_edi_ubl_cii`/`account`), `phonenumbers` library version drift (`phone_validation`), flaky `mail`/`discuss` subtests, and one CLI `test_configmanager` test. None of the 25 failures/errors are in `generic_booking_availability_engine`.
15. **Fixed during QA (pre-release)** — found only by actually clicking through a running instance, not by the automated tests:
    - `booking.availability` had no display name override, so the availability calendar rendered the literal internal string `booking.availability,1` instead of a readable label. Fixed with a `_compute_display_name` (`"<resource name> - <date>"`).
    - **Portal access design bug**: the module originally defined its own `group_booking_portal` group (implying `base.group_portal`) and granted `booking.order`/`booking.order.line` read access + the portal-own record rules to that custom group instead of directly to `base.group_portal`. Since real portal customers are never manually added to a module-specific group, this meant a genuine customer would never see their own bookings at all — the "Bookings" card would never appear on their portal home page. Found by logging in as an actual portal-group customer (not just admin) and seeing the card silently missing. Fixed by granting access directly to `base.group_portal`, matching the same pattern core `sale`/`account` use (`access_sale_order_portal ... base.group_portal`); the redundant custom group was removed entirely.
    - The portal booking detail controller passed the record into the template context via `_get_page_view_values`, which sets the key `object`, but the `portal_my_booking` QWeb template was written against a variable named `order` — every `t-out="order.xxx"` raised `KeyError: 'order'`, producing a real 500 on `/my/bookings/<id>` for every customer. Fixed by explicitly passing `'order': order_sudo` in the values dict.
    - All three fixes verified live: re-logged in as a real portal customer (a temporary test user against the `Acme Corporation` demo partner, removed after verification) and walked the full loop — portal home card now appears, bookings list shows the real booking, detail page renders lines/total, "Request Cancellation" transitions the order to `cancelled_by_customer` and computes the correct 100% refund from the `Flexible` cancellation policy, and the booking voucher PDF report content renders correctly (verified via the HTML-preview report route, since `wkhtmltopdf` isn't installed in this dev environment — see [[project-odoo-dev-environment]]).
16. **Community Compatibility**: Full — installs and runs on Odoo 18 Community with only `base`/`mail`/`portal`/`product`/`sale`.
17. **Enterprise Compatibility**: Fully compatible; no Enterprise-only feature is used or required.
18. **External Python Dependencies**: None.
19. **Data**: `data/ir_sequence_data.xml` (booking order reference sequence, `BK/%(year)s/00000`), `data/mail_template_data.xml` (booking confirmation email template). `demo/demo_data.xml` — 3 resource categories, a Flexible and a Strict cancellation policy, 4 bookable resources (2 hotel rooms, a transfer vehicle, a guide), a seasonal pricing rule, a blackout date, and 3 demo booking orders in different states (confirmed, completed, draft) against 3 different demo partners.
20. **Store Assets**: `static/description/index.html` (English marketing copy, `<meta charset="utf-8"/>` as the first line), `static/description/icon.png` (MTO brand icon, reused byte-for-byte from the brand kit per house convention, `web_icon` set on the root menu), 12 real screenshots in `static/description/screenshots/` captured from an actually-running instance (backend list/kanban/form/calendar views and the customer portal, including the live cancellation-and-refund flow) — none are mockups or placeholders. `banner.png`/`cover.png` are **not** included — per established process these are composited separately (by the user or a designer) and are not auto-generated; do not add an `'images'` manifest key until they exist.
21. **ZIP File Path**: `marketplace_addons/dist/generic_booking_availability_engine_18.0.zip` (66 files, ~680 KB, module folder at the archive root, no `__pycache__`/`.pyc`/`.DS_Store`)
22. **Installation Command**:
    ```bash
    ./odoo-bin -d yourdb -i generic_booking_availability_engine --stop-after-init
    ```
23. **Upgrade Command**:
    ```bash
    ./odoo-bin -d yourdb -u generic_booking_availability_engine --stop-after-init
    ```
24. **Release Checklist**:
    - [x] Clean install on a fresh database alongside the full Community + Enterprise addons path (no parse errors, no missing external IDs)
    - [x] Module upgrade (`-u`) applied twice during QA to pick up bug fixes, both clean
    - [x] Full automated test suite passing (8/8 methods), both scoped and inside the unfiltered core suite
    - [x] Manual verification in a real browser: bookings list/kanban/form with guarded status-bar buttons, resource form with pricing-rules/availability tabs, availability calendar, cancellation policy form, bulk-availability-generator wizard entry point
    - [x] Portal verified as a real portal-group customer (not just admin): the Bookings card, list, detail page, live "Request Cancellation" → automatic refund calculation, and the PDF voucher report content
    - [x] Three real bugs found via click-through (not caught by unit tests) fixed and re-verified: calendar display name, portal access group design, template variable mismatch causing a 500
    - [x] `ir.model.access.csv` and record rules reviewed for least privilege; portal access follows the same pattern as core `sale`/`account` (`base.group_portal` directly, no redundant custom group)
    - [x] Price set to 30.0 EUR, license OPL-1, `application: True`, `installable: True`
    - [x] Real screenshots captured from the running app (not placeholders), per house convention
    - [ ] `banner.png` / `cover.png` — pending, handled separately (not auto-generated)
    - [ ] `i18n/ar.po` Arabic translation file — not yet built
    - [ ] PDF (as opposed to HTML-preview) report rendering — not verifiable in this environment (no `wkhtmltopdf`); recommend one manual check before the actual store upload

**This module is functionally complete, real-screenshot-verified (including three real bugs found and fixed through actual browser click-through, not just unit tests), and packaged**, but is not yet 100% store-upload-ready: banner/cover artwork and the Arabic `.po` file are still outstanding, and PDF report rendering should get one manual pass on an environment with `wkhtmltopdf` installed before the actual store upload.

See `/Users/mohamedtouny/Projects/Travel/ARCHITECTURE.md` for how this module fits into the broader Travel/Hajj/Umrah platform decomposition (Track A, item A1 — the foundation the rest of the platform is built on).
