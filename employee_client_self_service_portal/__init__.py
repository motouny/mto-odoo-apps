from . import models
from . import controllers


def post_init_hook(env):
    """hr_holidays ships Sick Time Off with leave_validation_type='hr'
    (its own noupdate="1" record, so a plain XML <record> override is
    silently ignored on install/upgrade). Set it here instead so the
    client's Portal Manager gets a first-approval step, same as Paid
    Time Off/Unpaid, with internal HR finalizing from the backend."""
    sick_leave_type = env.ref('hr_holidays.holiday_status_sl', raise_if_not_found=False)
    if sick_leave_type and sick_leave_type.leave_validation_type != 'both':
        sick_leave_type.leave_validation_type = 'both'
