{
    'name': 'Employee & Client Self-Service Portal - Payslips',
    'version': '18.0.2.0.0',
    'category': 'Human Resources',
    'summary': 'Adds My Payslips to the Employee & Client Self-Service Portal (requires Payroll / Enterprise)',
    'description': """
Employee & Client Self-Service Portal - Payslips
==================================================
Optional add-on for `employee_client_self_service_portal`. Only installable where
`hr_payroll` is available (Odoo Enterprise or Odoo.sh) - kept as a
separate module so the base portal (Profile, Time Off, Attendance,
My Team, My Assignments) installs cleanly on Community, where
`hr_payroll` does not exist.

* My Payslips - view and download finalized payslips from the portal
""",
    'author': 'MTO',
    'price': 29.0,
    'currency': 'EUR',
    'support': 'support@mto-solutions.com',
    'category': 'Human Resources',
    'summary': 'Adds My Payslips to the Employee & Client Self-Service Portal (requires Payroll / Enterprise)',
    'description': """
Employee & Client Self-Service Portal - Payslips
==================================================
Optional add-on for `employee_client_self_service_portal`. Only installable where
`hr_payroll` is available (Odoo Enterprise or Odoo.sh) - kept as a
separate module so the base portal (Profile, Time Off, Attendance,
My Team, My Assignments) installs cleanly on Community, where
`hr_payroll` does not exist.

* My Payslips - view and download finalized payslips from the portal
""",
    'author': 'MTO',
    'images': ['static/description/banner.png'],
    'depends': ['employee_client_self_service_portal', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'security/employee_client_self_service_portal_payroll_security.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'license': 'OPL-1',
}
