"""Step 2: turn cached tables and identity-checked text lines into one row per assessment unit, matched to the
official 2025 unit list (groundwater_assessment in groundwater.db, read-only)."""
import collections, csv, difflib, glob, json, os, re, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize import STATE, ncat, clean, tol
from extract_state_blocks import classify, num

F = ["recharge", "natural_discharge", "extractable", "irrigation", "industrial", "domestic", "total_extraction",
     "allocation_domestic", "net_availability", "stage_pct"]
TYPEWORDS = {"block", "taluk", "taluka", "mandal", "firka", "tehsil", "district", "valley", "island", "islands", "watershed", "ward", "cd", "assessmentunit"}

def key(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def load_units(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    units = collections.defaultdict(list)
    for st, d, u, cat, typ in c.execute("select state, district, assessment_unit, category, assessment_unit_type from groundwater_assessment"):
        units[st].append({"district": d, "unit": u, "category": cat, "type": typ, "kd": key(d), "ku": key(u)})
    return units

# ---------- rect tables ----------
def header_cols(rows, k):
    hdr = [r for r in rows[:k] if sum(1 for c in r if (c or "").strip()) >= 2]
    ncol = max(len(r) for r in rows)
    return [" ".join((r[j] or "").replace("\n", "") for r in hdr if j < len(r) and r[j]) for j in range(ncol)]

def map_cols(cols, data):
    m = {}
    for j, t in enumerate(cols):
        f = classify(t)
        n = key(t)
        if "totalc" in n and f is None: f = "total_extraction"
        if f in ("recharge_component", "geo_area", "worthy_area", None, "state", "serial"): continue
        if f == "district" and ("assessmentunit" in n or "block" in n): f = "unit_mixed"
        if f == "unit" and "numberof" in n: continue
        if f == "unit" and "unit" in m:
            vals = [(r[m["unit"]] or "") for r in data[:5] if m["unit"] < len(r)]
            if vals and all(re.match(r"^[A-Z]{2}\d{4,}$", (v or "").strip()) for v in vals):
                m["unit"] = j
            continue
        if f not in m: m[f] = j
    # a column whose data are names is a name column; a column with small sequential integers is a serial
    return m

def is_data(r):
    cells = [(c or "").replace("\n", "").strip() for c in r]
    return sum(num(c) is not None for c in cells) >= 4

def rect_records(pid, tables):
    out = []; last = None
    for t in tables:
        if "rows" not in t: continue
        rows = t["rows"]
        k = next((i for i, r in enumerate(rows) if is_data(r)), None)
        if k is None: continue
        cols = header_cols(rows, k)
        m = map_cols(cols, rows[k:])
        if ("unit" in m or "unit_mixed" in m) and any(f in m for f in ("recharge", "extractable", "total_extraction", "stage_pct")):
            last = (m, t["ncol"])
        elif last and last[1] == t["ncol"] and not any(f in m for f in ("recharge", "extractable", "total_extraction")):
            m = last[0]
        else:
            continue
        cur_d = ""
        for r in rows[k:]:
            g = lambda f: (r[m[f]] if f in m and m[f] < len(r) else None)
            if "unit_mixed" in m:
                name = clean(g("unit_mixed"))
                if not is_data(r):
                    if name and num(name) is None: cur_d = name
                    continue
                d, u = cur_d, name
            else:
                if not is_data(r): continue
                d, u = clean(g("district")), clean(g("unit"))
                if d: cur_d = d
                else: d = cur_d
            if not u or num(u) is not None: continue
            rec = {"pub": pid, "page": t["page"], "method": "ruled_table", "district_raw": d, "unit_raw": u,
                   "category_raw": clean(g("category"))}
            for f in F: rec[f] = num(g(f))
            out.append(rec)
    return out

# ---------- text rows ----------
def text_records(pid, lines):
    out = []
    for r in lines:
        n = r["nums"]; rec = {"pub": pid, "page": r["page"], "method": "text_identity", "name_raw": r["name"],
                             "prev": r["prev"], "next": r["next"], "category_raw": r["tail"]}
        for f in F: rec[f] = None
        if r["trip"] is not None:
            i = r["trip"]; rec["recharge"], rec["natural_discharge"], rec["extractable"] = n[i], n[i + 1], n[i + 2]
        if r.get("ext_before") and r["quad"] is not None:
            rec["extractable"] = n[r["quad"] - 1]
        if r["quad"] is not None:
            q = r["quad"]; rec["irrigation"], rec["industrial"], rec["domestic"], rec["total_extraction"] = n[q:q + 4]
            s = r["stage"]
            if s is not None:
                rec["stage_pct"] = n[s]
                if s - (q + 4) == 2: rec["allocation_domestic"], rec["net_availability"] = n[q + 4], n[q + 5]
        out.append(rec)
    return out

def strip_words(name, state):
    toks = [t for t in re.split(r"\s+", name or "") if t]
    sk = key(state)
    while toks and key(toks[0]) in (sk, key(state.split()[0]), "tamilnadu", "puducherry", "nctdelhi"):
        toks = toks[1:]
    while toks and key(toks[-1]) in TYPEWORDS: toks = toks[:-1]
    return " ".join(toks)

def match(rec, units, state, dalias=None):
    if rec["method"] == "ruled_table":
        kd = key(rec["district_raw"])
        kd = (dalias or {}).get((state, kd), kd)
        forms = {key(strip_words(rec["unit_raw"], state)), key(rec["unit_raw"])} - {""}
        for ku in forms:
            c = [u for u in units if u["ku"] == ku and (not kd or u["kd"] == kd)]
            if len(c) == 1: return c[0], "exact"
        for ku in forms:
            c = [u for u in units if u["ku"] == ku]
            if len(c) == 1: return c[0], "unit_name_unique"
        # unit renamed together with its district (e.g. Osmanabad -> Dharashiv)
        if key(rec["unit_raw"]) == key(rec["district_raw"]) and kd != key(rec["district_raw"]):
            c = [u for u in units if u["kd"] == kd and u["ku"] == kd]
            if len(c) == 1: return c[0], "renamed_with_district"
        pool = [u for u in units if not kd or u["kd"] == kd or difflib.SequenceMatcher(None, u["kd"], kd).ratio() > 0.85]
        for ku in forms:
            best = max(pool, key=lambda u: difflib.SequenceMatcher(None, u["ku"], ku).ratio(), default=None)
            if best and difflib.SequenceMatcher(None, best["ku"], ku).ratio() >= 0.88: return best, "fuzzy"
        return None, "no_match"
    names = [rec["name_raw"]]
    pv, nx = rec.get("prev", ""), rec.get("next", "")
    if pv and not re.search(r"\d", pv): names.append(pv + " " + rec["name_raw"])
    if nx and not re.search(r"\d", nx): names.append(rec["name_raw"] + " " + nx)
    if pv and nx and not re.search(r"\d", pv + nx): names.append(pv + " " + rec["name_raw"] + " " + nx)
    for nm in names:
        k = key(strip_words(nm, state))
        if not k: continue
        cands = []
        for u in units:
            if k == u["kd"] + u["ku"] or k == u["ku"]:
                cands.append((3, u))
            elif k.endswith(u["ku"]) and len(u["ku"]) >= 3 and (k[: -len(u["ku"])] == "" or difflib.SequenceMatcher(None, k[: -len(u["ku"])], u["kd"]).ratio() > 0.8):
                cands.append((2, u))
        if not cands and len(k) >= 4:
            suf = [u for u in units if len(u["ku"]) >= 4 and k.endswith(u["ku"])]
            longest = max((len(u["ku"]) for u in suf), default=0)
            suf = [u for u in suf if len(u["ku"]) == longest]
            if len(suf) == 1 and sum(1 for u in units if u["ku"] == suf[0]["ku"]) == 1:
                return suf[0], "text_suffix_unique"
        if cands:
            top = max(c[0] for c in cands)
            cs = [c[1] for c in cands if c[0] == top]
            if len(cs) == 1: return cs[0], "text_exact" if top == 3 else "text_suffix"
            longest = max(cs, key=lambda u: len(u["ku"]))
            if sum(1 for u in cs if len(u["ku"]) == len(longest["ku"])) == 1: return longest, "text_longest"
    return None, "no_match"

HEADS = None
def page_kinds(path):
    """'district' for district-wise annexure pages (and the pages that continue them), else 'unit'/'other'."""
    h = json.load(open(path)); kinds = {}
    for pid, pages in h.items():
        prev = "other"
        for pg in sorted(pages, key=int):
            l = pages[pg].lower()
            dist = bool(re.search(r"district[\s-]*wise|name of district", l))
            unit = bool(re.search(r"assessment unit|block|mandal|taluk|firka|tehsil", l))
            k = "district" if dist and not unit else ("unit" if unit else ("district" if prev == "district" and not re.search(r"annexure", l) else "other"))
            kinds[(pid, int(pg))] = k; prev = k
    return kinds

def checks(r):
    res = {}
    if None not in (r["recharge"], r["natural_discharge"], r["extractable"]):
        res["extractable_identity"] = tol(r["extractable"], r["recharge"] - r["natural_discharge"])
    if None not in (r["irrigation"], r["industrial"], r["domestic"], r["total_extraction"]):
        res["extraction_identity"] = tol(r["total_extraction"], r["irrigation"] + r["industrial"] + r["domestic"])
    if None not in (r["total_extraction"], r["extractable"], r["stage_pct"]) and r["extractable"] > 0:
        res["stage_identity"] = tol(r["stage_pct"], 100 * r["total_extraction"] / r["extractable"], 0.01, 0.6)
    return res

def score(r):
    c = checks(r)
    return (sum(c.values()), sum(r[f] is not None for f in F), r["method"] == "ruled_table", r["method"] != "stage_list")

def main(tables_dir, text_dir, db, out_csv, out_json):
    units = load_units(db)
    recs = []
    for fp in sorted(glob.glob(os.path.join(tables_dir, "*.json"))):
        pid = os.path.basename(fp)[:5]; recs += [dict(r, state=STATE[pid]) for r in rect_records(pid, json.load(open(fp)))]
    for fp in sorted(glob.glob(os.path.join(text_dir, "*.json"))):
        pid = os.path.basename(fp)[:5]; recs += [dict(r, state=STATE[pid]) for r in text_records(pid, json.load(open(fp)))]
    for fp in sorted(glob.glob(os.path.join(os.path.dirname(text_dir.rstrip("/")), "stagelist", "*.json"))):
        pid = os.path.basename(fp)[:5]
        for r in json.load(open(fp)):
            if r["comparison_page"]: continue
            rec = {"pub": pid, "page": r["page"], "method": "stage_list", "name_raw": r["name"], "prev": "", "next": "",
                   "category_raw": r["category"], "state": STATE[pid]}
            for f in F: rec[f] = None
            rec["stage_pct"] = r["stage"]
            recs.append(rec)
    by = collections.defaultdict(list); unmatched = []
    # district aliases (renamed districts): learn from rows whose unit name is unique in the state
    votes = collections.defaultdict(collections.Counter)
    for r in recs:
        if r["method"] != "ruled_table" or not r.get("district_raw"): continue
        ku = key(r["unit_raw"]); c = [u for u in units[r["state"]] if u["ku"] == ku]
        if len(c) == 1: votes[(r["state"], key(r["district_raw"]))][c[0]["kd"]] += 1
    dalias = {k: v.most_common(1)[0][0] for k, v in votes.items() if v.most_common(1)[0][1] >= 2}
    kinds = page_kinds(os.path.join(os.path.dirname(text_dir.rstrip("/")), "page_heads.json"))
    ucount = collections.Counter((st, u["kd"]) for st, lst in units.items() for u in lst)
    dkeys = collections.defaultdict(set)
    for st, lst in units.items():
        for u in lst: dkeys[st].add(u["kd"])
    matched = []
    for r in recs:
        u, how = match(r, units[r["state"]], r["state"], dalias)
        if u is None:
            unmatched.append(r); continue
        matched.append((r, u, how))
    # judge each page of text-derived rows by its content: a district table lists district names
    pg = collections.defaultdict(lambda: [0, 0, 0])
    for r, u, how in matched:
        if r["method"] == "ruled_table": continue
        nm = key(strip_words(r.get("name_raw", ""), r["state"]))
        pg[(r["pub"], r["page"])][0] += 1
        if nm in dkeys[r["state"]] or (not nm and u["ku"] == u["kd"]): pg[(r["pub"], r["page"])][1] += 1
        c = checks(r)
        if len(c) == 3 and all(c.values()): pg[(r["pub"], r["page"])][2] += 1
    for r, u, how in matched:
        if r["method"] != "ruled_table":
            n, nd, nfull = pg[(r["pub"], r["page"])]
            district_like = kinds.get((r["pub"], r["page"])) == "district" or (n and nd / n >= 0.5)
            if district_like and ucount[(r["state"], u["kd"])] > 1:
                r["reject"] = "district_table"; unmatched.append(r); continue
            c = checks(r)
        r["match"] = how
        by[(r["state"], u["district"], u["unit"])].append(r)
    rows = []
    for st, lst in units.items():
        for u in lst:
            cand = by.get((st, u["district"], u["unit"]), [])
            if not cand:
                rows.append({"state": st, "district": u["district"], "assessment_unit": u["unit"], "status": "not_found",
                             "official_category": u["category"]}); continue
            cand.sort(key=score, reverse=True)
            best = dict(cand[0])
            # fill fields missing in the best candidate from other candidates whose overlapping fields agree
            for o in cand[1:]:
                agree = all(tol(best[f], o[f], 0.002, 0.05) for f in F if best[f] is not None and o[f] is not None)
                if agree:
                    for f in F:
                        if best[f] is None and o[f] is not None: best[f] = o[f]; best.setdefault("filled_from", set()).add(f"{o['pub']}p{o['page']}")
            # disagreement among complete candidates
            conflicts = [f"{o['pub']}p{o['page']}" for o in cand[1:] if any(not tol(best[f], o[f], 0.002, 0.05) for f in F if best[f] is not None and o[f] is not None)]
            c = checks(best)
            full = all(best[f] is not None for f in ("recharge", "extractable", "total_extraction"))
            status = "verified" if len(c) == 3 and all(c.values()) else ("checks_failed" if c and not all(c.values()) else "partial")
            cat = ncat(best.get("category_raw")) or next((ncat(o.get("category_raw")) for o in cand if ncat(o.get("category_raw"))), None)
            rows.append({"state": st, "district": u["district"], "assessment_unit": u["unit"], "status": status,
                         "official_category": u["category"], "report_category": cat or "",
                         **{f: best[f] for f in F},
                         "checks": ";".join(f"{k}={'ok' if v else 'FAIL'}" for k, v in c.items()),
                         "source_pub": best["pub"], "source_page": best["page"], "method": best["method"],
                         "match": best["match"], "name_in_source": best.get("unit_raw") or best.get("name_raw"),
                         "district_in_source": best.get("district_raw", ""),
                         "filled_from": ",".join(sorted(best.get("filled_from", []))), "other_sources_disagree": ",".join(conflicts),
                         "n_candidates": len(cand)})
    # a unit left partial whose figures come only from loose text lines is kept only when the page it came from
    # is an assessment-unit table, i.e. most units read from that page were fully verified
    pstat = collections.defaultdict(collections.Counter)
    for r in rows:
        if r["status"] != "not_found": pstat[(r["source_pub"], r["source_page"])][r["status"]] += 1
    for r in rows:
        if r["status"] in ("partial", "checks_failed") and r["method"] != "ruled_table":
            c = pstat[(r["source_pub"], r["source_page"])]
            tot = sum(c.values())
            pages = {(r["source_pub"], r["source_page"])} | {tuple(x.split("p")) for x in r.get("filled_from", "").split(",") if x}
            ok = any(sum(pstat[p].values()) >= 5 and pstat[p]["verified"] / max(1, sum(pstat[p].values())) >= 0.5 for p in pages)
            if not ok:
                keep = {k: r[k] for k in ("state", "district", "assessment_unit", "official_category")}
                r.clear(); r.update(keep, status="not_found", note="only unverified figures on a non-unit page; rejected")
    cols = ["state", "district", "assessment_unit", "status", "official_category", "report_category"] + F + \
           ["checks", "source_pub", "source_page", "method", "match", "name_in_source", "district_in_source", "filled_from",
            "other_sources_disagree", "n_candidates"]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in cols})
    json.dump([{k: v for k, v in r.items() if k not in ("prev", "next")} for r in unmatched], open(out_json, "w"), default=str)
    st = collections.defaultdict(collections.Counter)
    for r in rows: st[r["state"]][r["status"]] += 1
    tot = collections.Counter()
    for s in sorted(st):
        c = st[s]; tot.update(c)
        print(f"{s[:30]:30s} units {sum(c.values()):4d}  verified {c['verified']:4d}  partial {c['partial']:3d}  failed {c['checks_failed']:3d}  not_found {c['not_found']:4d}")
    print("TOTAL", dict(tot), "unmatched source rows:", len(unmatched))

if __name__ == "__main__":
    main(*sys.argv[1:6])
