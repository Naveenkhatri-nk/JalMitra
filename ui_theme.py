"""
ui_theme.py - JalMitra look and feel (UI redesign, 24 Nov 2026): Day / Night / System theme, clean chat layout.

  * two palettes as CSS variables (water-blue accent, soft neutrals), applied to the sidebar, chat bubbles, data
    cards, inputs, buttons, notices and dialogs; the system font stack of the computer (no web fonts, fully offline)
  * Streamlit's own colours come from .streamlit/config.toml ([theme.light] / [theme.dark], same palettes). A
    forced Day or Night choice is passed to Streamlit's theme switch in the browser (its local "active theme"
    entry), so tables and charts follow too; "System" follows the computer's setting
  * Streamlit's developer chrome (main menu, deploy button, footer, top decoration) is hidden
"""

import json

import streamlit as st

PALETTES = {
    "light": {
        "bg": "#FFFFFF", "sidebar": "#F7F9FC", "surface": "#F8FAFD", "surface2": "#EEF4FB", "border": "#E3E8EF",
        "text": "#1C2733", "muted": "#5B6878", "accent": "#1D6FB8", "accent-soft": "rgba(29,111,184,.08)",
        "accent-text": "#FFFFFF", "user-bubble": "#EAF3FD", "user-text": "#12324F", "ok": "#1F7A3A",
        "ok-soft": "rgba(31,122,58,.10)", "warn": "#9A6700", "warn-soft": "rgba(212,160,23,.12)", "bad": "#B42318",
        "bad-soft": "rgba(180,35,24,.08)", "shadow": "0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.08)",
        "hover": "rgba(29,111,184,.07)",
    },
    "dark": {
        "bg": "#0F1419", "sidebar": "#0A0E12", "surface": "#161E27", "surface2": "#1B2631", "border": "#26323F",
        "text": "#E6EDF3", "muted": "#97A4B2", "accent": "#5AB0F0", "accent-soft": "rgba(90,176,240,.14)",
        "accent-text": "#08131D", "user-bubble": "#1A3047", "user-text": "#E6EDF3", "ok": "#5CC97F",
        "ok-soft": "rgba(92,201,127,.12)", "warn": "#E8B949", "warn-soft": "rgba(232,185,73,.12)", "bad": "#F97066",
        "bad-soft": "rgba(249,112,102,.10)", "shadow": "0 1px 2px rgba(0,0,0,.4)", "hover": "rgba(90,176,240,.10)",
    },
}
FONT = ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", '
        '"Nirmala UI", "Mangal", sans-serif, "Apple Color Emoji", "Segoe UI Emoji"')
STREAMLIT_THEME = {"day": "Light", "night": "Dark", "system": "System"}   # Streamlit's stored theme names

BASE_CSS = """
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp input, .stApp textarea, .stApp button, .stMarkdown, [data-testid="stSidebar"] { font-family: var(--jm-font) !important; }
.stApp { background: var(--jm-bg); color: var(--jm-text); }
/* ---- Streamlit chrome: no menu, deploy button, footer or decoration (local app) */
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"], [data-testid="stToolbarActions"], #MainMenu,
footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
/* ---- sidebar */
[data-testid="stSidebar"] { background: var(--jm-sidebar) !important; border-right: 1px solid var(--jm-border); }
[data-testid="stSidebarContent"] { background: var(--jm-sidebar) !important; }
[data-testid="stSidebarUserContent"] { padding-top: .25rem; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: var(--jm-muted); }
.jm-side-group { font-size: .74rem; font-weight: 600; color: var(--jm-muted); letter-spacing: .02em;
  margin: .7rem 0 .15rem .35rem; }
.st-key-jm_newchat button { border-radius: 10px; font-weight: 600; justify-content: flex-start; padding: .45rem .8rem; }
[class*="st-key-jm_hist_"] { gap: 0 !important; }
[class*="st-key-jm_hist_"] [data-testid="stHorizontalBlock"] { gap: .1rem !important; align-items: center; }
[class*="st-key-jm_hist_"] button { border: none !important; background: transparent !important;
  justify-content: flex-start; text-align: left; min-height: 2rem; padding: .25rem .5rem; border-radius: 8px;
  color: var(--jm-text) !important; }
[class*="st-key-jm_hist_"] button p { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: .9rem; }
[class*="st-key-jm_hist_"] button:hover { background: var(--jm-hover) !important; }
.jm-active-chat [class*="st-key-jm_hist_"] button, [class*="st-key-jm_histon_"] button {
  background: var(--jm-accent-soft) !important; font-weight: 600; }
[class*="st-key-jm_histon_"] [data-testid="stHorizontalBlock"] { gap: .1rem !important; align-items: center; }
[class*="st-key-jm_histon_"] button { border: none !important; justify-content: flex-start; text-align: left;
  min-height: 2rem; padding: .25rem .5rem; border-radius: 8px; color: var(--jm-text) !important; }
[class*="st-key-jm_histon_"] button p { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: .9rem; }
[class*="st-key-jm_hist"] [data-testid="stPopover"] button { background: transparent !important; padding: .1rem .35rem;
  min-height: 1.8rem; justify-content: center; }
.st-key-jm_sidefoot button { justify-content: flex-start; border-radius: 10px; }
.st-key-jm_clear { margin-top: .4rem; }
.st-key-jm_clear [data-testid="stPopover"] > div > button { border: none !important; background: transparent !important;
  color: var(--jm-muted) !important; min-height: 1.8rem; font-size: .82rem; justify-content: flex-start; }
.st-key-jm_clear [data-testid="stPopover"] > div > button:hover { color: var(--jm-bad) !important; }
.st-key-jm_newchat button > div, [class*="st-key-jm_hist"] button > div, .st-key-jm_sidefoot button > div,
.st-key-jm_examples button > div { justify-content: flex-start; width: 100%; }
.st-key-jm_themeq button, .st-key-jm_themeq button > div,
[class*="st-key-jm_hist"] [data-testid="stPopover"] button > div { justify-content: center !important; }
/* ---- buttons, inputs, popovers, dialogs */
.stApp button[kind="primary"], .stApp [data-testid="stBaseButton-primary"] { background: var(--jm-accent) !important;
  border-color: var(--jm-accent) !important; color: var(--jm-accent-text) !important; }
.stApp [data-testid="stBaseButton-secondary"] { border-color: var(--jm-border); }
.stApp [data-testid="stBaseButton-secondary"]:hover { border-color: var(--jm-accent); color: var(--jm-accent); }
[data-testid="stDialog"] [role="dialog"] { border-radius: 16px; border: 1px solid var(--jm-border); }
[data-testid="stPopoverBody"] { border-radius: 12px; }
/* ---- notices (could-not-verify, AI not available, data warnings) */
.stApp [data-testid="stAlertContainer"] { border-radius: 12px; border: 1px solid var(--jm-border); }
.stApp [data-testid="stAlertContentError"], .stApp [data-testid="stAlertContentWarning"] { font-size: .97rem; }
/* ---- data cards (ui_components) */
.jm-card { background: var(--jm-surface); border: 1px solid var(--jm-border) !important;
  border-left: 4px solid var(--jm-accent) !important; border-radius: 12px; padding: .75rem .85rem; box-shadow: none; }
.jm-card.soil { border-left-color: #8B6B47 !important; } .jm-card.crop { border-left-color: var(--jm-ok) !important; }
.jm-card .jm-k { font-size: .72rem; color: var(--jm-muted); opacity: 1; font-weight: 600; letter-spacing: .04em; }
.jm-card .jm-v { font-size: 1.25rem; font-weight: 700; color: var(--jm-text); line-height: 1.3; }
.jm-card .jm-s { margin-top: .3rem; opacity: 1; display: flex; flex-wrap: wrap; gap: .25rem; }
.jm-chip { display: inline-block; font-size: .7rem; line-height: 1.4; padding: .05rem .45rem; border-radius: 999px;
  background: var(--jm-surface2); color: var(--jm-muted); border: 1px solid var(--jm-border); white-space: nowrap; }
.jm-chip.src { color: var(--jm-accent); background: var(--jm-accent-soft); border-color: transparent; }
"""


def palette_name(theme_choice, streamlit_type="light"):
    """'light' or 'dark' for the chosen theme ('system' follows what the browser reports)."""
    if theme_choice == "day":
        return "light"
    if theme_choice == "night":
        return "dark"
    return "dark" if streamlit_type == "dark" else "light"


def css_variables(name):
    p = PALETTES[name]
    lines = [f"--jm-{k}: {v};" for k, v in p.items()] + [f"--jm-font: {FONT};"]
    return ":root, .stApp {" + " ".join(lines) + " color-scheme: " + name + "; }"


def theme_css(name):
    return "<style>" + css_variables(name) + BASE_CSS + "</style>"


def sync_script(theme_choice):
    """JS (runs in the page) that applies a forced Day / Night choice to Streamlit's own theme switch.

    Streamlit keeps the reader's theme in localStorage ("stActiveTheme-<path>-v2" = "Light" | "Dark" | "System").
    If it differs from the JalMitra setting, the entry is updated and the page reloads once (the open chat is kept
    in the address as ?c=<id>, settings and history are on disk). A guard stops reload loops.
    """
    want = json.dumps(STREAMLIT_THEME.get(theme_choice, "System"))
    return f"""<script>
(function() {{
  try {{
    var want = {want};
    var paths = [window.location.pathname, "/", "/chat"];
    var cur = window.localStorage.getItem("stActiveTheme-" + window.location.pathname + "-v2");
    var have = cur ? JSON.parse(cur) : "System";
    if (have === want) return;
    paths.forEach(function(p) {{ window.localStorage.setItem("stActiveTheme-" + p + "-v2", JSON.stringify(want)); }});
    var last = Number(window.sessionStorage.getItem("jmThemeReload") || 0);
    if (Date.now() - last > 8000) {{
      window.sessionStorage.setItem("jmThemeReload", String(Date.now()));
      window.location.reload();
    }}
  }} catch (e) {{}}
}})();
</script>"""


def apply(theme_choice, streamlit_type="light"):
    """Inject the palette CSS and the theme switch for this run. Returns the palette name used."""
    name = palette_name(theme_choice, streamlit_type)
    st.html(theme_css(name))
    st.html(sync_script(theme_choice), unsafe_allow_javascript=True)
    return name
