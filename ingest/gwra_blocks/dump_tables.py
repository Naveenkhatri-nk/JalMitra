"""Step 1: dump every ruled table (with at least one numeric data row) from each PDF, page by page, as JSON."""
import json, os, re, sys
from concurrent.futures import ProcessPoolExecutor
import pdfplumber
NUMRE = re.compile(r"^-?\d+(\.\d+)?$")
def num(s):
    s = (s or "").replace("\n", "").replace(",", "").replace(" ", "")
    return float(s) if NUMRE.match(s) else None
def is_data_row(r):
    cells = [(c or "").replace("\n", "").strip() for c in r]
    return sum(num(c) is not None for c in cells) >= 4
def dump(fp):
    out = []
    with pdfplumber.open(fp) as pdf:
        for i, p in enumerate(pdf.pages):
            try:
                tables = p.extract_tables()
            except Exception as e:
                out.append({"page": i + 1, "error": repr(e)}); continue
            for t in tables:
                if t and any(is_data_row(r) for r in t):
                    out.append({"page": i + 1, "ncol": len(t[0]), "rows": t})
    return out
if __name__ == "__main__":
    outdir = sys.argv[1]; pdfs = sys.argv[2:]
    with ProcessPoolExecutor(4) as ex:
        for fp, res in zip(pdfs, ex.map(dump, pdfs)):
            json.dump(res, open(os.path.join(outdir, os.path.basename(fp)[:5] + ".json"), "w"))
            print(os.path.basename(fp)[:5], len(res), "tables", flush=True)
