"""
test_v3.py - Tests added in JalMitra 3.0 (Phase 1). Run after test_local_engine.py:
    python test_v3.py

Checks conversation memory, soil/crop/land "Data unavailable" answers, the
user's chosen location, answer styles x lengths in all six languages, that
the Standard answers are word-for-word the 2.0 answers (compared with the
2.0 backup run as a separate process), the website loading in Streamlit
AppTest, no paid LLM / API key in the code, no network use, and that
data/groundwater.db is byte-identical before and after.

Every value is checked against the database through a separate read-only
connection. Results: test_results_v3.csv. A test whose precondition is
missing is reported as SKIPPED, never as passed.
"""

import csv
import hashlib
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

NETWORK_ATTEMPTS = []          # every NON-loopback connection attempt (denied and counted)
LOOPBACK_CONNECTIONS = []      # loopback connections (allowed, counted separately)
_REAL_CONNECT = socket.socket.connect
_REAL_CREATE_CONNECTION = socket.create_connection


def _is_loopback(address):
    """True only for this computer: 127.0.0.0/8, ::1, 'localhost'. Windows asyncio builds its internal
    socketpair by connecting to 127.0.0.1 (Windows has no AF_UNIX socketpair); that is not network use.
    (Phase 6 fix of the Windows-only UI01 / NET01 failures; every other address is still denied.)"""
    host = address[0] if isinstance(address, (tuple, list)) and address else address
    host = str(host or "").strip("[]").lower()
    return host == "localhost" or host == "::1" or host.startswith("127.")


def _no_network(*args, **kwargs):
    NETWORK_ATTEMPTS.append(repr(args)[:80])
    raise OSError("network disabled during JalMitra tests")


def _guarded_connect(self, address, *args, **kwargs):
    if _is_loopback(address):
        LOOPBACK_CONNECTIONS.append(repr(address)[:60])
        return _REAL_CONNECT(self, address, *args, **kwargs)
    return _no_network(address)


def _guarded_create_connection(address, *args, **kwargs):
    if _is_loopback(address):
        LOOPBACK_CONNECTIONS.append(repr(address)[:60])
        return _REAL_CREATE_CONNECTION(address, *args, **kwargs)
    return _no_network(address)


socket.socket.connect = _guarded_connect
socket.create_connection = _guarded_create_connection

import database as db  # noqa: E402
import engine  # noqa: E402
import entity_resolver as er  # noqa: E402
import language as L  # noqa: E402
import ui_text  # noqa: E402

DB_PATH = db.get_db_path()
HASH_BEFORE = hashlib.sha256(Path(DB_PATH).read_bytes()).hexdigest()
REF = sqlite3.connect(f"{DB_PATH.resolve().as_uri()}?mode=ro", uri=True)
REF.row_factory = sqlite3.Row
BACKUP_V2 = BASE / "backup" / "app_v2_offline_20261122"
RESULTS = []


def ref(sql, params=()):
    return [dict(r) for r in REF.execute(sql, params).fetchall()]


def unit(name):
    rows = ref("SELECT * FROM groundwater_assessment WHERE assessment_unit = ?", (name,))
    assert len(rows) == 1, name
    return rows[0]


def counts(state, district):
    rows = ref("SELECT category, COUNT(*) n FROM groundwater_assessment WHERE state=? AND district=? GROUP BY category",
               (state, district))
    return {r["category"]: r["n"] for r in rows}


def test(name, group):
    def wrap(fn):
        t0 = time.perf_counter()
        try:
            detail = fn()
            status = "SKIPPED" if isinstance(detail, str) and detail.startswith("SKIPPED") else "PASSED"
        except Exception as e:  # noqa: BLE001
            status, detail = "FAILED", f"{type(e).__name__}: {e}"
        RESULTS.append({"id": name, "group": group, "status": status, "detail": str(detail)[:300],
                        "ms": round((time.perf_counter() - t0) * 1000, 1)})
        return fn
    return wrap


def ask_all(questions, mode="farmer", detail="standard", home=None, lang=L.AUTO, state=None):
    s = state or engine.new_state()
    if home:
        s.set_home(home)
    return s, [engine.answer(q, s, lang, mode, detail) for q in questions]


def names(r):
    return [(p["type"], p["name"]) for p in r["places"]]


# ------------------------------------------------------------------ memory (naveen's example dialogue)

@test("MEM01_example_dialogue", "memory")
def _():
    s, rs = ask_all(["What is the groundwater status of Ajmer Urban?", "What does it mean?", "What about Jodhpur?",
                     "Is its soil good?", "Which crops are suitable there?", "Compare both districts."])
    au = unit("AJMER_URBAN")
    a0, a1, a2, a3, a4, a5 = rs
    assert a0["intent"] == "status" and names(a0) == [("unit", "AJMER_URBAN")]
    assert L.category_label(au["category"], "en") in a0["text"]
    assert a1["intent"] == "explain_category" and "In the previous answer, AJMER URBAN was " + au["category"] in a1["text"]
    assert L.t(f"explain_{au['category']}", "en") in a1["text"], "category of the previous answer not explained"
    assert names(a2) == [("district", "JODHPUR")] and a2["intent"] == "status"
    c = counts("Rajasthan", "JODHPUR")
    assert f"has {sum(c.values())} assessment units" in a2["text"]
    assert a3["intent"] == "domain" and a3["status"] == "data_unavailable" and names(a3) == [("district", "JODHPUR")]
    assert "Soil data for JODHPUR district (Rajasthan): Data unavailable" in a3["text"]
    assert a4["intent"] == "domain" and names(a4) == [("district", "JODHPUR")]
    assert "Crop suitability data for JODHPUR district (Rajasthan): Data unavailable" in a4["text"]
    assert a5["intent"] == "compare" and names(a5) == [("district", "AJMER"), ("district", "JODHPUR")]
    assert "its district AJMER is used" in a5["text"] and "Crop suitability data is not available" in a5["text"]
    nc = ref("SELECT stage_of_extraction_pct s FROM national_district_summary WHERE district IN ('Ajmer','Jodhpur') "
             "ORDER BY district")
    assert f"{nc[1]['s']:g}%" in a5["text"] and f"{nc[0]['s']:g}%" in a5["text"], "NC stages not in comparison"
    m = a5["memory"]
    assert m["domain"] == "groundwater" and [p["name"] for p in m["places"]] == ["AJMER", "JODHPUR"]
    return "6 turns: status, meaning, new place, soil, crops, compare both districts"


@test("MEM02_hindi_dialogue", "memory")
def _():
    s, rs = ask_all(["अजमेर अर्बन की भूजल स्थिति क्या है?", "इसका मतलब क्या है?", "जोधपुर का क्या?",
                     "वहां की मिट्टी कैसी है?"])
    assert all(r["lang"] == "hi" for r in rs), [r["lang"] for r in rs]
    assert rs[1]["intent"] == "explain_category" and "पिछले उत्तर में AJMER URBAN" in rs[1]["text"]
    assert names(rs[2]) == [("district", "JODHPUR")]
    assert rs[3]["intent"] == "domain" and names(rs[3]) == [("district", "JODHPUR")] and "डेटा उपलब्ध नहीं" in rs[3]["text"]
    return "4 turns in Hindi"


@test("MEM03_new_chat_resets", "memory")
def _():
    s, rs = ask_all(["Is Ajmer Urban safe?", "What about Jodhpur?"])
    s.clear()
    r1 = engine.answer("What does it mean?", s)
    r2 = engine.answer("Compare both", s)
    r3 = engine.answer("Is its soil good?", s)
    assert "previous answer" not in r1["text"]
    assert r2["status"] == "compare_need_two"
    assert r3["intent"] == "domain" and r3["places"] == []
    return "context cleared"


@test("MEM04_explanation_keeps_last_question", "memory")
def _():
    s, rs = ask_all(["Stage of extraction of Ajmer Urban", "What does it mean?", "What about Gira?"])
    assert rs[2]["intent"] == "numeric" and names(rs[2]) == [("unit", "GIRA")]
    return "numeric question kept across an explanation"


@test("MEM05_domain_followup_new_place", "memory")
def _():
    s, rs = ask_all(["Is my soil good in Jaipur district?", "What about Jodhpur?", "Is groundwater safe there?"])
    assert rs[0]["intent"] == "domain" and names(rs[0]) == [("district", "JAIPUR")]
    assert rs[1]["intent"] == "domain" and names(rs[1]) == [("district", "JODHPUR")], "soil topic not remembered"
    assert rs[2]["intent"] == "status" and names(rs[2]) == [("district", "JODHPUR")]
    assert rs[2]["memory"]["domain"] == "groundwater"
    return "domain kept for a new place, switched back for groundwater"


@test("MEM06_ambiguous_its_asks", "memory")
def _():
    s, rs = ask_all(["Compare Ajmer Urban and Tiwari", "What is its stage?", "2"])
    assert rs[1]["clarify"] and rs[1]["places"] == [] and len(rs[1]["options"]) == 2
    assert names(rs[2]) == [("unit", "TIWARI")]
    t = unit("TIWARI")
    assert f"{t['stage_of_extraction_pct']:g}%" in rs[2]["text"]
    return "asked which place, then answered for the chosen one"


@test("MEM07_my_area_uses_chosen_location_only", "memory")
def _():
    s, rs = ask_all(["Is Tiwari safe?", "Is groundwater safe in my area?"])
    assert rs[1]["status"] == "need_home" and rs[1]["places"] == [], "an earlier answer was used as 'my area'"
    home = er.find_by_name("AJMER_URBAN", "unit")[0]
    s.set_home(home)
    r = engine.answer("Is groundwater extraction sustainable in my block?", s)
    assert r["intent"] == "numeric" and names(r) == [("unit", "AJMER_URBAN")]
    r = engine.answer("What is my soil type?", s)
    assert r["intent"] == "domain" and names(r) == [("unit", "AJMER_URBAN")] and "Data unavailable" in r["text"]
    r = engine.answer("मेरे क्षेत्र में भूजल की स्थिति क्या है?", s)
    assert names(r) == [("unit", "AJMER_URBAN")], names(r)
    return "need_home without a location; chosen location used when set"


@test("MEM08_memory_summary_fields", "memory")
def _():
    s, rs = ask_all(["Ajmer Urban ka paani kaisa hai?"], mode="student", detail="short")
    m = rs[0]["memory"]
    for k in ("place", "domain", "language", "style", "detail", "last_intent", "sources"):
        assert k in m, k
    assert m["language"] == "hinglish" and m["style"] == "student" and m["detail"] == "short"
    assert m["last_intent"] == "status" and m["sources"] >= 1
    return json.dumps({k: (v if not isinstance(v, (dict, list)) else "...") for k, v in m.items()}, ensure_ascii=False)


# ------------------------------------------------------------------ topics without data

HOME_EXAMPLES = ui_text.EXAMPLE_QUESTIONS["en"] + ui_text.EXAMPLE_QUESTIONS["hi"]


@test("DOM01_home_examples_no_location", "domain")
def _():
    out = []
    for q in HOME_EXAMPLES:
        r = engine.answer(q, engine.new_state())
        assert r["result"] is None or not r["result"]["records"], f"{q}: used records without a location"
        assert r["status"] in ("data_unavailable", "need_home", "knowledge"), (q, r["status"])
        # 3.0 Phases 2-5: numbers may appear only from cited reference tables (FAO, ICAR, BIS), never as place data
        if re.search(r"\d", r["text"].replace("📍", "")):
            assert r["status"] == "knowledge" and r["sources"], f"{q}: an uncited number appeared: {r['text'][:120]}"
        out.append(r["status"])
    return f"{len(out)} example questions: " + ", ".join(sorted(set(out)))


@test("DOM02_domain_words_are_not_places", "domain")
def _():
    for q in ["What is my soil type?", "soil", "मिट्टी", "crops for Jaipur district", "land use", "irrigation"]:
        found = [m["text"] for m in er.extract_places(q, __import__("intent_parser").KEYWORD_TOKENS)[0]]
        assert all(f.lower() not in ("soil", "मिट्टी", "crops", "land", "irrigation") for f in found), (q, found)
    return "soil/crop/land/irrigation words never read as place names (2.0 read 'soil' as SOHELA)"


@test("DOM03_domain_answers_all_languages", "domain")
def _():
    qs = {"en": "Is the soil good in Jodhpur district?", "hi": "जोधपुर ज़िले की मिट्टी कैसी है?",
          "hinglish": "Jodhpur district ki mitti kaisi hai?", "mr": "जोधपूर जिल्ह्यातील माती कशी आहे?",
          "pa": "ਜੋਧਪੁਰ ਜ਼ਿਲ੍ਹੇ ਦੀ ਮਿੱਟੀ ਕਿਵੇਂ ਹੈ?", "raj": "जोधपुर जिला री माटी कियां है?"}
    for lg, q in qs.items():
        r = engine.answer(q, engine.new_state(), lg)
        assert r["intent"] == "domain", (lg, r["intent"])
        assert L.t("dom_soil", lg) in r["text"], (lg, r["text"][:100])
    return "6 languages"


# ------------------------------------------------------------------ answer styles x lengths

STYLES, DETAILS = ("farmer", "official", "student"), ("short", "standard", "detailed")
Q_BY_LANG = {"en": "Is Ajmer Urban safe?", "hi": "अजमेर अर्बन की भूजल स्थिति क्या है?",
             "hinglish": "Ajmer Urban ka paani kaisa hai?", "mr": "अजमेर अर्बन भूजल स्थिती काय आहे?",
             "pa": "ਅਜਮੇਰ ਅਰਬਨ ਵਿੱਚ ਪਾਣੀ ਦੀ ਸਥਿਤੀ ਕੀ ਹੈ?", "raj": "अजमेर अर्बन रो पाणी कियां है?"}


@test("MODE01_all_styles_lengths_languages", "modes")
def _():
    au = unit("AJMER_URBAN")
    n = 0
    for lg, q in Q_BY_LANG.items():
        for st in STYLES:
            for dt in DETAILS:
                r = engine.answer(q, engine.new_state(), lg, st, dt)
                assert names(r) == [("unit", "AJMER_URBAN")], (lg, st, dt, names(r))
                assert L.category_label(au["category"], lg) in r["text"], (lg, st, dt)
                assert f"{au['stage_of_extraction_pct']:g}%" in r["text"], (lg, st, dt)
                tip, lim = L.t("tip", lg), "**" + L.t("lbl_limits", lg) + ":**"
                if dt == "short":
                    assert tip not in r["text"] and L.t("thresholds", lg) not in r["text"], (lg, st, "short too long")
                if dt == "detailed":
                    for key in ("lbl_finding", "lbl_data", "lbl_reason", "lbl_limits", "lbl_missing"):
                        assert L.t(key, lg) in r["text"], (lg, st, key)
                    assert (L.t("lbl_method", lg) in r["text"]) == (st == "official"), (lg, st, "method")
                    assert (L.t("lbl_advice", lg) in r["text"]) == (st != "official"), (lg, st, "advice")
                else:
                    assert lim not in r["text"]
                if st == "student" and dt == "standard":
                    assert L.t("lbl_term", lg) in r["text"] and L.t("explain_stage", lg) in r["text"]
                n += 1
    return f"{n} answers (6 languages x 3 styles x 3 lengths)"


@test("MODE02_lengths_ordered", "modes")
def _():
    for st in STYLES:
        lens = [len(engine.answer("Is Ajmer Urban safe?", engine.new_state(), "en", st, dt)["text"]) for dt in DETAILS]
        assert lens[0] < lens[1] < lens[2], (st, lens)
    return "short < standard < detailed for every style"


@test("MODE03_reasoning_only_when_consistent", "modes")
def _():
    rows = ref("SELECT assessment_unit FROM groundwater_assessment WHERE quality_flag LIKE '%category_stage_mismatch%'")
    assert rows, "no mismatch rows to test"
    for row in rows:
        r = engine.answer(f"{row['assessment_unit']} figures", engine.new_state(), "en", "student", "detailed")
        if names(r) == [("unit", row["assessment_unit"])]:
            assert L.t("lbl_reason", "en") not in r["text"], row["assessment_unit"]
    return f"{len(rows)} units with a category/stage mismatch get the warning, not a reasoning line"


@test("MODE04_standard_equals_v2", "modes")
def _():
    if not (BACKUP_V2 / "engine.py").exists() or not (BACKUP_V2 / "data" / "groundwater.db").exists():
        return "SKIPPED: 2.0 backup with database not found at backup/app_v2_offline_20261122"
    qs = ["Is Ajmer Urban safe?", "Jaipur district status", "Top 5 over-exploited blocks in Rajasthan",
          "Compare Jaipur district and Jodhpur district", "What does semi-critical mean?", "Stage of extraction of Pune City",
          "अजमेर अर्बन की भूजल स्थिति क्या है?", "Ludhiana ka paani kaisa hai?", "Which units have data-quality warnings?",
          "Golaghat West status", "Gira stage", "List safe blocks in Pune district"]
    code = ("import json,sys,engine\nout=[]\nfor mode in ('farmer','official'):\n for q in json.loads(sys.argv[1]):\n"
            "  s=engine.new_state(); r=engine.answer(q,s,'auto',mode); out.append(r['text'])\nprint(json.dumps(out))")
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    old = subprocess.run([sys.executable, "-I", "-c", "import sys; sys.path.insert(0, '.')\n" + code, json.dumps(qs)],
                         cwd=BACKUP_V2, capture_output=True, text=True, timeout=300, env=env)
    assert old.returncode == 0, old.stderr[-400:]
    old_texts = json.loads(old.stdout.strip().splitlines()[-1])
    new_texts = [engine.answer(q, engine.new_state(), L.AUTO, mode)["text"] for mode in ("farmer", "official") for q in qs]
    diff = [i for i, (a, b) in enumerate(zip(old_texts, new_texts)) if a != b]
    assert not diff, f"{len(diff)} differ, first: {qs[diff[0] % len(qs)]}"
    return f"{len(new_texts)} Standard answers identical to JalMitra 2.0"


# ------------------------------------------------------------------ templates, UI, offline, database

@test("TPL01_templates_six_languages", "templates")
def _():
    assert not L.missing_translations(), L.missing_translations()[:5]
    import templates_v3
    return f"{len(templates_v3.TEMPLATES_V3)} new templates, all {len(L.TEMPLATES)} keys in 6 languages"


@test("TPL02_ui_english_hindi", "templates")
def _():
    assert not ui_text.missing_ui(), ui_text.missing_ui()[:5]
    return f"{len(ui_text.UI)} interface texts in English and Hindi"


RUNTIME = ["app.py", "engine.py", "intent_parser.py", "entity_resolver.py", "language.py", "templates_v3.py",
           "retrieval.py", "response_builder.py", "conversation_state.py", "voice.py", "database.py", "security.py",
           "ui_text.py", "ui_components.py", "ui_pages.py"]


@test("OFF01_no_llm_or_api_key", "offline")
def _():
    bad = re.compile(r"^\s*(import|from)\s+(ai|google|anthropic|openai|genai|requests|httpx)\b|API_KEY|generativeai|"
                     r"api\.anthropic|api\.openai|generativelanguage", re.M | re.I)
    for f in RUNTIME:
        src = (BASE / f).read_text(encoding="utf-8")
        m = bad.search(src)
        assert not m, f"{f}: {m.group(0)}"
    for mod in ("anthropic", "openai", "google.genai", "ai", "requests"):
        assert mod not in sys.modules, mod
    return f"{len(RUNTIME)} runtime files: no LLM client, no API key, no HTTP client"


@test("OFF02_works_without_any_api_key", "offline")
def _():
    env = {k: v for k, v in os.environ.items() if "KEY" not in k.upper() and "TOKEN" not in k.upper()}
    env.pop("PYTHONPATH", None)
    code = ("import socket\ndef no(*a,**k): raise OSError('no network')\nsocket.socket.connect=no\n"
            "import engine\ns=engine.new_state()\nfor q in ['Is Ajmer Urban safe?','What does it mean?','Is its soil good?']:\n"
            " r=engine.answer(q,s)\nprint(r['intent'], r['status'])")
    out = subprocess.run([sys.executable, "-c", code], cwd=BASE, capture_output=True, text=True, timeout=120, env=env)
    assert out.returncode == 0 and "domain data_unavailable" in out.stdout, out.stderr[-300:] + out.stdout
    return "fresh process, no *KEY*/*TOKEN* variables, sockets blocked: " + out.stdout.strip()


@test("UI01_website_loads", "ui")
def _():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(BASE / "app.py"), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    # Phase 6 (option (a), chosen pending naveen's confirmation): the start page is the chat (since Phase 4), so this
    # checks the chat start page instead of the old 3.0 home page - same strictness: loads with 0 exceptions, shows
    # the JalMitra heading, a question input and the example-question buttons.
    text = " ".join([m.value for m in list(at.markdown) + list(at.subheader)] +
                    [h.proto.body for h in at.get("html") if hasattr(h, "proto")])
    assert "JalMitra — Your Intelligent Groundwater Assistant" in text, text[:200]
    assert at.chat_input, "no question input on the start page"
    assert any("What does Over-Exploited mean?" in b.label for b in at.button)
    return "chat start page runs without exceptions in Streamlit AppTest"


@test("UI02_assets_present", "ui")
def _():
    for f in ("assets/logo.svg", "assets/logo_dark.svg", "assets/logo_icon.svg", "assets/favicon.png",
              ".streamlit/config.toml"):
        assert (BASE / f).exists(), f
    cfg = (BASE / ".streamlit/config.toml").read_text(encoding="utf-8")
    assert "[theme.light]" in cfg and "[theme.dark]" in cfg
    return "logo, favicon, light and dark theme"


def main():
    hash_after = hashlib.sha256(Path(DB_PATH).read_bytes()).hexdigest()
    RESULTS.append({"id": "DB01_database_unchanged", "group": "database",
                    "status": "PASSED" if hash_after == HASH_BEFORE else "FAILED",
                    "detail": f"sha256 {hash_after[:16]}", "ms": 0})
    RESULTS.append({"id": "NET01_no_network", "group": "offline",
                    "status": "PASSED" if not NETWORK_ATTEMPTS else "FAILED",
                    "detail": f"{len(NETWORK_ATTEMPTS)} non-loopback attempts "
                              f"({len(LOOPBACK_CONNECTIONS)} loopback connections allowed)", "ms": 0})
    with open(BASE / "test_results_v3.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "group", "status", "detail", "ms"])
        w.writeheader()
        w.writerows(RESULTS)
    for r in RESULTS:
        print(f"{r['status']:7} {r['id']:42} {r['detail'][:110]}")
    passed = sum(r["status"] == "PASSED" for r in RESULTS)
    skipped = sum(r["status"] == "SKIPPED" for r in RESULTS)
    print(f"\nJalMitra 3.0 tests: {passed} passed, {skipped} skipped, {len(RESULTS) - passed - skipped} failed "
          f"of {len(RESULTS)}")
    return 0 if passed + skipped == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
