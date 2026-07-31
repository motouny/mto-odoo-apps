/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Component, useState, useRef, onMounted, useExternalListener } from "@odoo/owl";

// Same deterministic per-app accent as the dropdown launcher
// (app_launcher.js) - kept identical so both surfaces read as one system.
const ACCENTS = ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8"];
function hashAccent(key) {
    let hash = 0;
    const str = String(key || "");
    for (let i = 0; i < str.length; i++) {
        hash = (hash * 31 + str.charCodeAt(i)) >>> 0;
    }
    return ACCENTS[hash % ACCENTS.length];
}

// A full-page "all apps" home screen, matching what Enterprise's own
// Home Menu gives you (a big searchable grid taking over the content
// area) - but built from scratch as an ir.actions.client so it works on
// Community too, not a copy of any Enterprise code. Reached from the
// existing dropdown launcher's "View All Apps" entry (app_launcher.xml),
// which stays as the quick-access surface - this is the deliberate
// "both together" full-page complement, not a replacement.
export class DgaHomeMenu extends Component {
    static template = "sa_dga_theme.DgaHomeMenu";
    static props = ["*"];

    setup() {
        this.menuService = useService("menu");
        this.state = useState({ query: "" });
        this.searchRef = useRef("search");

        onMounted(() => {
            this.searchRef.el?.focus();
        });

        useExternalListener(window, "keydown", (ev) => {
            if (ev.key === "Escape") {
                this.goBack();
            }
        });
    }

    get filteredApps() {
        const apps = this.menuService.getApps();
        const query = this.state.query.trim().toLowerCase();
        if (!query) {
            return apps;
        }
        return apps.filter((app) => app.name.toLowerCase().includes(query));
    }

    accentClass(app) {
        return "o_dga_accent_" + hashAccent(app.xmlid || app.id);
    }

    getHref(app) {
        return `/odoo/${app.actionPath || "action-" + app.actionID}`;
    }

    onAppClick(app) {
        this.menuService.selectMenu(app);
    }

    onSearchInput(ev) {
        this.state.query = ev.target.value;
    }

    goBack() {
        window.history.back();
    }

    get searchPlaceholder() {
        return _t("Search apps…");
    }

    get noResultsLabel() {
        return _t("No apps match your search");
    }

    get closeLabel() {
        return _t("Close");
    }
}

registry.category("actions").add("sa_dga_theme.home_menu", DgaHomeMenu);
