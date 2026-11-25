"""
eval/compare_models.py - side-by-side comparison of rule baseline and LLM runs (JalMitra 4.0 Phase 2).

Reads the files written by eval/model_selection.py and writes eval/comparison_<date>.md.

Usage:
  python eval/compare_models.py --date 2026-11-23 --models qwen3-4b qwen3-4b-instruct-2507-q4_K_M \
         --labels thinking instruct
"""

import argparse
import csv
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANGS = ["en", "hi", "hinglish", "raj", "pa", "mr"]
REVIEW = {"raj", "pa", "mr"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def t(v):
    return v == "True"


def rate(rows, key, kind=None):
    rs = [r for r in rows if (kind is None or r["kind"] == kind) and r.get(key) not in ("", None)]
    if not rs:
        return "-"
    ok = sum(1 for r in rs if t(r[key]))
    return f"{ok}/{len(rs)}"


def pct(vals, q):
    v = sorted(vals)
    if not v:
        return None
    return v[min(len(v) - 1, max(0, round(q / 100 * (len(v) - 1))))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-11-23")
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    a = ap.parse_args()
    rules = load(HERE / f"results_rules_{a.date}.csv")
    runs = []
    for tag, label in zip(a.models, a.labels):
        res = load(HERE / f"results_{tag}_{a.date}.csv")
        ph_path = HERE / f"phrasing_{tag}_{a.date}.csv"
        ph = load(ph_path) if ph_path.exists() else []
        runs.append((label, tag, res, ph))
    by_id_rules = {r["id"]: r for r in rules}

    L = [f"# Model comparison: rules vs {' vs '.join(l for l, *_ in runs)} ({a.date})", "",
         "Same 120 questions (eval/questions_6lang.tsv), num_ctx 4096, temperature 0, understanding with thinking off "
         "(JSON schema). Rule columns come from the existing engine (read-only).",
         "Runs: " + "; ".join(f"**{l}** = `{tag}`" for l, tag, *_ in runs) + ".",
         "**raj / pa / mr questions are still pending native-speaker review; their scores are provisional.**", ""]

    metrics = [  # (title, rule_key, llm_key, kind)
        ("intent", "rule_intent_ok", "llm_intent_ok", None),
        ("language label", "rule_lang_ok", "llm_lang_ok", None),
        ("places resolved", "rule_place_ok", "llm_place_ok", None),
        ("follow-ups (2)", "rule_followup_ok", "llm_followup_ok", "followup"),
        ("term explanations (2)", "rule_intent_ok", "llm_intent_ok", "explain"),
        ("ambiguous place (1)", "rule_place_ok", "llm_place_ok", "ambiguous"),
        ("injection / guess a figure (1)", "rule_intent_ok", "llm_intent_ok", "injection"),
        ("unknown location (1)", "rule_place_ok", "llm_place_ok", "unknown"),
    ]
    for title, rk, lk, kind in metrics:
        L += [f"## {title}", "", "| lang | rules | " + " | ".join(l for l, *_ in runs) + " |",
              "|---|---|" + "---|" * len(runs)]
        for lang in LANGS + ["all"]:
            pick = lambda rows: [r for r in rows if lang == "all" or r["lang"] == lang]
            L.append(f"| {lang} | {rate(pick(rules), rk, kind)} | " +
                     " | ".join(rate(pick(res), lk, kind) for _, _, res, _ in runs) + " |")
        L.append("")

    L += ["## JSON validity, hallucinated numbers, latency (understanding)", "",
          "| run | JSON valid | outputs with a number not in the question | unknown place mapped to a real place | "
          "p50 ms | p95 ms |", "|---|---|---|---|---|---|"]
    rms = [float(r["rule_ms"]) for r in rules]
    L.append(f"| rules | n/a | n/a | 0 | {pct(rms, 50):.1f} | {pct(rms, 95):.1f} |")
    for label, _, res, _ in runs:
        lat = [float(r["llm_latency_ms"]) for r in res]
        flags = sum(1 for r in res if t(r["llm_halluc_flag"]))
        unk = sum(1 for r in res if r["kind"] == "unknown" and r["llm_place_ok"] == "False")
        L.append(f"| {label} | {rate(res, 'llm_json_ok')} | {flags} | {unk} | {pct(lat, 50):.0f} | {pct(lat, 95):.0f} |")
    L.append("")
    L += ["### Latency per language (understanding p50 / p95 ms)", "",
          "| lang | " + " | ".join(l for l, *_ in runs) + " |", "|---|" + "---|" * len(runs)]
    for lang in LANGS:
        cells = []
        for _, _, res, _ in runs:
            lat = [float(r["llm_latency_ms"]) for r in res if r["lang"] == lang]
            cells.append(f"{pct(lat, 50):.0f} / {pct(lat, 95):.0f}")
        L.append(f"| {lang} | " + " | ".join(cells) + " |")
    L.append("")

    L += ["## Number preservation in phrasing (12 answers, 2 per language)", "",
          "Facts = engine.answer_places('numeric', [record], lang). 'preserved' = an answer was produced and every "
          "number in it is in the facts. 'empty/error' = no usable answer.", "",
          "| run | thinking | preserved | answer with a new number | empty/error | template numbers kept (median) | "
          "p50 ms | p95 ms |", "|---|---|---|---|---|---|---|---|"]
    for label, _, _, ph in runs:
        if not ph:
            L.append(f"| {label} | - | - | - | - | - | - | - |")
            continue
        prod = [p for p in ph if t(p["ok"])]
        new = [p for p in prod if p["not_in_facts"]]
        kept = [int(p["kept_key_numbers"].split("/")[0]) for p in prod]
        lat = [float(p["latency_ms"]) for p in ph]
        L.append(f"| {label} | {ph[0].get('think', '?')} | {sum(1 for p in ph if t(p['preserved']))}/{len(ph)} | "
                 f"{len(new)} | {len(ph) - len(prod)} | {statistics.median(kept) if kept else '-'}/11 | "
                 f"{pct(lat, 50):.0f} | {pct(lat, 95):.0f} |")
    L.append("")
    for label, _, _, ph in runs:
        if ph:
            L += [f"### Phrasing detail: {label}", "", "| id | preserved | new numbers | kept | ms | output (start) |",
                  "|---|---|---|---|---|---|"]
            for p in ph:
                out = (p["output"] or p["error"]).replace("|", "/")[:140]
                L.append(f"| {p['id']} | {p['preserved']} | {p['not_in_facts'] or '-'} | {p['kept_key_numbers']} | "
                         f"{float(p['latency_ms']):.0f} | {out} |")
            L.append("")

    L += ["## Rajasthani, Punjabi, Marathi: every failed check (pending native-speaker review)", ""]
    checks = [("intent", "llm_intent_ok", "rule_intent_ok"), ("language", "llm_lang_ok", "rule_lang_ok"),
              ("places", "llm_place_ok", "rule_place_ok"), ("follow-up", "llm_followup_ok", "rule_followup_ok"),
              ("metric", "llm_metric_ok", None)]
    for lang in sorted(REVIEW, key=LANGS.index):
        L += [f"### {lang}", "", "| id | question | expected | check | rules | " +
              " | ".join(l for l, *_ in runs) + " |", "|---|---|---|---|---|" + "---|" * len(runs)]
        rows = [r for r in runs[0][2] if r["lang"] == lang]
        idx = [{r["id"]: r for r in res} for _, _, res, _ in runs]
        for r0 in rows:
            rid = r0["id"]
            rr = by_id_rules[rid]
            for name, lk, rk in checks:
                vals = [ix[rid].get(lk, "") for ix in idx]
                rv = rr.get(rk, "") if rk else ""
                if "False" not in vals and rv != "False":
                    continue

                def show(rec, ok):
                    if ok in ("", None):
                        return "-"
                    if ok == "True":
                        return "ok"
                    if name == "language":
                        return f"✗ {rec.get('llm_lang') or rec.get('rule_lang')}"
                    if name in ("intent", "metric"):
                        return f"✗ {rec.get('llm_' + name) or rec.get('rule_raw_intent')}"
                    if name == "places":
                        got = rec.get("llm_places") or ""
                        res_ = rec.get("llm_resolved") or ""
                        return f"✗ {got[:60]} → {res_[:70] or 'nothing'}"
                    return "✗"

                rule_cell = "-" if not rk else ("ok" if rv == "True" else (
                    f"✗ {rr['rule_lang']}" if name == "language" else
                    f"✗ {rr['rule_raw_intent']}" if name == "intent" else
                    f"✗ {(rr['rule_places'] or ('asked to clarify' if rr['rule_clarify'] == 'True' else 'nothing'))[:70]}"))
                exp = {"intent": r0["expected_intent"], "language": lang, "places": r0["expected_places"][:60],
                       "follow-up": r0["expected_places"][:40], "metric": r0["expected_metric"]}[name]
                L.append(f"| {rid} | {r0['question']} | {exp} | {name} | {rule_cell} | " +
                         " | ".join(show(ix[rid], ix[rid].get(lk, "")) for ix in idx) + " |")
        L.append("")
    out = HERE / f"comparison_{a.date}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("written", out)


if __name__ == "__main__":
    main()
