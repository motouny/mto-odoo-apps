{
    'name': 'Employee & Client Self-Service Portal',
    'version': '18.0.3.0.1',
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

General request system (employee and client)
----------------------------------------------
* Employees and true external clients can submit typed requests
  (permission, attendance correction, overtime, letter/certificate,
  data change, equipment/custody, internal support, ...) with priority,
  attachments, comments and a full status history
  (Draft -> Submitted -> Under Review -> Waiting for Information ->
  Approved/Rejected -> In Progress -> Completed -> Closed, or Cancelled)
* In-portal notifications on every status change
* A rating prompt once a request is closed
* Backend triage for staff: My Tickets, Team Queue, Overdue, plus basic
  reports (by status, by type, by employee/client)

Client self-service (new, separate from the existing Portal Manager role)
----------------------------------------------------------------------------
* A dedicated Client group for external company contacts to submit and
  track their own requests, without seeing employee HR data

Branding automatically follows the installing company's own name and
logo - no fixed color scheme is imposed, so the portal matches your
existing website theme.

Install the separate `employee_client_self_service_portal_payroll`
add-on for a "My Payslips" page on top of this (requires Odoo
Enterprise's Payroll app).
""",
    'author': 'MTO',
    'price': 49.0,
    'currency': 'EUR',
    'support': 'support@mto-systems.com',
    'images': ['static/description/banner.png'],
    'depends': ['portal', 'hr', 'hr_holidays', 'hr_attendance', 'project', 'mail'],
    'data': [
        'security/ess_request_security.xml',
        'security/ir.model.access.csv',
        'security/employee_client_self_service_portal_security.xml',
        'data/hr_leave_type_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        'data/ess_request_sequence_data.xml',
        'data/ess_request_type_data.xml',
        'data/ess_mail_template_data.xml',
        'views/hr_employee_views.xml',
        'views/project_project_views.xml',
        'views/res_company_views.xml',
        'views/portal_templates.xml',
        'views/ess_request_views.xml',
        'views/ess_request_type_views.xml',
        'views/ess_request_team_views.xml',
        'views/ess_portal_templates.xml',
        'views/ess_menus.xml',
    ],
    'demo': [
        'data/portal_manager_demo.xml',
        'data/employee_portal_task_demo.xml',
        'data/ess_request_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'employee_client_self_service_portal/static/src/js/attendance_widget.js',
            'employee_client_self_service_portal/static/src/js/task_countdown.js',
            'employee_client_self_service_portal/static/src/scss/employee_client_self_service_portal.scss',
        ],
        'web.assets_backend': [
            'employee_client_self_service_portal/static/src/js/attendance_zone_map_field.js',
            'employee_client_self_service_portal/static/src/js/attendance_zone_map_field.xml',
            'employee_client_self_service_portal/static/src/scss/attendance_zone_map_field.scss',
        ],
    },
    'installable': True,
    'license': 'OPL-1',
    'post_init_hook': 'post_init_hook',
}
