# Changelog

## 18.0.1.0.1 (2026-07-15)

- Added the MTO publisher icon (`static/description/icon.png`) and set
  `web_icon` on the app's root menu so it shows the branded icon in Odoo's
  home menu / app switcher, not just the Apps Store listing.

## 18.0.1.0.0 (2026-07-13)

Initial release.

- Signature requests with sequential or parallel signers (internal,
  portal, or fully external).
- Signature/Initials/Name/Date/Text/Checkbox/Selection/Stamp field
  placement.
- Cryptographically random, single-purpose signing tokens with expiry,
  revocation and reuse prevention.
- Server-side PDF field burn-in and completion certificate generation
  using PyPDF2 and reportlab (both already core Odoo dependencies).
- SHA-256 hashing of the original and final document.
- Public, privacy-preserving document verification page with QR code.
- Immutable audit trail (view/sign/reject/resend/reminder/verification
  events, each with IP address and user agent).
- Expiration and reminder cron jobs.
- Multi-company, English and Arabic.
- Demo data includes a fully completed request generated through the
  real signing engine at install time.
