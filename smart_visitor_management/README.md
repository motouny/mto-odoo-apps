# Smart Visitor Management

Manage visitor invitations, approvals, secure QR-based check-in and
check-out, printed visitor badges, vehicle permits, a blacklist and a
live occupancy view - entirely inside Odoo 18.

- **Technical name**: `smart_visitor_management`
- **Version**: 18.0.1.0.0
- **License**: OPL-1
- **Price**: €30
- **Category**: Administration
- **Author**: MTO
- **Dependencies**: `base`, `mail`, `portal`, `web` (all standard Odoo Community modules - no other paid app required)

## Highlights

- Visit invitations with an approval workflow: Draft → Pending Approval →
  Approved/Scheduled → Checked In → Checked Out (plus Rejected, Cancelled,
  Expired, Blacklisted).
- Cryptographically random, single-purpose QR check-in tokens
  (`secrets.token_urlsafe`) with expiry, an allowed entry window, and
  automatic revocation on rejection/cancellation/checkout. The token is
  never the database record id.
- A backend camera-based QR scanner (Check-In Kiosk) that reuses Odoo's
  own barcode detection widget (`@web/core/barcode/barcode_video_scanner`)
  - no third-party JS scanning library - with a manual token-entry
  fallback.
- A public, token-protected self-registration page so an invited guest
  can complete their own details without an Odoo account, and without
  ever being able to see another visit (looked up by token, never by id).
- Vehicle permits, blacklist screening on every check-in attempt, and an
  immutable checkpoint scan audit log (successes and failures alike).
- Printable visitor badge and vehicle permit PDF reports (QR code
  embedded via Odoo's built-in `/report/barcode` route).
- Multi-company, with dedicated security groups: Visitor User, Host
  Employee, Receptionist, Security Officer, Visitor Manager, Auditor,
  Administrator.
- English and Arabic translations, RTL-ready.

## What this module intentionally does not do

- It does not modify Odoo core.
- It does not claim to prevent GPS/QR spoofing beyond standard token
  security (expiry, single company/visit scope, revocation, audit log).
- Group visits currently share one QR token per visit (accompanying
  guests are listed on the same visit rather than each having an
  independent badge/token). This keeps the security model simple and
  auditable; independent per-guest tokens can be a future extension.

## Support

- Email: support@mto-solutions.com
- Website: https://www.mto-solutions.com

See `INSTALLATION.md`, `USER_GUIDE.md` and `CHANGELOG.md` for more detail.
