"""
test_v4_ui.py - JalMitra chat interface tests (Streamlit AppTest, no browser). Written in Phase 4, updated in Phase 6
when the app became AI-first (naveen's Phase 6 spec: AI always on, no AI toggle, no user-facing rule answers).

A deterministic fake model (fake_ai_for_tests.py) stands in for Ollama, so these tests check the interface, not the
model. Covers: start page and branding, welcome examples, six-language selection, AI reply + official data cards +
sources, missing data, ambiguous locations (options from the place index), chat history and new conversation,
follow-ups, Coming Soon replies and page, no AI toggle (even in dev mode), model unavailable -> clear error (no
rule answer), invented / contradictory AI text never shown, Hindi replies, hidden soil / crop / land / irrigation /
water-quality pages (code kept), mobile CSS, database unchanged.
Phase 6 changes to expectations are marked "Phase 6:" next to the assertion.

Run: python test_v4_ui.py   (exit code 0 when all pass)
"""

import hashlib
import os
import re
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
for _k in [k for k in os.environ if k.startswith("JALMITRA_")]:
    del os.environ[_k]
os.environ.update(JALMITRA_LLM_CACHE="0", JALMITRA_SELF_CHECK="0", JALMITRA_SEMANTIC_SUPPORT="0")

from streamlit.testing.v1 import AppTest  # noqa: E402

import fake_ai_for_tests as fake  # noqa: E402
import llm_provider as lp  # noqa: E402

APP = str(BASE / "app.py")
TESTS = []


def test(group):
    def deco(fn):
        TESTS.append((group, fn))
        return fn
    return deco


def start():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def say(at, q):
    key = "v4_input_welcome" if [c for c in at.chat_input if c.key == "v4_input_welcome"] else "v4_input"
    at.chat_input(key=key).set_value(q).run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def texts(at):
    out = [m.value for m in at.markdown] + [c.value for c in at.caption] + [i.value for i in at.info]
    out += [w.value for w in at.warning] + [e.value for e in at.error]
    out += [h.proto.body for h in at.get("html") if hasattr(h, "proto")]
    return "\n".join(out)


def buttons(at):
    return [b.label for b in at.button]


class AI:
    """Fake local model installed for the duration of a test (down=True: model unavailable)."""
    def __init__(self, down=False, text=None):
        self.down, self.text = down, text

    def __enter__(self):
        fake.install(down=self.down)
        if self.text is not None:
            txt = self.text

            class Fixed(lp.LLMProvider):
                def chat(self, messages, **kw):
                    if "You check a short groundwater explanation" in messages[0]["content"]:
                        return lp.LLMResult(text="SUPPORTED", ok=True, provider="fake", model="fake")
                    return lp.LLMResult(text=txt, ok=True, provider="fake", model="fake")
            lp.LLMProvider = Fixed
        return self

    def __exit__(self, *a):
        fake.restore()


# ------------------------------------------------------------------ A. start page
@test("start")
def chat_is_start_page_with_branding_and_examples():
    with AI():
        at = start()
        body = texts(at)
        assert "JalMitra — Your Intelligent Groundwater Assistant" in body
        for q in ["What does Over-Exploited mean?", "Explain annual groundwater recharge in Hindi",
                  "मेरे जिले में भूजल की स्थिति क्या है?", "मेरे ब्लॉक को क्रिटिकल क्यों घोषित किया गया है?"]:
            assert q in buttons(at), q
        assert at.chat_input, "chat input missing"
        assert "Local AI connected" in body                      # Phase 6: connection status shown


@test("start")
def example_button_asks():
    with AI():
        at = start()
        next(b for b in at.button if b.label == "What does Over-Exploited mean?").click().run()
        assert not at.exception
        assert "checked against official data" in texts(at)     # Phase 6: the reply is written by the AI


# ------------------------------------------------------------------ B. answers
@test("answers")
def rule_reply_with_official_data_and_sources():
    with AI():
        at = say(start(), "Is Osian block safe?")
        body = texts(at)
        assert "Official groundwater data" in body and "Sources" in body          # Phase 6 section names
        assert "OSIAN" in body and "Over-exploited" in body and "395%" in body
        assert "Assessment year: 2025" in body and "AI2025" in body and "RJ2025" in body
        assert "classified as Over-exploited. Its recorded stage" not in body     # Phase 6: no rule text


@test("answers")
def six_languages_selectable():
    expect = {"en": r"[A-Za-z]", "hi": r"[ऀ-ॿ]", "hinglish": r"[A-Za-z]", "raj": r"[ऀ-ॿ]",
              "pa": r"[਀-੿]", "mr": r"[ऀ-ॿ]"}
    with AI():
        for code, script in expect.items():
            at = start()
            at.selectbox(key="v4_lang_w").set_value(code).run()
            say(at, "Is Osian block safe?")
            reply = [m.value for m in at.markdown if "jm4-reply" in m.value]
            assert reply, (code, texts(at)[-400:])
            assert re.search(script, re.sub(r"OSIAN|JODHPUR|Rajasthan|Over-exploited", "", reply[0])), code
            assert at.session_state["answer_lang"] == code


@test("answers")
def missing_data_and_ambiguous_place():
    with AI():
        at = say(start(), "status of Xyzabad")
        body = texts(at)
        assert "no official groundwater data" in body or "Which place do you mean" in body, body[-400:]
        at = say(start(), "Is Nagaur safe?")
        labels = buttons(at)
        assert any("NAGAUR district" in b for b in labels) and any("Block" in b for b in labels), labels


@test("answers")
def coming_soon_reply_no_data():
    with AI():
        for q in ["Which crop should I grow in Nagaur?", "What is the soil quality of my farm?",
                  "Is the groundwater in Jaipur fit for drinking?"]:
            at = say(start(), q)
            body = texts(at)
            assert "future JalMitra update" in body, (q, body[-300:])
            assert "Official groundwater data" not in body, q


# ------------------------------------------------------------------ C. conversations
@test("conversations")
def history_and_new_conversation():
    with AI():
        at = say(start(), "Is Osian block safe?")
        assert "Explain the assessment of my block" not in buttons(at)
        next(b for b in at.button if b.label == "New chat").click().run()     # UI redesign: sidebar "New chat"
        assert "Explain the assessment of my block" in buttons(at)
        assert any("Is Osian block safe?" in b for b in buttons(at))
        next(b for b in at.button if "Is Osian block safe?" in b.label).click().run()
        assert "OSIAN" in texts(at)


@test("conversations")
def follow_up_keeps_context():
    with AI():
        at = say(start(), "Is Osian block safe?")
        say(at, "what about its recharge?")
        assert "2288" in texts(at) or "Annual recharge" in texts(at)


# ------------------------------------------------------------------ D. AI (always on)
@test("ai")
def ai_toggle_hidden_without_dev_flag():
    with AI():
        os.environ["JALMITRA_DEV"] = "1"                         # Phase 6: no toggle even in the old dev mode
        try:
            at = start()
            assert not [t for t in at.toggle if t.key == "v4_ai"]
        finally:
            os.environ.pop("JALMITRA_DEV", None)


@test("ai")
def ai_on_model_unavailable_falls_back():
    with AI(down=True):                                          # Phase 6: clear error, no rule answer
        at = say(start(), "Is Osian block safe?")
        body = texts(at)
        assert "Local AI not available" in body and "START_JALMITRA.bat" in body
        assert "classified as Over-exploited. Its recorded stage" not in body


@test("ai")
def ai_on_verified_explanation_shown_as_experimental():
    with AI():
        at = say(start(), "Is Osian block safe?")
        body = texts(at)
        assert "checked against official data" in body and "395%" in body
        assert body.index("checked against official data") < body.index("Official groundwater data")


@test("ai")
def ai_on_general_question_with_document_source():
    with AI():
        at = say(start(), "How does the monsoon affect the groundwater recharge? Explain.")
        body = texts(at)
        assert "checked against official data" in body, body[-800:]
        assert "PDF page 57" in body and "NC2025" in body


@test("ai")
def ai_contradictory_or_invented_not_shown():
    for bad in ["During the monsoon the water table becomes deeper [P1].",
                "OSIAN is Over-exploited; its stage of extraction is 120%.", "OSIAN is Safe."]:
        q = "How does the monsoon affect the groundwater recharge? Explain." if "[P1]" in bad else "Is Osian block safe?"
        with AI(text=bad):
            at = say(start(), q)
            body = texts(at)
            assert "could not be verified" in body, bad                    # Phase 6: honest message
            assert "deeper" not in body and "120%" not in body and "OSIAN is Safe" not in body, bad


@test("ai")
def hindi_ai_off_by_default_even_in_dev_mode():
    with AI():                                                  # Phase 6: Hindi AI replies are ON (naveen's spec)
        at = start()
        at.selectbox(key="v4_lang_w").set_value("hi").run()
        say(at, "Is Osian block safe?")
        reply = [m.value for m in at.markdown if "jm4-reply" in m.value]
        assert reply and re.search(r"[ऀ-ॿ]", reply[0])


# ------------------------------------------------------------------ E. navigation and layout
@test("navigation")
def other_domains_hidden_but_code_kept():
    src = (BASE / "app.py").read_text(encoding="utf-8")
    for key in ["gwq", "soil", "soilprofile", "land", "landdeg", "crop", "irrigation", "soilreport", "ask"]:
        block = re.search(r'"' + key + r'": st\.Page\((.*?)\),\n', src, re.S).group(1)
        assert "visibility=HIDDEN" in block, key
    import ui_pages_v3
    for fn in ["page_soil", "page_crop", "page_land", "page_irrigation", "page_gw_quality"]:
        assert callable(getattr(ui_pages_v3, fn)), fn


@test("navigation")
def coming_soon_page_lists_six_modules():
    code = f"import sys\nsys.path.insert(0, {str(BASE)!r})\nimport ui_coming_soon\nui_coming_soon.page_coming_soon()\n"
    at = AppTest.from_string(code, default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    body = " ".join(m.value for m in at.markdown)
    for name in ["Soil Health Analysis", "Crop Advisory", "Water Quality Analysis", "Irrigation Intelligence",
                 "Land Intelligence", "Advanced Voice Assistant"]:
        assert name in body, name


@test("navigation")
def mobile_css_present():
    import ui_chat_v4
    assert "@media (max-width: 640px)" in ui_chat_v4.CSS


# ------------------------------------------------------------------ F. UI redesign (24 Nov 2026): history, settings, theme
class Store:
    """A temporary history / settings folder (JALMITRA_HISTORY_DIR) for the duration of a test."""
    def __enter__(self):
        import tempfile
        self.dir = Path(tempfile.mkdtemp(prefix="jm_ui_test_"))
        os.environ["JALMITRA_HISTORY_DIR"] = str(self.dir)
        return self

    def __exit__(self, *a):
        import shutil
        os.environ.pop("JALMITRA_HISTORY_DIR", None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def chats(self):
        import json
        return [json.loads(p.read_text(encoding="utf-8")) for p in self.dir.glob("chat_*.json")]

    def settings(self):
        import json
        p = self.dir / "settings.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


@test("redesign")
def history_saved_and_reopened_with_data_cards():
    with AI(), Store() as store:
        say(start(), "Is Osian block safe?")
        chats = store.chats()
        assert len(chats) == 1 and chats[0]["title"] == "Is Osian block safe?", chats
        roles = [m["role"] for m in chats[0]["messages"]]
        assert roles == ["user", "assistant"], roles
        assert chats[0]["messages"][1]["records"], "official data cards not stored"
        at = start()                                              # a new session = app restarted
        assert "Explain the assessment of my block" in buttons(at)    # opens on a new, empty chat
        next(b for b in at.button if b.label == "Is Osian block safe?").click().run()
        assert not at.exception, [e.value for e in at.exception]
        body = texts(at)
        assert "OSIAN" in body and "395%" in body and "Official groundwater data" in body   # cards reopened
        assert "checked against official data" in body
        say(at, "what about its recharge?")                       # the reopened chat continues
        assert len(store.chats()) == 1 and len(store.chats()[0]["messages"]) == 4


@test("redesign")
def history_grouped_rename_delete_and_clear_all():
    with AI(), Store() as store:
        at = say(start(), "Is Osian block safe?")
        assert "Today" in texts(at)
        cid = store.chats()[0]["id"]
        at.text_input(key=f"jm_ren_{cid}").set_value("Osian check").run()
        assert store.chats()[0]["title"] == "Osian check" and "Osian check" in buttons(at)
        at.button(key=f"jm_del_{cid}").click().run()
        assert not at.exception and store.chats() == [] and "Osian check" not in buttons(at)
        assert "Explain the assessment of my block" in buttons(at)          # the deleted open chat -> new chat
        say(at, "What does Over-Exploited mean?")
        next(b for b in at.button if b.label == "New chat").click().run()
        say(at, "Is Osian block safe?")
        assert len(store.chats()) == 2
        at.button(key="jm_clear_side").click().run()
        assert not at.exception and store.chats() == [], store.chats()
        assert not [b for b in at.button if b.key and b.key.startswith("v4conv_")]
    import chat_store
    now = time.time()
    assert [chat_store.group_label(now - d * 86400, now) for d in (0, 1, 3)] == ["Today", "Yesterday", "Earlier"]


@test("answers")
def concept_question_shows_no_place_or_data_card():
    with AI():                                  # fix (naveen, 24 Nov): "water cycle" was answered as the block CHICHLI
        at = say(start(), "explain basic structure of water cycle")
        body = texts(at)
        assert "CHICHLI" not in body and "Official groundwater data" not in body, body[-500:]


@test("answers")
def state_report_figures_in_cards_and_fallback():
    with AI():                                  # 24 Nov: block figures from the CGWB 2025 state reports
        body = texts(say(start(), "Is Chichli block safe?"))
        assert "60.51%" in body and "20438.79 ham" in body, body[-800:]
        assert "CGWB Madhya Pradesh 2025" in body and "Dynamic Ground Water Resources of Madhya Pradesh" in body
        body = texts(say(start(), "Naykal mandal status"))
        assert "Telangana 2025 state report gives district totals only" in body
        assert "District totals instead" in body and "NC2025" in body


@test("redesign")
def broken_history_file_is_skipped():
    with AI(), Store() as store:
        (store.dir / "chat_abcdef123456.json").write_text("{not json", encoding="utf-8")
        at = start()
        assert not at.exception and "Explain the assessment of my block" in buttons(at)


@test("redesign")
def settings_saved_and_restored():
    with AI(), Store() as store:
        at = start()

        def dialog():          # AppTest reruns the whole script, which closes the dialog: open it before each change
            at.button(key="jm_settings_btn").click().run()
            assert [s for s in at.selectbox if s.key == "w_answer_lang"], "settings dialog not shown"
            return at
        dialog().selectbox(key="w_answer_lang").set_value("hi").run()
        dialog().selectbox(key="w_loc_state").set_value("Rajasthan").run()
        groups = dialog().get("button_group")
        groups[[g.key for g in groups].index("w_detail")].set_value("short").run()
        assert not at.exception, [e.value for e in at.exception]
        saved = store.settings()
        assert saved.get("answer_lang") == "hi" and saved.get("loc_state") == "Rajasthan", saved
        assert saved.get("detail") == "short", saved
        at = start()                                                         # restart: settings come back
        assert at.session_state["answer_lang"] == "hi" and at.session_state["loc_state"] == "Rajasthan"
        assert at.session_state["detail"] == "short"
        assert at.selectbox(key="v4_lang_w").value == "hi"
        body = texts(at)
        assert "Local AI connected" in body                                  # small status chip on the main screen
        assert "Ollama" not in " ".join(c.value for c in at.caption)         # details only in Settings


@test("redesign")
def theme_toggle_and_setting_persist():
    import ui_theme
    with AI(), Store() as store:
        at = start()
        html = " ".join(h.proto.body for h in at.get("html") if hasattr(h, "proto"))
        assert ui_theme.PALETTES["light"]["bg"] in html and '"Light"' in html       # default: Day (naveen, 24 Nov)
        assert at.session_state["theme"] == "day"
        at.button(key="jm_theme_toggle").click().run()                              # quick toggle -> Night
        assert at.session_state["theme"] == "night" and store.settings().get("theme") == "night"
        html = " ".join(h.proto.body for h in at.get("html") if hasattr(h, "proto"))
        assert ui_theme.PALETTES["dark"]["bg"] in html and '"Dark"' in html
        at = start()                                                                # restart: Night kept
        assert at.session_state["theme"] == "night"
        at.button(key="jm_theme_toggle").click().run()                              # and back to Day
        assert at.session_state["theme"] == "day" and store.settings().get("theme") == "day"
        at.button(key="jm_settings_btn").click().run()
        group = at.get("button_group")[[g.key for g in at.get("button_group")].index("w_theme")]
        group.set_value("system").run()
        assert not at.exception and store.settings().get("theme") == "system"


@test("redesign")
def tests_never_touch_real_history_and_chrome_hidden():
    import chat_store
    import ui_theme
    before = sorted(p.name for p in chat_store.DEFAULT_DIR.glob("*")) if chat_store.DEFAULT_DIR.exists() else []
    with AI():
        say(start(), "Is Osian block safe?")                 # no JALMITRA_HISTORY_DIR: a private temp folder
    after = sorted(p.name for p in chat_store.DEFAULT_DIR.glob("*")) if chat_store.DEFAULT_DIR.exists() else []
    assert before == after, (before, after)
    for chrome in ["stMainMenu", "stAppDeployButton", "footer"]:
        assert chrome in ui_theme.BASE_CSS, chrome
    cfg = (BASE / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert 'address = "localhost"' in cfg


@test("integrity")
def db_unchanged():
    h = hashlib.sha256((BASE / "data" / "groundwater.db").read_bytes()).hexdigest()
    assert h == "9eeaee1533b478c1e649b86a56b56f4415e5255e0a3311e37a466f20bdeaa46a", h


def main():
    t0 = time.perf_counter()
    passed, failed, groups = 0, [], {}
    for group, fn in TESTS:
        try:
            fn()
            ok = True
            print(f"PASSED  {group:13s} {fn.__name__}")
        except Exception as e:
            ok = False
            failed.append(fn.__name__)
            print(f"FAILED  {group:13s} {fn.__name__}: {type(e).__name__}: {str(e)[:400]}")
        passed += ok
        g = groups.setdefault(group, [0, 0])
        g[0] += ok
        g[1] += 1
    print()
    for g, (a, b) in groups.items():
        print(f"  {g:13s} {a}/{b}")
    print(f"\nJalMitra 4.0 UI tests: {passed} passed, {len(failed)} failed of {len(TESTS)} "
          f"({time.perf_counter() - t0:.1f} s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
