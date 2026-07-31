/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { Component } from "@odoo/owl";

// Keep in sync with CHROMA_FONT_PAIRS in models/res_company.py.
const CHROMA_FONT_PAIRS = {
    ibm_plex: { arabic: '"IBM Plex Sans Arabic"', latin: '"IBM Plex Sans"' },
    cairo: { arabic: '"Cairo"', latin: '"Cairo"' },
    tajawal: { arabic: '"Tajawal"', latin: '"Tajawal"' },
    noto_kufi: { arabic: '"Noto Kufi Arabic"', latin: '"IBM Plex Sans"' },
};

// A record-bound (not field-bound) settings widget: renders a small live
// preview card that reacts to every color/font field on the same
// res.config.settings record, so the admin can judge the look before
// saving rather than guessing from hex codes alone.
export class ChromaThemePreview extends Component {
    static template = "chroma_identity_theme.ChromaThemePreview";
    static props = { ...standardWidgetProps };

    get data() {
        return this.props.record.data;
    }

    get fontFamily() {
        const pair = CHROMA_FONT_PAIRS[this.data.chroma_font_pair] || CHROMA_FONT_PAIRS.ibm_plex;
        return `${pair.arabic}, ${pair.latin}, sans-serif`;
    }

    // Mirrors _chroma_readable_text_color() in models/res_company.py so the
    // mock navbar/sidebar strip in the preview picks legible text without a
    // round-trip - same luminance formula, same 0.6 threshold.
    readableTextColor(hex) {
        const clean = (hex || "").replace("#", "");
        if (clean.length !== 6) {
            return "#FFFFFF";
        }
        const r = parseInt(clean.slice(0, 2), 16);
        const g = parseInt(clean.slice(2, 4), 16);
        const b = parseInt(clean.slice(4, 6), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance > 0.6 ? "#1A1A1A" : "#FFFFFF";
    }

    get previewStyle() {
        const d = this.data;
        const chrome = d.chroma_chrome_color || "#0A0A0A";
        const vars = {
            "--chroma-preview-primary": d.chroma_primary_color || "#046A38",
            "--chroma-preview-accent": d.chroma_accent_color || "#0B7A45",
            "--chroma-preview-chrome": chrome,
            "--chroma-preview-on-chrome": this.readableTextColor(chrome),
            "--chroma-preview-heading": d.chroma_heading_color || "#111827",
            "--chroma-preview-body": d.chroma_body_color || "#1F2937",
            "--chroma-preview-muted": d.chroma_muted_color || "#6B7280",
            "font-family": this.fontFamily,
        };
        return Object.entries(vars)
            .map(([key, value]) => `${key}: ${value}`)
            .join("; ");
    }
}

registry.category("view_widgets").add("chroma_identity_theme_preview", {
    component: ChromaThemePreview,
});
