import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { scanBarcode } from "@web/core/barcode/barcode_dialog";
import { Component, useState } from "@odoo/owl";

export class VisitorKioskScanner extends Component {
    static template = "smart_visitor_management.KioskScanner";
    static props = ["*"];

    setup() {
        this.state = useState({
            mode: "check_in",
            manualToken: "",
            busy: false,
            lastResult: null,
        });
    }

    setMode(mode) {
        this.state.mode = mode;
        this.state.lastResult = null;
    }

    async onScanClick() {
        let token;
        try {
            token = await scanBarcode(this.env);
        } catch {
            return;
        }
        await this.submitToken(token);
    }

    async onManualSubmit(ev) {
        ev.preventDefault();
        if (!this.state.manualToken) {
            return;
        }
        await this.submitToken(this.state.manualToken);
        this.state.manualToken = "";
    }

    async submitToken(token) {
        this.state.busy = true;
        try {
            const result = await rpc("/visitor/kiosk/scan", {
                token,
                action: this.state.mode,
            });
            this.state.lastResult = result;
        } finally {
            this.state.busy = false;
        }
    }
}

registry.category("actions").add("visitor_kiosk_scanner", VisitorKioskScanner);
