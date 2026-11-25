"""
Catalogue and download CGWB publications (Central Ground Water Board, Publications and Media Warehouse).

Detail page : https://cgwb.gov.in/cgwbpnm/public/publication-detail/<id>
File        : https://cgwb.gov.in/cgwbpnm/public/download/<id>      (direct PDF, no login)

Step 1 (catalogue): read every detail page id 1..--max-id, keep each page's HTML (gzip) under
        data/monitoring/raw/cgwb_publication_pages/ and write data/monitoring/catalog/cgwb_publications_catalog.csv
Step 2 (download): download the selected publications to data/monitoring/raw/cgwb_publications/<id>_<slug>.pdf,
        never overwriting, and record size, SHA256, URL and time in data/monitoring/catalog/cgwb_downloads.csv

Selection (default, JalMitra priorities): Rajasthan first, then national.
    * Resource Assessment   : state Rajasthan or All (national compilations, block-wise categorisation tables)
    * Ground Water Level    : all
    * Year Book             : Rajasthan or All
    * Ground Water Quality  : Rajasthan or All
    * Aquifer Mapping / Pilot Aquifer Mapping / Aquifer Atlas and Maps : Rajasthan or All
    --all-states-resource-assessment adds every state's resource assessment report.

Usage:  python ingest/download_cgwb_publications.py [--catalog-only] [--max-id 2400]
"""
from __future__ import annotations

import argparse
import gzip
import html
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

BASE = "https://cgwb.gov.in/cgwbpnm/public"
PAGES = C.RAW / "cgwb_publication_pages"
FILES = C.RAW / "cgwb_publications"
CAT = C.CATALOG / "cgwb_publications_catalog.csv"
DL = C.CATALOG / "cgwb_downloads.csv"
CAT_FIELDS = ["pub_id", "title", "category", "state", "district", "block", "year_of_issue", "authors", "keywords",
              "detail_url", "download_url", "page_sha256", "read_utc"]
DL_FIELDS = ["pub_id", "title", "category", "state", "year_of_issue", "download_url", "file", "bytes", "sha256",
             "content_type", "server_filename", "status", "time_utc", "note"]
MAX_BYTES = 300 * 1024 * 1024

SELECT_RAJ_OR_ALL = {"Resource Assessment", "Year Book", "Ground Water Quality", "Aquifer Mapping",
                     "Pilot Aquifer Mapping", "Aquifer Atlas and Maps"}
SELECT_ALWAYS = {"Ground Water Level"}


def clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def parse_detail(page: str) -> dict:
    # the publication title is the <h3> inside the details tab; earlier headings carry the site name
    m = re.search(r'id="nav-tabContent".*?<h3[^>]*>(.*?)</h3>', page, re.S)
    if not m:
        heads = [h for h in re.findall(r"<h3[^>]*>(.*?)</h3>", page, re.S) if "Warehouse" not in h]
        title = clean(heads[0]) if heads else ""
    else:
        title = clean(m.group(1))
    fields = {clean(k): clean(v) for k, v in re.findall(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", page, re.S)}
    return {"title": title, "category": fields.get("Category", ""), "state": fields.get("State", ""),
            "district": fields.get("District", ""), "block": fields.get("Block", ""),
            "year_of_issue": fields.get("Year of Issue", ""), "authors": fields.get("Name of Authors", ""),
            "keywords": fields.get("Keywords", "")}


def catalogue_one(pid: int):
    p = PAGES / f"{pid:05d}.html.gz"
    if p.exists():
        body = gzip.decompress(p.read_bytes())
    else:
        try:
            st, _, body = C.http(f"{BASE}/publication-detail/{pid}", timeout=60, retries=0)
        except Exception as e:  # noqa: BLE001
            return {"pub_id": pid, "error": repr(e)}
        if st != 200:
            return {"pub_id": pid, "error": f"HTTP {st}"}
        C.write_new(p, gzip.compress(body))
    d = parse_detail(body.decode("utf-8", "replace"))
    if not (d["title"] or d["category"]):
        return None
    d.update(pub_id=pid, detail_url=f"{BASE}/publication-detail/{pid}", download_url=f"{BASE}/download/{pid}",
             page_sha256=C.sha256_bytes(body), read_utc=C.now_utc())
    return d


def build_catalogue(max_id: int, workers: int):
    C.ensure_dirs()
    PAGES.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(catalogue_one, range(1, max_id + 1)))
    rows = [r for r in res if r and "error" not in r]
    errs = [r for r in res if r and "error" in r]
    import csv
    tmp = CAT.with_suffix(".csv.part")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAT_FIELDS)
        w.writeheader()
        for r in sorted(rows, key=lambda r: r["pub_id"]):
            w.writerow({k: r.get(k, "") for k in CAT_FIELDS})
    # the catalogue is a derived file (not an original), so it is refreshed in place
    import os
    os.replace(tmp, CAT)
    for e in errs:
        C.append_csv(C.LOGS / "cgwb_catalogue_errors.csv", {"pub_id": e["pub_id"], "error": e["error"],
                                                            "time_utc": C.now_utc()}, ["pub_id", "error", "time_utc"])
    print(f"catalogue: {len(rows)} publications, {len(errs)} page errors -> {CAT}")
    return rows


def selected(r: dict, all_states_ra: bool) -> bool:
    st = (r["state"] or "").strip().lower()
    cat = r["category"]
    if cat in SELECT_ALWAYS:
        return True
    if cat == "Resource Assessment" and all_states_ra:
        return True
    return cat in SELECT_RAJ_OR_ALL and (st in ("rajasthan", "all") or "rajasthan" in r["title"].lower())


def download_one(r: dict):
    done = {x["pub_id"] for x in C.read_csv(DL) if x["status"] == "ok"}
    if str(r["pub_id"]) in done:
        return "skip"
    url = r["download_url"]
    row = {k: r.get(k, "") for k in ("pub_id", "title", "category", "state", "year_of_issue")}
    row.update(download_url=url, time_utc=C.now_utc())
    try:
        st, hdr, body = C.http(url, timeout=600, retries=2)
    except Exception as e:  # noqa: BLE001
        row.update(status="error", note=repr(e)[:300])
        C.append_csv(DL, row, DL_FIELDS)
        return "error"
    ctype = hdr.get("Content-Type", hdr.get("content-type", ""))
    disp = hdr.get("Content-Disposition", hdr.get("content-disposition", ""))
    m = re.search(r'filename="?([^";]+)', disp or "")
    ext = ".pdf" if "pdf" in ctype.lower() else (Path(m.group(1)).suffix if m else ".bin")
    row.update(content_type=ctype, server_filename=m.group(1) if m else "", bytes=len(body))
    if st != 200 or not body:
        row.update(status=f"http_{st}")
    elif len(body) > MAX_BYTES:
        row.update(status="skipped_too_large")
    elif ext == ".pdf" and b"%PDF" not in body[:1024]:
        # some CGWB files start with a newline before %PDF; they are kept byte-for-byte as served
        row.update(status="not_a_pdf", note=body[:80].decode("latin-1"))
    else:
        fp = FILES / f"{int(r['pub_id']):05d}_{C.slug(r['title'], 70)}{ext}"
        wrote = C.write_new(fp, body)
        row.update(file=str(fp.relative_to(C.ROOT)), sha256=C.sha256_bytes(body),
                   status="ok", note="" if wrote else "file already existed; not overwritten")
    C.append_csv(DL, row, DL_FIELDS)
    time.sleep(0.5)
    return row["status"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-id", type=int, default=2400)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--catalog-only", action="store_true")
    ap.add_argument("--all-states-resource-assessment", action="store_true")
    ap.add_argument("--ids", nargs="*", type=int, help="download only these publication ids")
    args = ap.parse_args()
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)
    rows = build_catalogue(args.max_id, args.workers)
    if args.catalog_only:
        return
    FILES.mkdir(parents=True, exist_ok=True)
    pick = [r for r in rows if (r["pub_id"] in args.ids if args.ids else selected(r, args.all_states_resource_assessment))]
    print(f"{len(pick)} publications selected for download")
    with ThreadPoolExecutor(max_workers=3) as ex:
        res = list(ex.map(download_one, pick))
    from collections import Counter
    print(Counter(res))
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)


if __name__ == "__main__":
    main()
