#!/usr/bin/env python3
"""Generate the Home Assistant theme pack for JI Engineering Style.

Single source of truth: ji-design-system/web/ji.css (base role tokens, light+dark)
and ji-design-system/themes/*.css (per-theme role-token overrides). We parse the
--ji-* role tokens, resolve var() references against the base palette, and map
them onto Home Assistant frontend variables, emitting one YAML with every theme,
each carrying light + dark modes.

No colour is invented here: every value traces to a --ji-* token in the CSS.
"""
import re, sys, pathlib

DS = pathlib.Path(sys.argv[1])          # ji-design-system dir
OUT = pathlib.Path(sys.argv[2])         # output yaml

CSS = (DS / "web" / "ji.css").read_text()

# ---- parse the base :root palette + light roles, and the forced dark roles ----
def block(text, selector):
    """Return the declaration body of `selector { ... }` (no nested braces here)."""
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", text)
    return m.group(1) if m else ""

def decls(body):
    d = {}
    for name, val in re.findall(r"(--ji-[a-z0-9-]+)\s*:\s*([^;]+);", body):
        d[name.strip()] = val.strip()
    return d

# base :root is the first {...} after ":root {" that holds the palette
base_root = block(CSS, ":root")
base_raw = decls(base_root)
dark_raw = decls(block(CSS, ':root[data-theme="dark"]'))

def resolve(d):
    """Resolve var(--ji-x) chains to a literal; leave non-var values as-is."""
    out = {}
    def r(v, seen=()):
        m = re.fullmatch(r"var\((--ji-[a-z0-9-]+)\)", v.strip())
        if not m:
            return v.strip()
        k = m.group(1)
        if k in seen or k not in d:
            return v.strip()
        return r(d[k], seen + (k,))
    for k, v in d.items():
        out[k] = r(v)
    return out

base_light = resolve(base_raw)
# base has no --ji-accent; base accent = brand azure
base_light.setdefault("--ji-accent", base_light.get("--ji-azure", "#189CE4"))

# dark roles overlay the light base (dark block carries literal hex)
base_dark = dict(base_light)
for k, v in resolve({**base_raw, **dark_raw}).items():
    if k in dark_raw:
        base_dark[k] = v
base_dark.setdefault("--ji-accent", base_dark.get("--ji-azure", "#189CE4"))

# ---- per-theme overrides ----
THEMES = [
    ("JI Engineering", None, "Brand blue #1557C0 — the default JI identity."),
    ("JI Baltic",   "baltic",   "Baltic sea teal + amber."),
    ("JI Polish",   "polish",   "Polish red + crown gold."),
    ("JI Tatra",    "tatra",    "Granite slate + pine."),
    ("JI Mazury",   "mazury",   "Lake teal + reed gold."),
    ("JI Forest",   "forest",   "Pine green + copper."),
    ("JI Graphite", "graphite", "Graphite + cyan — panels/monitoring."),
    ("JI Copper",   "copper",   "Steel slate + copper — maker/engineering."),
    ("JI Nord",     "nord",     "Frost + aurora."),
    ("JI HighVis",  "highvis",  "Safety amber — alarms/ops."),
    ("JI Terminal", "terminal", "Phosphor green — dev/logs, dark-first."),
]

def theme_modes(slug):
    if slug is None:
        return dict(base_light), dict(base_dark)
    tcss = (DS / "themes" / f"{slug}.css").read_text()
    l_over = resolve(decls(block(tcss, f':root[data-ji-theme="{slug}"]')))
    d_over = resolve(decls(block(tcss, f':root[data-ji-theme="{slug}"][data-theme="dark"]')))
    light = dict(base_light); light.update(l_over)
    dark  = dict(base_dark);  dark.update(d_over)
    return light, dark

def hexrgb(v):
    v = v.strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", v)
    if not m:
        return None
    h = m.group(1)
    return f"{int(h[0:2],16)}, {int(h[2:4],16)}, {int(h[4:6],16)}"

def g(t, k, fallback="#000000"):
    return t.get(f"--ji-{k}", fallback)

def mode_vars(t):
    """Map resolved JI role tokens -> HA frontend variables for one mode."""
    primary = g(t, "primary"); accent = g(t, "accent"); onprim = g(t, "on-primary")
    surface = g(t, "surface"); onsurf = g(t, "on-surface")
    rows = [
        # --- text ---
        ("primary-text-color", onsurf),
        ("secondary-text-color", g(t, "on-surface-variant")),
        ("text-primary-color", onprim),
        ("disabled-text-color", g(t, "outline")),
        # --- brand ---
        ("primary-color", primary),
        ("light-primary-color", g(t, "primary-container")),
        ("dark-primary-color", g(t, "link", primary)),
        ("accent-color", accent),
        # --- backgrounds ---
        ("primary-background-color", g(t, "bg")),
        ("secondary-background-color", g(t, "surface-variant")),
        ("card-background-color", surface),
        ("ha-card-background", surface),
        ("ha-card-border-color", g(t, "outline-variant")),
        ("divider-color", g(t, "outline-variant")),
        ("app-header-background-color", surface),
        ("app-header-text-color", onsurf),
        ("app-header-selection-bar-color", primary),
        # --- sidebar ---
        ("sidebar-background-color", surface),
        ("sidebar-text-color", g(t, "on-surface-variant")),
        ("sidebar-icon-color", g(t, "on-surface-variant")),
        ("sidebar-selected-text-color", primary),
        ("sidebar-selected-icon-color", primary),
        # --- icons / states ---
        ("state-icon-color", g(t, "on-surface-variant")),
        ("state-icon-active-color", primary),
        ("state-active-color", primary),
        ("paper-item-icon-color", g(t, "on-surface-variant")),
        ("paper-item-icon-active-color", primary),
        # --- toggles / sliders ---
        ("switch-checked-color", primary),
        ("switch-checked-button-color", primary),
        ("switch-checked-track-color", g(t, "primary-container")),
        ("switch-unchecked-button-color", g(t, "on-surface-variant")),
        ("switch-unchecked-track-color", g(t, "outline")),
        ("paper-toggle-button-checked-button-color", primary),
        ("paper-toggle-button-checked-bar-color", primary),
        ("paper-slider-active-color", primary),
        ("paper-slider-knob-color", primary),
        # --- semantics ---
        ("error-color", g(t, "danger-btn")),
        ("warning-color", g(t, "warning")),
        ("success-color", g(t, "success")),
        ("info-color", g(t, "info")),
        # --- material (mdc) ---
        ("mdc-theme-primary", primary),
        ("mdc-theme-secondary", accent),
        ("mdc-theme-on-primary", onprim),
        ("mdc-theme-surface", surface),
        ("mdc-theme-on-surface", onsurf),
        # --- label badges ---
        ("label-badge-background-color", surface),
        ("label-badge-text-color", onsurf),
        ("label-badge-red", g(t, "danger-btn")),
        ("label-badge-green", g(t, "success")),
        ("label-badge-blue", g(t, "info")),
        ("label-badge-yellow", g(t, "warning")),
        # --- tables / code ---
        ("table-row-background-color", surface),
        ("table-row-alternative-background-color", g(t, "surface-variant")),
        ("code-editor-background-color", g(t, "surface-variant")),
        # --- rgb variants (cards that need them) ---
        ("rgb-primary-color", hexrgb(primary) or "21, 87, 192"),
        ("rgb-accent-color", hexrgb(accent) or "24, 156, 228"),
        ("rgb-primary-text-color", hexrgb(onsurf) or "16, 24, 40"),
        ("rgb-card-background-color", hexrgb(surface) or "255, 255, 255"),
        # --- JI brand tokens exposed for custom cards / card-mod ---
        ("ji-primary", primary),
        ("ji-on-primary", onprim),
        ("ji-primary-container", g(t, "primary-container")),
        ("ji-on-primary-container", g(t, "on-primary-container")),
        ("ji-accent", accent),
        ("ji-bg", g(t, "bg")),
        ("ji-surface", surface),
        ("ji-on-surface", onsurf),
        ("ji-surface-variant", g(t, "surface-variant")),
        ("ji-on-surface-variant", g(t, "on-surface-variant")),
        ("ji-outline", g(t, "outline")),
        ("ji-outline-variant", g(t, "outline-variant")),
        ("ji-success", g(t, "success")), ("ji-success-bg", g(t, "success-bg")),
        ("ji-warning", g(t, "warning")), ("ji-warning-bg", g(t, "warning-bg")),
        ("ji-danger", g(t, "danger-btn")), ("ji-danger-bg", g(t, "danger-bg")),
        ("ji-info", g(t, "info")), ("ji-info-bg", g(t, "info-bg")),
    ]
    return rows

SANS = "'Manrope', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'SF Mono', 'Roboto Mono', ui-monospace, monospace"
MDC_FONT_KEYS = [
    "mdc-typography-body1-font-family", "mdc-typography-body2-font-family",
    "mdc-typography-subtitle1-font-family", "mdc-typography-subtitle2-font-family",
    "mdc-typography-caption-font-family", "mdc-typography-button-font-family",
    "mdc-typography-headline6-font-family", "mdc-typography-overline-font-family",
]

def q(v):
    """Quote a YAML scalar value."""
    return '"' + v.replace('"', '\\"') + '"'

def emit_theme(name, slug, desc):
    light, dark = theme_modes(slug)
    L = []
    L.append(f'# {name} — {desc}')
    L.append(f'"{name}":')
    # ---- shared (mode-independent): fonts, radii, card look, card-mod tick ----
    L.append('  # typefaces (registered by ji-font.js via frontend.extra_module_url; falls back if absent)')
    L.append(f'  ji-font-sans: {q(SANS)}')
    L.append(f'  ji-font-mono: {q(MONO)}')
    L.append('  ha-font-family-body: var(--ji-font-sans)')
    L.append('  ha-font-family-heading: var(--ji-font-sans)')
    L.append('  ha-font-family-longform: var(--ji-font-sans)')
    L.append('  primary-font-family: var(--ji-font-sans)')
    L.append('  paper-font-common-base_-_font-family: var(--ji-font-sans)')
    L.append('  code-font-family: var(--ji-font-mono)')
    for k in MDC_FONT_KEYS:
        L.append(f'  {k}: var(--ji-font-sans)')
    L.append('  # tight JI radii (buttons/chips 5, cards 8)')
    L.append('  ha-card-border-radius: "8px"')
    L.append('  mdc-shape-small: "5px"')
    L.append('  mdc-shape-medium: "8px"')
    L.append('  mdc-shape-large: "8px"')
    L.append('  ha-card-border-width: "1px"')
    L.append('  button-card-border-radius: "5px"')
    # card-mod: the channel-tick signature on every ha-card (ignored if card-mod absent)
    L.append(f'  card-mod-theme: "{name}"')
    L.append('  card-mod-card: |')
    L.append('    ha-card {')
    L.append('      position: relative;')
    L.append('      border: 1px solid var(--ha-card-border-color);')
    L.append('    }')
    L.append('    ha-card::after {')
    L.append('      content: "";')
    L.append('      position: absolute;')
    L.append('      left: 0;')
    L.append('      top: 16px;')
    L.append('      width: 3px;')
    L.append('      height: 20px;')
    L.append('      border-radius: 0 2px 2px 0;')
    L.append('      background: var(--ji-primary, var(--primary-color));')
    L.append('      z-index: 1;')
    L.append('      pointer-events: none;')
    L.append('    }')
    # ---- modes ----
    L.append('  modes:')
    for mode, t in (("light", light), ("dark", dark)):
        L.append(f'    {mode}:')
        for k, v in mode_vars(t):
            L.append(f'      {k}: {q(v)}')
    return "\n".join(L)

header = (
    "# =============================================================================\n"
    "# JI Engineering Style — Home Assistant theme pack\n"
    "# Generated from the design system's single source of truth:\n"
    "#   web/ji.css (base role tokens) + themes/<name>.css (per-theme overrides).\n"
    "# Do not hand-edit: change tokens.json / the CSS and regenerate.\n"
    "#\n"
    "# Each theme carries light + dark modes (auto-follows HA's dark mode setting).\n"
    "# Colours, semantics and tight radii apply with the theme alone. Two optional\n"
    "# extras, both degrading silently if missing:\n"
    "#   * fonts   -> ji-font.js wired via frontend.extra_module_url (see README)\n"
    "#   * the channel-tick bar on cards -> lovelace-card-mod (HACS)\n"
    "# =============================================================================\n"
)
blocks = [emit_theme(n, s, d) for (n, s, d) in THEMES]
OUT.write_text(header + "\n" + "\n\n".join(blocks) + "\n")
print(f"wrote {OUT} ({len(blocks)} themes, {OUT.stat().st_size} bytes)")
