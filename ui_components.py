"""
ui_components.py - Shared building blocks of the JalMitra 3.0 website (Streamlit).

  * CSS for the hero banner and cards (works in the light and dark theme)
  * location lists for the selectors (from the database index only)
  * groundwater cards: a card is shown only for a value that exists in the
    database; a missing value says "Data unavailable" (never 0); every card
    names its source and assessment year
  * "Data unavailable" panels for topics without data
  * chat message rendering, charts, CSV / Markdown report downloads
"""

import csv
import datetime as dt
import io
from pathlib import Path

import pandas as pd
import streamlit as st

import database as db
import entity_resolver as er
import language as L
import response_builder as rb
from retrieval import fmt, numbers_available
from ui_text import u

BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
CAT_COLORS = {"Safe": "#2e9e4f", "Semi-critical": "#e0b400", "Critical": "#f07f1d", "Over-exploited": "#d62728",
              "Saline": "#8c8c8c"}
FEEDBACK_FILE = BASE / "feedback" / "feedback_log.csv"

CSS = """
<style>
:root { --jm-navy:#0B3B5B; --jm-blue:#1E6FA8; --jm-green:#2F7D32; --jm-earth:#8B6B47; }
.jm-hero { background: linear-gradient(120deg, #0B3B5B 0%, #1E6FA8 55%, #2F7D32 100%);
  color:#fff; border-radius: 18px; padding: 1.6rem 1.8rem 1.4rem; margin-bottom: .6rem; }
.jm-hero h1 { color:#fff; font-size: 2.1rem; margin: 0 0 .2rem; padding:0; line-height:1.2; }
.jm-hero .jm-tag { font-size: 1.05rem; font-weight: 600; opacity: .95; margin: 0 0 .7rem; }
.jm-hero p { color:#F1F7FB; margin: .2rem 0; font-size: 1.02rem; }
.jm-hero .jm-sub { font-size: 1.15rem; font-weight: 600; }
.jm-card { border:1px solid rgba(128,128,128,.28); border-radius: 14px; padding: .85rem 1rem; height: 100%;
  border-left: 6px solid var(--jm-blue); }
.jm-card.soil { border-left-color: var(--jm-earth); }
.jm-card.crop { border-left-color: var(--jm-green); }
.jm-card .jm-k { font-size: .85rem; opacity: .8; text-transform: uppercase; letter-spacing: .03em; }
.jm-card .jm-v { font-size: 1.45rem; font-weight: 700; margin: .1rem 0 .2rem; }
.jm-card .jm-s { font-size: .82rem; opacity: .78; }
.jm-na { display:inline-block; padding: .1rem .55rem; border-radius: 999px; font-size: .85rem; font-weight: 600;
  background: rgba(139,107,71,.16); color: inherit; border: 1px solid rgba(139,107,71,.45); }
.jm-ok { display:inline-block; padding: .1rem .55rem; border-radius: 999px; font-size: .85rem; font-weight: 600;
  background: rgba(47,125,50,.15); border: 1px solid rgba(47,125,50,.45); }
.jm-cat { display:inline-block; width:.8rem; height:.8rem; border-radius:3px; margin-right:.35rem; vertical-align:middle; }
.jm-step { font-size: 1.6rem; font-weight: 800; color: var(--jm-blue); }
div[data-testid="stChatMessage"] p { font-size: 1.04rem; line-height: 1.6; }
@media (max-width: 640px) {
  .jm-hero { padding: 1.1rem 1rem; } .jm-hero h1 { font-size: 1.6rem; }
  .jm-card .jm-v { font-size: 1.2rem; }
}
</style>
"""


def inject_css():
    st.html(CSS)


def theme_type():
    try:
        return st.context.theme.type or "light"
    except Exception:  # noqa: BLE001 - older Streamlit
        return "light"


# ------------------------------------------------------------------ locations (database index only)

@st.cache_data(show_spinner=False)
def location_tree():
    """{state: {district: [unit names]}} from the database index."""
    tree = {}
    for p in er.index()["places"]:
        if p["type"] == "unit":
            tree.setdefault(p["state"], {}).setdefault(p["district"], []).append(p["name"])
    return {s: {d: sorted(us) for d, us in sorted(ds.items())} for s, ds in sorted(tree.items())}


def place_for(state, district=None, unit=None):
    """The database place dict for a selection, or None."""
    if not state:
        return None
    for p in er.index()["places"]:
        if unit and p["type"] == "unit" and p["state"] == state and p["district"] == district and p["name"] == unit:
            return p
        if not unit and district and p["type"] == "district" and p["state"] == state and p["district"] == district:
            return p
        if not unit and not district and p["type"] == "state" and p["state"] == state:
            return p
    return None


@st.cache_data(show_spinner=False)
def all_place_options():
    """Every place as (key, label) for search boxes; key = 'type|state|district|name'."""
    out = []
    for p in er.index()["places"]:
        key = f"{p['type']}|{p['state']}|{p.get('district') or ''}|{p['name']}"
        if p["type"] == "unit":
            label = f"{rb.show_name(p['name'])} — {p.get('kind') or 'unit'}, {rb.show_name(p['district'])}, {p['state']}"
        elif p["type"] == "district":
            label = f"{rb.show_name(p['district'])} — district, {p['state']}"
        else:
            label = f"{p['state']} — state"
        out.append((key, label))
    order = {"state": 0, "district": 1, "unit": 2}
    return sorted(out, key=lambda kv: (order[kv[0].split("|")[0]], kv[1]))


def place_from_key(key):
    if not key:
        return None
    kind, state, district, name = key.split("|", 3)
    return place_for(state, district or None, name if kind == "unit" else None)


def place_title(p, lang):
    return rb.place_label(p, lang) if p else ""


# ------------------------------------------------------------------ cards

def _chips(sub):
    """Card footnote as small chips: 'Source: X p3 · Year 2025' -> [Source: X p3] [Year 2025] (UI redesign)."""
    parts = [p.strip() for p in (sub or "").split(" · ") if p.strip()]
    return "".join(f'<span class="jm-chip{" src" if i == 0 and len(parts) > 1 else ""}">{p}</span>'
                   for i, p in enumerate(parts))


def _card(label, value, sub, kind=""):
    value_html = value if value is not None else f'<span class="jm-na">{label_na()}</span>'
    st.html(f'<div class="jm-card {kind}"><div class="jm-k">{label}</div><div class="jm-v">{value_html}</div>'
            f'<div class="jm-s">{_chips(sub)}</div></div>')


_NA = {"text": "Data unavailable"}


def label_na():
    return _NA["text"]


def set_ui_lang(lang):
    _NA["text"] = u("data_unavailable", lang)


def _vol(orig, unit, bcm):
    if orig is None:
        return None
    if unit == "bcm" or bcm is None:
        return f"{fmt(orig)} {unit or ''}".strip()
    return f"{fmt(orig)} {unit}<br><span style='font-size:.8rem;opacity:.8'>{fmt(bcm)} bcm</span>"


def unit_cards(r, ui, lang):
    """Groundwater cards for one assessment unit (only database values)."""
    year = r["year"]
    cat_src = f"{u('source', ui)}: {r['source_id']} p{r['source_page']} · {u('year', ui)} {year}"
    fig_src = (f"{u('source', ui)}: {r['values_source_id']} p{r['values_source_page']} · {u('year', ui)} {year}"
               if r.get("values_source_id") else f"{u('source', ui)}: — · {u('year', ui)} {year}")
    color = CAT_COLORS.get(r["category"], "#888")
    cat_html = f'<span class="jm-cat" style="background:{color}"></span>{L.category_label(r["category"], lang)}'
    cols = st.columns(5)
    with cols[0]:
        _card(u("category", ui), cat_html, cat_src)
    has = numbers_available(r)
    st_val = f"{fmt(r['stage_of_extraction_pct'])}%" if has and r["stage_of_extraction_pct"] is not None else None
    with cols[1]:
        _card(u("stage", ui), st_val, fig_src)
    with cols[2]:
        _card(u("recharge", ui), _vol(r["annual_recharge_original"], r["annual_recharge_original_unit"],
                                      r["annual_recharge_bcm"]) if has else None, fig_src)
    with cols[3]:
        _card(u("extractable", ui), _vol(r["extractable_resource_original"], r["extractable_resource_original_unit"],
                                         r["extractable_resource_bcm"]) if has else None, fig_src)
    with cols[4]:
        _card(u("extraction", ui), _vol(r["total_extraction_original"], r["total_extraction_original_unit"],
                                        r["total_extraction_bcm"]) if has else None, fig_src)


def area_cards(place, ui, lang):
    """Cards for a district or state: unit counts by category and the National Compilation totals."""
    state = place["state"]
    district = place["district"] if place["type"] == "district" else None
    counts = db.category_counts(state, district)
    total = sum(counts.values())
    numeric = db.numeric_unit_count(state, district)
    year = ", ".join(db.years())
    src = f"{u('source', ui)}: AI2025 · {u('year', ui)} {year}"
    cols = st.columns(3)
    with cols[0]:
        _card(u("units", ui), f"{total:,}", src)
    report_n = _state_report_units(state, district) if not numeric else 0    # 24 Nov: CGWB 2025 state reports
    with cols[1]:
        if numeric or not report_n:
            _card(u("units_with_figures", ui), f"{numeric:,} / {total:,}" if numeric else None,
                  f"{u('source', ui)}: RJ2025 · {u('year', ui)} {year}" if numeric else src)
        else:
            _card(u("units_with_figures", ui), f"{report_n:,} / {total:,}",
                  f"{u('source', ui)}: CGWB {state} 2025 · {u('year', ui)} {year}")
    nc = db.national_district_summary(district, state) if district else db.national_state_summary(state)
    nc = nc[0] if len(nc) == 1 else None
    with cols[2]:
        stage = f"{fmt(nc['stage_of_extraction_pct'])}%" if nc and nc["stage_of_extraction_pct"] is not None else None
        _card(u("stage", ui), stage,
              (f"{u('source', ui)}: NC2025 p{nc['source_page']} · {u('year', ui)} {nc['year']} · "
               f"{u('area_total_note', ui)}") if nc else f"{u('source', ui)}: NC2025")
    category_count_cards(counts, src, lang)
    if nc:
        cols = st.columns(3)
        with cols[0]:
            _card(u("recharge", ui), _vol(nc["annual_recharge"], nc["original_unit"], nc["annual_recharge_bcm"]),
                  f"NC2025 p{nc['source_page']} · {u('area_total_note', ui)}")
        with cols[1]:
            _card(u("extractable", ui), _vol(nc["extractable_resource"], nc["original_unit"], nc["extractable_resource_bcm"]),
                  f"NC2025 p{nc['source_page']} · {u('area_total_note', ui)}")
        with cols[2]:
            _card(u("extraction", ui), _vol(nc["total_extraction"], nc["original_unit"], nc["total_extraction_bcm"]),
                  f"NC2025 p{nc['source_page']} · {u('area_total_note', ui)}")
    return counts


def _state_report_units(state, district):
    """Units of a district / state with figures in the CGWB 2025 state report (read-only lookup), 0 if none."""
    try:
        import gwra_blocks_retrieval as gwra
        if district:
            r = gwra.district_units(state, district)
            return r.get("units_with_figures", 0) if r.get("status") == "ok" else 0
        r = gwra.state_coverage(state)
        return (r.get("usable") or 0) if r.get("status") == "ok" else 0
    except Exception:                                    # noqa: BLE001 - optional data; never breaks a page
        return 0


def category_count_cards(counts, src, lang, ncols=5):
    """One card per category with its number of assessment units (database counts)."""
    cols = st.columns(ncols)
    for i, cat in enumerate(db.CATEGORIES):
        with cols[i % ncols]:
            _card(f'<span class="jm-cat" style="background:{CAT_COLORS[cat]}"></span>{L.category_label(cat, lang)}',
                  f"{counts.get(cat, 0):,}", src)


def unavailable_panel(title, items, ui, kind="soil", lang="en"):
    """'Data unavailable' cards for a topic with no data (no buttons that do nothing)."""
    st.markdown(f"#### {title}")
    cols = st.columns(min(4, max(1, len(items))))
    for i, item in enumerate(items):
        with cols[i % len(cols)]:
            _card(item, None, u("coming_phase", ui), kind)


def counts_chart(counts_by_area):
    df = pd.DataFrame.from_dict(counts_by_area, orient="index").reindex(columns=db.CATEGORIES).fillna(0).astype(int)
    st.bar_chart(df, y=db.CATEGORIES, y_label="assessment units", color=[CAT_COLORS[c] for c in db.CATEGORIES])


# ------------------------------------------------------------------ chat messages

def show_chart(chart, ui):
    data = chart["data"]
    if chart["type"] == "counts":
        counts_chart(data)
    elif chart["type"] == "stage":
        st.bar_chart(pd.DataFrame({"stage of extraction (%)": data}), y_label="stage of extraction (%)")
    else:
        st.bar_chart(pd.DataFrame({"assessment units": data}), y_label="assessment units")
    st.caption(u("chart_note", ui))


def csv_bytes(rows):
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8-sig")


def report_markdown(chat, title="JalMitra conversation report"):
    """Markdown report of the session: questions, answers, warnings, sources."""
    lines = [f"# {title}", "", f"Created {dt.datetime.now():%Y-%m-%d %H:%M} by JalMitra 3.0 (offline engine).",
             "Answers come only from the official groundwater assessment database; missing values are reported "
             "as not available.", ""]
    for m in chat:
        if m["role"] == "user":
            lines += [f"## Q: {m['text']}", ""]
        else:
            lines += [m["text"], ""]
            if m.get("year"):
                lines.append(f"_Assessment year: {m['year']}_")
            for w in m.get("warnings") or []:
                lines.append(f"> Warning: {w}")
            for s in m.get("sources") or []:
                lines.append(f"- Source {s.get('source_id')} p{s.get('page')}: {s.get('title') or ''} "
                             f"({s.get('used_for')}) {s.get('url') or ''}")
            lines.append("")
    return "\n".join(lines).encode("utf-8")


def save_feedback(question, intent, rating):
    """Rating of an answer, kept in a local CSV on this computer (no personal data, nothing uploaded)."""
    FEEDBACK_FILE.parent.mkdir(exist_ok=True)
    new = not FEEDBACK_FILE.exists()
    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "question", "intent", "rating"])
        w.writerow([dt.datetime.now().isoformat(timespec="seconds"), question, intent,
                    "helpful" if rating == 1 else "not helpful"])
