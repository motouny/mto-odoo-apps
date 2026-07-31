# Secure Digital Signature Workflow

Internal electronic signature workflow with an audit trail and document
verification, for Odoo 18. This is **not** a government-certified or
legally-qualified electronic signature service - it is a self-hosted
document signing workflow you fully control.

- **Technical name**: `secure_digital_signature`
- **Version**: 18.0.1.0.0
- **License**: OPL-1
- **Price**: €30
- **Author**: MTO
- **Dependencies**: `base`, `mail`, `portal`, `web` (all standard Odoo Community modules)

## What it does

- Upload a PDF and add internal, portal or fully external signers.
- Place Signature / Initials / Name / Date / Text / Checkbox / Selection /
  Stamp fields on the document (page number + X/Y/width/height as
  percentages of the page, edited from a simple field list rather than a
  drag-and-drop designer - see **Known limitations** below).
- Sequential or parallel signing order, with expiration and reminders.
- Each signer gets a single-purpose, cryptographically random signing
  token (`secrets.token_urlsafe`), revoked the moment the request is
  rejected, cancelled or completed - the token is never the database id.
- The final signed PDF is generated server-side: every field is burned
  into the actual page using **PyPDF2** and **reportlab**, both of which
  are already core Odoo Python dependencies (see
  `odoo/requirements.txt`) - this app does not add a single new external
  dependency.
- SHA-256 hashing of both the original and the final document.
- A completion certificate (PDF) listing every signer, timestamp and IP
  address, with a QR code (drawn with reportlab's own QR widget) linking
  to a public verification page that confirms validity **without**
  exposing any signer's name, email or IP to the public.
- A full, immutable audit trail (`digital.signature.event`) - every view,
  field fill, signature, rejection, resend and verification attempt is
  logged with a timestamp, IP address and user agent, and cannot be
  edited or deleted by anyone through the UI, including administrators.

## Security model

- Field position/definition (type, page, x/y/width/height, required) is
  frozen the moment a request leaves Draft/Ready - the ORM `write()` and
  `unlink()` on `digital.signature.field` raise an error on any attempt
  to change these after send, with **no** sudo bypass, since the app's
  own code never needs one.
- The original document cannot be replaced once the request has left
  Draft, for the same reason.
- A user only ever sees their own signature requests (`created_by_uid`
  ownership `ir.rule`); a **Manager** group sees every request in their
  company. Multi-company is enforced everywhere.
- The public signer page and the public verification page look records
  up strictly by their own random token - never by database id - so
  neither can be used to enumerate or browse anyone else's request.
- A signed/rejected/expired token cannot be reused to sign again.

## Known limitations

- Field placement is done by entering page number and X/Y/width/height
  percentages in a list, not by dragging a box on a live PDF preview.
  This keeps the app dependency-free and predictable, at the cost of a
  less visual placement experience - a future version may add a visual
  designer.
- This app does not claim any level of legal or regulatory qualification
  (eIDAS, ESIGN Act, etc.). It is a workflow and audit-trail tool, not a
  certified signature provider.

## Support

- Email: support@mto-solutions.com
- Website: https://www.mto-solutions.com
