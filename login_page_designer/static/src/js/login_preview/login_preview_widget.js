/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { rpc } from "@web/core/network/rpc";
import { useDebounced } from "@web/core/utils/timing";
import { Component, useEffect, useRef, useState } from "@odoo/owl";

// Keep in sync with fileTypeMagicWordMap in
// @web/views/fields/image/image_field.js - used to guess a mimetype for
// the data-URI preview of an unsaved background-image upload, since the
// live preview can't reach a saved attachment yet.
const FILE_TYPE_MAGIC_WORD_MAP = { "/": "jpg", R: "gif", i: "png", P: "svg+xml", U: "webp" };

// A record-bound settings widget: renders a live iframe of the real
// /web/login page and keeps it in sync with the (possibly unsaved)
// res.config.settings field values, via a small session-stashed draft
// on the server (see /login_page_designer/set_preview).
export class LoginPageDesignerPreview extends Component {
    static template = "login_page_designer.LoginPageDesignerPreview";
    static props = { ...standardWidgetProps };

    setup() {
        this.iframeRef = useRef("lpdIframe");
        this.state = useState({ src: "/web/login?login_page_designer_preview=1" });

        this.pushPreview = useDebounced(this._pushPreview.bind(this), 400);

        useEffect(
            () => {
                this.pushPreview();
            },
            () => this._dependencies()
        );
    }

    get data() {
        return this.props.record.data;
    }

    _dependencies() {
        const d = this.data;
        return [
            d.lpd_position, d.lpd_card_bg_color, d.lpd_card_text_color, d.lpd_button_color,
            d.lpd_bg_type, d.lpd_bg_color, d.lpd_bg_gradient_start, d.lpd_bg_gradient_end,
            d.lpd_bg_gradient_angle, d.lpd_bg_image, d.lpd_bg_overlay_opacity,
            d.lpd_welcome_title, d.lpd_welcome_subtitle, d.lpd_pro_mode,
            d.lpd_custom_css, d.lpd_custom_html,
        ];
    }

    _buildConfig() {
        const d = this.data;
        let bgImageUrl = false;
        if (d.lpd_bg_type === "image" && d.lpd_bg_image) {
            const magic = FILE_TYPE_MAGIC_WORD_MAP[d.lpd_bg_image[0]] || "png";
            bgImageUrl = `data:image/${magic};base64,${d.lpd_bg_image}`;
        }
        return {
            position: d.lpd_position || "center",
            card_bg_color: d.lpd_card_bg_color || "#FFFFFF",
            card_text_color: d.lpd_card_text_color || "#1F2937",
            button_color: d.lpd_button_color || "#714B67",
            bg_type: d.lpd_bg_type || "none",
            bg_color: d.lpd_bg_color || "#F1F0F2",
            bg_gradient_start: d.lpd_bg_gradient_start || "#5E4766",
            bg_gradient_end: d.lpd_bg_gradient_end || "#0A0A0A",
            bg_gradient_angle: d.lpd_bg_gradient_angle || 0,
            bg_image_url: bgImageUrl,
            bg_overlay_opacity: d.lpd_bg_overlay_opacity || 0,
            welcome_title: d.lpd_welcome_title || "",
            welcome_subtitle: d.lpd_welcome_subtitle || "",
            pro_mode: !!d.lpd_pro_mode,
            custom_css: d.lpd_pro_mode ? (d.lpd_custom_css || "") : "",
            custom_html: d.lpd_pro_mode ? (d.lpd_custom_html || "") : "",
        };
    }

    async _pushPreview() {
        const config = this._buildConfig();
        await rpc("/login_page_designer/set_preview", { config });
        this.state.src = `/web/login?login_page_designer_preview=1&lpd_ts=${Date.now()}`;
    }
}

registry.category("view_widgets").add("login_page_designer_preview", {
    component: LoginPageDesignerPreview,
});
