# Installation

## Requirements

- Odoo 18.0 (Community or Enterprise)
- No new external Python packages - `PyPDF2` and `reportlab` are already
  part of Odoo's own `requirements.txt`.

## Steps

```bash
./odoo-bin -d yourdb -i secure_digital_signature --stop-after-init
```

Then go to **Apps**, search **Secure Digital Signature Workflow**, and
confirm it shows as installed (or install from there directly instead of
the command line).

## Upgrade

```bash
./odoo-bin -d yourdb -u secure_digital_signature --stop-after-init
```

## Post-install configuration

1. Assign the **User** group (`Digital Signature / User`) to anyone who
   should be able to create and send signature requests.
2. Assign the **Manager** group to anyone who should see every request
   in the company, not just their own.
3. Optional: create reusable **Templates** under **Digital Signature ->
   Configuration -> Templates** with a pre-defined field layout.

## Uninstall

Uninstalling removes all requests, documents, signers, fields and the
audit trail. Export anything you need to keep before uninstalling.
