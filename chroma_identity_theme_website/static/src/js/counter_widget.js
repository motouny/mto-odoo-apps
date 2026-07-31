/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// No count-up widget exists anywhere in Odoo 18 core to reuse (confirmed
// by research: website's own `s_numbers` snippet is static markup, and
// `WebsiteAnimate` only handles fade/slide-in-on-scroll, not digit
// counting) - this is a small, from-scratch IntersectionObserver-based
// count-up, not a reimplementation of anything that already exists.
const COUNT_DURATION_MS = 1200;

publicWidget.registry.ChromaCounter = publicWidget.Widget.extend({
    selector: ".o_chroma_counter",

    start() {
        const res = this._super(...arguments);
        this.target = parseInt(this.el.dataset.count, 10) || 0;
        this.suffix = this.el.dataset.suffix || "";
        this.animated = false;

        const prefersReducedMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;
        if (prefersReducedMotion) {
            this._setValue(this.target);
            return res;
        }

        this.observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && !this.animated) {
                    this.animated = true;
                    this._animate();
                }
            },
            { threshold: 0.4 }
        );
        this.observer.observe(this.el);
        return res;
    },

    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        this._super(...arguments);
    },

    _setValue(value) {
        this.el.textContent = value.toLocaleString() + this.suffix;
    },

    _animate() {
        const start = performance.now();
        const step = (now) => {
            const progress = Math.min((now - start) / COUNT_DURATION_MS, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            this._setValue(Math.round(this.target * eased));
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    },
});

export default publicWidget.registry.ChromaCounter;
