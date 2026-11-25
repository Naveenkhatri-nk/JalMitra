import json, os, re, sys, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_state_blocks import num, FIELDS
STATE = {"02095":"Andaman And Nicobar","02096":"Andhra Pradesh","02097":"Arunachal Pradesh","02098":"Assam","02099":"Bihar",
"02100":"Chandigarh","02101":"Chhattisgarh","02102":"Dadra and Nagar Haveli and Daman and Diu","02103":"Delhi","02104":"Goa",
"02105":"Gujarat","02106":"Haryana","02107":"Himachal Pradesh","02108":"Jharkhand","02109":"Karnataka","02110":"Kerala",
"02111":"Ladakh","02112":"Lakshadweep","02113":"Madhya Pradesh","02114":"Maharashtra","02115":"Manipur","02116":"Meghalaya",
"02117":"Mizoram","02118":"Nagaland","02119":"Puducherry","02120":"Rajasthan","02121":"Sikkim","02122":"Tamil Nadu",
"02123":"Telangana","02124":"Tripura","02125":"Uttar Pradesh","02126":"Uttarakhand","02127":"West Bengal",
"02128":"Jammu And Kashmir","02129":"Odisha","01542":"Punjab","01843":"Punjab"}
CATS = {"safe":"Safe","semicritical":"Semi-critical","critical":"Critical","overexploited":"Over-exploited","oe":"Over-exploited","saline":"Saline","salinity":"Saline"}
def ncat(s):
    k = re.sub(r"[^a-z]", "", (s or "").lower())
    return CATS.get(k)
def clean(s): return re.sub(r"\s+", " ", (s or "").replace("\n", " ")).strip()
def key(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def records(raw):
    out = []
    for fn, tables in raw.items():
        pid = fn[:5]
        for t in tables:
            m = t["map"]
            if "unit" not in m: continue
            for r in t["rows"]:
                g = lambda f: r[m[f]] if f in m and m[f] < len(r) else None
                rec = {"pub": pid, "state": STATE[pid], "page": t["page"], "district": clean(g("district")),
                       "unit": clean(g("unit")), "unit_type": clean(g("unit_type")), "category": ncat(g("category")),
                       "category_raw": clean(g("category"))}
                for f in FIELDS:
                    rec[f] = num(g(f))
                if not rec["unit"] or num(rec["unit"]) is not None: continue
                out.append(rec)
    return out

def tol(a, b, rel=0.01, absol=1.0):
    return abs(a - b) <= max(absol, rel * max(abs(a), abs(b)))

def check(r):
    res = {}
    if None not in (r["recharge"], r["natural_discharge"], r["extractable"]):
        res["extractable_identity"] = tol(r["extractable"], r["recharge"] - r["natural_discharge"])
    if None not in (r["irrigation"], r["industrial"], r["domestic"], r["total_extraction"]):
        res["extraction_identity"] = tol(r["total_extraction"], r["irrigation"] + r["industrial"] + r["domestic"])
    if None not in (r["total_extraction"], r["extractable"], r["stage_pct"]) and r["extractable"] > 0:
        res["stage_identity"] = tol(r["stage_pct"], 100 * r["total_extraction"] / r["extractable"], rel=0.01, absol=0.6)
    return res

def merge(recs):
    by = collections.OrderedDict()
    conflicts = []
    for r in recs:
        k = (r["state"], key(r["district"]), key(r["unit"]))
        if k not in by:
            by[k] = dict(r, pages=str(r["page"]))
            continue
        b = by[k]
        if str(r["page"]) not in b["pages"].split(","): b["pages"] += "," + str(r["page"])
        for f in FIELDS + ["category", "unit_type", "category_raw"]:
            if r.get(f) in (None, ""): continue
            if b.get(f) in (None, ""): b[f] = r[f]
            elif b[f] != r[f] and not (isinstance(b[f], float) and tol(b[f], r[f], 0.001, 0.01)):
                conflicts.append({"state": r["state"], "district": r["district"], "unit": r["unit"], "field": f,
                                  "a": b[f], "b": r[f], "pages": b["pages"]})
    return list(by.values()), conflicts
