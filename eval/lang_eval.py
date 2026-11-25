"""
eval/lang_eval.py - six-language evaluation (JalMitra 4.0 Phase 5).

Writes one dataset per language, eval/lang_<code>.tsv (the 20 questions of eval/questions_6lang.tsv for that
language + the expected AI policy), then measures for each language:
  * rule engine: intent, language label, places, follow-ups (eval/model_selection.py scoring, read-only)
  * Coming Soon reply language for a crop question (ui_chat_v4.SOON_TEXT exists for the language)
  * AI policy: en / hinglish = Experimental (explanation allowed), hi = Disabled pending factuality validation,
    raj / pa / mr = Disabled pending native review -> llm_compose returns "language_off" (fake provider, no model)
Native-speaker review of hi / raj / pa / mr wording is still pending: nothing here is a native-level claim.

Usage: python eval/lang_eval.py  -> eval/lang_<code>.tsv + eval/lang_eval_<date>.md
"""

import csv
import datetime as dt
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
for _k in [k for k in os.environ if k.startswith("JALMITRA_")]:
    del os.environ[_k]
os.environ["JALMITRA_LLM_CACHE"] = "0"

import engine  # noqa: E402
import llm_compose  # noqa: E402
import llm_provider as lp  # noqa: E402
import model_selection as ms  # noqa: E402
import ui_chat_v4  # noqa: E402

LANGS = ["en", "hi", "hinglish", "raj", "pa", "mr"]
POLICY = {"en": "Experimental", "hinglish": "Experimental", "hi": "Disabled (factuality validation pending)",
          "raj": "Disabled (native review pending)", "pa": "Disabled (native review pending)",
          "mr": "Disabled (native review pending)"}


class Fake:
    def is_enabled(self):
        return True

    def chat(self, messages, **kw):
        return lp.LLMResult(text="This block is Over-exploited.", ok=True, provider="fake", model="fake")


def main():
    rows = list(csv.DictReader(open(HERE / "questions_6lang.tsv", encoding="utf-8"), delimiter="\t"))
    for lang in LANGS:
        rs = [dict(r, ai_policy=POLICY[lang]) for r in rows if r["lang"] == lang]
        with open(HERE / f"lang_{lang}.tsv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rs[0]), delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rs)
    rule = ms.run_rules(rows)
    L = [f"# Six-language evaluation ({dt.date.today().isoformat()})", "",
         "Datasets: eval/lang_<code>.tsv (20 questions each). Rule-engine results are read-only runs of engine.answer. "
         "**hi / raj / pa / mr wording has not been reviewed by native speakers; no native-level accuracy is claimed.**",
         "", "| lang | intent | language label | places | follow-ups | Coming Soon reply in language | AI policy | "
         "AI policy enforced |", "|---|---|---|---|---|---|---|---|"]
    q = "What is the annual recharge of Phagi?"
    for lang in LANGS:
        rs = [r for r in rows if r["lang"] == lang]
        sc = [ms.score_rules(r, rule[r["id"]]) for r in rs]
        rate = lambda k: ms.fmt_rate(ms.rate([s.get(k) for s in sc]))   # noqa: E731
        os.environ["JALMITRA_SEMANTIC_SUPPORT"] = "0"
        os.environ["JALMITRA_SELF_CHECK"] = "0"
        ref = engine.answer(q, engine.new_state(), lang_choice=lang)
        info = llm_compose.enhance(q, ref, provider=Fake())["llm"]
        for k in ("JALMITRA_SEMANTIC_SUPPORT", "JALMITRA_SELF_CHECK"):
            os.environ.pop(k)
        expected_off = lang not in ("en", "hinglish")
        enforced = (info["status"] == "language_off") == expected_off
        L.append(f"| {lang} | {rate('intent_ok')} | {rate('lang_ok')} | {rate('place_ok')} | {rate('followup_ok')} | "
                 f"{'yes' if lang in ui_chat_v4.SOON_TEXT else 'no'} | {POLICY[lang]} | "
                 f"{'yes' if enforced else 'NO'} ({info['status']}) |")
    allr = [ms.score_rules(r, rule[r["id"]]) for r in rows]
    L.append(f"| all | {ms.fmt_rate(ms.rate([s['intent_ok'] for s in allr]))} | "
             f"{ms.fmt_rate(ms.rate([s['lang_ok'] for s in allr]))} | {ms.fmt_rate(ms.rate([s['place_ok'] for s in allr]))} "
             f"| {ms.fmt_rate(ms.rate([s.get('followup_ok') for s in allr]))} | | | |")
    L += ["", "Rule misses by language are listed in eval/comparison_2026-11-23.md (unchanged rule engine since Phase 2)."]
    out = HERE / f"lang_eval_{dt.date.today().isoformat()}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
