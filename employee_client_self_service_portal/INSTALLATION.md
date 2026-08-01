# Installation

## Requirements

- Odoo 18.0 (Community or Enterprise)
- Depends on standard Odoo modules only: `portal`, `hr`, `hr_holidays`,
  `hr_attendance`, `project`, `mail`. No external Python packages.

## Steps

1. Copy the `employee_client_self_service_portal` folder into an addons
   path your Odoo instance loads.
2. Restart the Odoo server.
3. Go to **Apps**, search **Employee & Client Self-Service Portal**, click
   **Install**.

```bash
./odoo-bin -d yourdb -i employee_client_self_service_portal --stop-after-init
```

## Upgrade

```bash
./odoo-bin -d yourdb -u employee_client_self_service_portal --stop-after-init
```

## Post-install configuration

1. On each employee you want to self-serve, use **Grant Portal Access**
   from their form (Employees app) to create/link their portal user.
2. On a project, set **Portal Manager** to the portal user who should
   oversee that project's team; set each team member's **Portal Project**
   to the same project.
3. Under **Settings -> Users**, assign the **Client** group to any
   external contact who should get their own request self-service area,
   and **Request Manager** to internal staff who will triage requests
   under the new **Employee & Client Requests** app.
4. Optional: adjust **Employee & Client Requests -> Configuration ->
   Request Types / Teams** to your own categories.

## Uninstall

Uninstalling removes all module data: requests, comments, status history,
notifications, portal tasks and the security groups/rules this module
added. Leave (`hr.leave`) and attendance data belonging to the core `hr`
modules are not removed. Export anything you need to keep first.
