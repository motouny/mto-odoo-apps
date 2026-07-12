# Employee & Client Self-Service Portal

HR self-service for portal (non-licensed) employees, plus a project-scoped
client "Portal Manager" role, entirely under Odoo's standard `/my` portal.

## Installation

1. Copy this folder into your Odoo addons path.
2. Update the apps list and install **Employee & Client Self-Service Portal**.
3. (Optional) Install **Employee & Client Self-Service Portal - Payslips** as
   well if you're on Odoo Enterprise and want a "My Payslips" page.

## Setup

1. Open an employee's form (Employees app) and click **Grant Portal Access**.
   This creates (or reuses) a portal user for that employee's related
   contact and links it as the employee's user, so they can log in and reach
   `/my`.
2. Open a Project (Project app) and set its **Portal Manager** field to the
   portal user who should oversee that project's employees (e.g. a client
   contact). This field is independent from the internal **Project Manager**
   field above it.
3. On each employee working on that project, set the **Portal Project**
   field (Work Information tab) to that same project.
4. That's it:
   - The employee sees My Profile / My Time Off / My Attendances / My Tasks
     (and My Assignments once they have one) on their portal home.
   - The Portal Manager sees a My Team tile, with a card grid of that
     project's employees and pending approvals.

## Two-stage time off approval

Time off and Permission requests submitted by an employee are first
reviewed by their project's Portal Manager (`/my/team/approvals`). Approving
there moves the request to the second stage, where your internal HR team
finalizes it from the standard Time Off app in the backend. The Portal
Manager is a gatekeeper, not the final approver.

## Daily task reminders

A Portal Manager can assign a lightweight task (title, description,
deadline) to one of their project's employees from `/my/team/tasks`. The
employee accepts it and posts status updates from `/my/assignments`. A daily
scheduled action (`Employee Portal: Assignment Status Reminder`) emails
anyone with an unfinished task until they mark it done.

## Security model

No new security groups are introduced - everything runs on the standard
Portal (`base.group_portal`) user type. All record-level access is enforced
through `ir.rule`s scoped to that group (see
`security/employee_client_self_service_portal_security.xml`), and every
write performed on behalf of a portal user goes through an explicit
controller method that verifies ownership in Python before calling
`sudo()` - the portal group itself is never granted broad write access.

## Branding

The portal banner shown on every `/my/*` page uses your own company's name
and logo (`res.company`) automatically. There is no fixed color palette;
buttons and accents follow Bootstrap's theme variables, so the portal
matches whichever theme color your site already uses.

## Translations

Ships with English (source) and Arabic (`i18n/ar.po`). Users can switch
their portal language from Preferences.
