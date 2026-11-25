"""
extract_data.py - Extract block-level groundwater data from an official
CGWB / State "Dynamic Ground Water Resources" report PDF, and check it.

This script ONLY reads the PDF and writes a CSV for a human to check.
It never fills in, guesses or changes a missing number, and it never
touches the SQLite database. After you have compared the rows with the
printed report, import the CSV with load_data.py.

Currently supported table
-------------------------
"Annexure VI - Block wise resources of Rajasthan, GWRA-2025"
(Dynamic Ground Water Resources of Rajasthan - 2025, CGWB Western Region,
Jaipur and Ground Water Department, Govt. of Rajasthan, November 2025),
PDF pages 126-136. Values in that table are in hectare-metres (Ham).

Usage (from the JalMitra folder):

    pip install pdfplumber
    python extract_data.py data/raw/bulk_17781482431554file.pdf ^
        --source-url "https://...where you downloaded it..." ^
        --out data/extracted/rajasthan_gwra2025_blocks.csv

Outputs:
    <out>.csv              one row per assessment unit, values as printed
    <out>_problems.csv     every row that failed a check, with the reason
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------- settings

# The table we know how to read. Add more reports here later.
KNOWN_TABLES = {
    "rajasthan_2025_annexure_vi": {
        "title_contains": "Block wise resources of Rajasthan, GWRA-2025",
        "table_name": "Annexure VI - Block wise resources of Rajasthan, GWRA-2025",
        "report_title": "Dynamic Ground Water Resources of Rajasthan - 2025",
        "publisher": "CGWB Western Region, Jaipur & Ground Water Department, Govt. of Rajasthan",
        "publication_year": "2025",
        "assessment_year": "GWRA-2025",
        "unit": "ham",
        # Column positions in each printed table row (21 columns).
        "columns": [
            "state", "district", "assessment_unit", "assessment_unit_type",
            "total_geographical_area_ha", "recharge_worthy_area_ha",
            "recharge_rainfall_monsoon_ham", "recharge_other_monsoon_ham",
            "recharge_rainfall_nonmonsoon_ham", "recharge_other_nonmonsoon_ham",
            "annual_recharge_ham", "natural_discharge_ham",
            "extractable_resource_ham", "irrigation_use_ham",
            "industrial_use_ham", "domestic_use_ham", "total_extraction_ham",
            "domestic_allocation_ham", "net_availability_future_ham",
            "stage_of_extraction_pct", "category_raw",
        ],
    }
}

# How the report writes categories -> how JalMitra writes them.
CATEGORY_MAP = {
    "safe": "Safe",
    "semi_critical": "Semi-critical",
    "semicritical": "Semi-critical",
    "semi-critical": "Semi-critical",
    "critical": "Critical",
    "over_exploited": "Over-exploited",
    "over-exploited": "Over-exploited",
    "overexploited": "Over-exploited",
    "oe": "Over-exploited",
    "saline": "Saline",
    "salinity": "Saline",
}

# Columns written to the output CSV (this is also the CSV template).
OUTPUT_COLUMNS = [
    "state", "district", "assessment_unit", "assessment_unit_type",
    "assessment_year",
    "annual_recharge_ham", "extractable_resource_ham",
    "total_extraction_ham", "stage_of_extraction_pct",
    "category", "category_raw",
    # extra printed columns, kept so the checks can be re-done later
    "recharge_rainfall_monsoon_ham", "recharge_other_monsoon_ham",
    "recharge_rainfall_nonmonsoon_ham", "recharge_other_nonmonsoon_ham",
    "natural_discharge_ham", "irrigation_use_ham", "industrial_use_ham",
    "domestic_use_ham",
    # where the row came from
    "source_file", "source_url", "source_report", "source_table",
    "source_page", "publication_year", "unit",
    "name_was_wrapped", "check_status", "check_notes",
]

NUMBER_COLUMNS = [
    "total_geographical_area_ha", "recharge_worthy_area_ha",
    "recharge_rainfall_monsoon_ham", "recharge_other_monsoon_ham",
    "recharge_rainfall_nonmonsoon_ham", "recharge_other_nonmonsoon_ham",
    "annual_recharge_ham", "natural_discharge_ham",
    "extractable_resource_ham", "irrigation_use_ham", "industrial_use_ham",
    "domestic_use_ham", "total_extraction_ham", "domestic_allocation_ham",
    "net_availability_future_ham", "stage_of_extraction_pct",
]

# Printed values are rounded to whole numbers, so sums can differ slightly.
SUM_TOLERANCE = 3        # Ham
STAGE_TOLERANCE = 1.5    # percentage points


# ----------------------------------------------------------------- helpers

def to_number(text):
    """'1,234' -> 1234.0. Empty or '-' -> None. Anything else -> ValueError."""
    t = (text or "").strip().replace(",", "")
    if t in ("", "-", "--", "NA", "N/A"):
        return None
    return float(t)


def join_wrapped(text):
    """The PDF breaks long names over two lines ('KISHANGA\\nRH'). Join them."""
    if text is None:
        return "", False
    wrapped = "\n" in text
    return re.sub(r"\s*\n\s*", "", text).strip(), wrapped


def expected_category(stage):
    """Category from stage of extraction (official limits 70 / 90 / 100 %)."""
    if stage is None:
        return None
    if stage <= 70:
        return "Safe"
    if stage <= 90:
        return "Semi-critical"
    if stage <= 100:
        return "Critical"
    return "Over-exploited"


def check_row(r):
    """Return a list of problems with one extracted row. Never changes it."""
    notes = []
    n = {c: r.get(c + "_num") for c in NUMBER_COLUMNS}

    for c in ["annual_recharge_ham", "extractable_resource_ham",
              "total_extraction_ham", "stage_of_extraction_pct"]:
        if n[c] is None:
            notes.append(f"{c} is missing in the report")

    parts = [n["recharge_rainfall_monsoon_ham"], n["recharge_other_monsoon_ham"],
             n["recharge_rainfall_nonmonsoon_ham"], n["recharge_other_nonmonsoon_ham"]]
    if None not in parts and n["annual_recharge_ham"] is not None:
        if abs(sum(parts) - n["annual_recharge_ham"]) > SUM_TOLERANCE:
            notes.append(f"recharge parts add to {sum(parts):g}, total printed {n['annual_recharge_ham']:g}")

    if None not in (n["annual_recharge_ham"], n["natural_discharge_ham"], n["extractable_resource_ham"]):
        diff = n["annual_recharge_ham"] - n["natural_discharge_ham"]
        if abs(diff - n["extractable_resource_ham"]) > SUM_TOLERANCE:
            notes.append(f"recharge - discharge = {diff:g}, extractable printed {n['extractable_resource_ham']:g}")

    uses = [n["irrigation_use_ham"], n["industrial_use_ham"], n["domestic_use_ham"]]
    if None not in uses and n["total_extraction_ham"] is not None:
        if abs(sum(uses) - n["total_extraction_ham"]) > SUM_TOLERANCE:
            notes.append(f"uses add to {sum(uses):g}, total extraction printed {n['total_extraction_ham']:g}")

    if n["extractable_resource_ham"] and n["total_extraction_ham"] is not None and n["stage_of_extraction_pct"] is not None:
        calc = 100 * n["total_extraction_ham"] / n["extractable_resource_ham"]
        if abs(calc - n["stage_of_extraction_pct"]) > STAGE_TOLERANCE:
            notes.append(f"extraction/extractable = {calc:.1f}%, stage printed {n['stage_of_extraction_pct']:g}%")

    if r["category"] is None:
        notes.append(f"unknown category '{r['category_raw']}'")
    elif r["category"] != "Saline":
        exp = expected_category(n["stage_of_extraction_pct"])
        if exp and exp != r["category"]:
            notes.append(f"category printed {r['category']} but stage suggests {exp}")

    return notes


# ----------------------------------------------------------------- extraction

def extract(pdf_path, table_key, source_url):
    try:
        import pdfplumber
    except ImportError:
        sys.exit("pdfplumber is not installed. Run: pip install pdfplumber")

    spec = KNOWN_TABLES[table_key]
    cols = spec["columns"]
    rows, pages_used = [], []

    with pdfplumber.open(pdf_path) as pdf:
        # Find the first page of the table by its title, then read on
        # until a page has no matching rows.
        start = None
        for i, page in enumerate(pdf.pages):
            if spec["title_contains"].lower() in (page.extract_text() or "").lower():
                start = i
                break
        if start is None:
            sys.exit(f"Could not find the table '{spec['table_name']}' in {pdf_path}")

        for i in range(start, len(pdf.pages)):
            page_no = i + 1
            found_here = 0
            page = pdf.pages[i]
            words = page.extract_words()
            if not words:
                if rows:
                    break
                continue
            # Continuation pages have no ruled line above their first row,
            # so pdfplumber would drop that row. Add one just above the text.
            top = min(w["top"] for w in words) - 1
            settings = {"explicit_horizontal_lines": [top]}
            for table in page.extract_tables(settings):
                for cells in table:
                    if len(cells) != len(cols):
                        continue
                    first = (cells[0] or "").strip().upper()
                    if first in ("", "STATE") or first.startswith("ANNEXURE"):
                        continue  # title row or header row
                    raw = dict(zip(cols, cells))
                    name, wrapped = join_wrapped(raw["assessment_unit"])
                    district, d_wrapped = join_wrapped(raw["district"])
                    row = {
                        "state": join_wrapped(raw["state"])[0],
                        "district": district,
                        "assessment_unit": name,
                        "assessment_unit_type": join_wrapped(raw["assessment_unit_type"])[0],
                        "assessment_year": spec["assessment_year"],
                        "category_raw": join_wrapped(raw["category_raw"])[0],
                        "source_file": Path(pdf_path).name,
                        "source_url": source_url or "",
                        "source_report": spec["report_title"],
                        "source_table": spec["table_name"],
                        "source_page": page_no,
                        "publication_year": spec["publication_year"],
                        "unit": spec["unit"],
                        "name_was_wrapped": "yes" if (wrapped or d_wrapped) else "no",
                    }
                    row["category"] = CATEGORY_MAP.get(row["category_raw"].strip().lower())
                    bad_numbers = []
                    for c in NUMBER_COLUMNS:
                        txt = join_wrapped(raw[c])[0]
                        try:
                            row[c + "_num"] = to_number(txt)
                        except ValueError:
                            row[c + "_num"] = None
                            bad_numbers.append(f"{c} not a number: '{txt}'")
                        row[c] = txt  # keep the printed text exactly
                    notes = bad_numbers + check_row(row)
                    row["check_status"] = "ok" if not notes else "check"
                    row["check_notes"] = "; ".join(notes)
                    rows.append(row)
                    found_here += 1
            if found_here == 0 and rows:
                break  # table has ended
            if found_here:
                pages_used.append(page_no)

    return rows, pages_used


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            out = dict(r)
            if out.get("category") is None:
                out["category"] = ""
            w.writerow(out)


def write_template(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(OUTPUT_COLUMNS)


def main(argv=None):
    p = argparse.ArgumentParser(description="Extract official block-level groundwater data from a report PDF.")
    p.add_argument("pdf", nargs="?", help="Path to the official report PDF")
    p.add_argument("--table", default="rajasthan_2025_annexure_vi", choices=list(KNOWN_TABLES))
    p.add_argument("--source-url", default="", help="Official URL the PDF was downloaded from")
    p.add_argument("--out", default="data/extracted/rajasthan_gwra2025_blocks.csv")
    p.add_argument("--template", help="Only write an empty CSV template to this path")
    args = p.parse_args(argv)

    if args.template:
        write_template(Path(args.template))
        print("Template written:", args.template)
        return 0
    if not args.pdf:
        p.error("give the PDF path, or --template")

    rows, pages = extract(args.pdf, args.table, args.source_url)
    out = Path(args.out)
    write_csv(out, rows)
    problems = [r for r in rows if r["check_status"] != "ok"]
    write_csv(out.with_name(out.stem + "_problems.csv"), problems)

    print(f"Table: {KNOWN_TABLES[args.table]['table_name']}")
    print(f"PDF pages used: {pages[0]}-{pages[-1]}" if pages else "No rows found")
    print(f"Rows extracted: {len(rows)}")
    print(f"Rows needing a manual check: {len(problems)}")
    if not args.source_url:
        print("WARNING: --source-url was not given; source_url is blank in the CSV.")
    print("Written:", out)
    print("Nothing was written to the database.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
