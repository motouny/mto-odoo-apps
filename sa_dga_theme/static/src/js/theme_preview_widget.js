/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { Component } from "@odoo/owl";

// Keep in sync with DGA_FONT_PAIRS in models/res_company.py.
const DGA_FONT_PAIRS = {
    ibm_plex: { arabic: '"IBM Plex Sans Arabic"', latin: '"IBM Plex Sans"' },
    cairo: { arabic: '"Cairo"', latin: '"Cairo"' },
    tajawal: { arabic: '"Tajawal"', latin: '"Tajawal"' },
    noto_kufi: { arabic: '"Noto Kufi Arabic"', latin: '"IBM Plex Sans"' },
};

// A record-bound (not field-bound) settings widget: renders a small live
// preview card that reacts to every color/font field on the same
// res.config.settings record, so the admin can judge the look before
// saving rather than guessing from hex codes alone.
export class DgaThemePreview extends Component {
    static template = "sa_dga_theme.DgaThemePreview";
    static props = { ...standardWidgetProps };

    get data() {
        return this.props.record.data;
    }

    get fontFamily() {
        const pair = DGA_FONT_PAIRS[this.data.sa_dga_font_pair] || DGA_FONT_PAIRS.ibm_plex;
        return `${pair.arabic}, ${pair.latin}, sans-serif`;
    }

    get previewStyle() {
        const d = this.data;
        const vars = {
            "--dga-preview-primary": d.sa_dga_primary_color || "#046A38",
            "--dga-preview-accent": d.sa_dga_accent_color || "#0B7A45",
            "--dga-preview-heading": d.sa_dga_heading_color || "#111827",
            "--dga-preview-body": d.sa_dga_body_color || "#1F2937",
            "--dga-preview-muted": d.sa_dga_muted_color || "#6B7280",
            "font-family": this.fontFamily,
        };
        return Object.entries(vars)
            .map(([key, value]) => `${key}: ${value}`)
            .join("; ");
    }
}

registry.category("view_widgets").add("sa_dga_theme_preview", {
    component: DgaThemePreview,
});
