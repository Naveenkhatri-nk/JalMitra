"""Reproduce data/monitoring/gwra_blocks_2025.db from the downloaded CGWB 2025 state reports.

    .venv\\Scripts\\python.exe ingest\\gwra_blocks\\run_gwra_blocks.py

Steps (each writes under data/monitoring/extracted/gwra_blocks_2025/<run>/):
  1 dump_tables.py   ruled tables of every page            -> tables/<pub>.json
  2 text_rows.py     text lines that pass GEC-2015 identities -> text/<pub>.json
  3 stage_lists.py   'unit  stage%  category' list lines   -> stagelist/<pub>.json
  4 page_heads.py    first lines of each page               -> page_heads.json
  5 match_blocks.py  match to the official 2025 unit list (groundwater.db, read-only) -> matched_units.csv
  6 build_gwra_blocks_db.py -> scratch database, integrity check, then promoted to data/monitoring/gwra_blocks_2025.db
groundwater.db's SHA256 is checked before and after. Existing files are never overwritten: an existing
gwra_blocks_2025.db is moved to data/monitoring/scratch/previous/ first.
"""
import datetime, os, shutil, sqlite3, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common as C  # noqa: E402

PUBS = list(range(2095, 2130)) + [1542]   # 2025 state reports (+ Punjab 2024, read but not attached)
PDF_DIR = C.RAW / "cgwb_publications"
OUT_DB = C.MON / "gwra_blocks_2025.db"

def run(step, *args):
    cmd = [sys.executable, "-I", str(HERE / step), *map(str, args)]
    print(">", step, flush=True)
    subprocess.run(cmd, check=True)

def main():
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    work = C.EXTRACTED / "gwra_blocks_2025" / stamp
    for d in ("tables", "text", "stagelist"): (work / d).mkdir(parents=True, exist_ok=True)
    pdfs = sorted(str(p) for p in PDF_DIR.glob("*.pdf") if int(p.name[:5]) in PUBS)
    if len(pdfs) != len(PUBS): print(f"warning: found {len(pdfs)} of {len(PUBS)} reports in {PDF_DIR}")
    run("dump_tables.py", work / "tables", *pdfs)
    run("text_rows.py", work / "text", *pdfs)
    run("stage_lists.py", work / "stagelist", *pdfs)
    run("page_heads.py", work / "page_heads.json", *pdfs)
    run("match_blocks.py", work / "tables", work / "text", C.EXISTING_DB, work / "matched_units.csv", work / "unmatched_rows.json")
    C.SCRATCH.mkdir(parents=True, exist_ok=True)
    scratch = C.SCRATCH / f"gwra_blocks_2025_{stamp}.db"
    run("build_gwra_blocks_db.py", "--matched", work / "matched_units.csv", "--tables", work / "tables",
        "--groundwater-db", C.EXISTING_DB, "--catalog", C.CATALOG / "cgwb_publications_catalog.csv",
        "--pdf-dir", PDF_DIR, "--out", scratch)
    con = sqlite3.connect(scratch)
    assert con.execute("pragma integrity_check").fetchone()[0] == "ok"
    con.close()
    if OUT_DB.exists():
        prev = C.SCRATCH / "previous"; prev.mkdir(parents=True, exist_ok=True)
        shutil.move(str(OUT_DB), str(prev / f"gwra_blocks_2025_before_{stamp}.db"))
    shutil.copy2(scratch, OUT_DB)
    print("promoted", OUT_DB, C.sha256_file(OUT_DB))
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)

if __name__ == "__main__":
    main()
