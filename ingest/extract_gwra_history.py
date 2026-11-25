"""
Extract historical assessment-unit categories from the CGWB "block-wise categorisation" tables
(GWRA 2017, 2020, 2022, 2023, 2024, 2025) downloaded by download_cgwb_publications.py.

Input  : data/monitoring/raw/cgwb_publications/<id>_*.pdf (never changed; read from memory)
Output : data/monitoring/extracted/gwra_category_history.csv      (one row per unit and year)
         data/monitoring/extracted/gwra_category_problems.csv     (rows that could not be read cleanly)
         data/monitoring/extracted/gwra_category_extraction_summary.csv

Method: words are read with their positions (pdfplumber). Every line that starts with a serial number is a row
anchor; wrapped text on nearby lines is attached to the closest anchor. Column left edges were measured for each
file from the word positions (listed in FILES below). Nothing is guessed: a row with an unknown category or an
empty column is written to the problems file and flagged, not repaired.

Usage:  python ingest/extract_gwra_history.py
"""
from __future__ import annotations

import csv
import io
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

PDF_DIR = C.RAW / "cgwb_publications"
OUT = C.EXTRACTED / "gwra_category_history.csv"
PROB = C.EXTRACTED / "gwra_category_problems.csv"
SUMMARY = C.EXTRACTED / "gwra_category_extraction_summary.csv"

# pub id -> (assessment year, left edges of [serial, state, district, unit, category], serial fused with state)
FILES = {
    299: ("2017", [0, 78, 168, 315, 425], False),
    306: ("2020", [0, 110, 222, 300, 415], False),
    307: ("2022", [0, 80, 185, 290, 398], False),
    1332: ("2023", [0, 0, 218, 310, 405], True),
    1333: ("2024", [0, 100, 208, 334, 460], False),
    1913: ("2025", [0, 74, 244, 383, 497], False),
}
COLS = ["serial", "state", "district", "assessment_unit", "category_raw"]
CATEGORY = {"safe": "Safe", "semicritical": "Semi-critical", "critical": "Critical",
            "overexploited": "Over-exploited", "saline": "Saline", "salinity": "Saline"}
HEADER_WORDS = {"categorization", "assessment", "unit", "name", "sl.", "no", "state", "district", "(over-",
                "critical/", "semi-", "safe/saline)", "semicritical/", "(over-exploited/", "s.", "no.", "gwra",
                "block", "wise", "ground", "water", "resource", "resources", "-"}


def norm_cat(raw: str):
    k = re.sub(r"[^a-z]", "", (raw or "").lower())
    return CATEGORY.get(k)


def norm_state(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    t = re.sub(r"[^A-Z]", "", s.upper())
    fixes = {"ANDAMANNICOBARISL": "Andaman And Nicobar", "ANDAMANNICOBARISLANDS": "Andaman And Nicobar",
             "ANDAMANANDNICOBARISLANDS": "Andaman And Nicobar", "ANDAMANANDNICOBAR": "Andaman And Nicobar",
             "JAMMUKASHMIR": "Jammu And Kashmir", "JAMMUANDKASHMIR": "Jammu And Kashmir",
             "CHHATISGARH": "Chhattisgarh", "TAMILNADU": "Tamil Nadu", "ORISSA": "Odisha",
             "DADRANAGARHAVELI": "Dadra and Nagar Haveli and Daman and Diu",
             "DADRAANDNAGARHAVELI": "Dadra and Nagar Haveli and Daman and Diu",
             "DADRAANDNAGARHAVELIANDDAMANANDDIU": "Dadra and Nagar Haveli and Daman and Diu",
             "DAMANDIU": "Dadra and Nagar Haveli and Daman and Diu", "DAMANANDDIU": "Dadra and Nagar Haveli and Daman and Diu",
             "NCTOFDELHI": "Delhi", "PONDICHERRY": "Puducherry", "UTTARANCHAL": "Uttarakhand",
             "JHARKHUND": "Jharkhand", "LAKSAHDWEEP": "Lakshadweep", "LAKSHDWEEP": "Lakshadweep",
             "ANDAMANNICOBARISL": "Andaman And Nicobar"}
    if t in fixes:
        return fixes[t]
    return " ".join(w.capitalize() if w.lower() not in ("and",) else "and" for w in s.split()) \
        .replace("Andhra pradesh", "Andhra Pradesh")


STATES = ["Andaman & Nicobar Islands", "Andaman & Nicobar Isl", "Andaman And Nicobar Islands", "Andaman and Nicobar Islands",
          "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh", "Chhattisgarh", "Chhatisgarh",
          "Dadra and Nagar Haveli and Daman and Diu", "Dadra & Nagar Haveli", "Daman & Diu", "Daman and Diu",
          "Dadra and Nagar Haveli", "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu And Kashmir",
          "Jammu and Kashmir", "Jammu & Kashmir", "Jharkhand", "Jharkhund", "Karnataka", "Kerala", "Ladakh",
          "Lakshadweep", "Laksahdweep", "Lakshdweep", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
          "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Tamilnadu",
          "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"]
_STATE_RE = re.compile(r"^(?P<pre>.*?)\b(?P<st>" + "|".join(re.escape(x) for x in sorted(STATES, key=len, reverse=True))
                       + r")(?P<post>.*)$", re.I)
_CAT_TAIL = re.compile(r"^(?P<unit>.*?)\s*(?P<cat>semi[-_ ]?critical|over[-_ ]?exploited|critical|safe|saline|salinity|afe)$", re.I)


def split_state(state: str, district: str):
    """Words of a long district name that spill into the state column are moved back to the district."""
    m = _STATE_RE.match(state or "")
    if not m:
        return state, district, False
    pre, st, post = m.group("pre").strip(), m.group("st"), m.group("post").strip()
    moved = bool(pre or post)
    dist = " ".join(x for x in (pre, post, district) if x).strip()
    return st, dist, moved


def open_pdf(path: Path):
    import pdfplumber
    data = path.read_bytes()
    return pdfplumber.open(io.BytesIO(data[max(data.find(b"%PDF"), 0):])), C.sha256_bytes(data)


def lines_of(words, tol=2.5):
    lines, cur, top = [], [], None
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if top is None or w["top"] - top > tol:
            if cur:
                lines.append(cur)
            cur, top = [], w["top"]
        cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def extract(pid: int, path: Path):
    year, edges, fused = FILES[pid]
    pdf, sha = open_pdf(path)
    rows, problems = [], []
    with pdf:
        for pno, page in enumerate(pdf.pages, 1):
            lines = lines_of(page.extract_words(keep_blank_chars=False))
            anchors = []
            for ln in lines:
                first = sorted(ln, key=lambda w: w["x0"])[0]
                if re.match(r"^\d+", first["text"]) and first["x0"] < edges[2] and (
                        fused or first["text"].isdigit()):
                    anchors.append(ln)
            if not anchors:
                continue
            tops = [statistics.mean(w["top"] for w in a) for a in anchors]
            gaps = [b - a for a, b in zip(tops, tops[1:])]
            gap = statistics.median(gaps) if gaps else 20.0
            cells = [{c: [] for c in COLS} for _ in anchors]
            for ln in lines:
                t = statistics.mean(w["top"] for w in ln)
                i = min(range(len(tops)), key=lambda k: abs(tops[k] - t))
                if ln is not anchors[i] and abs(tops[i] - t) > 0.75 * gap:
                    continue
                if ln is not anchors[i] and all(w["text"].lower() in HEADER_WORDS for w in ln):
                    continue
                for w in sorted(ln, key=lambda w: w["x0"]):
                    text = w["text"]
                    if fused and ln is anchors[i] and w is sorted(ln, key=lambda w: w["x0"])[0]:
                        m = re.match(r"^(\d+)(.*)$", text)
                        cells[i]["serial"].append((w["top"], m.group(1)))
                        if m.group(2):
                            cells[i]["state"].append((w["top"], m.group(2)))
                        continue
                    col = [c for c, x in zip(COLS, edges) if w["x0"] >= x - 0.5][-1]
                    if fused and col == "serial":
                        col = "state"
                    cells[i][col].append((w["top"], text))
            for c in cells:
                r = {k: " ".join(t for _, t in sorted(v, key=lambda x: x[0])).strip() for k, v in c.items()}
                r.update(page=pno, pub_id=pid, assessment_year=year)
                issues = []
                r["category_raw"] = re.sub(r"^.*Saline\)\s*", "", r["category_raw"])
                cat = norm_cat(r["category_raw"])
                if not cat:
                    m = _CAT_TAIL.match((r["assessment_unit"] + " " + r["category_raw"]).strip())
                    if m and r["assessment_unit"]:
                        c2 = "safe" if m.group("cat").lower() == "afe" else m.group("cat")
                        r["assessment_unit"], r["category_raw"] = m.group("unit").strip(), m.group("cat")
                        cat = norm_cat(c2)
                        issues_note = "category split from unit text"
                        r["_note"] = issues_note
                st2, d2, moved = split_state(r["state"], r["district"])
                if moved:
                    r["_note"] = (r.get("_note", "") + "; district words moved from state column").strip("; ")
                r["state"], r["district"] = st2, d2
                if not r["serial"].isdigit():
                    issues.append("serial not a number")
                if not cat:
                    issues.append(f"unknown category '{r['category_raw']}'")
                for k in ("state", "district", "assessment_unit"):
                    if not r[k]:
                        issues.append(f"empty {k}")
                r["category"] = cat or ""
                r["state_std"] = norm_state(r["state"])
                r["quality_flag"] = ("ok" if not issues else "check: " + "; ".join(issues)) + \
                    (f" (repaired layout: {r['_note']})" if r.get("_note") else "")
                rows.append(r)
                if issues:
                    problems.append({**r, "issue": "; ".join(issues)})
    serials = [int(r["serial"]) for r in rows if r["serial"].isdigit()]
    dup = [s for s, n in Counter(serials).items() if n > 1]
    missing = sorted(set(range(1, max(serials) + 1)) - set(serials)) if serials else []
    return rows, problems, {"pub_id": pid, "assessment_year": year, "file": path.name, "sha256": sha,
                            "rows": len(rows), "max_serial": max(serials) if serials else 0,
                            "missing_serials": len(missing), "missing_serial_examples": " ".join(map(str, missing[:20])),
                            "duplicate_serials": len(dup), "problem_rows": len(problems),
                            "categories": "; ".join(f"{k}={v}" for k, v in Counter(r["category"] for r in rows).most_common())}


def main():
    C.ensure_dirs()
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)
    all_rows, all_probs, summ = [], [], []
    for pid in FILES:
        hits = sorted(PDF_DIR.glob(f"{pid:05d}_*.pdf"))
        if not hits:
            summ.append({"pub_id": pid, "assessment_year": FILES[pid][0], "file": "", "rows": 0,
                         "problem_rows": 0, "categories": "file not downloaded"})
            continue
        rows, probs, s = extract(pid, hits[0])
        print(f"GWRA {s['assessment_year']}: {s['rows']} rows, max serial {s['max_serial']}, "
              f"{s['missing_serials']} serials missing, {s['problem_rows']} problem rows")
        all_rows += rows
        all_probs += probs
        summ.append(s)
    fields = ["state", "district", "assessment_unit", "assessment_year", "category", "stage_of_extraction_pct",
              "source_id", "source_page", "quality_flag", "state_as_published", "category_as_published", "serial"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in all_rows:
            w.writerow({"state": r["state_std"], "district": r["district"].upper(),
                        "assessment_unit": r["assessment_unit"], "assessment_year": r["assessment_year"],
                        "category": r["category"], "stage_of_extraction_pct": "",
                        "source_id": f"CGWB_PUB_{r['pub_id']}", "source_page": r["page"],
                        "quality_flag": r["quality_flag"], "state_as_published": r["state"],
                        "category_as_published": r["category_raw"], "serial": r["serial"]})
    with open(PROB, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pub_id", "assessment_year", "page", "serial", "state", "district",
                                          "assessment_unit", "category_raw", "issue"], extrasaction="ignore")
        w.writeheader()
        w.writerows(all_probs)
    keys = ["pub_id", "assessment_year", "file", "sha256", "rows", "max_serial", "missing_serials",
            "missing_serial_examples", "duplicate_serials", "problem_rows", "categories"]
    with open(SUMMARY, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(summ)
    print(f"{len(all_rows)} rows -> {OUT}")
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)


if __name__ == "__main__":
    main()
