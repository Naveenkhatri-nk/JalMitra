import json, os, sys, glob
from concurrent.futures import ProcessPoolExecutor
import pdfplumber
def heads(fp):
    out = {}
    with pdfplumber.open(fp) as pdf:
        for i, p in enumerate(pdf.pages):
            try: out[i + 1] = (p.extract_text() or "")[:700]
            except Exception: out[i + 1] = ""
    return out
if __name__ == "__main__":
    pdfs = sys.argv[2:]
    with ProcessPoolExecutor(4) as ex:
        res = dict(zip([os.path.basename(p)[:5] for p in pdfs], ex.map(heads, pdfs)))
    json.dump(res, open(sys.argv[1], "w"))
