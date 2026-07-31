# Chroma Identity Theme — Release Report

**Modules**: `chroma_identity_theme` (€49) + `chroma_identity_theme` (free, auto-installs with Website)
**Version**: 18.0.1.0.0 (both modules)
**Formerly**: `sa_dga_theme` / `sa_dga_theme_website` ("DGA-Ready Theme")

## 1. Why this module was rebranded

The product was originally built as a Saudi DGA-specific theme. The publisher
decided to generalize it into a sellable, general-purpose Odoo Store product
- full brand identity customization (colors, typography, layout) for ANY
customer, with the Saudi government-specific content repositioned as one
**optional, opt-in pack** rather than the product's whole identity. This is
a full technical rename, not a cosmetic relabel:

- Technical module names: `sa_dga_theme` → `chroma_identity_theme`,
  `sa_dga_theme_website` → `chroma_identity_theme_website`
- Every field, CSS custom property (`--dga-*` → `--chroma-*`), CSS/JS class
  prefix (`o_dga_*` → `o_chroma_*`), widget name, Python/JS class name, and
  action tag renamed to match
- Since no customer had ever purchased/installed the old technical module
  name, this was done as a clean rename (old module fully uninstalled,
  new one installed fresh) rather than a versioned upgrade path/migration
  bridge - there is nothing to migrate for real customers
- Version reset to **18.0.1.0.0** - this is the first release of the new
  product identity, even though the underlying feature set carries the
  full development history of the old `sa_dga_theme` (v1.0 → v1.8)

### What's still Saudi-flavored, now clearly optional

- **Government / Public Sector header & footer** (`views/website_header_footer_templates.xml`,
  `template_header_government` / `template_footer_government`): registered
  as an extra choice in Odoo's own Website > Configure > Theme header/footer
  pickers, `active="False"` by default - exactly as opt-in as the header/
  footer picker mechanism already made the old "DGA Government" variant,
  just relabeled
- **Default homepage content was neutralized**: the old homepage shipped
  gov-flavored copy ("Renew a License", "Citizens Served", "Digital
  Government Services") **active by default for every install** - that's
  no longer appropriate for a general-purpose product. The homepage
  structure (hero / services grid / stats / news) is unchanged and stays
  active by default (a real homepage beats Odoo's blank one for any
  customer), but the copy is now industry-neutral ("A Modern Digital
  Experience, Built for You", "Get Started Quickly", "Happy Clients")
- **Color presets** (`mto_signature`/`saudi_green`/`gov_navy`) are just
  color schemes, not gov-specific content - kept as-is, `mto_signature`
  (purple/black) stays the default per the publisher's own brand identity
- **Arabic-as-website-language** `post_init_hook` is general RTL/i18n
  value, not gov-specific - kept as-is

## 2. Product positioning

Full brand identity customization for Odoo backend, portal and (via the
companion module) website/eCommerce:
- Primary, accent and "chrome" (dark navbar/sidebar frame) colors, heading/
  body/muted text colors, 4 curated Arabic+Latin Google Fonts pairs - all
  changeable from **Settings > Chroma Identity**, applied instantly, no
  rebuild
- Live-preview settings card (now including a mock navbar/sidebar strip
  showing the chrome color live - previously chrome had no preview at all)
- One-click "Extract colors from logo"
- From-scratch backend app launcher (searchable card grid) + optional
  persistent left app sidebar, both Community-safe (no Enterprise
  dependency)
- Full Arabic/RTL support via Odoo's own `rtlcss` pipeline
- Accessibility layer: focus rings, skip-to-content link, font-size
  adjuster
- Optional Government/Public Sector header+footer pack for public-sector
  customers

## 3. Technical notes worth remembering

- **CSS custom properties, not Sass variable overrides**: colors are
  injected at runtime via a `<style>` tag in `web.layout`'s `<head>`
  (`views/layout_templates.xml`), computed per-request from
  `request.env.company`. Deliberately NOT using Odoo's
  `web._assets_primary_variables` Sass-injection bundle (what
  `web_enterprise` itself uses) - that would bake colors in at asset
  *compile* time, breaking "changeable from Settings" without a full
  asset rebuild per company.
- **`ir.http.session_info()` override** (`models/ir_http.py`) exposes
  `chroma_sidebar_enabled` synchronously at webclient boot, since the
  sidebar is a `main_components` entry that mounts before any ORM call
  could resolve.
- **XML comments cannot contain `--`**: caught during this rename - a
  comment referencing `--chroma-*` tokens literally broke XML parsing
  (`not well-formed (invalid token)`). Any future doc comment mentioning a
  CSS custom property by its `--name` must avoid writing the double-hyphen,
  or split it (e.g. "chroma design tokens" instead of "--chroma-* tokens").
- **Field-label collision with Odoo core**: `res.company` already has its
  own unrelated `primary_color`/`secondary_color` fields (report-layout
  branding, `odoo/addons/base/models/res_company.py`) with default labels
  "Primary Color"/"Secondary Color". Our fields needed distinct labels
  ("Brand Primary Color"/"Brand Accent Color") to avoid Odoo's
  `ir_model`-level "two fields have the same label" warning and field-list
  ambiguity.
- **Boolean field defaults do NOT backfill onto pre-existing rows**: adding
  `chroma_sidebar_enabled = fields.Boolean(default=True)` via `_inherit` on
  `res.company` only applies `default=True` to records created *after* the
  column exists - the `res.company` row that already existed before install
  (which is every real customer's situation - a company record always
  predates a theme install) gets backfilled as SQL NULL/False at column-add
  time, not the Python default. Confirmed by testing: a genuinely new
  company got `True` correctly, the pre-existing one did not. **Fixed with
  a `post_init_hook`** in `chroma_identity_theme/__init__.py` that
  explicitly sets the field `True` for all existing companies on install -
  without this, the sidebar would silently default to hidden on every real
  customer install despite the code saying `default=True`. This is a
  general Odoo gotcha worth remembering for any future Boolean field added
  via `_inherit` to a model that always has pre-existing rows.
- **`--i18n-overwrite` is required to force-refresh already-loaded
  translations**: during this rename, an intermediate `.po` state got
  loaded into the DB (correct location/context, but with an English source
  text that didn't yet match the final field label after a later text
  edit). A plain `-u` upgrade does **not** overwrite already-present
  translation values by default (to protect manually-edited translations)
  - only `-u ... --i18n-overwrite` forces the DB to match the `.po` file
  exactly. Confirmed via direct DB inspection
  (`ir.model.fields.field_description` with `lang='ar_001'` context)
  before/after. Also confirmed this is a genuinely separate issue from
  browser-side translation caching (which also needed a hard reload / a
  fresh tab to rule out as a false lead).
- **`--i18n-overwrite` cannot be combined with `-i`** (fresh install) -
  only valid with `-u` (update) or `--i18n-import`. Fresh installs always
  load translations cleanly from scratch, so this is a non-issue for real
  customer installs; it only mattered for this session's dev-iteration
  DBs that had already loaded a stale intermediate translation once.

## 4. i18n

Both modules' `i18n/ar.po` were rebuilt from a freshly-exported POT
(`--i18n-export`) against the final renamed code, not hand-patched from the
old files - this guarantees every `msgctxt`/location reference matches the
actual current field/view/template names. Translations for unchanged
strings were carried over from the old `.po` files by matching source text;
~22 new/changed strings per module (new field labels, new block titles, new
homepage copy) were freshly translated. A handful of entries were
deliberately left untranslated: `ir.http`'s auto-registered "HTTP Routing"
model name (core Odoo terminology, not module content), two markup-fragment
artifacts from inline snippet counters (a `t-translation="off"` candidate
for a future cleanup pass, not fixed here), and proper nouns / a placeholder
email address.

## 5. Verification performed

- [x] Both old modules cleanly uninstalled from both local databases
  (`dga_theme_community`:8069 Community-only addons-path, `odoo18`:8070
  Enterprise-in-path) via `button_immediate_uninstall()`
- [x] Both new modules installed fresh on both databases, zero errors
  (only the benign, known "module description is empty!" log line from
  Odoo's module-list-update step, which is a false positive - confirmed
  the description IS correctly populated by reading it back from
  `ir.module.module` directly)
- [x] Python syntax-checked (`py_compile`) and XML well-formedness checked
  (`xml.etree.ElementTree.parse`) on every file before install
- [x] Settings > Chroma Identity verified live on a fresh browser tab
  (bypassing all cache): every label/help text renders the correct new
  Arabic translation, live-preview card shows the new chrome-color mock
  navbar/sidebar strip reacting to the chrome color field, block titles
  show the new colored left-accent-bar treatment
- [x] `getComputedStyle()` confirmed: `.o_main_navbar` and
  `.o_chroma_app_sidebar` both resolve to the same chrome color
  (`rgb(10, 10, 10)` / `#0A0A0A` default), sidebar renders at desktop
  width with the correct `o_rtl` body class and no `o_chroma_sidebar_hidden`
  class present
- [x] Fresh-install test confirmed the `post_init_hook` sidebar-default
  fix: uninstalled + reinstalled on Community, `chroma_sidebar_enabled`
  read back as `True` on the pre-existing company with no manual fix
  needed
- [x] Homepage verified live: neutral generic copy renders (hero/services/
  stats/news), counters resolve to final values, no leftover
  government-specific placeholder text
- [x] `ir.model.data` confirmed the Government/Public Sector header and
  footer views exist with `active=False` (opt-in) and the options-picker
  view is `active=True` (so the choice appears in Website > Configure >
  Theme), matching the "optional pack" design decision exactly
- [x] Arabic translations spot-checked directly against the DB
  (`ir.model.fields.field_description` with `lang='ar_001'` context) both
  before and after the `--i18n-overwrite` fix, not just visually in the
  browser

## 6. Pending before Store upload

- [ ] Decide the fate of the old `marketplace_addons/sa_dga_theme(_website)`
  source trees - kept on disk as-is for now (not deleted), no longer
  installed anywhere; confirm with the publisher whether to archive or
  remove them
- [ ] Banner/cover art for the new brand name - handled separately per
  house policy, `images` manifest key still intentionally omitted
- [ ] Odoo 19.0 verification - still no local 19 checkout
- [ ] New store-listing screenshots under the new name/branding - the 3
  existing screenshots (`static/description/screenshots/`) predate this
  rebrand entirely (old "DGA Theme" navbar/settings labels) and must be
  recaptured
- [ ] A full unfiltered `--test-enable` run to completion has not been
  re-run since the rebrand (was last run clean, pre-rebrand, partially -
  see prior release history)
- [ ] The two markup-fragment i18n artifacts in the website module's
  homepage counters/service icons could be cleaned up with
  `t-translation="off"` on the inner `<span>`/`<i>` tags - cosmetic, not
  blocking
- [ ] Final price confirmation - currently €49 (base) / free (website
  companion), unchanged from the prior product

## 7. ZIP file paths

- `marketplace_addons/dist/chroma_identity_theme_18.0.zip`
- `marketplace_addons/dist/chroma_identity_theme_website_18.0.zip`

## 8. Install / upgrade commands

```bash
./odoo-bin -d yourdb -i chroma_identity_theme --stop-after-init
# chroma_identity_theme_website auto-installs once Website is also installed

./odoo-bin -d yourdb -u chroma_identity_theme,chroma_identity_theme_website --stop-after-init
```

---

For the full development history prior to the rebrand (every bug found and
fixed, every design decision through v1.0–v1.8 of the old `sa_dga_theme`),
see `SA_DGA_THEME_RELEASE_REPORT.md` in this same directory - preserved as
historical record, not updated further.
