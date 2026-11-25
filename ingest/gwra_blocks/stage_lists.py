"""Step 1c: lines that list one assessment unit with its stage of extraction (%) and category,
e.g. '3 ALIPURDUAR FALAKATA 12.12 Safe'. Lines naming two categories (2024 vs 2025 comparisons) are skipped."""
import json, os, re, sys
from concurrent.futures import ProcessPoolExecutor
import pdfplumber
CAT = r"(safe|semi[\s_-]*critical|critical|over[\s_-]*exploited|saline)"
LINE = re.compile(r"^\s*(\d+)\.?\s+(.+?)\s+(\d+(?:\.\d+)?)\s*%?\s+" + CAT + r"\b(.*)$", re.I)
def scan(fp):
    out = []
    with pdfplumber.open(fp) as pdf:
        for i, p in enumerate(pdf.pages):
            try: t = p.extract_text() or ""
            except Exception: continue
            head = t[:600].lower()
            for k, l in enumerate(t.split("\n")):
                if len(re.findall(CAT, l, re.I)) != 1: continue
                m = LINE.match(l)
                if not m: continue
                name = m.group(2)
                if re.search(r"\d", name): continue
                out.append({"page": i + 1, "serial": m.group(1), "name": name, "stage": float(m.group(3)),
                            "category": m.group(4), "rest": m.group(5).strip(), "comparison_page": "comparison" in head})
    return out
if __name__ == "__main__":
    outdir = sys.argv[1]; pdfs = sys.argv[2:]
    with ProcessPoolExecutor(4) as ex:
        for fp, res in zip(pdfs, ex.map(scan, pdfs)):
            json.dump(res, open(os.path.join(outdir, os.path.basename(fp)[:5] + ".json"), "w"))
            print(os.path.basename(fp)[:5], len(res), end="; ", flush=True)
