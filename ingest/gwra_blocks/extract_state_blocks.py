"""Helpers (header classification, number parsing) for the GWRA 2025 unit extraction.
Originally: extract assessment-unit (block/taluk/mandal/firka) GWRA-2025 figures from CGWB state reports.
Tables are read with pdfplumber's ruled-cell table finder; columns are mapped from header text; every row
is checked against the GEC-2015 identities (extractable = recharge - natural discharge; total = irrigation +
industrial + domestic; stage = total / extractable x 100). Nothing is estimated or filled in."""
import argparse, csv, glob, json, os, re, sys
from concurrent.futures import ProcessPoolExecutor
import pdfplumber

FIELDS = ["recharge", "natural_discharge", "extractable", "irrigation", "industrial", "domestic", "total_extraction",
          "allocation_domestic", "net_availability", "stage_pct"]

def norm(s):
    return re.sub(r"[^a-z0-9%]", "", (s or "").lower())

def classify(h):
    """map one column's joined header text to a field name"""
    n = norm(h)
    if not n: return None
    if n in ("slno", "sno", "sn", "srno", "s.no", "slno.") or n.startswith("sl") and len(n) <= 5 or n in ("sno",): return "serial"
    if "categor" in n: return "category"
    if "stage" in n: return "stage_pct"
    if "netground" in n or "futureuse" in n or "netavail" in n: return "net_availability"
    if "allocation" in n: return "allocation_domestic"
    if "extractable" in n: return "extractable"
    if "naturaldis" in n: return "natural_discharge"
    if "totalannualgroundwater" in n or "totalannualrecharge" in n or ("annualgroundwaterrecharge" in n) or n in ("totalannualgroundwaterrecharge",): return "recharge"
    if n.startswith("rechargefrom") or n.startswith("recharge"): return "recharge_component"
    if "irrigation" in n: return "irrigation"
    if "industrial" in n: return "industrial"
    if "domestic" in n: return "domestic"
    if "totalextraction" in n or n in ("total", "totalham", "totalextractionham"): return "total_extraction"
    if "worthy" in n: return "worthy_area"
    if "geograph" in n or "totalarea" in n: return "geo_area"
    if "district" in n: return "district"
    if "type" in n: return "unit_type"
    if "assessmentunit" in n or "nameof" in n or n in ("block", "blockname", "taluk", "mandal", "firka", "unitname", "assessmentunitname"): return "unit"
    if n == "state": return "state"
    return None

NUMRE = re.compile(r"^-?\d+(\.\d+)?$")
def num(s):
    s = (s or "").replace("\n", "").replace(",", "").replace(" ", "").rstrip("%")
    return float(s) if NUMRE.match(s) else None

def is_data_row(r):
    cells = [(c or "").replace("\n", "").strip() for c in r]
    nums = sum(num(c) is not None for c in cells)
    first = next((c for c in cells if c), "")
    return nums >= 5 and re.match(r"^\d+", first or "") is not None

def header_map(rows):
    """rows: header rows (top to bottom). Join text per column (including text of the nearest filled cell to the left
    within the same header row only for group headers is NOT done; each column uses its own cells)."""
    ncol = max(len(r) for r in rows)
    cols = []
    for j in range(ncol):
        txt = " ".join((r[j] or "").replace("\n", "") for r in rows if j < len(r) and r[j])
        cols.append(txt)
    m = {}
    for j, t in enumerate(cols):
        f = classify(t)
        if f and f not in m: m[f] = j
        elif f and f in m and f not in ("recharge_component",):
            m.setdefault(f + "_dup", j)
    return m, cols

