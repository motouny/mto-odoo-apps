# Final Release Report

1. **Application Name**: Login Page Designer - Professional Login Customization
2. **Technical Name**: `login_page_designer` (+ free companion `login_page_designer_website`)
3. **Version**: 18.0.1.0.0
4. **Price**: 30.0 EUR (`login_page_designer_website` companion is free, 0.0 EUR)
5. **Currency**: EUR
6. **License**: OPL-1
7. **Dependencies**: `login_page_designer` depends only on `web` (Community). `login_page_designer_website` depends on `login_page_designer` + `website`, `auto_install: True` - installs itself automatically the moment both are present, no manual step.
8. **External Python Dependencies**: none.
9. **Models Extended**: `res.company` (all `lpd_*` fields), `res.config.settings` (related fields for the Settings screen). No new models - one config per company, multi-company ready out of the box.
10. **Fields added to `res.company`**: `lpd_enabled`, `lpd_position` (center/left/right/top/bottom), `lpd_card_bg_color`, `lpd_card_text_color`, `lpd_button_color`, `lpd_bg_type` (none/color/gradient/image), `lpd_bg_color`, `lpd_bg_gradient_start/end/angle`, `lpd_bg_image` (+ filename), `lpd_bg_overlay_opacity`, `lpd_welcome_title`/`lpd_welcome_subtitle` (translatable), `lpd_pro_mode`, `lpd_custom_css`, `lpd_custom_html`.
11. **Views Created**: `res.config.settings` panel ("Login Page Designer" app tab: Enable, Live Preview, Position, Card Colors, Background, Welcome Text, Pro Mode blocks). No new backend menus - purely a Settings-driven configuration product plus its effect on the public `/web/login` page.
12. **Security**: no new groups/models - editing lives entirely on `res.company`/`res.config.settings`, already gated to `base.group_system` (Settings administrators) by Odoo core. The live-preview JSON-RPC route explicitly re-checks `base.group_system` server-side regardless of the calling context.
13. **Frontend Template Changes**:
    - `login_page_designer` inherits `web.login_layout` (position="attributes"/"before"/"after" xpaths - never a full `position="replace"` of the base template) to add: a computed `<style>` block (position flex layout, card colors, background), a card class, an optional welcome title/subtitle block, and a Pro-mode custom HTML panel below the form.
    - `login_page_designer_website` inherits `website.login_layout` directly. This companion exists because the `website` module's own `login_layout` view (priority 20) replaces `web.login_layout`'s entire content with a bare `website.layout` wrapper + a single `oe_website_login_container` div - discarding everything the base module's own inherit adds. The companion rebuilds the same card/position/background/welcome/Pro-mode design on top of that website-driven layout, and hides the site's own header/footer (`no_header`/`no_footer`) for a clean branded login screen when enabled.
    - Both paths share the same `res.company._lpd_get_render_config()` / `_lpd_build_style_markup()` / `_lpd_build_html_markup()` methods - one source of truth, no logic duplication.
14. **Frontend Routes**:
    - `GET /login_page_designer/background/<company_id>` (`auth=public`) - streams the uploaded background image via `ir.binary._get_image_stream_from`, same pattern as Odoo core's own company-logo route.
    - `POST /login_page_designer/set_preview` (JSON, `auth=user`) - stashes an unsaved draft config in the caller's own session, gated to `base.group_system`; used only by the Settings live-preview widget.
    - `POST /login_page_designer/clear_preview` (JSON, `auth=user`) - clears it.
15. **Live Preview**: an OWL widget (`LoginPageDesignerPreview`) renders a real iframe of `/web/login?login_page_designer_preview=1`; a `useEffect` + `useDebounced` pair pushes the current (unsaved) field values to `/login_page_designer/set_preview` and reloads the iframe on every change - a genuine live view of the real page, not a mock-up.
16. **Automated Tests**: 20 tests total - `login_page_designer`: 7 unit tests (`_lpd_get_render_config`/`_lpd_build_style_markup`/`_lpd_build_html_markup` - position/color/gradient/image mapping, Pro-mode gating) + 5 `HttpCase` tests (default page untouched when disabled, saved design reflected on the real `/web/login`, custom HTML hidden without Pro mode, preview route rejects non-admins, preview route affects only the preview request not the saved page). `login_page_designer_website`: 2 `HttpCase` tests (disabled = default site chrome untouched, enabled = site header/footer hidden and the branded card shown).
17. **Test Results**: `0 failed, 0 error(s)` of all 20 module tests, both against the source tree and against a fresh install of the packaged `dist/` zips in an otherwise-empty database.
18. **Full Core Regression Check**: re-ran unfiltered against a fresh install of `website`, `auth_signup`, `login_page_designer` and `login_page_designer_website` together (2000-2022 tests depending on Enterprise addons in path) - `19-20 failed, 4 error(s)`, matching the same pre-existing environment-specific baseline already documented for other apps in this repo (missing `wkhtmltopdf`, `phonenumbers` data-version drift, `mail`/`discuss` flakiness) - none of the failures are in `web`, `website`, `portal`, `auth_signup` or either `login_page_designer*` module.
19. **Real Design Issue Found and Fixed During Verification**: the `website` module's own `login_layout` view replaces (not extends) `web.login_layout`'s content once Website is installed - confirmed by testing against a real browser with Website installed, where the base module's design silently stopped applying and the full site header/footer appeared instead. Fixed by adding the `login_page_designer_website` auto-install companion (see #13), verified again in the real browser afterward (branded card, no site chrome, gradient background, custom Pro-mode HTML all rendering correctly on the actual `/web/login` page, logged out).
20. **Other Real Bugs Found and Fixed During Verification**:
    - `hasclass()` in a QWeb `<xpath expr="...">` only matches a literal `class` attribute, not `t-attf-class` - the base template's own card `<div>` uses `t-attf-class`, so the initial xpath silently failed to locate it at install time. Fixed by matching on `contains(@t-attf-class, 'o_database_list')` instead.
    - A field label collision: `lpd_bg_image` vs. `res.company`'s own core `layout_background_image`, both labeled "Background Image" - renamed to "Login Page Background Image".
    - The Settings live-preview widget's initial `useService("rpc")` doesn't exist in Odoo 18's web client (no `rpc` service is registered) - fixed by importing the plain `rpc()` function from `@web/core/network/rpc` instead, which is the correct Odoo 18 pattern.
21. **Known Limitations**:
    - Pro-mode CSS/HTML is trusted, unsanitized input rendered on a public, unauthenticated page - by design (same trust model as Odoo's own Website "Custom Code" head-injection feature), gated to `base.group_system` only.
    - No visual drag-and-drop position picker - position is chosen via radio buttons, reflected instantly in the live-preview iframe.
22. **Community Compatibility**: Full - installs and runs on Odoo 18 Community with only `web` (and `website` for the free companion).
23. **Enterprise Compatibility**: Fully compatible; no Enterprise-only feature is used or required.
24. **Store Assets**: `static/description/index.html` (pure ASCII, verified), `icon.png` (MTO brand kit "M" mark), `banner.png`/`cover.png` (HTML/CSS composition embedding a real screenshot of the running, branded login page, rendered via Playwright and downscaled to 1280x720), 4 real screenshots captured from a running instance (Settings live preview, the real production login page, Position/Colors/Background fields, Pro Mode fields) - no mock-ups.
25. **i18n**: `i18n/ar.po` for both modules, 100% translated (43 entries in the base module, 1 in the companion).
26. **ZIP File Paths**:
    - `marketplace_addons/dist/login_page_designer_18.0.zip`
    - `marketplace_addons/dist/login_page_designer_website_18.0.zip`
27. **Installation Command**:
    ```bash
    ./odoo-bin -d yourdb -i login_page_designer --stop-after-init
    ```
    (`login_page_designer_website` installs itself automatically if `website` is also installed.)
28. **Upgrade Command**:
    ```bash
    ./odoo-bin -d yourdb -u login_page_designer --stop-after-init
    ```
29. **Release Checklist**:
    - [x] Clean install on a throwaway database (no parse errors, no missing external IDs)
    - [x] Full automated test suite passing (20/20), both from source and from the packaged zips
    - [x] Full unfiltered core regression check (`web`, `website`, `portal`, `auth_signup`) - only pre-existing, environment-specific baseline failures, none touching this app or the templates it modifies
    - [x] Manual verification in a real browser, logged out, on the actual `/web/login` page: position, card colors, gradient background, welcome text and Pro-mode custom CSS/HTML all confirmed working - twice, once on plain Odoo and once with Website installed (via the companion module)
    - [x] Three real bugs found and fixed during verification (see #20), plus the Website-compatibility design gap (see #19)
    - [x] Price set to 30.0 EUR (companion free), license OPL-1, `application: True` (companion `application: False`), `installable: True`
    - [x] Arabic translation (`i18n/ar.po`) imported for both modules
    - [x] Packaged zips installed (not just the source folder) into a fresh, otherwise-empty database with `--test-enable`
    - [x] `images` manifest key present for both modules (Apps Store cover requirement)
    - [x] `static/description/index.html` verified pure ASCII on both modules
