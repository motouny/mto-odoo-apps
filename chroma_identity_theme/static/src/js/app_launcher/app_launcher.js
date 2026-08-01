/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

// Deterministic accent so the same app always gets the same card color,
// giving the grid visual rhythm without needing per-app category data
// (Odoo's menu service doesn't expose one uniformly across all apps).
const ACCENTS = ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8"];

function hashAccent(key) {
    let hash = 0;
    const str = String(key || "");
    for (let i = 0; i < str.length; i++) {
        hash = (hash * 31 + str.charCodeAt(i)) >>> 0;
    }
    return ACCENTS[hash % ACCENTS.length];
}

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.dgaLauncherState = useState({ query: "" });
    },

    get dgaFilteredApps() {
        const apps = this.menuService.getApps();
        const query = this.dgaLauncherState.query.trim().toLowerCase();
        if (!query) {
            return apps;
        }
        return apps.filter((app) => app.name.toLowerCase().includes(query));
    },

    dgaAppAccent(app) {
        return hashAccent(app.xmlid || app.id);
    },

    onChromaLauncherSearchInput(ev) {
        this.dgaLauncherState.query = ev.target.value;
    },

    get dgaSearchPlaceholder() {
        return _t("Search apps…");
    },

    get dgaNoResultsLabel() {
        return _t("No apps match your search");
    },

    get dgaViewAllAppsLabel() {
        return _t("View All Apps");
    },

    onChromaViewAllApps() {
        // this.actionService is already set by NavBar's own setup() above.
        this.actionService.doAction("chroma_identity_theme.action_chroma_home_menu");
    },
});
