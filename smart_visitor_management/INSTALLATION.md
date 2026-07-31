# Installation

## Requirements

- Odoo 18.0 (Community or Enterprise)
- No external Python packages beyond what Odoo 18 already ships with
  (the module uses Odoo's own `qrcode`-based barcode report route; it
  does not add any new `external_dependencies`).

## Steps

1. Copy the `smart_visitor_management` folder into an addons path that
   your Odoo instance loads (e.g. your `addons_path` custom directory).
2. Restart the Odoo server so it picks up the new module.
3. Go to **Apps**, remove the "Apps" filter, search for
   **Smart Visitor Management**, and click **Install**.
4. Optional: install with demo data (`-d yourdb -i smart_visitor_management`
   without `--without-demo`) to get a ready-made set of locations, gates,
   hosts, guests and visits in different states for evaluation.

Command line equivalent:

```bash
./odoo-bin -d yourdb -i smart_visitor_management --stop-after-init
```

## Upgrade

```bash
./odoo-bin -d yourdb -u smart_visitor_management --stop-after-init
```

## Post-install configuration

1. Go to **Visitor Management → Configuration → Locations** and create
   your site(s).
2. Go to **Configuration → Gates** and attach at least one gate to each
   location.
3. Go to **Configuration → Hosts** and create a host record for every
   employee who will receive visitors (optionally linked to their
   internal user).
4. Go to **Settings → Visitor Management** to review the default entry
   grace period, whether manager approval is required, and whether
   overdue visits auto-expire.
5. Assign the relevant security group to each user under
   **Settings → Users** (Host Employee, Receptionist, Security Officer,
   Visitor Manager, Auditor).

## Uninstall

Uninstalling from **Apps** removes all module data (visits, guests,
locations, gates, blacklist entries, scan logs). Export anything you
need to keep before uninstalling.
