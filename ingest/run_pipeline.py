"""
Run the JalMitra 4.0 monitoring pipeline after the downloads (reproducible, in order):

  1. check data/groundwater.db SHA256
  2. extract historical GWRA categories from downloaded CGWB block-wise PDFs (if pdfplumber is installed)
  3. build data/groundwater_monitoring.db (scratch first, integrity checks, then promote)
  4. write the reports in data/monitoring/reports/
  5. run test_monitoring.py
  6. check data/groundwater.db SHA256 again

Downloads are separate (they take hours):  ingest/run_downloads.ps1, or
  python ingest/download_cgwb_publications.py
  python ingest/download_indiawris_gwl.py --scope rajasthan
  python ingest/download_indiawris_gwl.py --scope national

Usage:  python ingest/run_pipeline.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402


def run(args):
    print("\n$ " + " ".join(args), flush=True)
    r = subprocess.run([sys.executable, *args], cwd=C.ROOT)
    return r.returncode


def main():
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)
    steps = []
    if (HERE / "extract_gwra_history.py").exists():
        steps.append(["ingest/extract_gwra_history.py"])
    steps += [["ingest/build_monitoring_db.py"], ["ingest/generate_reports.py"], ["test_monitoring.py"]]
    codes = [(s[0], run(s)) for s in steps]
    C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256)
    print("\nsummary:")
    for s, c in codes:
        print(f"  {s}: {'ok' if c == 0 else 'exit ' + str(c)}")
    print("data/groundwater.db SHA256 unchanged")
    sys.exit(max(c for _, c in codes))


if __name__ == "__main__":
    main()
