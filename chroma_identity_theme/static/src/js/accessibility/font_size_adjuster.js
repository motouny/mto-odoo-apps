/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

const STORAGE_KEY = "chroma_identity_theme_font_scale";
const SCALES = ["", "o_chroma_font_scale_lg", "o_chroma_font_scale_xl"];
const LABELS = ["A", "A+", "A++"];

// Mirrors the font-size adjuster pattern published on Saudi government
// digital service guidelines - a simple, dependency-free floating control,
// present on every frontend/portal page (mounted once on #wrapwrap).
publicWidget.registry.ChromaFontSizeAdjuster = publicWidget.Widget.extend({
    selector: "#wrapwrap",

    start() {
        this._applyStoredScale();
        this._renderControl();
        return this._super(...arguments);
    },

    _applyStoredScale() {
        const stored = window.localStorage.getItem(STORAGE_KEY);
        const index = SCALES.indexOf(stored);
        this.scaleIndex = index === -1 ? 0 : index;
        this._applyScale();
    },

    _applyScale() {
        const html = document.documentElement;
        SCALES.filter(Boolean).forEach((cls) => html.classList.remove(cls));
        const cls = SCALES[this.scaleIndex];
        if (cls) {
            html.classList.add(cls);
        }
    },

    _renderControl() {
        if (document.querySelector(".o_chroma_font_adjuster")) {
            return;
        }
        const container = document.createElement("div");
        container.className = "o_chroma_font_adjuster";
        container.setAttribute("role", "group");
        container.setAttribute("aria-label", _t("Adjust text size"));
        LABELS.forEach((label, index) => {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = label;
            button.setAttribute("aria-label", _t("Text size %s", label));
            button.addEventListener("click", () => this._onSelect(index));
            container.appendChild(button);
        });
        document.body.appendChild(container);
        this.controlEl = container;
        this._syncActiveButton();
    },

    _onSelect(index) {
        this.scaleIndex = index;
        window.localStorage.setItem(STORAGE_KEY, SCALES[index]);
        this._applyScale();
        this._syncActiveButton();
    },

    _syncActiveButton() {
        if (!this.controlEl) {
            return;
        }
        [...this.controlEl.children].forEach((btn, index) => {
            btn.classList.toggle("active", index === this.scaleIndex);
        });
    },
});

export default publicWidget.registry.ChromaFontSizeAdjuster;
