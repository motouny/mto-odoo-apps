/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.EmployeeSelfPortalAttendance = publicWidget.Widget.extend({
    selector: "#o_attendance_toggle_btn",
    events: {
        click: "_onToggleClick",
    },

    async _onToggleClick(ev) {
        const button = ev.currentTarget;
        button.disabled = true;
        try {
            const result = await rpc("/my/attendances/toggle", {});
            if (result.attendance_state === "checked_in") {
                button.textContent = "Check Out";
            } else {
                button.textContent = "Check In";
            }
            window.location.reload();
        } finally {
            button.disabled = false;
        }
    },
});

export default publicWidget.registry.EmployeeSelfPortalAttendance;
