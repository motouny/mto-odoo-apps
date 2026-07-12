# Employee & Client Self-Service Portal - Payslips

Optional add-on for **Employee & Client Self-Service Portal** that adds a
"My Payslips" page.

## Requirements

- `employee_client_self_service_portal` (base module)
- `hr_payroll` (Odoo Enterprise)

## What it adds

- A **My Payslips** tile on the portal home and a quick-action button on the
  dashboard.
- `/my/payslips` - list of the employee's finalized (done / paid) payslips.
- `/my/payslips/<id>/download` - streams the payslip PDF report.

Kept as a separate module so the base portal installs cleanly on Odoo
Community, where `hr_payroll` isn't available.
