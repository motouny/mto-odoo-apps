# Changelog

## 18.0.1.0.3 (2026-07-28)

- Fixed the Visitor Badge print: it now uses its own compact card-sized
  paper format (10 x 14cm, zero margins) instead of the company's default
  A4/Letter format, and skips Odoo's one-time "Configure your document
  layout" onboarding wizard (which shows a generic sample *invoice*
  preview on the very first report print in a company that hasn't set up
  its letterhead yet - easily mistaken for "printing a badge produces an
  invoice"). Also fixed the QR code and badge number overflowing past the
  card's border in the printed layout.
- Added a proper `visitor.department` master-data model (Configuration >
  Departments) with its own list/form view and security. `visitor.visit`
  and `visitor.host` now use a `Department` selection field linked to it
  instead of free text, with the visit's department auto-filled from the
  chosen host.

## 18.0.1.0.2 (2026-07-15)

- Added the MTO publisher icon (`static/description/icon.png`) and set
  `web_icon` on the app's root menu so it shows the branded icon in Odoo's
  home menu / app switcher, not just the Apps Store listing.

## 18.0.1.0.1 (2026-07-15)

- Fixed the Vehicle Permit PDF report: `t-field` was used directly on `<td>`
  elements in the vehicle table, which Odoo's QWeb engine rejects
  (`AssertionError: QWeb widgets do not work correctly on 'td' elements`).
  This crashed the report at render time in a real Odoo instance despite
  passing module install; caught by running Odoo core's own
  `base.tests.test_reports` suite against the module, not by the module's
  own tests. Fields are now wrapped in `<span>` inside each `<td>`.

## 18.0.1.0.0 (2026-07-13)

Initial release.

- Visit invitation and approval workflow.
- Secure random QR check-in/check-out with expiry and revocation.
- Public tokenized guest self-registration page.
- Backend Check-In Kiosk (camera QR scan + manual entry).
- Vehicle permits, blacklist screening, immutable checkpoint scan log.
- Visitor badge and vehicle permit PDF reports.
- Multi-company security groups and record rules.
- English and Arabic translations.
- Demo data set covering all visit states.
