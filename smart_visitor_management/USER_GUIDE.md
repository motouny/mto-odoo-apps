# User Guide

## Roles

| Group | Typical user | Can do |
|---|---|---|
| Visitor User | Any employee | Read-only view of visits at their company |
| Host Employee | Employee expecting guests | Create/submit/cancel their own visits only |
| Receptionist | Front desk | Create/manage any visit, manual check-in/out, send invitations, print badges |
| Security Officer | Gate/security staff | Use the Check-In Kiosk (QR scan or manual token), view scan log |
| Visitor Manager | Facilities/security manager | Approve/reject visits, manage locations, gates, hosts, badge templates, blacklist, settings |
| Auditor | Compliance/audit | Read-only access to everything, including the scan log and blacklist |
| Administrator | App owner | Everything (implied from Visitor Manager) |

## Creating and approving a visit

1. **Visitor Management → Visits → New**. Fill in the primary guest,
   host, location, purpose and time window.
2. Click **Submit for Approval**.
3. If your company requires approval (default), a Visitor Manager
   reviews it under **Pending Approval** and clicks **Approve** or
   **Reject** (with a reason).
4. On approval, a random QR check-in token is generated and (if the
   guest has an email) an approval notification is sent.
5. Optionally click **Send Invitation** at any point before check-out to
   email the guest a link where they can complete their own details
   (identity, photo, vehicle) without needing an Odoo account.

## Checking a guest in/out

- **At the gate (kiosk)**: go to **Check-In Kiosk**, choose Check In or
  Check Out, then either **Scan QR Code** (uses the device camera) or
  type the token manually and press Submit.
- **From the visit form**: a Receptionist, Security Officer or Manager
  can also use the **Check In** / **Check Out** buttons directly on the
  visit record.
- Every scan attempt - successful or not - is recorded in the
  **Scan Log** tab with the reason (invalid token, expired, outside the
  allowed window, blacklisted, etc.).

## Blacklist

Visitor Managers (and Receptionists for creation) can add a guest to
**Blacklist** by identity type + number. Any visit for a blacklisted
identity is automatically moved to the *Blacklisted* state on approval
or check-in, and the check-in is refused.

## Badges and vehicle permits

From an approved/checked-in visit, click **Print Badge** for a PDF
visitor badge (with photo and QR code) or **Vehicle Permit** if a
vehicle was registered on the visit.

## Reports

**Reports → Checkpoint Scan Log** lists every scan attempt company-wide,
filterable by result and groupable by gate - useful for security
reviews and troubleshooting.

## Privacy note

The public self-registration link only ever looks up a visit by its own
random token - it never accepts or exposes a database id, and it cannot
be used to browse or guess any other visitor's data.
