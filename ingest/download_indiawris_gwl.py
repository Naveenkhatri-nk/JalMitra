"""
Download groundwater-level records from the public India-WRIS API (National Water Informatics Centre).

API (no key, documented at https://indiawris.gov.in/swagger-ui/index.html):
    POST https://indiawris.gov.in/Dataset/Ground%20Water%20Level
         ?stateName=&districtName=&agencyName=&startdate=YYYY-MM-DD&enddate=YYYY-MM-DD&download=false&page=N&size<=1000
District master: https://india-water.gov.in/eswis-api/getAllDistrictListDataViewPage/<state code>/

Every non-empty response page is kept unchanged (gzip JSON) under
    data/monitoring/raw/indiawris_gwl/<agency>/<state>/<district>/<start>_<end>_p<page>.json.gz
Every request (including empty ones) is logged in data/monitoring/logs/indiawris_requests.csv.
Completed windows are recorded in data/monitoring/logs/indiawris_windows_done.csv so the run can resume.
Existing files are never overwritten.

Known API behaviour (observed 23 Nov 2026): the API sometimes answers "No data found" for a window that
does have data on a later try. Empty answers are therefore retried before a window is accepted as empty.

Usage:
    python ingest/download_indiawris_gwl.py --scope rajasthan          # CGWB + Rajasthan GW, all modes, all years
    python ingest/download_indiawris_gwl.py --scope national           # CGWB, all other states, manual months 2022+
    python ingest/download_indiawris_gwl.py --scope rajasthan --districts Jaipur Ajmer --from-year 2015
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

API = "https://indiawris.gov.in/Dataset/Ground%20Water%20Level"
DISTRICT_MASTER = "https://india-water.gov.in/eswis-api/getAllDistrictListDataViewPage/{code}/"
AGENCY_MASTER = "https://india-water.gov.in/eswis-api/getMasterAgencyListDataViewPage/"
PAGE_SIZE = 1000
EMPTY_RETRIES = 1            # extra tries when the API says "No data found"
OUT = C.RAW / "indiawris_gwl"
MASTER_OUT = C.RAW / "indiawris_masters"
REQ_LOG = C.LOGS / "indiawris_requests.csv"
DONE_LOG = C.LOGS / "indiawris_windows_done.csv"
REQ_FIELDS = ["time_utc", "agency", "state", "district", "start", "end", "page", "attempt", "http_status",
              "message", "rows", "file", "sha256", "error"]
DONE_FIELDS = ["agency", "state", "district", "start", "end", "pages", "rows", "status", "time_utc"]

# India-WRIS state codes (as used by getAllDistrictListDataViewPage) -> candidate stateName spellings.
# The first spelling that returns data is used; the choice is logged in indiawris_state_resolution.csv.
STATE_CODES = {
    "01": ["Andhra Pradesh"], "02": ["Arunachal Pradesh"], "03": ["Assam"], "04": ["Bihar"], "05": ["Goa"],
    "06": ["Gujarat"], "07": ["Haryana"], "08": ["Himachal Pradesh"], "09": ["Jammu and Kashmir", "Jammu & Kashmir"],
    "10": ["Karnataka"], "11": ["Kerala"], "12": ["Madhya Pradesh"], "13": ["Maharashtra"], "14": ["Manipur"],
    "15": ["Meghalaya"], "16": ["Mizoram"], "17": ["Nagaland"], "18": ["Odisha", "Orissa"], "19": ["Punjab"],
    "20": ["Rajasthan"], "21": ["Sikkim"], "22": ["Tamil Nadu"], "23": ["Tripura"], "24": ["Uttar Pradesh"],
    "25": ["West Bengal"], "26": ["Chhattisgarh"], "27": ["Jharkhand"], "28": ["Uttarakhand", "Uttaranchal"],
    "29": ["Telangana"], "30": ["Ladakh"], "31": ["Lakshadweep"], "32": ["Puducherry"], "33": ["Puducherry"],
    "41": ["Andaman and Nicobar Islands", "Andaman and Nicobar", "Andaman & Nicobar Islands"],
    "42": ["Chandigarh"], "43": ["Dadra and Nagar Haveli", "Dadra and Nagar Haveli and Daman and Diu"],
    "44": ["Daman and Diu", "Dadra and Nagar Haveli and Daman and Diu"], "45": ["Delhi", "NCT of Delhi"],
}
MANUAL_MONTHS = (1, 3, 4, 5, 8, 11)   # CGWB manual campaign months (Jan, pre-monsoon Mar-May, Aug, Nov)


def fetch_masters() -> dict[str, list[dict]]:
    """Download (once) and return the India-WRIS district master per state code."""
    MASTER_OUT.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    agencies = MASTER_OUT / f"agencies_{stamp}.json"
    if not agencies.exists():
        st, _, body = C.http(AGENCY_MASTER)
        if st == 200:
            C.write_new(agencies, body)
    out = {}
    for code in [f"{i:02d}" for i in range(1, 46)]:
        p = MASTER_OUT / f"districts_{code}_{stamp}.json"
        if not p.exists():
            try:
                st, _, body = C.http(DISTRICT_MASTER.format(code=code))
            except Exception as e:  # noqa: BLE001
                print(f"  district master {code}: {e}")
                continue
            if st != 200:
                continue
            C.write_new(p, body)
        try:
            rows = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if rows:
            out[code] = [{"districtId": r.get("districtId"), "name": r.get("name")} for r in rows]
    return out


def call(agency, state, district, start, end, page):
    """One API call with empty-answer retries. Returns (rows, message, attempts_log)."""
    params = {"stateName": state, "districtName": district, "agencyName": agency, "startdate": start,
              "enddate": end, "download": "false", "page": str(page), "size": str(PAGE_SIZE)}
    attempts = []
    for attempt in range(EMPTY_RETRIES + 1):
        err, msg, rows, status, body = "", "", None, "", b""
        try:
            status, _, body = C.http(API, method="POST", params=params, accept="application/json", timeout=120)
            j = json.loads(body.decode("utf-8"))
            msg = j.get("message", "")
            rows = j.get("data") or []
        except Exception as e:  # noqa: BLE001
            err = repr(e)[:300]
        attempts.append({"attempt": attempt, "http_status": status, "message": msg,
                         "rows": -1 if rows is None else len(rows), "error": err, "body": body if rows else b""})
        if rows:
            return rows, msg, attempts
        time.sleep(3)
    return [], attempts[-1]["message"], attempts


def window_done_set(recheck_empty=False):
    rows = C.read_csv(DONE_LOG)
    if recheck_empty:
        rows = [r for r in rows if r["status"] != "empty"]
    return {(r["agency"], r["state"], r["district"], r["start"], r["end"]) for r in rows}


def fetch_window(agency, state, district, start, end, done):
    key = (agency, state, district, start, end)
    if key in done:
        return None
    ddir = OUT / C.slug(agency) / C.slug(state) / C.slug(district)
    total, page, status = 0, 0, "ok"
    while True:
        rows, msg, attempts = call(agency, state, district, start, end, page)
        fname = ""
        sha = ""
        if rows:
            body = attempts[-1]["body"]
            fp = ddir / f"{start}_{end}_p{page:03d}.json.gz"
            C.write_new(fp, gzip.compress(body))
            fname = str(fp.relative_to(C.ROOT))
            sha = C.sha256_bytes(body)
        for a in attempts:
            C.append_csv(REQ_LOG, {"time_utc": C.now_utc(), "agency": agency, "state": state, "district": district,
                                   "start": start, "end": end, "page": page, "attempt": a["attempt"],
                                   "http_status": a["http_status"], "message": a["message"], "rows": a["rows"],
                                   "file": fname if a is attempts[-1] else "", "sha256": sha if a is attempts[-1] else "",
                                   "error": a["error"]}, REQ_FIELDS)
        if any(a["error"] for a in attempts) and not rows:
            status = "error"
        total += len(rows)
        if len(rows) < PAGE_SIZE:
            if page > 0 and not rows:
                status = "ok_end_on_empty_page"   # previous page was full; next page empty after retries
            break
        page += 1
        if page > 2000:
            status = "page_limit"
            break
    row = {"agency": agency, "state": state, "district": district, "start": start, "end": end,
           "pages": page + (1 if total else 0), "rows": total, "status": status if (total or status != "ok") else "empty",
           "time_utc": C.now_utc()}
    if status != "error":
        C.append_csv(DONE_LOG, row, DONE_FIELDS)
    return row


def month_windows(y, months=range(1, 13)):
    import calendar
    today = date.today()
    for m in months:
        if date(y, m, 1) > today:
            break
        last = calendar.monthrange(y, m)[1]
        yield f"{y}-{m:02d}-01", f"{y}-{m:02d}-{last:02d}"


def plan_windows(scope, from_year):
    """Rajasthan: decade probes to 1999, yearly windows 2000-2017 (manual era), monthly from 2018 (telemetry era).
    National: decade probes to 2009, yearly 2010-2021, CGWB manual campaign months from 2022."""
    this_year = date.today().year
    if scope == "rajasthan":
        return 1999, 2017, 2018, range(1, 13), this_year
    return 2009, 2021, 2022, MANUAL_MONTHS, this_year


def fetch_district(agency, state, district, scope, from_year, done):
    decade_end, yearly_end, monthly_from, late_months, this_year = plan_windows(scope, from_year)
    results = []
    for d0 in range(max(1970, from_year - from_year % 10), decade_end + 1, 10):
        d1 = min(d0 + 9, decade_end)
        r = fetch_window(agency, state, district, f"{d0}-01-01", f"{d1}-12-31", done)
        if r is not None:
            results.append(r)
    for y in range(max(decade_end + 1, from_year), yearly_end + 1):
        # years already fetched month by month by an earlier version of this script are not asked again
        months = [(agency, state, district, s, e) for s, e in month_windows(y)]
        covered = any(k[0] == agency and k[2] == district and k[3] <= f"{y}-01-01" and k[4] >= f"{y}-12-31"
                      for k in done)
        if covered or all(m in done for m in months):
            continue
        r = fetch_window(agency, state, district, f"{y}-01-01", f"{y}-12-31", done)
        if r is not None:
            results.append(r)
    for y in range(max(monthly_from, from_year), this_year + 1):
        for s, e in month_windows(y, late_months):
            r = fetch_window(agency, state, district, s, e, done)
            if r is not None:
                results.append(r)
    return results


def resolve_state(code, candidates, districts, agency):
    res_path = C.LOGS / "indiawris_state_resolution.csv"
    for r in C.read_csv(res_path):
        if r["code"] == code and r["agency"] == agency:
            return r["state_name"] or None
    chosen = None
    for cand in candidates:
        for d in districts[:4]:
            for y in (2019, 2015, 2010):
                rows, _, _ = call(agency, cand, d["name"], f"{y}-01-01", f"{y}-12-31", 0)
                if rows:
                    chosen = cand
                    break
            if chosen:
                break
        if chosen:
            break
    C.append_csv(res_path, {"code": code, "agency": agency, "state_name": chosen or "",
                            "candidates": "|".join(candidates), "time_utc": C.now_utc()},
                 ["code", "agency", "state_name", "candidates", "time_utc"])
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["rajasthan", "national"], required=True)
    ap.add_argument("--districts", nargs="*", help="limit to these district names (case-insensitive)")
    ap.add_argument("--states", nargs="*", help="national scope: limit to these state codes or names")
    ap.add_argument("--from-year", type=int, default=1960)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--recheck-empty", action="store_true", help="ask again for windows that came back empty")
    args = ap.parse_args()
    C.ensure_dirs()
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)
    masters = fetch_masters()
    print(f"district masters for {len(masters)} state codes")
    jobs = []
    if args.scope == "rajasthan":
        dists = masters.get("20", [])
        for agency in ("CGWB", "Rajasthan GW"):
            for d in dists:
                jobs.append((agency, "Rajasthan", d["name"]))
    else:
        for code, cands in STATE_CODES.items():
            if code == "20" or code not in masters:
                continue
            if args.states and not ({code, *[c.lower() for c in cands]} & {s.lower() for s in args.states}):
                continue
            st = resolve_state(code, cands, masters[code], "CGWB")
            if not st:
                print(f"  state code {code} ({cands[0]}): no CGWB data found under any spelling")
                continue
            for d in masters[code]:
                jobs.append(("CGWB", st, d["name"]))
    if args.districts:
        want = {x.lower() for x in args.districts}
        jobs = [j for j in jobs if j[2].lower() in want]
    print(f"{len(jobs)} agency/district jobs")
    done = window_done_set(args.recheck_empty)
    n = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_district, a, s, d, args.scope, args.from_year, done): (a, s, d) for a, s, d in jobs}
        for f in as_completed(futs):
            a, s, d = futs[f]
            n += 1
            try:
                res = f.result()
                rows = sum(r["rows"] for r in res)
                print(f"[{n}/{len(jobs)}] {a} / {s} / {d}: {len(res)} new windows, {rows} rows")
            except Exception as e:  # noqa: BLE001
                print(f"[{n}/{len(jobs)}] {a} / {s} / {d}: FAILED {e!r}")
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)
    print("done; existing groundwater.db unchanged")


if __name__ == "__main__":
    main()
