"""
ui_auth.py - JalMitra login screens, account settings, admin page and privacy page (27 Nov 2026).

The logic and all security rules are in auth.py; this file only draws the screens and keeps the login in the
Streamlit session.

How a login is kept
  * after a successful login the server creates a session (auth.create_session) and the browser stores only its
    random token in the cookie "jalmitra_session" (SameSite=Strict, Secure on https). A page reload (for example
    the Day / Night switch) reads the cookie and resumes the session; nothing else about the user is in the browser
  * every minute the session is checked again in the database, so logout, a password change, an admin disabling
    the account and the idle / total time limits take effect within a minute everywhere
  * on logout the session is revoked in the database and the cookie is deleted

Login is required by default. JALMITRA_AUTH=off turns it off (single-user use on your own computer); the automated
UI tests (Streamlit AppTest) also run without it unless JALMITRA_AUTH=on.
"""

import ipaddress
import json
import logging
import os
import sys
import time

import pandas as pd
import streamlit as st

import auth

COOKIE = "jalmitra_session"
CHECK_EVERY = 60                    # seconds between database checks of an open session
log = logging.getLogger("jalmitra.auth")


def enabled():
    v = os.environ.get("JALMITRA_AUTH", "").strip().lower()
    if v in ("off", "0", "false", "no"):
        return False
    if v in ("on", "1", "true", "yes"):
        return True
    return "streamlit.testing.v1" not in sys.modules


def client_ip():
    """The visitor's IP address (used only for rate limits, stored only as a keyed hash)."""
    ip = None
    try:
        ip = st.context.ip_address
    except Exception:                                  # noqa: BLE001
        pass
    try:
        fwd = st.context.headers.get("X-Forwarded-For") or ""
    except Exception:                                  # noqa: BLE001
        fwd = ""
    if fwd:
        # behind a proxy (Streamlit Cloud) the real address is the last one the proxy added; the first entries can be
        # typed by the visitor, so they are not trusted
        last = fwd.split(",")[-1].strip()
        try:
            private = ip is None or ipaddress.ip_address(ip).is_private or ipaddress.ip_address(ip).is_loopback
        except ValueError:
            private = True
        if private and last:
            ip = last
    return ip or None


def user():
    """The logged-in user (dict with uid, email, name, role) or None."""
    return st.session_state.get("_jm_auth")


def user_id():
    a = user()
    return a["uid"] if a else None


def is_admin():
    a = user()
    return bool(a and a.get("role") == "admin")


# ------------------------------------------------------------------ cookie helpers (run in the page)
def _cookie_script(token, remember):
    age = f"; max-age={int(auth.config()['max_hours'] * 3600)}" if remember else ""
    value = json.dumps(token)
    return f"""<script>(function() {{
  var sec = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = "{COOKIE}=" + encodeURIComponent({value}) + "; path=/; SameSite=Strict{age}" + sec;
}})();</script>"""


def _clear_cookie_script():
    return f"""<script>(function() {{
  var sec = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = "{COOKIE}=; path=/; max-age=0; SameSite=Strict" + sec;
}})();</script>"""


def _cookie_token():
    try:
        v = st.context.cookies.get(COOKIE)
    except Exception:                                  # noqa: BLE001
        return None
    return v if isinstance(v, str) and 20 <= len(v) <= 100 else None


def _start(u, token, remember=True):
    """Fresh session state for a newly logged-in user (nothing from before the login is kept)."""
    st.session_state.clear()
    st.session_state["_jm_auth"] = {"uid": u["id"], "email": u["email"], "name": u["name"], "role": u["role"],
                                    "token": token, "checked": time.time()}
    st.session_state["_jm_cookie_set"] = (token, remember)


def _end(reason=None):
    a = user()
    if a:
        try:
            auth.revoke_session(a.get("token"))
        except Exception:                              # noqa: BLE001
            pass
        auth.record("logout" if not reason else "session_end", user_id=a["uid"], ip=client_ip(), detail=reason)
    st.session_state.clear()
    st.session_state["_jm_cookie_clear"] = True
    st.session_state["_jm_dead_token"] = (a or {}).get("token") or _cookie_token()
    if reason:
        st.session_state["_jm_auth_note"] = reason


def logout():
    _end()


def _check():
    """Validate the session (from the session state or the cookie). Returns the user or None."""
    a = user()
    now = time.time()
    if a and now - a.get("checked", 0) < CHECK_EVERY:
        return a
    token = a["token"] if a else _cookie_token()
    if not a and token and token == st.session_state.get("_jm_dead_token"):
        return None                                    # the cookie of a session that was just ended
    if not token:
        return None
    u = auth.resume_session(token)
    if u is None:
        if a:
            _end("Your session has ended. Please log in again.")
        return None
    if a:
        a.update(name=u["name"], email=u["email"], role=u["role"], checked=now)
        return a
    _start(u, token, remember=True)
    st.session_state.pop("_jm_cookie_set", None)       # the cookie is already there
    return user()


def require_login():
    """Call at the top of app.py. Returns the user, or draws the login screen and stops the run."""
    if not enabled():
        return None
    if st.session_state.pop("_jm_cookie_clear", False):
        st.html(_clear_cookie_script(), unsafe_allow_javascript=True)
    pending = st.session_state.pop("_jm_cookie_set", None)
    if pending:
        st.html(_cookie_script(*pending), unsafe_allow_javascript=True)
    try:
        u = _check()
    except Exception:                                  # noqa: BLE001 - database down: say so, never let anyone in
        log.exception("account database not reachable")
        st.error("JalMitra cannot reach its account database right now. Please try again in a few minutes.")
        st.stop()
    if u:
        return u
    login_screen()
    st.stop()


# ------------------------------------------------------------------ login / sign-up / reset screen
LOGIN_CSS = """<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display:none;}
.jm-auth-head {text-align:center; margin: 2.2rem 0 0.6rem 0;}
.jm-auth-head h1 {font-size: 1.9rem; margin: 0.4rem 0 0.2rem 0;}
.jm-auth-head p {opacity: 0.75; margin: 0;}
.jm-auth-foot {text-align:center; font-size: 0.85rem; opacity: 0.7; margin-top: 1.2rem;}
</style>"""

PRIVACY = """
**What JalMitra stores about you**

* Your **name and email**, so you can log in.
* Your **password only as a secure hash** (Argon2id). Nobody, including the JalMitra team, can read your password.
* Your **saved chats and settings**, so you can continue later. Only you can see them. You can delete one chat,
  all chats, or your whole account at any time (Account → Delete account).
* **Security records** (logins, failed logins, password resets) with the email and IP address stored only as
  one-way codes, to stop people who try to guess passwords.

**What JalMitra does not do**

* It does not sell or share your data, show ads, or track your location (you choose a location yourself).
* The groundwater figures come from official government data (CGWB / State GWRA 2025). The AI explains them, but
  please confirm important decisions with your local groundwater office.

Questions or a request to delete your data: contact the JalMitra team (Section DC).
"""

PW_RULES = (f"At least {auth.PASSWORD_MIN} characters. Mix letters with numbers or symbols, or use a long "
            "pass-phrase (16+ characters). Do not use your name or email.")


def _strength_bar(score):
    labels = ["Very weak", "Weak", "OK", "Strong", "Very strong"]
    colors = ["#C62828", "#E65100", "#F9A825", "#2E7D32", "#1B5E20"]
    pct = (score + 1) * 20
    st.html(f'<div style="height:6px;border-radius:3px;background:#e3e8ef;margin-top:-6px">'
            f'<div style="height:6px;width:{pct}%;border-radius:3px;background:{colors[score]}"></div></div>'
            f'<div style="font-size:0.8rem;opacity:0.75;margin-top:2px">Password strength: {labels[score]}</div>')


def _logo():
    try:
        import ui_chat_v4 as chat4
        return f'<img src="{chat4._logo_uri()}" width="64" height="64" alt="JalMitra">'
    except Exception:                                  # noqa: BLE001
        return "💧"


def login_screen():
    st.html(LOGIN_CSS)
    note = st.session_state.pop("_jm_auth_note", None)
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.html(f'<div class="jm-auth-head">{_logo()}<h1>Welcome to JalMitra</h1>'
                "<p>Your groundwater assistant. Please log in or create a free account.</p></div>")
        if note:
            st.info(note)
        cfg = auth.config()
        names = ["Log in", "Create account", "Forgot password"] if cfg["allow_signup"] else ["Log in",
                                                                                            "Forgot password"]
        tabs = dict(zip(names, st.tabs(names)))
        with tabs["Log in"]:
            _login_form()
        if "Create account" in tabs:
            with tabs["Create account"]:
                _signup_form()
        with tabs["Forgot password"]:
            _reset_forms()
        with st.expander("Privacy: what we store", icon=":material/shield_lock:"):
            st.markdown(PRIVACY)
        st.html('<div class="jm-auth-foot">Passwords are protected with Argon2id hashing. '
                "Never share your password with anyone.</div>")


def _login_form():
    with st.form("jm_login", clear_on_submit=False, border=False):
        email = st.text_input("Email", key="jm_li_email", max_chars=auth.EMAIL_MAX, autocomplete="email")
        password = st.text_input("Password", type="password", key="jm_li_pw", max_chars=auth.PASSWORD_MAX,
                                 autocomplete="current-password")
        remember = st.checkbox("Keep me logged in on this device", value=True, key="jm_li_rem",
                               help="Do not tick this on a shared or public computer.")
        go = st.form_submit_button("Log in", type="primary", width="stretch")
    if go:
        try:
            u = auth.authenticate(email, password, ip=client_ip())
            token = auth.create_session(u["id"])
        except auth.AuthError as e:
            st.error(str(e))
            return
        _start(u, token, remember)
        st.rerun()


def _signup_form():
    with st.form("jm_signup", clear_on_submit=False, border=False):
        name = st.text_input("Your name", key="jm_su_name", max_chars=auth.NAME_MAX, autocomplete="name")
        email = st.text_input("Email", key="jm_su_email", max_chars=auth.EMAIL_MAX, autocomplete="email")
        pw = st.text_input("Password", type="password", key="jm_su_pw", max_chars=auth.PASSWORD_MAX,
                           help=PW_RULES, autocomplete="new-password")
        pw2 = st.text_input("Type the password again", type="password", key="jm_su_pw2",
                            max_chars=auth.PASSWORD_MAX, autocomplete="new-password")
        st.caption(PW_RULES)
        agree = st.checkbox("I have read the privacy note below and agree.", key="jm_su_agree")
        go = st.form_submit_button("Create account", type="primary", width="stretch")
    if pw:
        _strength_bar(auth.password_strength(pw))
    if go:
        if not agree:
            st.error("Please tick the box to agree to the privacy note.")
            return
        if pw != pw2:
            st.error("The two passwords are not the same.")
            return
        try:
            u = auth.register(email, name, pw, ip=client_ip())
            token = auth.create_session(u["id"])
        except auth.AuthError as e:
            st.error(str(e))
            return
        _start(u, token, True)
        st.session_state["_jm_toast"] = f"Welcome to JalMitra, {u['name']}! Your account is ready."
        st.rerun()


def _reset_forms():
    if not auth.email_enabled():
        st.info("Password reset by email is not switched on yet. Please ask the JalMitra admin: they can give you a "
                "new temporary password from the Admin page.")
        return
    st.caption("Step 1: we email you a one-time code (valid for 15 minutes).")
    with st.form("jm_reset1", border=False):
        email = st.text_input("Email", key="jm_rs_email", max_chars=auth.EMAIL_MAX)
        go = st.form_submit_button("Send me a code", width="stretch")
    if go:
        try:
            auth.request_reset(email, ip=client_ip())
            st.success("If an account with this email exists, a code is on its way. Check your inbox and spam "
                       "folder.")
        except auth.AuthError as e:
            st.error(str(e))
    st.caption("Step 2: type the code and choose a new password.")
    with st.form("jm_reset2", border=False):
        email2 = st.text_input("Email", key="jm_rs_email2", max_chars=auth.EMAIL_MAX)
        code = st.text_input("Code from the email", key="jm_rs_code", max_chars=12)
        pw = st.text_input("New password", type="password", key="jm_rs_pw", max_chars=auth.PASSWORD_MAX,
                           help=PW_RULES, autocomplete="new-password")
        pw2 = st.text_input("Type the new password again", type="password", key="jm_rs_pw2",
                            max_chars=auth.PASSWORD_MAX, autocomplete="new-password")
        go2 = st.form_submit_button("Set new password", type="primary", width="stretch")
    if go2:
        if pw != pw2:
            st.error("The two passwords are not the same.")
            return
        try:
            auth.reset_password(email2, code, pw, ip=client_ip())
        except auth.AuthError as e:
            st.error(str(e))
            return
        st.success("Your password is changed. You can log in now (all other devices were logged out).")


# ------------------------------------------------------------------ account dialog (from the sidebar)
def sidebar_account():
    """Small account row at the bottom of the sidebar."""
    a = user()
    if not a:
        return
    if st.button(a["name"], key="jm_account_btn", icon=":material/account_circle:", width="stretch",
                 help=a["email"]):
        st.session_state["_jm_open_account"] = True


def maybe_open_account():
    if st.session_state.pop("_jm_open_account", False):
        _account_dialog()


@st.dialog("Your account", width="medium")
def _account_dialog():
    a = user()
    if not a:
        st.rerun()
    st.markdown(f"**{a['name']}**  \n{a['email']}" + ("  \n🛡️ Admin" if a.get("role") == "admin" else ""))
    if st.button("Log out", key="jm_logout", icon=":material/logout:", type="primary", width="stretch"):
        logout()
        st.rerun()
    with st.expander("Change password", icon=":material/key:"):
        with st.form("jm_chpw", clear_on_submit=True, border=False):
            old = st.text_input("Current password", type="password", max_chars=auth.PASSWORD_MAX,
                                autocomplete="current-password")
            new = st.text_input("New password", type="password", max_chars=auth.PASSWORD_MAX, help=PW_RULES,
                                autocomplete="new-password")
            new2 = st.text_input("Type the new password again", type="password", max_chars=auth.PASSWORD_MAX,
                                 autocomplete="new-password")
            go = st.form_submit_button("Change password", width="stretch")
        if go:
            if new != new2:
                st.error("The two new passwords are not the same.")
            else:
                try:
                    auth.change_password(a["uid"], old, new, ip=client_ip(), keep_token=a["token"])
                    st.success("Password changed. Your other devices were logged out.")
                except auth.AuthError as e:
                    st.error(str(e))
    with st.expander("Delete my account", icon=":material/person_remove:"):
        st.caption("This deletes your account, all your saved chats and settings. It cannot be undone.")
        with st.form("jm_delacc", clear_on_submit=True, border=False):
            pw = st.text_input("Password", type="password", max_chars=auth.PASSWORD_MAX)
            sure = st.checkbox("Yes, delete my account and all my data")
            go = st.form_submit_button("Delete account", width="stretch")
        if go:
            if not sure:
                st.error("Please tick the box first.")
            else:
                try:
                    auth.delete_account(a["uid"], pw, ip=client_ip())
                except auth.AuthError as e:
                    st.error(str(e))
                else:
                    st.session_state.clear()
                    st.session_state["_jm_cookie_clear"] = True
                    st.session_state["_jm_auth_note"] = "Your account and data were deleted."
                    st.rerun()
    with st.expander("Privacy", icon=":material/shield_lock:"):
        st.markdown(PRIVACY)


# ------------------------------------------------------------------ pages
def page_privacy():
    st.title("Privacy")
    st.markdown(PRIVACY)


def _when(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else ""


def page_admin():
    if not is_admin():                                 # checked again here, not only in the menu
        st.error("This page is only for JalMitra admins.")
        st.stop()
    me = user()
    st.title("Admin")
    st.caption(f"Accounts database: {auth.storage_kind()}. Every action here is recorded.")
    s = auth.stats()
    cols = st.columns(6)
    for col, (label, key) in zip(cols, [("Users", "users"), ("Active 24 h", "active_24h"),
                                        ("New 24 h", "signups_24h"), ("Failed logins 24 h", "failed_24h"),
                                        ("Locked now", "locked_now"), ("Saved chats", "chats")]):
        col.metric(label, s[key])

    users = auth.list_users()
    st.subheader("Users")
    if users:
        now = time.time()
        df = pd.DataFrame([{"Name": u["name"], "Email": u["email"], "Role": u["role"],
                            "Status": "disabled" if not u["is_active"] else
                            ("locked" if (u["locked_until"] or 0) > now else "active"),
                            "Joined": _when(u["created_at"]), "Last login": _when(u["last_login_at"])}
                           for u in users])
        st.dataframe(df, hide_index=True, width="stretch")
        by_label = {f"{u['name']} <{u['email']}>": u for u in users}
        pick = st.selectbox("Choose a user", list(by_label), key="jm_adm_pick")
        target = by_label[pick]
        c = st.columns(5)
        actions = [("enable" if not target["is_active"] else "disable", c[0]), ("unlock", c[1]),
                   ("make_user" if target["role"] == "admin" else "make_admin", c[2])]
        for action, col in actions:
            if col.button(action.replace("_", " ").capitalize(), key=f"jm_adm_{action}", width="stretch"):
                try:
                    auth.admin_update(me["uid"], target["id"], action)
                    st.success("Done.")
                    st.rerun()
                except auth.AuthError as e:
                    st.error(str(e))
        if c[3].button("New temporary password", key="jm_adm_temp", width="stretch"):
            try:
                temp = auth.admin_reset_password(me["uid"], target["id"])
                st.warning(f"Give this temporary password to {target['name']} privately. It is shown only once; ask "
                           f"them to change it after logging in:\n\n`{temp}`")
            except auth.AuthError as e:
                st.error(str(e))
        with c[4].popover("Delete", icon=":material/delete:", width="stretch"):
            st.caption("Deletes the account and all its chats. Cannot be undone.")
            if st.button("Yes, delete", key="jm_adm_del", type="primary"):
                try:
                    auth.admin_update(me["uid"], target["id"], "delete")
                    st.rerun()
                except auth.AuthError as e:
                    st.error(str(e))

    st.subheader("Recent security events")
    ev = auth.recent_events(200)
    if ev:
        st.dataframe(pd.DataFrame([{"Time": _when(e["ts"]), "Event": e["kind"], "User": e["user_id"] or "",
                                    "Email code": e["email_tag"] or "", "IP code": e["ip_tag"] or "",
                                    "Detail": e["detail"] or ""} for e in ev]), hide_index=True, width="stretch")
