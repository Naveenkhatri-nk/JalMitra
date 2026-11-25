"""
eval/semantic_factuality.py - labelled evaluation of the semantic gate (JalMitra 4.0 Phase 4).

71 short explanations, each labelled GOOD (correct, supported) or BAD (wrong direction, wrong definition,
contradicts the database figures, unsupported cause or claim). Topics: groundwater depth direction,
pre- vs post-monsoon, recharge vs extraction, depletion, seasonal change, category explanations, unsupported
causal claims, contradictions with the figures, claims not supported by the sources. Languages: en, hi,
hinglish (+ a few mr / pa). Case 41 is the real Phase 3 Hindi output that passed the number verifier.

Contexts are REAL: fact blocks are the rule engine's template answers and table rows; passages are chunks
from data/rag/chunks.jsonl (sentences with digits removed, as llm_compose does).

Gate variants measured:  L1 rules | L1+L2 rules + sentence support (bge-m3) | L1+L2+L3 (+ model self-check)
Positive class = BAD (the gate should reject it). precision = rejected-and-bad / rejected;
recall = rejected-and-bad / bad; false-rejection rate = good rejected / good.

Usage: python eval/semantic_factuality.py [--no-embed] [--self-check] [--sweep]
Writes eval/semantic_results_<date>.csv and eval/semantic_summary_<date>.md
"""

import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
for _k in [k for k in os.environ if k.startswith("JALMITRA_")]:
    del os.environ[_k]

import engine  # noqa: E402
import llm_compose as lc  # noqa: E402
import rag  # noqa: E402
import semantic_gate as sg  # noqa: E402

G, B = "good", "bad"
CASES = [  # (id, lang, ctx, topic, label, text)
    # ---- English, place answer (PHAGI: Over-exploited, 117 %, recharge 5949 < extraction 6265 ham)
    (1, "en", "phagi_en", "category", G, "PHAGI block is Over-exploited, with a stage of extraction of 117%."),
    (2, "en", "phagi_en", "depletion", G, "More groundwater is taken out each year than is replaced, so the stage is above 100%."),
    (3, "en", "phagi_en", "recharge_vs_extraction", G, "Total extraction of 6265 ham is higher than the annual recharge of 5949 ham."),
    (4, "en", "phagi_en", "figures", G, "The annual recharge of Phagi is 5949 ham (0.05949 bcm)."),
    (5, "en", "phagi_en", "contradiction", B, "Annual recharge of 5949 ham is more than the extraction of 6265 ham, so the block is safe."),
    (6, "en", "phagi_en", "unsupported_cause", B, "Phagi is Over-exploited because of rapid industrial growth and factories."),
    (7, "en", "phagi_en", "depletion", B, "Because extraction is more than recharge, the water level in Phagi keeps rising."),
    (8, "en", "phagi_en", "category", B, "Over-exploited means the stage of extraction is between 70% and 90%."),
    (9, "en", "phagi_en", "stage_formula", B, "The stage of extraction is calculated as annual recharge divided by total extraction."),
    (10, "en", "phagi_en", "unsupported_claim", B, "Phagi receives heavy rainfall every year, so farmers need not worry."),
    # ---- English, general explanations
    (11, "en", "general", "recharge", G, "Groundwater recharge is water that rain and other sources add to the aquifer each year."),
    (12, "en", "general", "pre_post_monsoon", G, "The water table is usually deeper before the monsoon and becomes shallower during the monsoon."),
    (13, "en", "general", "depth_direction", G, "During the monsoon, recharge from rainfall raises the groundwater level."),
    (14, "en", "general", "recharge", G, "Rainfall is the main source of groundwater recharge."),
    (15, "en", "general", "category", G, "Semi-critical means the stage of extraction is more than 70% and up to 90%."),
    (16, "en", "general", "category", G, "Safe means the stage of extraction is up to 70%."),
    (17, "en", "general", "depletion", G, "When extraction is more than recharge, groundwater levels fall over time."),
    (18, "en", "general", "category", G, "Critical means the stage of extraction is more than 90% and up to 100%."),
    (19, "en", "general", "depth_direction", B, "During the monsoon the water table becomes deeper."),
    (20, "en", "general", "seasonal", B, "In the rainy season the groundwater level falls because more water is used."),
    (21, "en", "general", "depth_direction", B, "Depth to water increases during the monsoon months."),
    (22, "en", "general", "recharge_vs_extraction", B, "Recharge lowers the water level in the aquifer."),
    (23, "en", "general", "depletion", B, "If extraction exceeds recharge the groundwater situation improves."),
    (24, "en", "general", "category", B, "Safe means the stage of extraction is more than 100%."),
    (25, "en", "general", "unsupported_cause", B, "Groundwater is falling mainly because of climate change and global warming."),
    (26, "en", "general", "stage_formula", B, "The stage of extraction is recharge divided by extraction, in percent."),
    (27, "en", "general", "unsupported_claim", B, "Monsoon rains do not matter for groundwater in India."),
    (28, "en", "general", "depth_direction", B, "Pumping more groundwater raises the water level."),
    (29, "en", "conserve", "depletion", G, "Rainwater harvesting and artificial recharge structures can help reduce groundwater depletion."),
    (30, "en", "conserve", "depletion", G, "Restricting new wells in over-exploited areas is one recommended measure."),
    (31, "en", "conserve", "unsupported_claim", B, "Building more borewells is the best way to reduce groundwater depletion."),
    (32, "en", "conserve", "seasonal", B, "Depletion can be reduced by pumping more water during the monsoon."),
    # ---- Hindi, place answer
    (33, "hi", "phagi_hi", "category", G, "फागी ब्लॉक अतिदोहित श्रेणी में है, यहाँ दोहन का स्तर 117% है।"),
    (34, "hi", "phagi_hi", "depletion", G, "यहाँ जितना पानी हर साल भरता है उससे ज़्यादा पानी निकाला जा रहा है।"),
    (35, "hi", "phagi_hi", "contradiction", B, "फागी में पुनर्भरण 5949 हैम निकासी 6265 हैम से अधिक है, इसलिए स्थिति ठीक है।"),
    (36, "hi", "phagi_hi", "unsupported_cause", B, "फागी अतिदोहित है क्योंकि वहाँ बहुत सारे कारखाने हैं।"),
    (37, "hi", "phagi_hi", "depth_direction", B, "दोहन ज़्यादा होने से भूजल स्तर बढ़ता है।"),
    (38, "hi", "phagi_hi", "category", B, "अतिदोहित का मतलब है कि दोहन का स्तर 70% से 90% के बीच है।"),
    # ---- Hindi, general
    (39, "hi", "general", "depth_direction", G, "मानसून के दौरान बारिश से पुनर्भरण होता है और भूजल स्तर ऊपर आता है।"),
    (40, "hi", "general", "pre_post_monsoon", G, "मानसून से पहले भूजल तल आमतौर पर गहरा होता है।"),
    (41, "hi", "general", "pre_post_monsoon", B, "बरसात के मौसम में भूजल तल गहरा होता है और बरसात के बाद इसका स्तर घटता है।"),
    (42, "hi", "general", "depth_direction", B, "बारिश के मौसम में जल स्तर नीचे चला जाता है।"),
    (43, "hi", "general", "category", G, "सुरक्षित श्रेणी का मतलब है दोहन का स्तर 70% तक।"),
    (44, "hi", "general", "category", B, "सुरक्षित का मतलब है दोहन 100% से अधिक।"),
    (45, "hi", "general", "recharge", G, "भूजल पुनर्भरण वह पानी है जो बारिश और अन्य स्रोतों से हर साल ज़मीन में जाता है।"),
    (46, "hi", "general", "recharge_vs_extraction", B, "पुनर्भरण से भूजल स्तर नीचे गिरता है।"),
    (47, "hi", "general", "unsupported_cause", B, "भूजल घटने का मुख्य कारण जलवायु परिवर्तन है।"),
    (48, "hi", "general", "depletion", G, "जब निकासी पुनर्भरण से अधिक होती है तो भूजल स्तर गिरता है।"),
    (49, "hi", "conserve", "depletion", G, "वर्षा जल संचयन और कृत्रिम पुनर्भरण से भूजल की कमी कम की जा सकती है।"),
    # ---- Hinglish, place answer
    (50, "hinglish", "phagi_hing", "category", G, "Phagi block Over-exploited category mein hai, extraction stage 117% hai."),
    (51, "hinglish", "phagi_hing", "depletion", G, "Yahan jitna paani har saal bharta hai usse zyada paani nikala ja raha hai."),
    (52, "hinglish", "phagi_hing", "contradiction", B, "Phagi mein recharge extraction se zyada hai, isliye block safe hai."),
    (53, "hinglish", "phagi_hing", "unsupported_cause", B, "Phagi Over-exploited hai kyunki wahan factory bahut hain."),
    (54, "hinglish", "phagi_hing", "category", B, "Over-exploited ka matlab stage 70% se 90% ke beech hai."),
    # ---- Hinglish, general
    (55, "hinglish", "general", "depth_direction", G, "Monsoon mein barish se recharge hota hai aur water level upar aata hai."),
    (56, "hinglish", "general", "depth_direction", B, "Monsoon mein water level neeche chala jata hai."),
    (57, "hinglish", "general", "seasonal", B, "Barish ke mausam mein paani ka level girta hai."),
    (58, "hinglish", "general", "pre_post_monsoon", G, "Monsoon se pehle water level aam taur par gehra hota hai."),
    (59, "hinglish", "general", "depth_direction", B, "Extraction zyada hone se water level badhta hai."),
    (60, "hinglish", "general", "category", G, "Safe ka matlab hai stage of extraction 70% tak."),
    (61, "hinglish", "general", "unsupported_cause", B, "Groundwater kam hone ka sabse bada karan jalvayu parivartan hai."),
    (62, "hinglish", "general", "depletion", G, "Jab extraction recharge se zyada hota hai to water level girta hai."),
    # ---- English, safe block (TODARAISINGH: Safe, 64 %, recharge 6079 > extraction 3627 ham)
    (63, "en", "todar_en", "category", G, "TODARAISINGH is Safe; its stage of extraction is 64%."),
    (64, "en", "todar_en", "recharge_vs_extraction", G, "Annual recharge of 6079 ham is more than the extraction of 3627 ham."),
    (65, "en", "todar_en", "contradiction", B, "Extraction of 3627 ham is more than the recharge of 6079 ham."),
    (66, "en", "todar_en", "category", B, "TODARAISINGH is Safe because its stage is 95%."),
    # ---- Marathi / Punjabi (rules cover only some words; native review pending)
    (67, "mr", "general", "depth_direction", B, "पावसाळ्यात भूजल पातळी खोल जाते."),
    (68, "mr", "general", "depth_direction", G, "पावसाळ्यात पुनर्भरणामुळे भूजल पातळी वर येते."),
    (69, "pa", "general", "depth_direction", B, "ਮਾਨਸੂਨ ਵਿੱਚ ਪਾਣੀ ਦਾ ਪੱਧਰ ਹੇਠਾਂ ਜਾਂਦਾ ਹੈ।"),
    (70, "pa", "general", "depth_direction", G, "ਮਾਨਸੂਨ ਵਿੱਚ ਮੀਂਹ ਨਾਲ ਪਾਣੀ ਦਾ ਪੱਧਰ ਉੱਪਰ ਆਉਂਦਾ ਹੈ।"),
    # ---- real Phase 3 English output (difference between extraction and recharge)
    (71, "en", "general", "recharge_vs_extraction", G,
     "Recharge is the amount of water that naturally enters the ground, like from rainfall or streams, to refill "
     "aquifers. Extraction is the amount of water taken out from groundwater for use, such as for irrigation or "
     "industry. When extraction exceeds recharge, the groundwater level drops and may go beyond safe limits."),
]

# HELD-OUT cases: written after the rules were tuned on CASES and scored once, without further tuning.
HELDOUT = [
    (101, "en", "general", "depth_direction", B, "Groundwater levels go down sharply when the monsoon rains arrive."),
    (102, "en", "general", "depth_direction", G, "The monsoon recharges aquifers, so wells usually have water closer to the surface afterwards."),
    (103, "en", "general", "pre_post_monsoon", G, "Before the monsoon, the groundwater table is generally at its deepest."),
    (104, "en", "general", "seasonal", B, "The water table is shallowest in May, just before the monsoon."),
    (105, "en", "general", "depletion", B, "Taking out more water than is recharged makes groundwater more plentiful."),
    (106, "en", "general", "category", B, "A block is Critical when its stage of extraction is below 50%."),
    (107, "en", "general", "category", G, "A block is Over-exploited when extraction is more than the annual extractable resource."),
    (108, "en", "general", "stage_formula", G, "Stage of extraction compares total extraction with the annual extractable resource."),
    (109, "en", "general", "stage_formula", B, "Stage of extraction is the extractable resource divided by the extraction."),
    (110, "en", "general", "unsupported_cause", B, "Over-exploitation in Rajasthan is caused mainly by urbanisation."),
    (111, "en", "conserve", "depletion", G, "Rainwater harvesting can help to recharge groundwater in stressed areas."),
    (112, "en", "conserve", "unsupported_claim", B, "Groundwater depletion can only be solved by importing water from other states."),
    (113, "en", "phagi_en", "contradiction", B, "Phagi is replenished faster than it is used."),
    (114, "en", "phagi_en", "depletion", G, "In Phagi, use of groundwater is greater than what is replaced each year."),
    (115, "en", "todar_en", "contradiction", B, "In Todaraisingh more water is pumped out than is recharged."),
    (116, "hi", "general", "depth_direction", B, "मानसून आने पर कुओं का पानी और नीचे चला जाता है।"),
    (117, "hi", "general", "depth_direction", G, "मानसून की बारिश से कुओं में पानी का स्तर ऊपर आ जाता है।"),
    (118, "hi", "general", "category", B, "गंभीर श्रेणी का मतलब है दोहन का स्तर 50% से कम।"),
    (119, "hi", "general", "unsupported_cause", B, "भूजल में गिरावट की वजह शहरीकरण है।"),
    (120, "hi", "phagi_hi", "contradiction", B, "फागी में जितना पानी निकलता है उससे ज़्यादा भर जाता है।"),
    (121, "hinglish", "general", "depth_direction", B, "Barsaat mein kuon ka paani aur gehra chala jata hai."),
    (122, "hinglish", "general", "depth_direction", G, "Monsoon ki barish se kuon mein paani upar aata hai."),
    (123, "hinglish", "general", "category", B, "Critical ka matlab hai stage 50% se kam."),
    (124, "hinglish", "phagi_hing", "contradiction", B, "Phagi mein paani nikalne se zyada recharge hota hai."),
]

PASSAGE_IDS = {"general": ["NC2025-p057-c0", "NC2025-p083-c0", "RJ2025-p074-c0"],
               "conserve": ["RJ2025-p015-c0", "RJ2025-p105-c0", "NC2025-p030-c0"]}


def contexts():
    chunks = {json.loads(l)["chunk_id"]: json.loads(l) for l in open(HERE.parent / "data" / "rag" / "chunks.jsonl",
                                                                       encoding="utf-8")}

    def passages(ids):
        return [lc._no_digit_sentences(rag.sanitize(chunks[i]["text"])) for i in ids]

    def place(q, lang):
        out = engine.answer(q, engine.new_state(), lang_choice=lang)
        return lc.facts_block(out), out["table"]
    defs = lc.official_definitions()
    ctx = {"general": (defs, passages(PASSAGE_IDS["general"]), None),
           "conserve": (defs, passages(PASSAGE_IDS["conserve"]), None)}
    for key, (q, lang) in {"phagi_en": ("What is the annual recharge of Phagi?", "en"),
                           "phagi_hi": ("What is the annual recharge of Phagi?", "hi"),
                           "phagi_hing": ("What is the annual recharge of Phagi?", "hinglish"),
                           "todar_en": ("What is the annual recharge of Todaraisingh?", "en")}.items():
        facts, table = place(q, lang)
        ctx[key] = (facts, [], table)
    return ctx


def metrics(rows, key):
    tp = sum(1 for r in rows if r["label"] == B and r[key])
    fp = sum(1 for r in rows if r["label"] == G and r[key])
    fn = sum(1 for r in rows if r["label"] == B and not r[key])
    nb, ng = sum(1 for r in rows if r["label"] == B), sum(1 for r in rows if r["label"] == G)
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / nb if nb else None
    fpr = fp / ng if ng else None
    return tp, fp, fn, nb, ng, prec, rec, fpr


def fmt(x):
    return "-" if x is None else f"{100 * x:.0f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-embed", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--heldout", action="store_true", help="score the held-out set instead of the tuning set")
    a = ap.parse_args()
    cases = HELDOUT if a.heldout else CASES
    ctx = contexts()
    provider = None
    if a.self_check:
        import llm_provider as lp
        provider = lp.LLMProvider("ollama", model=os.environ.get("JALMITRA_LLM_MODEL", lp.DEFAULT_MODEL))
    rows = []
    for cid, lang, cname, topic, label, text in cases:
        facts, passages, table = ctx[cname]
        t0 = time.perf_counter()
        hits = sg.rule_check(text, facts, passages, table)
        row = {"id": cid, "lang": lang, "ctx": cname, "topic": topic, "label": label, "text": text,
               "rule_hits": "; ".join(sorted({h[0] for h in hits})), "L1": bool(hits)}
        if not a.no_embed:
            try:
                bad, sims = sg.support_check(text, facts, passages)
                row["min_best_sim"] = min(s[1] for s in sims) if sims else None
                row["min_overlap"] = min(s[2] for s in sims) if sims else None
                row["support_fail"] = bool(bad)
                row["sims"] = sims
            except Exception as e:
                row["support_fail"], row["error"] = True, f"{type(e).__name__}: {e}"
            row["L12"] = row["L1"] or row["support_fail"]
            if provider is not None:
                verdict = None if row["L12"] else sg.llm_self_check(text, facts, passages, provider)
                row["self_check"] = verdict
                row["L123"] = row["L12"] or verdict == "NOT_SUPPORTED"
        row["ms"] = round((time.perf_counter() - t0) * 1000, 1)
        rows.append(row)
        print(f"{cid:3d} {lang:8s} {label:4s} L1={row['L1']!s:5s} L12={row.get('L12', '-')!s:5s} "
              f"L123={row.get('L123', '-')!s:5s} {row['rule_hits']}", flush=True)

    date = dt.date.today().isoformat() + ("_heldout" if a.heldout else "")
    keys =["L1"] + (["L12"] if not a.no_embed else []) + (["L123"] if provider else [])
    names = {"L1": "rules only", "L12": "rules + sentence support", "L123": "rules + support + model self-check"}
    L = [f"# Semantic factuality gate: labelled evaluation ({date})", "",
         ("**HELD-OUT set: written after tuning, scored once, rules not changed afterwards.**" if a.heldout else
          "**TUNING set: the rules were developed on these cases, so these scores are optimistic.**"), "",
         f"{len(rows)} explanations: {sum(1 for r in rows if r['label'] == B)} BAD, "
         f"{sum(1 for r in rows if r['label'] == G)} GOOD. Positive class = BAD (should be rejected).",
         "Cases written for this evaluation plus 2 real model outputs (41 = the Phase 3 Hindi monsoon error, 71). "
         "Labels by the developer; hi / hinglish / mr / pa labels and wording still need native review.", "",
         "| gate | rejected BAD (TP) | rejected GOOD (FP) | missed BAD (FN) | precision | recall | false-rejection rate |",
         "|---|---|---|---|---|---|---|"]
    for k in keys:
        tp, fp, fn, nb, ng, p, r, f = metrics(rows, k)
        L.append(f"| {names[k]} | {tp}/{nb} | {fp}/{ng} | {fn} | {fmt(p)} | {fmt(r)} | {fmt(f)} |")
    L += ["", "## By language (last gate)", "", "| lang | n | precision | recall | false-rejection rate |",
          "|---|---|---|---|---|"]
    k = keys[-1]
    for lang in ["en", "hi", "hinglish", "mr", "pa"]:
        rs = [r for r in rows if r["lang"] == lang]
        if rs:
            _, _, _, _, _, p, rc, f = metrics(rs, k)
            L.append(f"| {lang} | {len(rs)} | {fmt(p)} | {fmt(rc)} | {fmt(f)} |")
    L += ["", "## By topic (last gate)", "", "| topic | n | recall (BAD caught) | false rejections |", "|---|---|---|---|"]
    for t in sorted({r["topic"] for r in rows}):
        rs = [r for r in rows if r["topic"] == t]
        _, fp, _, nb, ng, _, rc, _ = metrics(rs, k)
        L.append(f"| {t} | {len(rs)} | {fmt(rc) if nb else '-'} | {fp}/{ng} |")
    if a.sweep and not a.no_embed:
        L += ["", "## Support threshold sweep (rules + support)", "", "| sim threshold | precision | recall | FPR |",
              "|---|---|---|---|"]
        for t in [0.5, 0.55, 0.6, 0.65, 0.7, 0.75]:
            for r in rows:
                r["_s"] = r["L1"] or any(s[1] < t and s[2] < sg.OVERLAP_THRESHOLD for s in r.get("sims", []))
            _, _, _, _, _, p, rc, f = metrics(rows, "_s")
            L.append(f"| {t} | {fmt(p)} | {fmt(rc)} | {fmt(f)} |")
    L += ["", "## Every case", "", "| id | lang | topic | label | rule hits | min sim | min overlap | rejected by | text |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        by = "L1" if r["L1"] else ("L2" if r.get("support_fail") else ("L3" if r.get("L123") else "-"))
        L.append(f"| {r['id']} | {r['lang']} | {r['topic']} | {r['label']} | {r['rule_hits']} | "
                 f"{r.get('min_best_sim', '-')} | {r.get('min_overlap', '-')} | {by} | {r['text'][:110]} |")
    (HERE / f"semantic_summary_{date}.md").write_text("\n".join(L), encoding="utf-8")
    with open(HERE / f"semantic_results_{date}.csv", "w", newline="", encoding="utf-8") as f:
        cols = [c for c in rows[0] if c not in ("sims", "_s")]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("\n".join(L[:12]))


if __name__ == "__main__":
    main()
