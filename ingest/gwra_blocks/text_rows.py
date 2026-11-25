"""Step 1b: read every text line of every page and keep lines whose numbers satisfy the GEC-2015 identities.
Columns are found from the arithmetic, not from header positions:
  extractable = recharge - natural discharge   (three consecutive numbers)
  total = irrigation + industrial + domestic   (four consecutive numbers, after the triple)
  stage = 100 * total / extractable            (a later number)
Lines that only satisfy part of this are kept as partial rows."""
import json, os, re, sys
from concurrent.futures import ProcessPoolExecutor
import pdfplumber
NUM = re.compile(r"^-?\d+(?:\.\d+)?$")
def tol(a, b, rel=0.006, ab=0.15):
    return abs(a - b) <= max(ab, rel * max(abs(a), abs(b)))
def ttol(a, b, ints):
    # published figures are rounded to 2 decimals (or to whole hectare-metres in some states)
    return abs(a - b) <= max(1.01 if ints else 0.15, 0.0005 * max(abs(a), abs(b)))
def parse_line(line):
    toks = line.split()
    vals = []; raw = []
    for ix, t in enumerate(toks):
        t2 = t.replace(",", "").rstrip("%")
        if NUM.match(t2):
            vals.append((ix, float(t2))); raw.append(t2)
    if len(vals) < 4: return None
    n = [v for _, v in vals]
    isint = ["." not in x for x in raw]
    trips = [i for i in range(len(n) - 2)
             if n[i] > 0 and 0 <= n[i + 1] < n[i] and n[i + 2] > 0 and ttol(n[i + 2], n[i] - n[i + 1], all(isint[i:i + 3]))]
    quads = [m for m in range(len(n) - 3)
             if n[m + 3] > 0 and min(n[m:m + 3]) >= 0 and ttol(n[m + 3], n[m] + n[m + 1] + n[m + 2], all(isint[m:m + 4]))]
    best = None
    for i in trips:
        for m in quads:
            if m < i + 3: continue
            want = 100 * n[m + 3] / n[i + 2]
            for s in range(m + 4, len(n)):
                if tol(n[s], want, rel=0.01, ab=0.6):
                    best = (i, m, s); break
            if best: break
        if best: break
    ext_before = False
    if best is None and quads:
        # some annexures print only the extractable resource before the extraction columns
        for m in quads:
            if m >= 1 and n[m - 1] > 0:
                want = 100 * n[m + 3] / n[m - 1]
                s = next((s for s in range(m + 4, len(n)) if tol(n[s], want, rel=0.01, ab=0.6)), None)
                if s is not None:
                    best = (None, m, s); ext_before = True; break
    if best is None:
        best = (trips[0] if trips else None, next((m for m in quads if not trips or m >= trips[0] + 3), None), None)
    trip, quad, stage = best
    if trip is None and quad is None: return None
    lead = toks[:vals[0][0]] if vals[0][0] > 0 else []
    serial = None
    if vals[0][0] == 0:
        serial = toks[0]
        nxt = vals[1][0] if len(vals) > 1 else len(toks)
        lead = toks[1:nxt]
    m2 = re.match(r"^(\d+)([A-Za-z].*)$", toks[0])
    if m2 and serial is None:
        serial = m2.group(1); lead = [m2.group(2)] + lead[1:]
    tail = [t for t in toks[vals[-1][0] + 1:]]
    return {"serial": serial, "name": " ".join(lead), "tail": " ".join(tail), "nums": n,
            "trip": trip, "quad": quad, "stage": stage, "ext_before": ext_before}
def scan(fp):
    out = []
    with pdfplumber.open(fp) as pdf:
        for i, p in enumerate(pdf.pages):
            try:
                lines = (p.extract_text() or "").split("\n")
            except Exception:
                continue
            for k, l in enumerate(lines):
                r = parse_line(l)
                if r:
                    r["page"] = i + 1; r["line"] = k
                    r["prev"] = lines[k - 1] if k else ""
                    r["next"] = lines[k + 1] if k + 1 < len(lines) else ""
                    out.append(r)
    return out
if __name__ == "__main__":
    outdir = sys.argv[1]; pdfs = sys.argv[2:]
    with ProcessPoolExecutor(4) as ex:
        for fp, res in zip(pdfs, ex.map(scan, pdfs)):
            json.dump(res, open(os.path.join(outdir, os.path.basename(fp)[:5] + ".json"), "w"))
            full = sum(1 for r in res if r["stage"] is not None)
            print(os.path.basename(fp)[:5], len(res), "lines,", full, "full", flush=True)
