"""
build_dataset.py - Build the JalMitra preview dataset from the three official
PDFs in data/raw/, and write a data-quality report.

PREVIEW ONLY. This script does NOT create or change groundwater.db.
It never edits the files in data/raw/. It never fills in a missing value.

Sources (identified by the text inside each PDF, not by file name):
  AI2025   All India Blockwise GWRA 2025 (assessment-unit categories)
  RJ2025   Dynamic Ground Water Resources of Rajasthan - 2025 (block values)
  NC2025   National Compilation on Dynamic Ground Water Resources of India, 2025
           (state and district summaries, used ONLY for validation)

Run from the JalMitra folder:
    pip install pdfplumber
    python build_dataset.py

Outputs (all inside data/):
    groundwater.csv          one row per assessment unit (primary preview dataset)
    data_sources.csv         source metadata
    import_errors.csv        problematic rows (kept, never dropped)
    duplicate_records.csv    overlapping / duplicate records
    quality_report.csv       every check with PASS / WARN / INFO
    processed/               cleaned per-source extracts + proposed schema
"""

import argparse
import csv
import hashlib
import io
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import extract_data  # Rajasthan Annexure VI extractor (same folder)

HAM_PER_BCM = 100000  # 1 BCM = 100,000 hectare-metres

CATEGORY_MAP = {
    "safe": "Safe", "semi_critical": "Semi-critical", "critical": "Critical",
    "over_exploited": "Over-exploited", "salinity": "Saline", "saline": "Saline",
}

# Display names used in the National Compilation, for the spellings found in
# the All India list. The published spelling is always kept in `state`.
STATE_STANDARD = {
    "ANDAMAN AND NICOBAR ISLANDS": "Andaman And Nicobar", "ANDHRA PRADESH": "Andhra Pradesh",
    "ARUNACHAL PRADESH": "Arunachal Pradesh", "ASSAM": "Assam", "BIHAR": "Bihar",
    "CHANDIGARH": "Chandigarh", "CHHATTISGARH": "Chhattisgarh",
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": "Dadra and Nagar Haveli and Daman and Diu",
    "DELHI": "Delhi", "GOA": "Goa", "GUJARAT": "Gujarat", "HARYANA": "Haryana",
    "HIMACHAL PRADESH": "Himachal Pradesh", "JAMMU AND KASHMIR": "Jammu And Kashmir",
    "JHARKHAND": "Jharkhand", "KARNATAKA": "Karnataka", "KERALA": "Kerala",
    "LADAKH": "Ladakh", "LAKSHADWEEP": "Lakshadweep", "MADHYA PRADESH": "Madhya Pradesh",
    "MAHARASHTRA": "Maharashtra", "MANIPUR": "Manipur", "MEGHALAYA": "Meghalaya",
    "MIZORAM": "Mizoram", "NAGALAND": "Nagaland", "ODISHA": "Odisha",
    "PUDUCHERRY": "Puducherry", "PUNJAB": "Punjab", "RAJASTHAN": "Rajasthan",
    "SIKKIM": "Sikkim", "TAMILNADU": "Tamil Nadu", "TELANGANA": "Telangana",
    "TRIPURA": "Tripura", "UTTAR PRADESH": "Uttar Pradesh", "UTTARAKHAND": "Uttarakhand",
    "WEST BENGAL": "West Bengal",
}

# Assessment-unit type per state, from the note under "Categorization of
# Blocks/Mandals/Talukas in India (2025)", National Compilation PDF page 213.
UNIT_TYPE_NOTE_PAGE = 213
UNIT_TYPE_BY_STATE = {
    **{s: "Block" for s in [
        "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Haryana",
        "Himachal Pradesh", "Jharkhand", "Kerala", "Madhya Pradesh", "Manipur",
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
        "Sikkim", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Andaman And Nicobar", "Jammu And Kashmir", "Ladakh", "Lakshadweep"]},
    **{s: "Taluk" for s in ["Goa", "Gujarat", "Karnataka", "Maharashtra", "Tamil Nadu", "Puducherry"]},
    "Andhra Pradesh": "Mandal", "Telangana": "Mandal",
    "Dadra and Nagar Haveli and Daman and Diu": "District",
    "Chandigarh": "UT", "Delhi": "Tehsil",
}

GW_COLUMNS = [
    "record_id", "state", "state_standard", "district", "assessment_unit",
    "assessment_unit_type", "assessment_unit_type_source",
    "assessment_year", "publication_year",
    "category", "category_raw",
    "annual_recharge_ham", "extractable_resource_ham", "total_extraction_ham",
    "stage_of_extraction_pct",
    "annual_recharge_bcm", "extractable_resource_bcm", "total_extraction_bcm",
    "original_volume_unit",
    "category_source_id", "category_source_page", "category_source_serial",
    "values_source_id", "values_source_page", "values_source_table",
    "values_source_unit_name", "category_in_values_source",
    "quality_flag", "source_note",
]


def norm(text):
    """Key for matching names across sources: upper case, letters/digits only."""
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def open_pdf(path):
    """Open a PDF read-only. Some files have bytes before '%PDF'; we skip them
    in memory only. The file on disk is never changed."""
    import pdfplumber
    data = Path(path).read_bytes()
    start = data.find(b"%PDF")
    note = ""
    if start > 0:
        note = f"file has {start} byte(s) before the %PDF header; read from memory without changing the file"
    return pdfplumber.open(io.BytesIO(data[max(start, 0):])), note


def fnum(text):
    """Printed number -> float. Commas removed. '' or '-' -> None (never 0)."""
    t = (text or "").strip().replace(",", "")
    if t in ("", "-"):
        return None
    return float(t)


def to_bcm(ham_text):
    v = fnum(ham_text)
    if v is None:
        return ""
    return format(v / HAM_PER_BCM, ".10f").rstrip("0").rstrip(".") or "0"


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------ identify files

def identify(raw_dir):
    found = {}
    for path in sorted(Path(raw_dir).glob("*.pdf")):
        pdf, note = open_pdf(path)
        with pdf:
            first = "\n".join((pdf.pages[i].extract_text() or "") for i in range(min(3, len(pdf.pages))))
            pages = len(pdf.pages)
        if "Assessment Unit Name" in first and "Categorization" in first and "GWRA" in first:
            key = "AI2025"
        elif "National Compilation" in first:
            key = "NC2025"
        elif "Ground Water Resources of Rajasthan" in first:
            key = "RJ2025"
        else:
            key = None
        found[key or path.name] = {"path": path, "pages": pages, "read_note": note}
    return found


# ------------------------------------------------------------ All India list

AI_COLS = [("serial", 0), ("state", 75), ("district", 245), ("assessment_unit", 385), ("category_raw", 500)]


def extract_all_india(path):
    """Read every row by word position. Column left edges come from the page layout."""
    rows, problems = [], []
    pdf, _ = open_pdf(path)
    with pdf:
        for pno, page in enumerate(pdf.pages, 1):
            # Group words into printed lines. Words of one line can differ in
            # 'top' by a fraction of a point, so allow a 3-point tolerance.
            lines, current, line_top = [], [], None
            for w in sorted(page.extract_words(), key=lambda w: w["top"]):
                if line_top is None or w["top"] - line_top > 3:
                    if current:
                        lines.append(current)
                    current, line_top = [], w["top"]
                current.append(w)
            if current:
                lines.append(current)
            for line in lines:
                words = sorted(line, key=lambda w: w["x0"])
                if not words or not words[0]["text"].isdigit():
                    continue
                cells = {name: [] for name, _ in AI_COLS}
                for w in words:
                    col = [name for name, x in AI_COLS if w["x0"] >= x][-1]
                    cells[col].append(w["text"])
                row = {k: " ".join(v) for k, v in cells.items()}
                row["page"] = pno
                if not all(row[k] for k, _ in AI_COLS):
                    problems.append({**row, "issue": "a column is empty after reading"})
                rows.append(row)
    return rows, problems


# ------------------------------------------------------------ National Compilation

NUM = r"(?:-?\d[\d,]*(?:\.\d+)?|-)"  # numbers may have thousands commas; "-" = not given


def extract_national(path):
    """Annexure I (state, bcm) page 169-170 and Annexure II (district, ham) pages 173-210.
    Also the state totals in 'Categorization of Blocks/Mandals/Talukas' page 213."""
    state_rows, district_rows, district_totals, counts = [], [], [], {}
    num14 = re.compile(rf"^(\d+)\s+(.+?)\s+((?:{NUM}\s+){{13}}{NUM})$")
    tot14 = re.compile(rf"^(Total\(Ham\)|Total\(Bcm\)|Grand Total)\s+((?:{NUM}\s+){{13}}{NUM})$")
    fields = ["recharge_rainfall_monsoon", "recharge_other_monsoon", "recharge_rainfall_nonmonsoon",
              "recharge_other_nonmonsoon", "annual_recharge", "natural_discharge",
              "extractable_resource", "irrigation_use", "industrial_use", "domestic_use",
              "total_extraction", "domestic_allocation_2030", "net_availability_future",
              "stage_of_extraction_pct"]
    pdf, _ = open_pdf(path)
    with pdf:
        for pno in range(169, 211):
            text = pdf.pages[pno - 1].extract_text() or ""
            state = None
            m = re.search(r"RESOURCES OF INDIA, 2025\s*\n\s*([A-Z][A-Z &]+)\s*\n", text)
            if m:
                state = m.group(1).strip()
            level = "state" if pno <= 170 else "district"
            lines = [l.strip() for l in text.splitlines()]
            for idx, line in enumerate(lines):
                mm = num14.match(line)
                nameless = re.match(rf"^(\d+)\s+((?:{NUM}\s+){{13}}{NUM})$", line)
                if mm and not re.search(r"[A-Za-z]", mm.group(2)):
                    mm = None  # the printed column-number row "1 2 3 ... 16"
                if mm or nameless:
                    wrapped = ""
                    if mm:
                        serial, name, vals = mm.group(1), mm.group(2), mm.group(3).split()
                    else:
                        # Long names are printed above and below the number row.
                        serial, vals = nameless.group(1), nameless.group(2).split()
                        parts = []
                        for j in (idx - 1, idx + 1):
                            if 0 <= j < len(lines) and lines[j] and not re.search(r"\d", lines[j]) and len(lines[j]) < 40:
                                parts.append(lines[j])
                        name = "".join(parts) if parts else ""
                        wrapped = "yes"
                    rec = {"page": pno, "serial": serial, "name": name, "state": state or "",
                           "unit": "bcm" if level == "state" else "ham", "name_was_wrapped": wrapped}
                    rec.update(dict(zip(fields, vals)))
                    (state_rows if level == "state" else district_rows).append(rec)
                    continue
                tm = tot14.match(line)
                if tm:
                    vals = tm.group(2).split()
                    district_totals.append({"page": pno, "level": level, "state": state or "",
                                            "label": tm.group(1), **dict(zip(fields, vals))})
        # Annexure IV(A): names of semi-critical / critical / over-exploited units, one state per page
        for pno in range(366, 403):
            t = pdf.pages[pno - 1].extract_text() or ""
            m = re.search(r"CATEGORIZATION of ASSESSMENT UNITS, 2025\s*\n\s*([A-Z][A-Z &]+)\s*\n", t)
            if m:
                counts.setdefault("__iva__", {}).setdefault(m.group(1).strip(), []).append((pno, t))
        # per-state category counts (page 213), read by column position
        page = pdf.pages[UNIT_TYPE_NOTE_PAGE - 1]
        words = page.extract_words()
        nos_x = sorted(w["x0"] for w in words if w["text"] == "Nos.")
        cat_cols = dict(zip(["Safe", "Semi-critical", "Critical", "Over-exploited", "Saline"], nos_x))
        lines, current, line_top = [], [], None
        for w in sorted(words, key=lambda w: w["top"]):
            if line_top is None or w["top"] - line_top > 3:
                if current:
                    lines.append(current)
                current, line_top = [], w["top"]
            current.append(w)
        if current:
            lines.append(current)
        for line in lines:
            line = sorted(line, key=lambda w: w["x0"])
            if not line[0]["text"].isdigit() and line[0]["text"] not in ("Haveli", "Grand"):
                continue
            name = " ".join(w["text"] for w in line if w["x0"] < 140 and not w["text"].isdigit())
            nums = [w for w in line if w["x0"] >= 140 and re.fullmatch(r"\d+", w["text"])]
            if not name or not nums:
                continue
            if name.startswith("Haveli and Daman"):
                name = "Dadra and Nagar Haveli and Daman and Diu"
            cats = {}
            for c, x in cat_cols.items():
                hit = [w for w in nums if abs(w["x0"] - x) < 14]
                cats[c] = int(hit[0]["text"]) if hit else 0
            counts.setdefault("__by_state__", {})[name] = cats
        # state totals of assessed units (page 213)
        text = page.extract_text() or ""
        for line in text.splitlines():
            mm = re.match(r"^\s*(\d+)\s+([A-Za-z][A-Za-z ]+?)\s+(\d+)\s+(\d+)", line)
            if mm:
                counts[mm.group(2).strip()] = int(mm.group(3))
            gm = re.match(r"^\s*Grand Total\s+(\d+)\s+(\d+)\s+[\d.]+\s+(\d+)\s+[\d.]+\s+(\d+)\s+[\d.]+\s+(\d+)\s+[\d.]+\s+(\d+)", line)
            if gm:
                counts["__grand__"] = dict(zip(["total", "Safe", "Semi-critical", "Critical", "Over-exploited", "Saline"],
                                               map(int, gm.groups())))
        # "Dadra and Nagar / Haveli and Daman and / Diu" is printed over 3 lines
        if "Haveli and Daman and" in counts:
            counts["Dadra and Nagar Haveli and Daman and Diu"] = counts.pop("Haveli and Daman and")
    for r in district_rows:
        for f in fields[:-1]:
            r[f + "_bcm"] = to_bcm(r[f])
    return state_rows, district_rows, district_totals, counts, fields


# ------------------------------------------------------------ main build

def build(raw_dir, out_dir, urls):
    out = Path(out_dir)
    proc = out / "processed"
    quality, errors, dups, conflicts = [], [], [], []

    def q(check_id, scope, check, result, details=""):
        quality.append({"check_id": check_id, "scope": scope, "check": check, "result": result, "details": details})

    files = identify(raw_dir)
    for key in ("AI2025", "RJ2025", "NC2025"):
        if key not in files:
            sys.exit(f"Could not identify source {key} in {raw_dir}. Files: {list(files)}")

    # ---------------- sources
    meta = {
        "AI2025": dict(title="All India Blockwise GWRA 2025 (categorization of assessment units)",
                       publisher="Central Ground Water Board (per source URL; not printed in the PDF)",
                       publication_date="not printed in PDF (PDF file created 2025-12-09)",
                       publication_year="", assessment_year="2025",
                       role="PRIMARY for assessment-unit list and category",
                       original_units="none (no volume values in this file)",
                       notes="Columns: S. No., State, District, Assessment Unit Name, Categorization. "
                             "No recharge, extraction or stage values. PDF title metadata is 'Book1'."),
        "RJ2025": dict(title="Dynamic Ground Water Resources of Rajasthan - 2025",
                       publisher="CGWB Western Region, Jaipur and Ground Water Department, Govt. of Rajasthan",
                       publication_date="November 2025", publication_year="2025", assessment_year="2025",
                       role="Block-level values for Rajasthan; cross-verification of AI2025 Rajasthan rows",
                       original_units="ham (hectare-metres); stage in %",
                       notes="Annexure VI 'Block wise resources of Rajasthan, GWRA-2025', PDF pages 126-136."),
        "NC2025": dict(title="National Compilation on Dynamic Ground Water Resources of India, 2025",
                       publisher="Central Ground Water Board, Ministry of Jal Shakti (ISBN 978-81-984761-6-6)",
                       publication_date="November 2025", publication_year="2025", assessment_year="2025",
                       role="State and district summaries for validation only; never imported as block rows",
                       original_units="Annexure I: bcm; Annexure II: ham; stage in %",
                       notes="Report prints its own link https://cgwb.gov.in/cgwbpnm/publication-detail/1741. "
                             "Annexure I PDF pages 169-170, Annexure II pages 173-210, unit-type note page 213."),
    }
    sources = []
    for key in ("AI2025", "RJ2025", "NC2025"):
        f = files[key]
        sources.append({"source_id": key, "file_name": f["path"].name, "sha256": sha256(f["path"]),
                        "pdf_pages": f["pages"], "source_url": urls[key], **meta[key],
                        "read_note": f["read_note"]})
    write_csv(out / "data_sources.csv", list(sources[0].keys()), sources)

    # ---------------- AI2025
    ai_rows, ai_problems = extract_all_india(files["AI2025"]["path"])
    for p in ai_problems:
        errors.append({"source_id": "AI2025", "record_ref": f"S.No {p.get('serial')}", "page": p["page"],
                       "issue": p["issue"], "action": "kept, flagged"})
    serials = [int(r["serial"]) for r in ai_rows if r["serial"].isdigit()]
    q("AI-01", "AI2025", "rows extracted", "INFO", f"{len(ai_rows)} rows from {files['AI2025']['pages']} pages")
    q("AI-02", "AI2025", "serial numbers continuous 1..N",
      "PASS" if serials == list(range(1, len(serials) + 1)) else "WARN",
      f"first {serials[:1]}, last {serials[-1:]}")
    raw_cats = Counter(r["category_raw"] for r in ai_rows)
    unknown = [c for c in raw_cats if c.strip().lower() not in CATEGORY_MAP]
    q("AI-03", "AI2025", "category values recognised", "PASS" if not unknown else "WARN",
      "; ".join(f"{k}={v}" for k, v in raw_cats.items()))
    mixed_case = {c: n for c, n in raw_cats.items() if c != c.lower()}
    if mixed_case:
        q("AI-04", "AI2025", "category spelling", "INFO",
          f"capitalised variants kept in category_raw: {mixed_case}")

    write_csv(proc / "all_india_blockwise_gwra2025.csv",
              ["serial", "state", "district", "assessment_unit", "category_raw", "page"], ai_rows)

    # ---------------- RJ2025
    rj_rows, rj_pages = extract_data.extract(str(files["RJ2025"]["path"]), "rajasthan_2025_annexure_vi", urls["RJ2025"])
    for r in rj_rows:
        for c in ("annual_recharge_ham", "extractable_resource_ham", "total_extraction_ham"):
            r[c.replace("_ham", "_bcm")] = to_bcm(r[c])
    rj_cols = extract_data.OUTPUT_COLUMNS + ["annual_recharge_bcm", "extractable_resource_bcm", "total_extraction_bcm"]
    write_csv(proc / "rajasthan_gwra2025_blocks.csv", rj_cols, rj_rows)
    q("RJ-01", "RJ2025", "rows extracted", "INFO", f"{len(rj_rows)} rows, PDF pages {rj_pages[0]}-{rj_pages[-1]}")
    rj_cat = Counter(r["category"] for r in rj_rows)
    expected_rj = {"Safe": 36, "Semi-critical": 27, "Critical": 23, "Over-exploited": 213, "Saline": 3}
    q("RJ-02", "RJ2025", "row and category counts vs report's own Annexure III(A) (page 110)",
      "PASS" if dict(rj_cat) == expected_rj and len(rj_rows) == 302 else "WARN",
      f"extracted {dict(rj_cat)}; report 302 = {expected_rj}")
    for r in rj_rows:
        if r["check_status"] != "ok":
            errors.append({"source_id": "RJ2025", "record_ref": f"{r['district']} / {r['assessment_unit']}",
                           "page": r["source_page"], "issue": r["check_notes"], "action": "kept as published, flagged"})

    # ---------------- NC2025
    nc_states, nc_districts, nc_totals, nc_counts, nc_fields = extract_national(files["NC2025"]["path"])
    write_csv(proc / "national_state_summary_2025.csv",
              ["page", "serial", "name", "unit"] + nc_fields, nc_states)
    write_csv(proc / "national_district_summary_2025.csv",
              ["page", "state", "serial", "name", "name_was_wrapped", "unit"] + nc_fields + [f + "_bcm" for f in nc_fields[:-1]],
              nc_districts)
    write_csv(proc / "national_published_totals_2025.csv",
              ["page", "level", "state", "label"] + nc_fields, nc_totals)
    q("NC-01", "NC2025", "state rows (Annexure I)", "INFO", f"{len(nc_states)} rows")
    q("NC-02", "NC2025", "district rows (Annexure II)", "INFO",
      f"{len(nc_districts)} rows across {len({r['state'] for r in nc_districts})} states/UTs")
    # district sums vs printed Total(Ham) per state
    by_state = defaultdict(list)
    for r in nc_districts:
        by_state[r["state"]].append(r)
    bad, swapped = [], []
    totals_by_state = defaultdict(list)
    for t in nc_totals:
        if t["level"] == "district" and t["label"] in ("Total(Ham)", "Total(Bcm)"):
            totals_by_state[(t["state"], t["page"])].append(t)
    for (st, page), ts in totals_by_state.items():
        # Use the larger of the two printed totals as the ham total; note if the
        # labels look swapped in the report.
        ham = max(ts, key=lambda t: fnum(t["annual_recharge"]) or 0)
        if ham["label"] != "Total(Ham)":
            swapped.append(f"{st} (p{page})")
        rows = by_state.get(st, [])  # some states continue over two pages
        s = sum(fnum(r["annual_recharge"]) or 0 for r in rows)
        if abs(s - (fnum(ham["annual_recharge"]) or 0)) > 1:
            bad.append(f"{st} (p{page}): {len(rows)} district rows sum {s:.2f} vs printed total {ham['annual_recharge']}")
    q("NC-03", "NC2025", "district recharge rows add up to printed state total (ham)",
      "PASS" if not bad else "WARN", "; ".join(bad) or "all states match")
    if swapped:
        q("NC-04", "NC2025", "Total(Ham)/Total(Bcm) labels look swapped as printed", "WARN", "; ".join(swapped))
    wrapped_names = [f"{r['state']} {r['serial']} '{r['name']}' (p{r['page']})" for r in nc_districts if r.get("name_was_wrapped")]
    if wrapped_names:
        q("NC-05", "NC2025", "district names printed over several lines (joined; please check)", "INFO", "; ".join(wrapped_names))

    # ---------------- cross-checks AI vs NC
    ai_state_counts = Counter(STATE_STANDARD.get(r["state"].upper(), r["state"]) for r in ai_rows)
    diffs = []
    for st, n in sorted(ai_state_counts.items()):
        printed = nc_counts.get(st)
        if printed is None:
            diffs.append(f"{st}: not found on NC page 213")
        elif printed != n:
            diffs.append(f"{st}: AI {n} vs NC {printed}")
    q("X-01", "AI2025 vs NC2025", "assessment units per state vs NC page 213",
      "PASS" if not diffs else "WARN", "; ".join(diffs) or f"all {len(ai_state_counts)} states/UTs match")
    ai_cat = Counter(CATEGORY_MAP.get(r["category_raw"].lower(), "?") for r in ai_rows)
    grand = nc_counts.get("__grand__", {})
    cat_diff = {k: (ai_cat.get(k, 0), v) for k, v in grand.items() if k != "total" and ai_cat.get(k, 0) != v}
    q("X-02", "AI2025 vs NC2025", "national category totals vs NC page 213 Grand Total",
      "PASS" if not cat_diff and grand.get("total") == len(ai_rows) else "WARN",
      f"AI {dict(ai_cat)}; NC {grand}" + (f"; differences (AI, NC): {cat_diff}" if cat_diff else ""))
    per_state = defaultdict(Counter)
    for r in ai_rows:
        per_state[STATE_STANDARD.get(r["state"].upper(), r["state"])][CATEGORY_MAP.get(r["category_raw"].lower(), "?")] += 1
    st_diffs = []
    for st, cats in sorted(nc_counts.get("__by_state__", {}).items()):
        if st == "Grand Total":
            continue
        for c, n in cats.items():
            if per_state.get(st, Counter()).get(c, 0) != n:
                st_diffs.append(f"{st} {c}: AI {per_state.get(st, Counter()).get(c, 0)} vs NC {n}")
    q("X-02b", "AI2025 vs NC2025", "category counts per state vs NC page 213",
      "PASS" if not st_diffs else "WARN", "; ".join(st_diffs) or "all states match")
    differing = set()
    for st, cats in nc_counts.get("__by_state__", {}).items():
        for c, n in cats.items():
            # flag rows only in the category where AI2025 has MORE units than NC2025
            if st != "Grand Total" and per_state.get(st, Counter()).get(c, 0) > n:
                differing.add((st, c))

    # ---------------- duplicates inside AI2025
    seen = defaultdict(list)
    for r in ai_rows:
        seen[(norm(r["state"]), norm(r["district"]), norm(r["assessment_unit"]))].append(r)
    n_dup = 0
    for key, group in seen.items():
        if len(group) > 1:
            n_dup += 1
            for r in group:
                dups.append({"duplicate_type": "same state/district/unit inside AI2025",
                             "group_key": " | ".join(key), "source_id": "AI2025",
                             "record_ref": f"S.No {r['serial']}", "page": r["page"],
                             "category": r["category_raw"], "resolution": "all kept; flagged for review"})
    q("D-01", "AI2025", "duplicate state/district/unit inside the All India list",
      "PASS" if n_dup == 0 else "WARN", f"{n_dup} duplicate groups")

    # ---------------- build primary rows, merge RJ values
    rj_index = defaultdict(list)
    for r in rj_rows:
        rj_index[(norm(r["district"]), norm(r["assessment_unit"]))].append(r)
    matched_rj = set()
    gw = []
    for r in ai_rows:
        st_std = STATE_STANDARD.get(r["state"].upper(), "")
        flags, notes = [], []
        if not st_std:
            flags.append("state_name_not_mapped")
        utype = UNIT_TYPE_BY_STATE.get(st_std, "")
        rec = {
            "record_id": f"AI2025-{int(r['serial']):05d}",
            "state": r["state"], "state_standard": st_std, "district": r["district"],
            "assessment_unit": r["assessment_unit"],
            "assessment_unit_type": utype,
            "assessment_unit_type_source": f"NC2025 p{UNIT_TYPE_NOTE_PAGE} state-wise note" if utype else "",
            "assessment_year": "2025", "publication_year": "",
            "category": CATEGORY_MAP.get(r["category_raw"].strip().lower(), ""),
            "category_raw": r["category_raw"],
            "category_source_id": "AI2025", "category_source_page": r["page"],
            "category_source_serial": r["serial"],
            "original_volume_unit": "",
        }
        if not utype:
            flags.append("unit_type_unknown")
        cat_std = CATEGORY_MAP.get(r["category_raw"].strip().lower(), "")
        if (st_std, cat_std) in differing:
            # Look for this unit by name on the state's NC2025 Annexure IV(A) page.
            iva = nc_counts.get("__iva__", {}).get(st_std.upper(), [])
            named = [pno for pno, t in iva if norm(r["assessment_unit"]) in norm(t)]
            iva_pages = ",".join(str(pno) for pno, _ in iva) or "not found"
            if named:
                notes.append(f"NC2025 Annexure IV(A) p{named[0]} names this unit; consistent with AI2025")
            else:
                flags.append("category_conflict_between_sources")
                cid = f"C{len(conflicts) + 1:03d}"
                conflicts.append({"conflict_id": cid, "record_id": f"AI2025-{int(r['serial']):05d}", "state": st_std,
                                  "district": r["district"], "assessment_unit": r["assessment_unit"],
                                  "source_id": "AI2025", "source_page": r["page"],
                                  "observation": f"category printed as '{r['category_raw']}' (S.No {r['serial']})"})
                conflicts.append({"conflict_id": cid, "record_id": f"AI2025-{int(r['serial']):05d}", "state": st_std,
                                  "district": r["district"], "assessment_unit": r["assessment_unit"],
                                  "source_id": "NC2025", "source_page": f"{UNIT_TYPE_NOTE_PAGE}; {iva_pages}",
                                  "observation": f"unit is not named among {st_std}'s semi-critical/critical/over-exploited units "
                                                 f"(Annexure IV(A) p{iva_pages}); state counts on p{UNIT_TYPE_NOTE_PAGE} "
                                                 f"differ by one in this category"})
                errors.append({"source_id": "AI2025 vs NC2025", "record_ref": f"S.No {r['serial']} {r['district']} / {r['assessment_unit']}",
                               "page": r["page"], "issue": "category differs between sources (see category_conflicts.csv " + cid + ")",
                               "action": "both observations recorded; neither chosen as correct"})
        if not rec["category"]:
            flags.append("category_not_recognised")
        if len(seen[(norm(r["state"]), norm(r["district"]), norm(r["assessment_unit"]))]) > 1:
            flags.append("duplicate_in_source")

        match = rj_index.get((norm(r["district"]), norm(r["assessment_unit"]))) if st_std == "Rajasthan" else None
        prefix_match = False
        if st_std == "Rajasthan" and not match:
            # A name cut off in the RJ2025 PDF (e.g. 'GADRARO' for 'GADRAROAD'):
            # accept only a single unit in the same district whose name is a prefix.
            cands = [x for (d, u), xs in rj_index.items() for x in xs
                     if d == norm(r["district"]) and u and norm(r["assessment_unit"]).startswith(u)]
            if len(cands) == 1:
                match, prefix_match = cands, True
        if match and len(match) == 1:
            m = match[0]
            if prefix_match:
                flags.append("matched_by_name_prefix")
                notes.append(f"RJ2025 prints the name as '{m['assessment_unit']}'")
            matched_rj.add(id(m))
            rec.update({
                "annual_recharge_ham": m["annual_recharge_ham"], "extractable_resource_ham": m["extractable_resource_ham"],
                "total_extraction_ham": m["total_extraction_ham"], "stage_of_extraction_pct": m["stage_of_extraction_pct"],
                "annual_recharge_bcm": m["annual_recharge_bcm"], "extractable_resource_bcm": m["extractable_resource_bcm"],
                "total_extraction_bcm": m["total_extraction_bcm"], "original_volume_unit": "ham",
                "values_source_id": "RJ2025", "values_source_page": m["source_page"],
                "values_source_table": m["source_table"], "category_in_values_source": m["category_raw"],
                "values_source_unit_name": m["assessment_unit"],
                "publication_year": "2025",
            })
            if m["assessment_unit_type"] and m["assessment_unit_type"].lower() != utype.lower():
                notes.append(f"RJ2025 unit type '{m['assessment_unit_type']}'")
            if m["category"] != rec["category"]:
                flags.append("category_differs_between_sources")
                errors.append({"source_id": "AI2025+RJ2025", "record_ref": rec["record_id"], "page": r["page"],
                               "issue": f"category AI2025 '{r['category_raw']}' vs RJ2025 '{m['category_raw']}'",
                               "action": "kept AI2025 category; RJ2025 category stored alongside"})
            if m["check_status"] != "ok":
                flags.append("values_check_warning")
                notes.append("RJ2025 check: " + m["check_notes"])
            if m["category"] == "Saline" and not m["stage_of_extraction_pct"]:
                flags.append("saline_values_printed_as_zero")
            if m["name_was_wrapped"] == "yes":
                notes.append("name split over two lines in RJ2025 PDF")
            dups.append({"duplicate_type": "same unit in AI2025 and RJ2025 (overlap)",
                         "group_key": f"{norm(r['district'])} | {norm(r['assessment_unit'])}",
                         "source_id": "AI2025+RJ2025",
                         "record_ref": f"AI S.No {r['serial']} (p{r['page']}) = RJ p{m['source_page']}",
                         "page": r["page"], "category": f"{r['category_raw']} / {m['category_raw']}",
                         "resolution": "merged into one record: category from AI2025, values from RJ2025"})
        else:
            if match and len(match) > 1:
                flags.append("ambiguous_match_in_RJ2025")
            if st_std == "Rajasthan" and not match:
                flags.append("not_found_in_RJ2025")
            flags.append("values_not_in_uploaded_sources")
            notes.append("No block-level recharge/extraction values in the uploaded files for this state")
        rec["quality_flag"] = ";".join(flags)
        rec["source_note"] = "; ".join(notes)
        gw.append(rec)

    unmatched_rj = [r for r in rj_rows if id(r) not in matched_rj]
    for r in unmatched_rj:
        errors.append({"source_id": "RJ2025", "record_ref": f"{r['district']} / {r['assessment_unit']}",
                       "page": r["source_page"], "issue": "no matching unit in AI2025",
                       "action": "kept in processed/rajasthan_gwra2025_blocks.csv; not merged"})
    rj_in_ai = sum(1 for g in gw if g["state_standard"] == "Rajasthan")
    q("X-03", "AI2025 vs RJ2025", "Rajasthan units matched by district + unit name",
      "PASS" if not unmatched_rj and len(matched_rj) == rj_in_ai else "WARN",
      f"AI Rajasthan rows {rj_in_ai}, RJ rows {len(rj_rows)}, matched {len(matched_rj)}, RJ unmatched {len(unmatched_rj)}")
    n_catdiff = sum("category_differs_between_sources" in g["quality_flag"] for g in gw)
    q("X-04", "AI2025 vs RJ2025", "category agrees for matched Rajasthan units",
      "PASS" if n_catdiff == 0 else "WARN", f"{n_catdiff} differences")

    # RJ block sums vs NC Annexure II Rajasthan district rows (ham, rounding allowed)
    nc_rj = {norm(r["name"]): r for r in nc_districts if r["state"] == "RAJASTHAN"}
    rj_by_d = defaultdict(list)
    for r in rj_rows:
        rj_by_d[norm(r["district"])].append(r)
    off = []
    for d, rows in sorted(rj_by_d.items()):
        ncr = nc_rj.get(d)
        if not ncr:
            off.append(f"{d}: no NC district row")
            continue
        for f in ("annual_recharge", "extractable_resource", "total_extraction"):
            s = sum(fnum(x[f + "_ham"]) or 0 for x in rows)
            tol = 0.5 * len(rows) + 2
            if abs(s - (fnum(ncr[f]) or 0)) > tol:
                off.append(f"{d} {f}: blocks {s:g} vs NC {ncr[f]} (p{ncr['page']})")
    q("X-05", "RJ2025 vs NC2025", "Rajasthan block values add up to NC district values (rounding allowed)",
      "PASS" if not off else "WARN", "; ".join(off) or f"all {len(rj_by_d)} districts within rounding")

    # ---------------- coverage and missing values
    states = {g["state_standard"] or g["state"] for g in gw}
    districts = {(g["state"], g["district"]) for g in gw}
    with_values = sum(1 for g in gw if g.get("values_source_id"))
    q("C-01", "groundwater.csv", "coverage", "INFO",
      f"{len(gw)} assessment units, {len(states)} states/UTs, {len(districts)} districts")
    q("C-02", "groundwater.csv", "units with recharge/extraction values", "INFO",
      f"{with_values} of {len(gw)} (Rajasthan only); {len(gw) - with_values} have category only")
    q("C-03", "groundwater.csv", "unit types", "INFO", str(dict(Counter(g["assessment_unit_type"] for g in gw))))

    write_csv(out / "groundwater.csv", GW_COLUMNS, gw)
    write_csv(proc / "groundwater_preview.csv", GW_COLUMNS, gw)  # input for build_database.py
    write_csv(out / "import_errors.csv", ["source_id", "record_ref", "page", "issue", "action"], errors)
    write_csv(out / "duplicate_records.csv",
              ["duplicate_type", "group_key", "source_id", "record_ref", "page", "category", "resolution"], dups)
    write_csv(out / "quality_report.csv", ["check_id", "scope", "check", "result", "details"], quality)
    unit_counts = []
    for st, cats in sorted(nc_counts.get("__by_state__", {}).items()):
        if st == "Grand Total":
            continue
        unit_counts.append({"state": st, "total_units": nc_counts.get(st, ""), **cats,
                            "source_id": "NC2025", "source_page": UNIT_TYPE_NOTE_PAGE})
    write_csv(proc / "national_unit_counts_2025.csv",
              ["state", "total_units", "Safe", "Semi-critical", "Critical", "Over-exploited", "Saline",
               "source_id", "source_page"], unit_counts)
    write_csv(out / "category_conflicts.csv",
              ["conflict_id", "record_id", "state", "district", "assessment_unit", "source_id", "source_page", "observation"],
              conflicts)
    (proc / "proposed_schema.sql").write_text(PROPOSED_SCHEMA, encoding="utf-8")
    return gw, quality, errors, dups, sources


PROPOSED_SCHEMA = """-- JalMitra proposed production schema (NOT yet created)

CREATE TABLE data_sources (
    source_id          TEXT PRIMARY KEY,          -- AI2025, RJ2025, NC2025
    file_name          TEXT NOT NULL,
    sha256             TEXT NOT NULL,
    source_url         TEXT NOT NULL,
    title              TEXT NOT NULL,
    publisher          TEXT,
    publication_date   TEXT,
    publication_year   TEXT,
    assessment_year    TEXT NOT NULL,
    role               TEXT,
    original_units     TEXT,
    notes              TEXT,
    imported_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE groundwater (
    record_id                     TEXT PRIMARY KEY,   -- AI2025-00001
    state                         TEXT NOT NULL,      -- as published
    state_standard                TEXT,               -- National Compilation spelling
    district                      TEXT NOT NULL,
    assessment_unit               TEXT NOT NULL,      -- block / taluk / mandal / tehsil ...
    assessment_unit_type          TEXT,               -- NULL when not stated
    assessment_unit_type_source   TEXT,
    assessment_year               TEXT NOT NULL,      -- GWRA year, e.g. 2025
    publication_year              TEXT,               -- separate from assessment year
    category                      TEXT NOT NULL CHECK (category IN
                                    ('Safe','Semi-critical','Critical','Over-exploited','Saline')),
    category_raw                  TEXT NOT NULL,      -- exactly as published
    annual_recharge_ham           REAL,               -- original value, NULL if not published
    extractable_resource_ham      REAL,
    total_extraction_ham          REAL,
    stage_of_extraction_pct       REAL,
    annual_recharge_bcm           REAL,               -- = ham / 100000
    extractable_resource_bcm      REAL,
    total_extraction_bcm          REAL,
    original_volume_unit          TEXT,
    category_source_id            TEXT NOT NULL REFERENCES data_sources(source_id),
    category_source_page          INTEGER NOT NULL,
    category_source_serial        TEXT,
    values_source_id              TEXT REFERENCES data_sources(source_id),
    values_source_page            INTEGER,
    values_source_table           TEXT,
    category_in_values_source     TEXT,
    quality_flag                  TEXT,               -- ; separated codes
    source_note                   TEXT,
    UNIQUE (state, district, assessment_unit, assessment_year)
);

-- State and district summaries from the National Compilation are kept in
-- separate tables so they can never be mixed with assessment-unit rows.
CREATE TABLE national_summary (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    level                           TEXT NOT NULL CHECK (level IN ('state','district')),
    state                           TEXT NOT NULL,
    district                        TEXT,             -- NULL for state rows
    assessment_year                 TEXT NOT NULL,
    original_unit                   TEXT NOT NULL,    -- 'bcm' (Annexure I) or 'ham' (Annexure II)
    annual_recharge                 REAL,             -- in original_unit
    extractable_resource            REAL,
    total_extraction                REAL,
    stage_of_extraction_pct         REAL,
    annual_recharge_bcm             REAL,
    extractable_resource_bcm        REAL,
    total_extraction_bcm            REAL,
    source_id                       TEXT NOT NULL REFERENCES data_sources(source_id),
    source_page                     INTEGER NOT NULL,
    quality_flag                    TEXT,
    source_note                     TEXT
);
"""


def main(argv=None):
    p = argparse.ArgumentParser(description="Build the JalMitra preview dataset (no database).")
    p.add_argument("--raw", default="data/raw")
    p.add_argument("--out", default="data")
    p.add_argument("--url-ai", default="https://cgwb.gov.in/cgwbpnm/public/publication-detail/1913")
    p.add_argument("--url-rj", default="https://cgwb.gov.in/cgwbpnm/public/publication-detail/2120")
    p.add_argument("--url-nc", default="https://www.jalshakti-dowr.gov.in/static/uploads/2025/11/711d8d476bbf498cd90f8038e7371227.pdf")
    a = p.parse_args(argv)
    gw, quality, errors, dups, _ = build(a.raw, a.out, {"AI2025": a.url_ai, "RJ2025": a.url_rj, "NC2025": a.url_nc})
    for row in quality:
        print(f"[{row['result']:4}] {row['check_id']} {row['check']}: {row['details'][:200]}")
    print(f"\ngroundwater.csv rows: {len(gw)} | import_errors: {len(errors)} | duplicate_records: {len(dups)}")
    print("Preview only. groundwater.db was NOT created or changed.")


if __name__ == "__main__":
    main()
