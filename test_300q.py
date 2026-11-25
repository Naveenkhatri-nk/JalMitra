"""JalMitra - naveen's 300-question test (JalMitra_300_AI_Test_Questions.pdf, 25 Nov).

50 questions in each of English, Hindi, Hinglish, Rajasthani, Punjabi and Marathi:
  01-08 concepts, 09-18 official data lookup, 19-24 comparisons, 25-38 interpretation and advice,
  39-45 unclear location / missing data, 46-50 trick prompts.
Checks the kind of reply each question gets (general / data / ask_place / refuse ...) and the places used,
then runs every question through the full reply pipeline with a stand-in model (no network, no Ollama).
Run: python test_300q.py
"""
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

import engine                      # noqa: E402
import jalmitra_ai as ja           # noqa: E402
import llm_provider as lp          # noqa: E402

QUESTIONS = json.load(open(os.path.join(HERE, "tests_data", "questions_300.json"), encoding="utf-8"))
DB = os.path.join(HERE, "data", "groundwater.db")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


class Stand:
    """Stand-in model: a short refusal / explanation with no figures, and 'SUPPORTED' for the self-check."""
    provider, model = "fake", "fake-model"

    def is_enabled(self):
        return True

    def chat(self, messages, **kw):
        sys_msg = messages[0].get("content", "") if messages else ""
        text = "SUPPORTED" if "NOT_SUPPORTED" in sys_msg else \
            "I can only share official recorded values, so I cannot do that."
        return lp.LLMResult(text=text, ok=True, provider="fake", model="fake", latency_ms=1.0)


def main():
    t0 = time.perf_counter()
    before = sha(DB)
    fails, by_lang = [], {}
    for item in QUESTIONS:
        q, want = item["question"], set(item["kinds"])
        state = engine.new_state()
        rule = ja.rule_for(ja.normalize_states(q)[0], state)
        kind = ja.classify(rule, q)
        places = [p.get("name") for p in rule.get("places") or []]
        ok = kind in want and ("places" not in item or places == item["places"])
        lang = item["id"].split("-")[0]
        by_lang.setdefault(lang, [0, 0])[0 if ok else 1] += 1
        if not ok:
            fails.append(f"{item['id']}: got {kind} {places}, want {sorted(want)} {item.get('places', '')}  {q}")
    crashes = []
    for item in QUESTIONS:
        try:
            ja.respond(item["question"], engine.new_state(), provider=Stand(), retriever=lambda *a, **k: [])
        except Exception as e:                          # the pipeline must never crash on any question
            crashes.append(f"{item['id']}: {e!r}")
    for lang, (good, bad) in by_lang.items():
        print(f"  {lang}  {good}/{good + bad}")
    for f in fails + crashes:
        print("FAILED ", f)
    same = sha(DB) == before
    print(f"Database sha256 unchanged: {same}")
    total = len(QUESTIONS) * 2 + 1
    failed = len(fails) + len(crashes) + (0 if same else 1)
    print(f"\nJalMitra 300-question tests: {total - failed} passed, {failed} failed of {total} "
          f"({time.perf_counter() - t0:.1f} s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
