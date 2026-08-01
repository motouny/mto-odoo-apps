/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
import { Component, useState, useEffect } from "@odoo/owl";

const STORAGE_KEY = "chroma_identity_theme_sidebar_collapsed";

// A persistent, collapsible left icon rail (VS Code / Slack-style),
// registered as a main_component - the same mechanism the core
// notification manager uses (web/core/notifications/notification_service.js)
// - so it mounts once, body-level, without patching WebClient or its
// template at all. Layout shift is pure CSS (see app_sidebar.scss):
// this component only toggles two <body> classes.
export class AppSidebar extends Component {
    static template = "chroma_identity_theme.AppSidebar";
    static props = {};

    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        // Settings > Chroma Identity > Backend Layout - exposed via
        // ir.http.session_info() (models/ir_http.py) so it's available
        // synchronously at boot, before any ORM call could resolve.
        this.enabled = Boolean(session.chroma_sidebar_enabled);
        this.state = useState({
            collapsed: window.localStorage.getItem(STORAGE_KEY) === "1",
        });

        if (!this.enabled) {
            // Doesn't change during the component's lifetime (a fresh
            // page load is required to pick up the Settings change
            // either way), so a one-time class toggle is enough - no
            // need for the full useEffect below. Without this, the
            // body would still reserve the sidebar's width via padding
            // (app_sidebar.scss) even though nothing renders into it.
            document.body.classList.add("o_chroma_sidebar_disabled");
        }

        useEffect(
            (enabled, collapsed, isSmall) => {
                if (!enabled) {
                    return;
                }
                const classList = document.body.classList;
                classList.toggle("o_chroma_sidebar_collapsed", collapsed);
                classList.toggle("o_chroma_sidebar_hidden", isSmall);
                return () => {
                    classList.remove("o_chroma_sidebar_collapsed", "o_chroma_sidebar_hidden");
                };
            },
            () => [this.enabled, this.state.collapsed, this.env.isSmall]
        );
    }

    get apps() {
        return this.menuService.getApps();
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    isActive(app) {
        return Boolean(this.currentApp && this.currentApp.id === app.id);
    }

    getHref(app) {
        return `/odoo/${app.actionPath || "action-" + app.actionID}`;
    }

    onAppClick(app) {
        this.menuService.selectMenu(app);
    }

    toggleCollapsed() {
        this.state.collapsed = !this.state.collapsed;
        window.localStorage.setItem(STORAGE_KEY, this.state.collapsed ? "1" : "0");
    }

    get toggleLabel() {
        return this.state.collapsed ? _t("Expand sidebar") : _t("Collapse sidebar");
    }

    // One-click "open the full card grid" screen - lives at the top of
    // the sidebar (the app-navigation surface) rather than crammed into
    // the navbar's sections-tabs row, where an earlier attempt landed
    // in an awkward spot next to the current app's tab - found via user
    // feedback on a real screenshot.
    onOpenHomeMenu() {
        this.actionService.doAction("chroma_identity_theme.action_chroma_home_menu");
    }

    get openHomeMenuLabel() {
        return _t("View All Apps");
    }
}

registry.category("main_components").add("chroma_identity_theme.AppSidebar", { Component: AppSidebar });
