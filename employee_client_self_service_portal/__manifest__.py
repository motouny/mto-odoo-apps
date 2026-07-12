{
    'name': 'Employee & Client Self-Service Portal',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Employee HR self-service and client-side team oversight, entirely from the portal',
    'description': """
Employee & Client Self-Service Portal
======================================
Give employees who don't need a full internal Odoo license a self-service
area under /my, and give an external client contact (e.g. a project owner
or account manager) a lightweight portal role to oversee the employees
working on their project - no extra Odoo licenses required on either side.

Employee self-service
----------------------
* My Profile - edit private contact / emergency information
* My Time Off - view balances, submit and cancel leave requests
* My Attendances - check in/out, view monthly attendance
* My Tasks - read-only list of project tasks assigned to the employee
* My Assignments - accept lightweight tasks assigned by the project's
  Portal Manager and post status updates; unfinished ones get a daily
  email reminder until marked done

Client-side Portal Manager (project-scoped, portal-only)
----------------------------------------------------------
* My Team - card-grid view of a project's employees with today's status
  (present / on leave / on permission / absent)
* Time off approvals - first-stage approval on the employees' requests
  before internal HR finalizes them (two-stage validation)
* Team Tasks - assign lightweight tasks with a deadline to the project's
  employees and track their progress

Branding automatically follows the installing company's own name and
logo - no fixed color scheme is imposed, so the portal matches your
existing website theme.

Install the separate `employee_client_self_service_portal_payroll`
add-on for a "My Payslips" page on top of this (requires Odoo
Enterprise's Payroll app).
""",
    'author': 'Custom',
    'depends': ['portal', 'hr', 'hr_holidays', 'hr_attendance', 'project', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/employee_client_self_service_portal_security.xml',
        'data/hr_leave_type_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_employee_views.xml',
        'views/project_project_views.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'employee_client_self_service_portal/static/src/js/attendance_widget.js',
            'employee_client_self_service_portal/static/src/scss/employee_client_self_service_portal.scss',
        ],
    },
    'installable': True,
    'license': 'OPL-1',
    'post_init_hook': 'post_init_hook',
}
