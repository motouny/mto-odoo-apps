/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.EmployeeSelfPortalTaskCountdown = publicWidget.Widget.extend({
    selector: ".o_ess_task_countdown",

    start() {
        this.overdueLabel = this.el.dataset.overdueLabel || "Overdue by %s";
        this.leftLabel = this.el.dataset.leftLabel || "%s left";
        this._tick();
        this.timer = setInterval(this._tick.bind(this), 1000);
        return this._super(...arguments);
    },

    destroy() {
        clearInterval(this.timer);
        this._super(...arguments);
    },

    _tick() {
        const deadline = new Date(this.el.dataset.deadline);
        if (isNaN(deadline.getTime())) {
            return;
        }
        const pad = (n) => String(n).padStart(2, "0");
        const diff = deadline.getTime() - Date.now();
        const overdue = diff < 0;
        const abs = Math.abs(diff);
        const days = Math.floor(abs / 86400000);
        const hours = Math.floor((abs % 86400000) / 3600000);
        const minutes = Math.floor((abs % 3600000) / 60000);
        const seconds = Math.floor((abs % 60000) / 1000);
        const text = (days > 0 ? `${days}d ` : "") + `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
        this.el.textContent = (overdue ? this.overdueLabel : this.leftLabel).replace("%s", text);
        this.el.classList.toggle("text-danger", overdue);
        this.el.classList.toggle("fw-bold", overdue);
        this.el.classList.toggle("text-muted", !overdue);
    },
});

export default publicWidget.registry.EmployeeSelfPortalTaskCountdown;
