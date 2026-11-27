"""
test_auth.py - tests for the JalMitra accounts system (auth.py, ui_auth.py, chat_store per-user storage).

Run:  python test_auth.py         (uses a temporary SQLite database; never touches real accounts)
"""

import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="jalmitra_auth_test_")
# JALMITRA_TEST_DB_URL can point at an empty test PostgreSQL database (all tables in it are dropped!)
os.environ["JALMITRA_AUTH_DB_URL"] = os.environ.get("JALMITRA_TEST_DB_URL") or ("sqlite:///" + Path(TMP, "users.db")
                                                                                .as_posix())
os.environ["JALMITRA_ADMIN_EMAILS"] = "admin@example.com"
os.environ["JALMITRA_AUTH_SECRET"] = "test-secret"
os.environ["JALMITRA_HISTORY_DIR"] = TMP
sys.path.insert(0, str(Path(__file__).resolve().parent))

import auth  # noqa: E402

TESTS = []
GOOD = "Blue-river-42-sky"


def test(fn):
    TESTS.append(fn)
    return fn


def fresh():
    if os.environ.get("JALMITRA_TEST_DB_URL"):
        auth.META.drop_all(auth.engine())
    auth.reset_engine()
    p = Path(TMP, "users.db")
    if p.exists():
        p.unlink()


def raises(fn, *a, contains="", **kw):
    try:
        fn(*a, **kw)
    except auth.AuthError as e:
        assert contains.lower() in str(e).lower(), (str(e), contains)
        return str(e)
    raise AssertionError("no AuthError")


@test
def signup_and_login():
    fresh()
    u = auth.register("  Ravi@Example.COM ", "Ravi Kumar", GOOD, ip="1.1.1.1")
    assert u["email"] == "ravi@example.com" and u["role"] == "user" and "password_hash" not in u
    assert auth.authenticate("RAVI@example.com", GOOD, ip="1.1.1.1")["id"] == u["id"]
    with auth.engine().connect() as c:
        h = c.execute(auth.sa.select(auth.USERS.c.password_hash)).scalar_one()
    assert h.startswith("$argon2id$") and GOOD not in h


@test
def duplicate_email_refused():
    fresh()
    auth.register("a@example.com", "Asha", GOOD)
    raises(auth.register, "A@example.com", "Asha", GOOD, contains="already exists")


@test
def input_validation():
    fresh()
    for bad in ["", "no-at", "a@b", "a@@b.com", "a b@c.com", "x" * 250 + "@a.com", "a..b@c.com"]:
        raises(auth.register, bad, "Name", GOOD, contains="valid email")
    raises(auth.register, "n@example.com", "", GOOD, contains="name")
    raises(auth.register, "n@example.com", "<script>", GOOD, contains="name")
    raises(auth.register, "n@example.com", "N" * 61, GOOD, contains="too long")


@test
def weak_passwords_refused():
    fresh()
    for pw in ["short1!", "password123", "1234567890123", "aaaaaaaaaaaa", "Password1234", "qwerty123456",
               "abcdefghijkl", "x" * 129]:
        raises(auth.register, "p@example.com", "Priya", pw)
    raises(auth.register, "priyanka@example.com", "Someone", "priyanka-2026!", contains="email")
    raises(auth.register, "q@example.com", "Mahesh Patel", "mahesh-2026-xyz", contains="name")
    assert auth.password_problems("correct horse battery staple") == []        # long pass-phrase is fine
    assert auth.password_strength("short") <= 1 and auth.password_strength("A-long-Pass-phrase-99!") >= 3


@test
def wrong_password_and_unknown_email_same_message():
    fresh()
    auth.register("b@example.com", "Bina", GOOD)
    m1 = raises(auth.authenticate, "b@example.com", "Wrong-pass-123")
    m2 = raises(auth.authenticate, "nobody@example.com", "Wrong-pass-123")
    m3 = raises(auth.authenticate, "not-an-email", "Wrong-pass-123")
    assert m1 == m2 == m3


@test
def lockout_after_five_wrong():
    fresh()
    auth.register("c@example.com", "Chetan", GOOD)
    for _ in range(4):
        raises(auth.authenticate, "c@example.com", "Wrong-pass-123", contains="not correct")
    raises(auth.authenticate, "c@example.com", "Wrong-pass-123", contains="locked")
    raises(auth.authenticate, "c@example.com", GOOD, contains="locked")           # even the right password
    with auth.engine().begin() as c:                                               # time passes
        c.execute(auth.USERS.update().values(locked_until=time.time() - 1))
    assert auth.authenticate("c@example.com", GOOD)
    u = auth.get_user(auth.list_users()[0]["id"])
    assert u["failed_logins"] == 0 and u["lock_count"] == 0


@test
def lockout_grows():
    fresh()
    auth.register("g@example.com", "Gita", GOOD)
    for rnd in range(2):
        with auth.engine().begin() as c:
            c.execute(auth.USERS.update().values(locked_until=0))
        for _ in range(5):
            try:
                auth.authenticate("g@example.com", "Wrong-pass-123")
            except auth.AuthError:
                pass
    u = auth.list_users()[0]
    assert u["lock_count"] == 2 and u["locked_until"] - time.time() > 25 * 60      # 30 minutes the second time


@test
def rate_limit_per_ip():
    fresh()
    auth.register("d@example.com", "Dev", GOOD)
    limit = auth.LIMITS["login_ip"][0]
    msgs = []
    for i in range(limit + 1):
        try:
            auth.authenticate(f"user{i}@example.com", "Wrong-pass-123", ip="9.9.9.9")
        except auth.AuthError as e:
            msgs.append(str(e))
    assert msgs[-1] == auth.TOO_MANY and auth.TOO_MANY not in msgs[:-1]
    assert auth.authenticate("d@example.com", GOOD, ip="8.8.8.8")                 # other visitors are not blocked


@test
def signup_rate_limit():
    fresh()
    n = auth.LIMITS["signup_ip"][0]
    for i in range(n):
        auth.register(f"s{i}@example.com", "Sam", GOOD, ip="7.7.7.7")
    raises(auth.register, "extra@example.com", "Sam", GOOD, ip="7.7.7.7", contains="too many")


@test
def admin_from_config_and_admin_tools():
    fresh()
    a = auth.register("admin@example.com", "Admin", GOOD)
    u = auth.register("e@example.com", "Esha", GOOD)
    assert a["role"] == "admin" and u["role"] == "user"
    raises(auth.admin_update, u["id"], a["id"], "disable", contains="only an admin")
    raises(auth.admin_update, a["id"], a["id"], "disable", contains="own account")
    auth.admin_update(a["id"], u["id"], "disable")
    raises(auth.authenticate, "e@example.com", GOOD, contains="disabled")
    auth.admin_update(a["id"], u["id"], "enable")
    temp = auth.admin_reset_password(a["id"], u["id"])
    raises(auth.authenticate, "e@example.com", GOOD)
    assert auth.authenticate("e@example.com", temp)
    s = auth.stats()
    assert s["users"] == 2
    kinds = {e["kind"] for e in auth.recent_events()}
    assert {"signup", "admin_disable", "admin_password_reset", "login_disabled"} <= kinds
    auth.admin_update(a["id"], u["id"], "delete")
    assert auth.get_user(u["id"]) is None


@test
def events_never_store_plain_email_or_ip():
    fresh()
    auth.register("secret.person@example.com", "Sp", GOOD, ip="203.0.113.5")
    try:
        auth.authenticate("secret.person@example.com", "Wrong-pass-123", ip="203.0.113.5")
    except auth.AuthError:
        pass
    for e in auth.recent_events():
        blob = " ".join(str(v) for v in e.values())
        assert "secret.person" not in blob and "203.0.113.5" not in blob and "Wrong-pass" not in blob


@test
def sessions_resume_expire_revoke():
    fresh()
    u = auth.register("f@example.com", "Farah", GOOD)
    t = auth.create_session(u["id"])
    assert len(t) >= 40 and auth.resume_session(t)["id"] == u["id"]
    assert auth.resume_session("forged-token") is None and auth.resume_session(None) is None
    with auth.engine().connect() as c:                                             # only a hash is stored
        assert c.execute(auth.sa.select(auth.SESSIONS.c.token_hash)).scalar_one() != t
    auth.revoke_session(t)
    assert auth.resume_session(t) is None
    t2 = auth.create_session(u["id"])
    with auth.engine().begin() as c:                                               # idle too long
        c.execute(auth.SESSIONS.update().values(last_seen=time.time() - 10 * 3600))
    assert auth.resume_session(t2) is None


@test
def password_change_logs_out_other_devices():
    fresh()
    u = auth.register("h@example.com", "Hari", GOOD)
    here, other = auth.create_session(u["id"]), auth.create_session(u["id"])
    raises(auth.change_password, u["id"], "Wrong-pass-123", "New-river-77-moon", contains="current password")
    raises(auth.change_password, u["id"], GOOD, GOOD, contains="different")
    auth.change_password(u["id"], GOOD, "New-river-77-moon", keep_token=here)
    assert auth.resume_session(here) is not None and auth.resume_session(other) is None
    assert auth.authenticate("h@example.com", "New-river-77-moon")


@test
def reset_by_email_code():
    fresh()
    u = auth.register("r@example.com", "Rina", GOOD)
    t = auth.create_session(u["id"])
    sent = []
    auth.request_reset("r@example.com", send=lambda to, subj, body: sent.append((to, body)))
    auth.request_reset("nobody@example.com", send=lambda *a: sent.append(a))       # silent, nothing sent
    assert len(sent) == 1 and sent[0][0] == "r@example.com"
    code = [w for w in sent[0][1].split() if len(w) == 8 and w.isupper() or (len(w) == 8 and w.isalnum()
                                                                               and w.upper() == w)][0]
    raises(auth.reset_password, "r@example.com", "WRONGCOD", "Reset-sun-55-tree", contains="wrong")
    auth.reset_password("r@example.com", code.lower(), "Reset-sun-55-tree")
    assert auth.authenticate("r@example.com", "Reset-sun-55-tree")
    assert auth.resume_session(t) is None                                          # old sessions ended
    raises(auth.reset_password, "r@example.com", code, "Another-pw-66-x", contains="expired")   # one use only


@test
def reset_code_tries_limited():
    fresh()
    auth.register("t@example.com", "Tara", GOOD)
    sent = []
    auth.request_reset("t@example.com", send=lambda to, subj, body: sent.append(body))
    code = [w for w in sent[0].split() if len(w) == 8 and w.upper() == w and w.isalnum()][0]
    for _ in range(auth.RESET_CODE_TRIES):
        raises(auth.reset_password, "t@example.com", "AAAAAAAA", "Reset-sun-55-tree")
    raises(auth.reset_password, "t@example.com", code, "Reset-sun-55-tree")        # now even the right code fails


@test
def delete_account_removes_data():
    fresh()
    u = auth.register("k@example.com", "Kiran", GOOD)
    auth.save_chat(u["id"], "abc123", "t", time.time(), {"id": "abc123", "messages": []})
    auth.save_user_settings(u["id"], {"theme": "night"})
    raises(auth.delete_account, u["id"], "Wrong-pass-123", contains="not correct")
    auth.delete_account(u["id"], GOOD)
    assert auth.get_user(u["id"]) is None and auth.load_chats(u["id"]) == [] and auth.load_user_settings(u["id"]) == {}


@test
def chats_are_private_per_user():
    fresh()
    import chat_store
    import ui_auth
    a = auth.register("u1@example.com", "One", GOOD)
    b = auth.register("u2@example.com", "Two", GOOD)
    os.environ["JALMITRA_AUTH"] = "on"
    try:
        orig = ui_auth.user_id
        ui_auth.user_id = lambda: a["id"]
        chat_store.save_conversation({"id": "aaaa1111", "title": "mine", "messages": [{"role": "user",
                                                                                         "content": "hi"}]})
        chat_store.save_settings({"theme": "night"})
        assert [c["id"] for c in chat_store.load_conversations()] == ["aaaa1111"]
        ui_auth.user_id = lambda: b["id"]
        assert chat_store.load_conversations() == [] and chat_store.load_settings() == {}
        assert chat_store.delete_conversation("aaaa1111") is False                 # cannot delete someone else's
        ui_auth.user_id = lambda: None                                             # logged out: nothing at all
        assert chat_store.load_conversations() == [] and chat_store.save_conversation(
            {"id": "bbbb2222", "messages": [{"role": "user", "content": "x"}]}) is None
        assert not list(Path(TMP).glob("chat_*.json"))                             # no shared files written
        ui_auth.user_id = lambda: a["id"]
        assert chat_store.rename_conversation("aaaa1111", "renamed")
        assert chat_store.load_conversations()[0]["title"] == "renamed"
        assert chat_store.load_settings() == {"theme": "night"}
        assert chat_store.clear_conversations() == 1
    finally:
        ui_auth.user_id = orig
        os.environ.pop("JALMITRA_AUTH", None)


LOGIN_APP = '''
import os, streamlit as st
import ui_auth
u = ui_auth.require_login()
st.write("INSIDE as " + u["name"])
if st.button("logout"):
    ui_auth.logout()
    st.rerun()
'''


@test
def login_screen_blocks_and_lets_in():
    fresh()
    from streamlit.testing.v1 import AppTest
    os.environ["JALMITRA_AUTH"] = "on"
    try:
        auth.register("ui@example.com", "Uma", GOOD)
        at = AppTest.from_string(LOGIN_APP, default_timeout=60).run()
        assert not any("INSIDE" in m.value for m in at.markdown), "app content shown before login"
        at.text_input(key="jm_li_email").input("ui@example.com")
        at.text_input(key="jm_li_pw").input("Wrong-pass-123")
        at.button[0].click().run()                        # the form's submit button
        assert any("not correct" in e.value for e in at.error)
        assert not any("INSIDE" in m.value for m in at.markdown)
        at.text_input(key="jm_li_email").input("ui@example.com")
        at.text_input(key="jm_li_pw").input(GOOD)
        at.button[0].click().run()
        assert any("INSIDE as Uma" in m.value for m in at.markdown), [m.value for m in at.markdown]
        at.button(key=None) if False else None
        [b for b in at.button if b.label == "logout"][0].click().run()
        assert not any("INSIDE" in m.value for m in at.markdown)
    finally:
        os.environ.pop("JALMITRA_AUTH", None)


@test
def signup_screen_creates_account():
    fresh()
    from streamlit.testing.v1 import AppTest
    os.environ["JALMITRA_AUTH"] = "on"
    try:
        at = AppTest.from_string(LOGIN_APP, default_timeout=60).run()
        at.text_input(key="jm_su_name").input("Neha")
        at.text_input(key="jm_su_email").input("neha@example.com")
        at.text_input(key="jm_su_pw").input(GOOD)
        at.text_input(key="jm_su_pw2").input(GOOD)
        submit = [b for b in at.button if b.label == "Create account"][0]
        submit.click().run()
        assert any("agree" in e.value for e in at.error)                           # privacy box not ticked
        at.checkbox(key="jm_su_agree").check()
        [b for b in at.button if b.label == "Create account"][0].click().run()
        assert any("INSIDE as Neha" in m.value for m in at.markdown), [e.value for e in at.error]
    finally:
        os.environ.pop("JALMITRA_AUTH", None)


def main():
    passed, failed = 0, []
    t0 = time.perf_counter()
    for fn in TESTS:
        try:
            fn()
            passed += 1
            print(f"  ok   {fn.__name__}")
        except Exception:                                  # noqa: BLE001
            failed.append(fn.__name__)
            print(f"  FAIL {fn.__name__}\n{traceback.format_exc()}")
    print(f"\n{passed}/{len(TESTS)} auth tests passed in {time.perf_counter() - t0:.1f} s")
    auth.reset_engine()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
