"""
test_v4_semantic.py - tests for semantic_gate.py and its use in llm_compose (JalMitra 4.0 Phase 4).

No network: layer 2 uses a fake bag-of-words embedder here (the real bge-m3 layer is measured in
eval/semantic_factuality.py). Covers depth direction (monsoon / pre- vs post-monsoon), recharge vs
extraction, depletion, stage formula, category limits, contradictions with database figures, unsupported
causes, wrong remedies, clause handling (the real Phase 3 Hindi error), fail-closed support check, the
reject-only self-check, and the gate inside llm_compose.enhance.

Run: python test_v4_semantic.py   (exit code 0 when all pass)
"""

import hashlib
import math
import os
import re
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
for _k in [k for k in os.environ if k.startswith("JALMITRA_")]:
    del os.environ[_k]
os.environ["JALMITRA_LLM_CACHE"] = "0"          # every test needs a fresh outcome (the cache has its own tests)

import semantic_gate as sg  # noqa: E402

TESTS = []
PHAGI_TABLE = [{"assessment_unit": "PHAGI", "category": "Over-exploited", "stage_pct": 117.0,
                "annual_recharge_ham": 5949.0, "total_extraction_ham": 6265.0}]
PASSAGE = ("Groundwater table is usually deeper during pre- monsoon and before the onset of the monsoon and it "
           "becomes shallow during monsoon. Rainfall is the main source of ground water recharge.")


def test(group):
    def deco(fn):
        TESTS.append((group, fn))
        return fn
    return deco


def hits(text, facts="", passages=(), table=None):
    return {h[0] for h in sg.rule_check(text, facts, passages, table)}


def fake_embedder(texts):
    """Hashed bag of words (64 dims): similar wording -> high cosine."""
    out = []
    for t in texts:
        v = [0.0] * 64
        for w in re.findall(r"[a-zऀ-੿]{3,}", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1
        out.append(v)
    return out


# ------------------------------------------------------------------ direction
@test("direction")
def monsoon_wrong_direction_all_languages():
    for t in ["During the monsoon the water table becomes deeper.", "Depth to water increases during the monsoon.",
              "बारिश के मौसम में जल स्तर नीचे चला जाता है।", "Monsoon mein water level neeche chala jata hai.",
              "पावसाळ्यात भूजल पातळी खोल जाते.", "ਮਾਨਸੂਨ ਵਿੱਚ ਪਾਣੀ ਦਾ ਪੱਧਰ ਹੇਠਾਂ ਜਾਂਦਾ ਹੈ।"]:
        assert "monsoon_direction" in hits(t), t


@test("direction")
def monsoon_correct_statements_pass():
    for t in ["During the monsoon, recharge from rainfall raises the groundwater level.",
              "The water table is usually deeper before the monsoon and becomes shallower during the monsoon.",
              "मानसून से पहले भूजल तल आमतौर पर गहरा होता है।", "Monsoon se pehle water level aam taur par gehra hota hai.",
              "ਮਾਨਸੂਨ ਵਿੱਚ ਮੀਂਹ ਨਾਲ ਪਾਣੀ ਦਾ ਪੱਧਰ ਉੱਪਰ ਆਉਂਦਾ ਹੈ।"]:
        assert not hits(t, PASSAGE, [PASSAGE]), (t, hits(t))


@test("direction")
def real_phase3_hindi_error_caught():
    t = "बरसात के मौसम में भूजल तल गहरा होता है और बरसात के बाद इसका स्तर घटता है।"
    assert "monsoon_direction" in hits(t)


@test("direction")
def recharge_and_extraction_direction():
    assert "recharge_direction" in hits("Recharge lowers the water level in the aquifer.")
    assert "extraction_direction" in hits("Pumping more groundwater raises the water level.")
    assert "extraction_direction" in hits("दोहन ज़्यादा होने से भूजल स्तर बढ़ता है।")
    assert not hits("When extraction is more than recharge, groundwater levels fall over time.")


@test("depletion")
def depletion_direction():
    assert "depletion_direction" in hits("If extraction exceeds recharge the groundwater situation improves.")
    assert "depletion_direction" in hits("Because extraction is more than recharge, the water level keeps rising.")
    assert not hits("When extraction exceeds recharge, the groundwater level drops and may go beyond safe limits.")


@test("depletion")
def wrong_remedies():
    assert "wrong_remedy" in hits("Building more borewells is the best way to reduce groundwater depletion.")
    assert "wrong_remedy" in hits("Depletion can be reduced by pumping more water during the monsoon.")
    assert not hits("Rainwater harvesting and artificial recharge can help reduce groundwater depletion.")
    assert "rain_irrelevant" in hits("Monsoon rains do not matter for groundwater in India.")


# ------------------------------------------------------------------ definitions and figures
@test("definitions")
def stage_formula():
    assert "stage_formula" in hits("The stage of extraction is recharge divided by extraction, in percent.")
    assert not hits("Stage of extraction = total groundwater extraction divided by the annual extractable "
                    "groundwater resource.")


@test("definitions")
def category_limits():
    bad = ["Safe means the stage of extraction is more than 100%.", "Over-exploited means 70% to 90%.",
           "अतिदोहित का मतलब है कि दोहन का स्तर 70% से 90% के बीच है।", "Critical ka matlab hai stage 50% se kam."]
    for t in bad:
        assert "category_threshold" in hits(t), t
    good = ["Semi-critical means more than 70% and up to 90%.", "Critical means more than 90% and up to 100%.",
            "PHAGI is Over-exploited with a stage of 117%.", "सुरक्षित श्रेणी का मतलब है दोहन का स्तर 70% तक।"]
    for t in good:
        assert "category_threshold" not in hits(t), t


@test("definitions")
def contradiction_with_database_figures():
    assert "contradicts_figures" in hits("Annual recharge is more than the extraction, so the block is fine.",
                                         table=PHAGI_TABLE)
    assert "contradicts_figures" in hits("Phagi mein recharge extraction se zyada hai.", table=PHAGI_TABLE)
    assert not hits("Total extraction of 6265 ham is higher than the annual recharge of 5949 ham.",
                    table=PHAGI_TABLE)


@test("causes")
def unsupported_causes():
    assert "unsupported_cause" in hits("Groundwater is falling mainly because of climate change.", "facts", [PASSAGE])
    assert "unsupported_cause" in hits("भूजल घटने का मुख्य कारण जलवायु परिवर्तन है।", "facts", [PASSAGE])
    assert "unsupported_cause" not in hits("Groundwater falls because of climate change.", "climate change", [])
    assert not hits("Pollution is a concern.", "", [])          # no causal claim, no rule


# ------------------------------------------------------------------ layers 2 and 3
@test("support")
def support_check_with_embedder():
    facts = "PHAGI is Over-exploited. Its recorded stage of extraction is 117%."
    bad, sims = sg.support_check("PHAGI is Over-exploited with stage of extraction 117%.", facts, [],
                                 embedder=fake_embedder)
    assert not bad, sims
    bad, _ = sg.support_check("Farmers should sell their tractors and move to cities.", facts, [], embedder=fake_embedder)
    assert bad


@test("support")
def support_fails_closed():
    def broken(texts):
        raise ConnectionError("no embedder")
    r = sg.check("PHAGI is Over-exploited.", "PHAGI is Over-exploited.", [], embedder=broken)
    assert not r.ok and "could not run" in r.reasons[0]


@test("support")
def self_check_can_only_reject():
    facts = "PHAGI is Over-exploited."
    ok = sg.check("PHAGI is Over-exploited.", facts, [], embedder=fake_embedder, self_checker=lambda *a: "SUPPORTED")
    assert ok.ok
    no = sg.check("PHAGI is Over-exploited.", facts, [], embedder=fake_embedder,
                  self_checker=lambda *a: "NOT_SUPPORTED")
    assert not no.ok
    unsure = sg.check("PHAGI is Over-exploited.", facts, [], embedder=fake_embedder, self_checker=lambda *a: None)
    assert not unsure.ok                     # Phase 5: no clear verdict -> fail closed (still never approves alone)
    # a rule hit is never overturned by a SUPPORTED self-check
    bad = sg.check("During the monsoon the water table becomes deeper.", PASSAGE, [PASSAGE], embedder=fake_embedder,
                   self_checker=lambda *a: "SUPPORTED")
    assert not bad.ok


# ------------------------------------------------------------------ inside the pipeline
@test("pipeline")
def gate_rejects_inside_enhance():
    import engine
    import llm_compose
    import llm_provider as lp

    class Fake:
        def __init__(self, text):
            self.text = text

        def is_enabled(self):
            return True

        def chat(self, messages, **kw):
            return lp.LLMResult(text=self.text, ok=True, provider="fake", model="fake")
    # layers 1-2 only here (the self-check, on by default since Phase 5 and fail-closed, has its own test)
    os.environ.update(JALMITRA_LLM_LANGS="en,hi,hinglish", JALMITRA_SEMANTIC_SUPPORT="0", JALMITRA_SELF_CHECK="0")
    try:
        q = "What is the annual recharge of Phagi?"
        ref = engine.answer(q, engine.new_state())
        out = llm_compose.enhance(q, ref, provider=Fake("Because extraction is more than recharge, PHAGI's water "
                                                       "level keeps rising."))
        assert out["llm"]["status"] == "rejected" and "semantic" in out["llm"]["reason"], out["llm"]
        assert out["text"] == ref["text"] and out["table"] == ref["table"]
        good = llm_compose.enhance(q, ref, provider=Fake("PHAGI is Over-exploited; its stage of extraction is 117%."))
        assert good["llm"]["status"] == "verified", good["llm"]
        # with the support layer on and a fake embedder
        os.environ["JALMITRA_SEMANTIC_SUPPORT"] = "1"
        llm_compose.SEMANTIC_EMBEDDER = fake_embedder
        good = llm_compose.enhance(q, ref, provider=Fake("PHAGI is Over-exploited; its stage of extraction is 117%."))
        assert good["llm"]["status"] == "verified", good["llm"]
        off = llm_compose.enhance(q, ref, provider=Fake("Farmers should sell tractors and migrate to the cities."))
        assert off["llm"]["status"] == "rejected", off["llm"]
    finally:
        llm_compose.SEMANTIC_EMBEDDER = None
        for k in ("JALMITRA_LLM_LANGS", "JALMITRA_SEMANTIC_SUPPORT", "JALMITRA_SELF_CHECK"):
            os.environ.pop(k, None)


@test("pipeline")
def self_check_on_by_default_and_reject_only():
    import engine
    import llm_compose
    import llm_provider as lp
    calls = []

    class Fake:
        def is_enabled(self):
            return True

        def chat(self, messages, **kw):
            calls.append(messages[0]["content"][:40])
            if "You check a short groundwater explanation" in messages[0]["content"]:
                return lp.LLMResult(text="NOT_SUPPORTED", ok=True, provider="fake", model="fake")
            return lp.LLMResult(text="PHAGI is Over-exploited; its stage of extraction is 117%.", ok=True,
                                provider="fake", model="fake")
    os.environ.update(JALMITRA_SEMANTIC_SUPPORT="0")
    try:
        q = "What is the annual recharge of Phagi?"
        ref = engine.answer(q, engine.new_state())
        out = llm_compose.enhance(q, ref, provider=Fake())
        assert len(calls) == 2, calls                                   # explanation + self-check
        assert out["llm"]["status"] == "rejected" and "self-check" in out["llm"]["reason"], out["llm"]
        assert out["text"] == ref["text"]
    finally:
        os.environ.pop("JALMITRA_SEMANTIC_SUPPORT", None)


@test("pipeline")
def hindi_off_by_default():
    import llm_compose
    assert "hi" not in llm_compose.DEFAULT_LANGS.split(",")
    assert not {"raj", "pa", "mr"} & set(llm_compose.DEFAULT_LANGS.split(","))


def main():
    t0 = time.perf_counter()
    passed, failed, groups = 0, [], {}
    for group, fn in TESTS:
        try:
            fn()
            ok = True
            print(f"PASSED  {group:12s} {fn.__name__}")
        except Exception as e:
            ok = False
            failed.append(fn.__name__)
            print(f"FAILED  {group:12s} {fn.__name__}: {type(e).__name__}: {str(e)[:300]}")
        passed += ok
        g = groups.setdefault(group, [0, 0])
        g[0] += ok
        g[1] += 1
    print()
    for g, (a, b) in groups.items():
        print(f"  {g:12s} {a}/{b}")
    print(f"\nJalMitra 4.0 semantic tests: {passed} passed, {len(failed)} failed of {len(TESTS)} "
          f"({time.perf_counter() - t0:.1f} s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
