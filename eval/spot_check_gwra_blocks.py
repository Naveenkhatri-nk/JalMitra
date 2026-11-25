"""Spot-check of the state-report block figures used by the chat (24 Nov 2026).

10 random usable units from 5 states (fixed seed). For each one, the cited PDF page(s) of the CGWB 2025 state report
are read again with pdfplumber and every figure shown in the chat (stage, recharge, extractable, total extraction)
is looked for as printed text on those pages; the unit name must be on the page too. Read-only: the PDFs and both
databases are only read. Writes eval/spot_check_gwra_blocks_20261124.csv.

Run: .venv\\Scripts\\python eval\\spot_check_gwra_blocks.py
"""
import csv
import random
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import pdfplumber  # noqa: E402

import gwra_blocks_retrieval as g  # noqa: E402

RAW = BASE / "data" / "monitoring" / "raw" / "cgwb_publications"
STATES = ["Madhya Pradesh", "Uttar Pradesh", "Gujarat", "Karnataka", "Maharashtra"]
FIELDS = ["stage_pct", "recharge_ham", "extractable_ham", "total_extraction_ham"]


def variants(v):
    """Printed forms of a number: 20438.79, 20438.8, 20439, 20,438.79 ..."""
    out = {f"{v:.2f}", f"{v:.1f}", f"{v:.0f}", str(v)}
    if float(v).is_integer():
        out.add(str(int(v)))
    out |= {f"{float(x):,.2f}" if "." in x else f"{int(float(x)):,}" for x in list(out)}
    return {x.rstrip("0").rstrip(".") if "." in x else x for x in out} | out


def main():
    rnd = random.Random(20261124)
    con = g._connect()
    picks = []
    for s in STATES:
        rows = con.execute("select * from unit_resources where state=? and usable=1 and status='verified'", (s,)).fetchall()
        picks += rnd.sample(rows, 2)
    out = []
    for r in picks:
        res = g.unit_figures(r["state"], r["assessment_unit"], r["district"])
        pdf = next(RAW.glob(f"0{res['source']['pub_id']}_*.pdf"))
        text = ""
        with pdfplumber.open(pdf) as doc:
            for p in res["source"]["pages"]:
                text += doc.pages[p - 1].extract_text() or ""
        flat = re.sub(r"\s+", " ", text)
        name_ok = re.sub(r"[^a-z]", "", r["assessment_unit"].lower())[:6] in re.sub(r"[^a-z]", "", flat.lower())
        found = {f: any(x in flat for x in variants(res["figures"][f])) for f in FIELDS if f in res["figures"]}
        # narrow PDF columns: the text layer cuts or wraps the decimals ("14083." / "7689." + "62" on the next line);
        # then the whole-number part with its decimal point must be printed (checked by hand for this run)
        wrapped = {f: f"{int(res['figures'][f])}." in flat for f, v in found.items() if not v}
        ok = name_ok and all(v or wrapped.get(f) for f, v in found.items())
        out.append([r["state"], r["district"], r["assessment_unit"], pdf.name, ",".join(map(str, res["source"]["pages"])),
                    *[res["figures"].get(f) for f in FIELDS], name_ok,
                    ";".join(f for f, v in found.items() if not v) or "-",
                    ("match (decimals wrapped in the PDF text)" if wrapped else "match") if ok else "CHECK"])
        print(*out[-1], sep=" | ")
    dest = BASE / "eval" / "spot_check_gwra_blocks_20261124.csv"
    with open(dest, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["state", "district", "unit", "pdf", "pages", *FIELDS, "unit_name_on_page", "figures_not_found",
                    "result"])
        w.writerows(out)
    print(f"{sum(1 for o in out if o[-1].startswith('match'))}/{len(out)} match -> {dest}")


if __name__ == "__main__":
    main()
