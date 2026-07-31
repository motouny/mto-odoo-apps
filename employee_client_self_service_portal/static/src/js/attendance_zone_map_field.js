/** @odoo-module **/
/*global L*/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { AssetsLoadingError, loadCSS, loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";

const LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
const DEFAULT_CENTER = [24.7136, 46.6753]; // neutral default view, no marker implied
const DEFAULT_ZOOM = 12;
const WORLD_ZOOM = 3;

export class AttendanceZoneMapField extends Component {
    static template = "employee_client_self_service_portal.AttendanceZoneMapField";
    static props = { ...standardFieldProps };

    setup() {
        this.mapRef = useRef("map");
        this.leafletMap = null;
        this.marker = null;
        this.circle = null;
        this.state = useState({
            shouldLoadMap: false,
            loadError: false,
            searchText: "",
            searching: false,
        });

        onWillStart(async () => {
            try {
                await Promise.all([loadJS(LEAFLET_JS), loadCSS(LEAFLET_CSS)]);
                this.state.shouldLoadMap = true;
            } catch (error) {
                if (!(error instanceof AssetsLoadingError)) {
                    throw error;
                }
                this.state.loadError = true;
            }
        });

        useEffect(
            () => {
                if (!this.state.shouldLoadMap || !this.mapRef.el) {
                    return;
                }
                this.leafletMap = L.map(this.mapRef.el);
                L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
                    maxZoom: 19,
                    attribution: "&copy; OpenStreetMap contributors",
                }).addTo(this.leafletMap);

                const lat = this.latitude;
                const lng = this.longitude;
                if (lat && lng) {
                    this.leafletMap.setView([lat, lng], DEFAULT_ZOOM);
                    this._placeMarker(lat, lng);
                } else {
                    this.leafletMap.setView(DEFAULT_CENTER, WORLD_ZOOM);
                }

                if (!this.props.readonly) {
                    this.leafletMap.on("click", (ev) => {
                        this._setLocation(ev.latlng.lat, ev.latlng.lng);
                    });
                }

                return () => {
                    this.leafletMap.remove();
                    this.leafletMap = null;
                    this.marker = null;
                    this.circle = null;
                };
            },
            () => [this.state.shouldLoadMap]
        );

        // Keep the marker/circle synced if the values change from the inputs below.
        useEffect(
            () => {
                if (!this.leafletMap) {
                    return;
                }
                const lat = this.latitude;
                const lng = this.longitude;
                if (lat && lng) {
                    this._placeMarker(lat, lng, { pan: false });
                }
            },
            () => [this.latitude, this.longitude, this.radius]
        );
    }

    get latitude() {
        return this.props.record.data[this.props.name];
    }

    get longitude() {
        return this.props.record.data.attendance_longitude;
    }

    get radius() {
        return this.props.record.data.attendance_radius;
    }

    _placeMarker(lat, lng, { pan = true } = {}) {
        if (!this.marker) {
            this.marker = L.marker([lat, lng], { draggable: !this.props.readonly }).addTo(this.leafletMap);
            this.marker.on("dragend", () => {
                const pos = this.marker.getLatLng();
                this._setLocation(pos.lat, pos.lng);
            });
        } else {
            this.marker.setLatLng([lat, lng]);
        }
        if (!this.circle) {
            this.circle = L.circle([lat, lng], { radius: this.radius || 200, color: "#875A7B" }).addTo(this.leafletMap);
        } else {
            this.circle.setLatLng([lat, lng]);
            this.circle.setRadius(this.radius || 200);
        }
        if (pan) {
            this.leafletMap.setView([lat, lng], Math.max(this.leafletMap.getZoom(), DEFAULT_ZOOM));
        }
    }

    async _setLocation(lat, lng) {
        await this.props.record.update({
            [this.props.name]: lat,
            attendance_longitude: lng,
        });
    }

    async onLatInput(ev) {
        const value = parseFloat(ev.target.value);
        if (!isNaN(value)) {
            await this.props.record.update({ [this.props.name]: value });
        }
    }

    async onLngInput(ev) {
        const value = parseFloat(ev.target.value);
        if (!isNaN(value)) {
            await this.props.record.update({ attendance_longitude: value });
        }
    }

    async onRadiusInput(ev) {
        const value = parseInt(ev.target.value, 10);
        if (!isNaN(value)) {
            await this.props.record.update({ attendance_radius: value });
        }
    }

    useMyLocation() {
        if (!navigator.geolocation) {
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (position) => this._setLocation(position.coords.latitude, position.coords.longitude),
            () => {},
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.searchAddress();
        }
    }

    async searchAddress() {
        if (!this.state.searchText.trim()) {
            return;
        }
        this.state.searching = true;
        try {
            const url =
                "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" +
                encodeURIComponent(this.state.searchText);
            const response = await fetch(url);
            const results = await response.json();
            if (results.length) {
                await this._setLocation(parseFloat(results[0].lat), parseFloat(results[0].lon));
            }
        } finally {
            this.state.searching = false;
        }
    }

    get searchPlaceholder() {
        return _t("Search an address…");
    }
}

registry.category("fields").add("attendance_zone_map", {
    component: AttendanceZoneMapField,
    supportedTypes: ["float"],
});
