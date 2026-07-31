/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

function getPosition() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve(null);
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (position) => resolve({
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
            }),
            () => resolve(null),
            { enableHighAccuracy: true, timeout: 10000 }
        );
    });
}

publicWidget.registry.EmployeeSelfPortalAttendance = publicWidget.Widget.extend({
    selector: "#o_attendance_toggle_btn",
    events: {
        click: "_onToggleClick",
    },

    async _onToggleClick(ev) {
        const button = ev.currentTarget;
        const resultEl = document.getElementById("o_attendance_toggle_result");
        if (resultEl) {
            resultEl.textContent = "";
            resultEl.classList.remove("text-danger");
        }
        button.disabled = true;
        try {
            const position = await getPosition();
            await rpc("/my/attendances/toggle", position || {});
            window.location.reload();
        } catch (error) {
            if (resultEl) {
                resultEl.textContent = error.data?.message || error.message || "Something went wrong.";
                resultEl.classList.add("text-danger");
            }
            button.disabled = false;
        }
    },
});

export default publicWidget.registry.EmployeeSelfPortalAttendance;
