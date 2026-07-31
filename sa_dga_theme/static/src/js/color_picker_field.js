/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

const HEX_RE = /^#[0-9a-fA-F]{6}$/;

export class DgaColorPickerField extends Component {
    static template = "sa_dga_theme.DgaColorPickerField";
    static props = { ...standardFieldProps };

    get value() {
        return this.props.record.data[this.props.name] || "#000000";
    }

    onColorInput(ev) {
        this.props.record.update({ [this.props.name]: ev.target.value });
    }

    onTextChange(ev) {
        const value = ev.target.value.trim();
        if (HEX_RE.test(value)) {
            this.props.record.update({ [this.props.name]: value });
        } else {
            ev.target.value = this.value;
        }
    }
}

registry.category("fields").add("dga_color_picker", {
    component: DgaColorPickerField,
    supportedTypes: ["char"],
});

// Keep in sync with DGA_COLOR_PRESETS in models/res_company.py - this
// mirror was found out of date during testing (missing "mto_signature"
// entirely, added when that preset became the default in v1.4), so
// selecting it from the radio silently did nothing client-side even
// though the preset itself was selected - always update both together.
const DGA_COLOR_PRESETS = {
    mto_signature: { primary: "#5E4766", accent: "#010101", chrome: "#0A0A0A" },
    saudi_green: { primary: "#046A38", accent: "#0B7A45", chrome: "#0A2E1C" },
    gov_navy: { primary: "#0B3D59", accent: "#12608C", chrome: "#081E2E" },
};

// A plain "radio" widget for sa_dga_color_preset relies on a server
// onchange round-trip to fill in the hex fields, which turned out to be
// unreliable on this related-field + res.config.settings combination in
// testing (the RPC simply never fired from the UI, even though the same
// onchange logic worked perfectly when called directly). Setting all three
// fields together in one client-side record.update() sidesteps that
// entirely and is a better match for the "applied instantly" UI copy.
export class DgaPresetRadioField extends Component {
    static template = "sa_dga_theme.DgaPresetRadioField";
    static props = { ...standardFieldProps };

    get selection() {
        return this.props.record.fields[this.props.name].selection;
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    onSelect(value) {
        const vals = { [this.props.name]: value };
        const preset = DGA_COLOR_PRESETS[value];
        if (preset) {
            vals.sa_dga_primary_color = preset.primary;
            vals.sa_dga_accent_color = preset.accent;
            vals.sa_dga_chrome_color = preset.chrome;
        }
        this.props.record.update(vals);
    }
}

registry.category("fields").add("dga_preset_radio", {
    component: DgaPresetRadioField,
    supportedTypes: ["selection"],
});
