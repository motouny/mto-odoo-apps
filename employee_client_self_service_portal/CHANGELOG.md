# Changelog

## 18.0.3.0.1 (2026-07-15)

- Added the MTO publisher icon (`static/description/icon.png`) and set
  `web_icon` on the app's root menu so it shows the branded icon in Odoo's
  home menu / app switcher, not just the Apps Store listing. Previously
  `static/description/icon.png` alone was not enough - Odoo's app switcher
  reads the root `<menuitem>`'s `web_icon` attribute separately, so the app
  showed the generic default icon even with a real icon.png present.

## 18.0.3.0.0 (2026-07-13)

- Added a general-purpose request system (`ess.request` and related
  models): permission, attendance correction, overtime, letter/certificate,
  data change, equipment/custody, internal support and client service
  requests, each with a full state machine, immutable status history,
  comments, in-portal notifications and email updates.
- Added a dedicated **Client** group for true external self-service,
  separate from the existing project-scoped Portal Manager role.
- Added a **Request Manager** group and a new backend app ("Employee &
  Client Requests") for staff triage, with basic pivot/graph reporting.
- Fixed: `_get_managed_projects()` / `_get_managed_employees()` are now
  explicitly scoped to the current user's allowed companies.
- Fixed: tampered/unauthorized team approval attempts now show an error
  message instead of silently doing nothing.
- Added demo data linking the existing Portal Manager / Portal Project /
  Team Task features to real demo records (previously untested by demo
  data).
- Completed the remaining untranslated Arabic strings and added
  translations for all new request-system strings.
- Refreshed the Odoo Apps Store listing with real, freshly captured
  screenshots covering the new request system end to end (employee,
  client and staff views).

## 18.0.2.0.0 (previous)

- Paid app metadata (price, support, license) and manifest fixes.

## 18.0.1.0.0 (initial)

- Employee self-service (Profile, Time Off, Attendances, Tasks,
  Assignments) and project-scoped Portal Manager (Team, Approvals, Team
  Tasks).
