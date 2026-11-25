"""
eval/semantic_v5.py - scores the AI-explanation checks on the independent v5 held-out set (Phase 5).

eval/v5_heldout/items.tsv was written and labelled by a fresh subagent that never saw the checker code or the
earlier semantic sets; its sha256 was frozen (eval/v5_heldout/FROZEN_SHA256.txt) before any scoring.

The FULL production chain of llm_compose.enhance is applied to each text (same functions, same order):
  L0 answer_verifier.verify (numbers / quantity words / categories / injection / script / length) + place check
     + "your block" rule (general)
  L1 semantic_gate rules   L2 sentence support (bge-m3)   L3 model self-check (real Qwen3 instruct, reject-only)
Context: place items -> the engine's own answer for that place (template + table, answer language = item language);
general items -> the official category definitions + the cited chunks (sentences with digits removed, as in
production).

Positive class = BAD (should be rejected). Reported: TP (bad rejected), FP (good rejected), TN (good accepted),
FN (bad accepted), precision, recall, false acceptance rate = FN/bad, false rejection rate = FP/good.

Usage: python eval/semantic_v5.py --split dev|test_a|test_b [--no-self-check]
Writes eval/semantic_v5_<split>_<date>.csv / .md. Per-item details are printed for the dev split only.
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
for _k in [k for k in os.environ if k.startswith("JALMITRA_")]:
    del os.environ[_k]

import answer_verifier as av  # noqa: E402
import engine  # noqa: E402
import entity_resolver as er  # noqa: E402
import llm_compose as lc  # noqa: E402
import llm_provider as lp  # noqa: E402
import rag  # noqa: E402
import semantic_gate as sg  # noqa: E402

ITEMS = HERE / "v5_heldout" / "items.tsv"
SKIP_SUPPORT = False
FROZEN = "171825FB7E6364E894DE1FB932150BAD18BAED49BBAEBE638B96B51E4DCC7708"


def place_of(s):
    st, di, un = (s.split("|") + ["", "", ""])[:3]
    for p in er.index()["places"]:
        if un and p["type"] == "unit" and p["state"] == st and p["district"].lower() == di.lower() and \
                p["name"].lower() == un.lower():
            return p
        if not un and di and p["type"] == "district" and p["state"] == st and p["district"].lower() == di.lower():
            return p
        if not un and not di and p["type"] == "state" and p["state"] == st:
            return p
    return None


def context(item, chunks):
    lang = item["lang"]
    if item["context_type"] == "place":
        p = place_of(item["place"])
        if p is None:
            return None
        out = engine.answer_places("numeric" if p["type"] == "unit" else "status", [p], lang=lang)
        return {"mode": "data", "out": out, "facts": lc.facts_block(out), "passages": []}
    ids = [c for c in (item["chunk_ids"] or "").split(";") if c.strip()]
    ps = [{"text": lc._no_digit_sentences(rag.sanitize(chunks[c]["text"])), "raw": rag.sanitize(chunks[c]["text"]),
           "chunk_id": c} for c in ids if c in chunks]
    out = {"places": [], "table": [], "text": "", "lang": lang}
    return {"mode": "general", "out": out, "facts": lc.official_definitions(), "passages": ps}


def gate(text, ctx, lang, self_checker):
    """The checks of llm_compose.enhance after generation. Returns (rejected_by_layer or None, reasons)."""
    out, mode, facts, cited = ctx["out"], ctx["mode"], ctx["facts"], ctx["passages"]
    check = av.verify(text, facts, [], lang, fact_categories=lc.fact_categories(out) if mode == "data" else None,
                      key_figures=lc.key_figures(out), place_answer=mode == "data")
    reasons = list(check.reasons)
    if mode != "data" and lc.YOUR_AREA.search(text):
        reasons.append("your-area claim")
    bad_places = lc.foreign_places(text, lc.allowed_place_keys(out, cited))
    if bad_places:
        reasons.append("places: " + ", ".join(bad_places))
    if reasons:
        return "L0", reasons
    hits = sg.rule_check(text, facts, [p["text"] for p in cited], out.get("table"))
    if hits:
        return "L1", ["rules: " + ", ".join(sorted({h[0] for h in hits}))]
    if not SKIP_SUPPORT:
        try:
            bad, _ = sg.support_check(text, facts, [p["text"] for p in cited])
            if bad:
                return "L2", [f"{len(bad)} unsupported sentence(s)"]
        except Exception as e:
            return "L2", [f"support check could not run ({type(e).__name__})"]
    if self_checker is not None:
        v = self_checker(text, facts, [p["text"] for p in cited])
        if v == "NOT_SUPPORTED":
            return "L3", ["self-check: not supported"]
        if v is None:
            return "L3", ["self-check: no clear verdict (fail closed)"]
    return None, []


def metrics(rows, pred):
    tp = sum(1 for r in rows if r["label"] == "bad" and pred(r))
    fp = sum(1 for r in rows if r["label"] == "good" and pred(r))
    tn = sum(1 for r in rows if r["label"] == "good" and not pred(r))
    fn = sum(1 for r in rows if r["label"] == "bad" and not pred(r))
    nb, ng = tp + fn, fp + tn
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn, "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / nb if nb else None, "FAR": fn / nb if nb else None, "FRR": fp / ng if ng else None}


def pct(x):
    return "-" if x is None else f"{100 * x:.0f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test_a", "test_b"])
    ap.add_argument("--no-self-check", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--skip-support", action="store_true", help="variant: no sentence-support layer")
    ap.add_argument("--no-causal", action="store_true", help="variant: no causal word-overlap rule")
    a = ap.parse_args()
    global SKIP_SUPPORT
    SKIP_SUPPORT = a.skip_support
    sg.CAUSAL_OVERLAP = not a.no_causal
    h = hashlib.sha256(ITEMS.read_bytes()).hexdigest().upper()
    assert h == FROZEN, f"items.tsv changed after freezing: {h}"
    items = [r for r in csv.DictReader(open(ITEMS, encoding="utf-8"), delimiter="\t") if r["split"] == a.split]
    chunks = {json.loads(l)["chunk_id"]: json.loads(l) for l in open(BASE / "data" / "rag" / "chunks.jsonl",
                                                                         encoding="utf-8")}
    prov = None if a.no_self_check else lp.LLMProvider("ollama", model=lp.DEFAULT_MODEL, timeout=60)
    sc = None if prov is None else (lambda t, f, p: sg.llm_self_check(t, f, p, prov))
    rows = []
    t0 = time.time()
    for it in items:
        ctx = context(it, chunks)
        if ctx is None:
            layer, why = "ctx", ["place not found in DB index"]
        else:
            layer, why = gate(it["text"], ctx, it["lang"], sc)
        rows.append({**it, "rejected": layer is not None, "layer": layer or "-", "why": "; ".join(why)})
        if a.split == "dev":
            ok = (layer is not None) == (it["label"] == "bad")
            print(f"{'ok ' if ok else 'XX '} {it['id']:>5} {it['lang']:8s} {it['label']:4s} {it['error_type']:28s} "
                  f"{layer or '-':4s} {('; '.join(why))[:70]} | {it['text'][:120]}", flush=True)
    order = ["L0", "L1", "L2", "L3"]
    upto = lambda k: (lambda r: r["layer"] in order[:order.index(k) + 1] or r["layer"] == "ctx")   # noqa: E731
    date = dt.date.today().isoformat()
    name = f"semantic_v5_{a.split}{('_' + a.tag) if a.tag else ''}_{date}"
    L = [f"# Semantic checker on the independent v5 set — split {a.split} ({date})", "",
         f"items.tsv sha256 {h} (frozen before scoring). {len(rows)} items: "
         f"{sum(r['label'] == 'bad' for r in rows)} BAD / {sum(r['label'] == 'good' for r in rows)} GOOD. "
         f"Self-check: {'off' if prov is None else 'on (real model)'}. Run time {time.time() - t0:.0f} s.",
         "Labels were written by an AI subagent independent of the checker; they are NOT a substitute for review "
         "by a human groundwater expert.", "",
         "| checks applied | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |",
         "|---|---|---|---|---|---|---|---|---|"]
    names = {"L0": "number/category/place checks", "L1": "+ semantic rules", "L2": "+ sentence support",
             "L3": "+ model self-check (production)"}
    for k in order if prov is not None else order[:3]:
        m = metrics(rows, upto(k))
        L.append(f"| {names[k]} | {m['TP']} | {m['FP']} | {m['TN']} | {m['FN']} | {pct(m['precision'])} | "
                 f"{pct(m['recall'])} | {pct(m['FAR'])} | {pct(m['FRR'])} |")
    final = upto(order[-1] if prov is not None else "L2")
    L += ["", "## By language (all checks)", "", "| lang | n | TP | FP | TN | FN | precision | recall | false acceptance | "
          "false rejection |", "|---|---|---|---|---|---|---|---|---|---|"]
    for lang in ["en", "hinglish", "hi"]:
        rs = [r for r in rows if r["lang"] == lang]
        if rs:
            m = metrics(rs, final)
            L.append(f"| {lang} | {len(rs)} | {m['TP']} | {m['FP']} | {m['TN']} | {m['FN']} | {pct(m['precision'])} | "
                     f"{pct(m['recall'])} | {pct(m['FAR'])} | {pct(m['FRR'])} |")
    L += ["", "## BAD items by error type (all checks)", "", "| error type | n | caught | missed |", "|---|---|---|---|"]
    for et in sorted({r["error_type"] for r in rows if r["label"] == "bad"}):
        rs = [r for r in rows if r["error_type"] == et]
        c = sum(1 for r in rs if final(r))
        L.append(f"| {et} | {len(rs)} | {c} | {len(rs) - c} |")
    L += ["", "## GOOD items by context (all checks)", "", "| context | n | wrongly rejected |", "|---|---|---|"]
    for ct in ["place", "general"]:
        rs = [r for r in rows if r["label"] == "good" and r["context_type"] == ct]
        L.append(f"| {ct} | {len(rs)} | {sum(1 for r in rs if final(r))} |")
    L += ["", "## Rejections by layer", ""] + \
         [f"- {k}: {sum(1 for r in rows if r['layer'] == k)}" for k in ["ctx"] + order]
    (HERE / f"{name}.md").write_text("\n".join(L), encoding="utf-8")
    with open(HERE / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("\n".join(L[:14]))


if __name__ == "__main__":
    main()
