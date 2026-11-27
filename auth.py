"""
auth.py - user accounts for JalMitra: sign-up, login, lockout, password reset, admin tools (27 Nov 2026).

No Streamlit widgets here (the screens are in ui_auth.py), so this module can be tested on its own.

Security design
  * passwords are hashed with Argon2id (argon2-cffi, the winner of the Password Hashing Competition); the plain
    password is never stored or logged. Old hashes are upgraded automatically when the settings get stronger.
  * every input is checked (email format and length, name, password strength) and normalised (NFKC, lower-case email)
  * brute force is stopped twice: rate limits per IP address and per email, and an account lockout that grows
    (5 wrong passwords -> 15 min, then 30 min, 1 h ... up to 24 h)
  * login errors never say whether the email exists, and an unknown email costs the same time as a wrong password
  * password reset uses a one-time code sent by email: random, stored only as a hash, valid 15 minutes, 5 tries
  * changing or resetting a password ends every other open session of that account
  * security events (sign-up, login, failed login, lockout, reset, admin actions) go to the auth_events table and
    the app log, with the email and IP address stored only as keyed hashes
  * database address, admin emails and email (SMTP) settings come from Streamlit secrets or environment variables,
    never from the code (see .streamlit/secrets.toml.example)

Storage: any SQLAlchemy database. On the internet use a hosted PostgreSQL database (Neon, Supabase ...), because the
disk of Streamlit Community Cloud is wiped on every restart. Without a database address a local SQLite file
(data/users/jalmitra_users.db, never uploaded to GitHub) is used.
"""

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import smtplib
import ssl
import threading
import time
import unicodedata
import uuid
from email.message import EmailMessage
from pathlib import Path

import sqlalchemy as sa
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

log = logging.getLogger("jalmitra.auth")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)

BASE = Path(__file__).resolve().parent
DEFAULT_DB = BASE / "data" / "users" / "jalmitra_users.db"

# ------------------------------------------------------------------ rules (simple numbers, easy to change)
PASSWORD_MIN = 10
PASSWORD_MAX = 128                 # long enough for pass-phrases, short enough that hashing cannot be abused
NAME_MAX = 60
EMAIL_MAX = 254
LOCK_AFTER = 5                     # wrong passwords in a row before the account is locked
LOCK_FIRST_MIN = 15                # first lock: 15 minutes, doubled each time, at most 24 hours
LOCK_MAX_MIN = 24 * 60
RESET_CODE_MIN = 15                # a reset code is valid this many minutes
RESET_CODE_TRIES = 5
LIMITS = {                         # name: (max events, window in seconds)
    "login_ip": (30, 15 * 60),
    "login_email": (10, 15 * 60),
    "signup_ip": (5, 60 * 60),
    "signup_all": (200, 60 * 60),  # whole site: stops a flood of fake accounts
    "reset_email": (3, 60 * 60),
    "reset_ip": (10, 60 * 60),
}

# The most common passwords (from public breach lists). Any password that contains one of these as its whole
# "core" (letters and digits only, case ignored) is refused.
COMMON = set("""
password passw0rd password1 password12 password123 password1234 iloveyou princess admin administrator welcome
welcome1 welcome123 qwerty qwerty123 qwertyuiop asdfghjkl zxcvbnm 1q2w3e4r 1q2w3e4r5t 1qaz2wsx abc123 abcd1234
letmein monkey dragon football baseball sunshine master shadow superman batman trustno1 starwars whatever
123456789 1234567890 0987654321 1111111111 12345678910 0000000000 9876543210 1234554321 987654321 123123123
india india123 india@123 bharat jaimatadi jaishreeram krishna ganesh hanuman sairam omsairam mahadev
jalmitra jalmitra123 groundwater water12345 changeme secret secret123 test1234 testtest computer internet
""".split())

EMAIL_RE = re.compile(r"^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
                      r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")

_HASHER = PasswordHasher()         # Argon2id, 64 MiB memory, 3 passes, 4 lanes (OWASP-recommended or stronger)
_DUMMY_HASH = _HASHER.hash(secrets.token_urlsafe(16))


class AuthError(Exception):
    """A problem the user should see (the text is always safe to show)."""


# ------------------------------------------------------------------ configuration (secrets / environment)
def _secrets_section():
    try:
        import streamlit as st
        return dict(st.secrets.get("auth", {}))
    except Exception:                                  # noqa: BLE001 - no secrets file, or outside Streamlit
        return {}


def config():
    """Settings from [auth] in .streamlit/secrets.toml (or Streamlit Cloud secrets), else environment variables."""
    s = _secrets_section()
    smtp = dict(s.get("smtp", {}) or {})

    def pick(key, env, default=None):
        v = s.get(key)
        if v in (None, ""):
            v = os.environ.get(env, default)
        return v

    admins = pick("admin_emails", "JALMITRA_ADMIN_EMAILS", "")
    if isinstance(admins, str):
        admins = [a for a in re.split(r"[,\s]+", admins) if a]
    return {
        "database_url": pick("database_url", "JALMITRA_AUTH_DB_URL", ""),
        "secret_key": pick("secret_key", "JALMITRA_AUTH_SECRET", ""),
        "admin_emails": {a.strip().lower() for a in admins},
        "allow_signup": str(pick("allow_signup", "JALMITRA_ALLOW_SIGNUP", "true")).lower() not in ("0", "false", "no",
                                                                                                "off"),
        "idle_minutes": float(pick("session_idle_minutes", "JALMITRA_SESSION_IDLE_MIN", 60)),
        "max_hours": float(pick("session_max_hours", "JALMITRA_SESSION_MAX_HOURS", 12)),
        "smtp": {"host": smtp.get("host") or os.environ.get("JALMITRA_SMTP_HOST", ""),
                 "port": int(smtp.get("port") or os.environ.get("JALMITRA_SMTP_PORT", 587)),
                 "user": smtp.get("user") or os.environ.get("JALMITRA_SMTP_USER", ""),
                 "password": smtp.get("password") or os.environ.get("JALMITRA_SMTP_PASSWORD", ""),
                 "sender": smtp.get("sender") or os.environ.get("JALMITRA_SMTP_SENDER", "")},
    }


def email_enabled():
    c = config()["smtp"]
    return bool(c["host"] and c["sender"])


_KEY = {"value": None}


def _log_key():
    """Key for the hashes of emails and IP addresses in the log (random per run if no secret is set)."""
    if _KEY["value"] is None:
        k = config()["secret_key"]
        _KEY["value"] = k.encode() if k else secrets.token_bytes(32)
    return _KEY["value"]


def _tag(text):
    if not text:
        return None
    return hmac.new(_log_key(), str(text).lower().encode(), hashlib.sha256).hexdigest()[:32]


# ------------------------------------------------------------------ database
META = sa.MetaData()
USERS = sa.Table(
    "jm_users", META,
    sa.Column("id", sa.String(32), primary_key=True),
    sa.Column("email", sa.String(EMAIL_MAX), nullable=False, unique=True),
    sa.Column("name", sa.String(NAME_MAX), nullable=False),
    sa.Column("password_hash", sa.String(255), nullable=False),
    sa.Column("role", sa.String(10), nullable=False, default="user"),
    sa.Column("is_active", sa.Boolean, nullable=False, default=True),
    sa.Column("created_at", sa.Float, nullable=False),
    sa.Column("last_login_at", sa.Float),
    sa.Column("failed_logins", sa.Integer, nullable=False, default=0),
    sa.Column("lock_count", sa.Integer, nullable=False, default=0),
    sa.Column("locked_until", sa.Float, nullable=False, default=0),
    sa.Column("password_changed_at", sa.Float, nullable=False),
)
EVENTS = sa.Table(
    "jm_auth_events", META,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("ts", sa.Float, nullable=False, index=True),
    sa.Column("kind", sa.String(30), nullable=False),
    sa.Column("user_id", sa.String(32)),
    sa.Column("email_tag", sa.String(32)),
    sa.Column("ip_tag", sa.String(32)),
    sa.Column("detail", sa.String(200)),
)
RATE = sa.Table(
    "jm_rate_limits", META,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("bucket", sa.String(80), nullable=False, index=True),
    sa.Column("ts", sa.Float, nullable=False, index=True),
)
RESETS = sa.Table(
    "jm_reset_codes", META,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.String(32), nullable=False, index=True),
    sa.Column("code_hash", sa.String(64), nullable=False),
    sa.Column("expires", sa.Float, nullable=False),
    sa.Column("used", sa.Boolean, nullable=False, default=False),
    sa.Column("tries", sa.Integer, nullable=False, default=0),
)
SESSIONS = sa.Table(
    "jm_sessions", META,
    sa.Column("token_hash", sa.String(64), primary_key=True),
    sa.Column("user_id", sa.String(32), nullable=False, index=True),
    sa.Column("created", sa.Float, nullable=False),
    sa.Column("last_seen", sa.Float, nullable=False),
    sa.Column("expires", sa.Float, nullable=False),
    sa.Column("revoked", sa.Boolean, nullable=False, default=False),
)
CHATS = sa.Table(
    "jm_user_chats", META,
    sa.Column("user_id", sa.String(32), primary_key=True),
    sa.Column("chat_id", sa.String(32), primary_key=True),
    sa.Column("title", sa.String(120)),
    sa.Column("updated", sa.Float, nullable=False, index=True),
    sa.Column("data", sa.Text, nullable=False),
)
SETTINGS = sa.Table(
    "jm_user_settings", META,
    sa.Column("user_id", sa.String(32), primary_key=True),
    sa.Column("data", sa.Text, nullable=False),
)

_ENGINE = {"url": None, "engine": None}
_LOCK = threading.Lock()


def _url():
    url = config()["database_url"]
    if not url:
        DEFAULT_DB.parent.mkdir(parents=True, exist_ok=True)
        return "sqlite:///" + DEFAULT_DB.as_posix()
    if url.startswith("postgres://"):                  # Heroku / Neon style -> SQLAlchemy name
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def engine():
    """The shared database engine (tables are created on first use)."""
    url = _url()
    with _LOCK:
        if _ENGINE["engine"] is None or _ENGINE["url"] != url:
            kw = {"pool_pre_ping": True, "future": True}
            if url.startswith("sqlite"):
                kw["connect_args"] = {"check_same_thread": False, "timeout": 15}
            else:
                kw.update(pool_size=5, max_overflow=5, pool_recycle=300)
            eng = sa.create_engine(url, **kw)
            META.create_all(eng)
            _ENGINE.update(url=url, engine=eng)
    return _ENGINE["engine"]


def reset_engine():
    """Forget the engine (tests use this after changing the database address)."""
    with _LOCK:
        if _ENGINE["engine"] is not None:
            _ENGINE["engine"].dispose()
        _ENGINE.update(url=None, engine=None)
    _KEY["value"] = None


def storage_kind():
    return "sqlite (local file)" if _url().startswith("sqlite") else _url().split(":", 1)[0]


# ------------------------------------------------------------------ events and rate limits
def record(kind, user_id=None, email=None, ip=None, detail=None, conn=None):
    row = {"ts": time.time(), "kind": kind, "user_id": user_id, "email_tag": _tag(email), "ip_tag": _tag(ip),
           "detail": (detail or "")[:200] or None}
    try:
        if conn is not None:
            conn.execute(EVENTS.insert().values(**row))
        else:
            with engine().begin() as c:
                c.execute(EVENTS.insert().values(**row))
    except Exception as e:                             # noqa: BLE001 - logging never breaks a login
        log.warning("could not store auth event %s: %s", kind, type(e).__name__)
    log.info("auth %s user=%s email=%s ip=%s %s", kind, user_id or "-", row["email_tag"] or "-", row["ip_tag"] or "-",
             detail or "")


def _hit(conn, name, key):
    """Count one event in a rate-limit bucket. Returns False when the limit is already reached."""
    if not key:
        return True
    limit, window = LIMITS[name]
    bucket = f"{name}:{_tag(key)}"
    now = time.time()
    conn.execute(RATE.delete().where(RATE.c.ts < now - 24 * 3600))           # tidy old rows
    n = conn.execute(sa.select(sa.func.count()).select_from(RATE)
                     .where(RATE.c.bucket == bucket, RATE.c.ts >= now - window)).scalar_one()
    if n >= limit:
        return False
    conn.execute(RATE.insert().values(bucket=bucket, ts=now))
    return True


TOO_MANY = "Too many attempts. Please wait a few minutes and try again."


# ------------------------------------------------------------------ input checks
def clean_text(text):
    text = unicodedata.normalize("NFKC", text or "")
    return "".join(ch for ch in text if ch.isprintable()).strip()


def normalize_email(email):
    e = clean_text(email).lower()
    if not e or len(e) > EMAIL_MAX or not EMAIL_RE.match(e) or ".." in e or len(e.split("@")[0]) > 64:
        raise AuthError("Please enter a valid email address.")
    return e


def check_name(name):
    n = re.sub(r"\s+", " ", clean_text(name))
    if not n:
        raise AuthError("Please enter your name.")
    if len(n) > NAME_MAX:
        raise AuthError(f"Name is too long (at most {NAME_MAX} characters).")
    if re.search(r"[<>{}\[\]\\/@=;`$]", n):
        raise AuthError("Name can only have letters, spaces, dots, apostrophes and hyphens.")
    return n


def password_problems(password, email="", name=""):
    """Every rule the password breaks (empty list = strong enough). Length beats forced symbols (NIST 800-63B)."""
    p = unicodedata.normalize("NFKC", password or "")
    out = []
    if len(p) < PASSWORD_MIN:
        out.append(f"Use at least {PASSWORD_MIN} characters.")
    if len(p) > PASSWORD_MAX:
        out.append(f"Use at most {PASSWORD_MAX} characters.")
    core = re.sub(r"[^a-z0-9]", "", p.lower())
    if p.lower() in COMMON or core in COMMON or re.sub(r"\d+$", "", core) in COMMON:
        out.append("This password is too common. Choose something harder to guess.")
    if len(set(p)) < 5:
        out.append("Use more different characters.")
    if re.fullmatch(r"\d+", p):
        out.append("Do not use only numbers.")
    local = (email or "").split("@")[0].lower()
    if len(local) >= 4 and local in p.lower():
        out.append("Do not use your email in the password.")
    for part in re.split(r"\s+", (name or "").lower()):
        if len(part) >= 4 and part in p.lower():
            out.append("Do not use your name in the password.")
            break
    if not (re.search(r"[A-Za-z]", p) and re.search(r"[^A-Za-z]", p)) and len(p) < 16:
        out.append("Mix letters with numbers or symbols (or use a longer pass-phrase of 16+ characters).")
    return out


def password_strength(password):
    """0-4 score for the strength bar."""
    p = password or ""
    score = 0
    if len(p) >= PASSWORD_MIN:
        score += 1
    if len(p) >= 14:
        score += 1
    kinds = sum(bool(re.search(r, p)) for r in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]"))
    if kinds >= 3:
        score += 1
    if len(p) >= 18 or (kinds == 4 and len(p) >= 12):
        score += 1
    if password_problems(p):
        score = min(score, 1)
    return score


def _hash(password):
    return _HASHER.hash(unicodedata.normalize("NFKC", password))


def _verify(stored_hash, password):
    try:
        return _HASHER.verify(stored_hash, unicodedata.normalize("NFKC", password or ""))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _public(row):
    """A user row without the password hash."""
    if row is None:
        return None
    d = dict(row._mapping)
    d.pop("password_hash", None)
    return d


# ------------------------------------------------------------------ accounts
def register(email, name, password, ip=None):
    """Create an account. Returns the user (no password hash). Raises AuthError with a friendly message."""
    cfg = config()
    if not cfg["allow_signup"]:
        raise AuthError("New sign-ups are closed at the moment.")
    email = normalize_email(email)
    name = check_name(name)
    problems = password_problems(password, email, name)
    if problems:
        raise AuthError(" ".join(problems))
    with engine().begin() as c:
        allowed = _hit(c, "signup_ip", ip) and _hit(c, "signup_all", "site")
        if not allowed:
            record("signup_limited", email=email, ip=ip, conn=c)
    if not allowed:                                     # raised after the commit, so the attempt is counted
        raise AuthError(TOO_MANY)
    pw_hash = _hash(password)                           # slow on purpose; done outside the transaction
    now = time.time()
    uid = uuid.uuid4().hex
    role = "admin" if email in cfg["admin_emails"] else "user"
    try:
        with engine().begin() as c:
            c.execute(USERS.insert().values(id=uid, email=email, name=name, password_hash=pw_hash, role=role,
                                            is_active=True, created_at=now, failed_logins=0, lock_count=0,
                                            locked_until=0, password_changed_at=now))
            record("signup", user_id=uid, email=email, ip=ip, detail=role, conn=c)
    except sa.exc.IntegrityError:
        raise AuthError("An account with this email already exists. Please log in, or use 'Forgot password'.")
    return get_user(uid)


def get_user(user_id):
    with engine().connect() as c:
        return _public(c.execute(sa.select(USERS).where(USERS.c.id == user_id)).first())


def authenticate(email, password, ip=None):
    """Check email + password. Returns the user. Raises AuthError (never says whether the email exists)."""
    wrong = "Email or password is not correct."
    try:
        email = normalize_email(email)
    except AuthError:
        _verify(_DUMMY_HASH, password)
        raise AuthError(wrong)
    if not password or len(password) > PASSWORD_MAX:
        raise AuthError(wrong)
    with engine().begin() as c:
        allowed = _hit(c, "login_ip", ip) and _hit(c, "login_email", email)
        if not allowed:
            record("login_limited", email=email, ip=ip, conn=c)
        row = c.execute(sa.select(USERS).where(USERS.c.email == email)).first()
    if not allowed:
        _verify(_DUMMY_HASH, password)
        raise AuthError(TOO_MANY)
    now = time.time()
    if row is None:
        _verify(_DUMMY_HASH, password)                  # same work as a real check: no timing hint
        record("login_failed", email=email, ip=ip, detail="unknown email")
        raise AuthError(wrong)
    if row.locked_until and row.locked_until > now:
        mins = max(1, round((row.locked_until - now) / 60))
        record("login_locked", user_id=row.id, email=email, ip=ip)
        raise AuthError(f"This account is locked for about {mins} minutes after too many wrong passwords. "
                        "You can also reset your password.")
    ok = _verify(row.password_hash, password)
    if not ok:
        failed = (row.failed_logins or 0) + 1
        values = {"failed_logins": failed}
        if failed >= LOCK_AFTER:
            lock_min = min(LOCK_MAX_MIN, LOCK_FIRST_MIN * 2 ** (row.lock_count or 0))
            values.update(failed_logins=0, lock_count=(row.lock_count or 0) + 1, locked_until=now + lock_min * 60)
        with engine().begin() as c:
            c.execute(USERS.update().where(USERS.c.id == row.id).values(**values))
            record("lockout" if "locked_until" in values else "login_failed", user_id=row.id, email=email, ip=ip,
                   conn=c)
        if "locked_until" in values:
            raise AuthError(f"Too many wrong passwords. This account is locked for "
                            f"{round((values['locked_until'] - now) / 60)} minutes.")
        raise AuthError(wrong)
    if not row.is_active:
        record("login_disabled", user_id=row.id, email=email, ip=ip)
        raise AuthError("This account is disabled. Please contact the JalMitra team.")
    values = {"failed_logins": 0, "lock_count": 0, "locked_until": 0, "last_login_at": now}
    if _HASHER.check_needs_rehash(row.password_hash):
        values["password_hash"] = _hash(password)
    if email in config()["admin_emails"] and row.role != "admin":
        values["role"] = "admin"
    with engine().begin() as c:
        c.execute(USERS.update().where(USERS.c.id == row.id).values(**values))
        record("login", user_id=row.id, email=email, ip=ip, conn=c)
    return get_user(row.id)


def _set_password(conn, user_id, password):
    revoke_all(user_id, conn=conn)
    conn.execute(USERS.update().where(USERS.c.id == user_id).values(
        password_hash=_hash(password), password_changed_at=time.time(), failed_logins=0, lock_count=0,
        locked_until=0))


def change_password(user_id, old_password, new_password, ip=None, keep_token=None):
    with engine().connect() as c:
        row = c.execute(sa.select(USERS).where(USERS.c.id == user_id)).first()
    if row is None or not _verify(row.password_hash, old_password):
        record("password_change_failed", user_id=user_id, ip=ip)
        raise AuthError("Your current password is not correct.")
    problems = password_problems(new_password, row.email, row.name)
    if problems:
        raise AuthError(" ".join(problems))
    if _verify(row.password_hash, new_password):
        raise AuthError("The new password must be different from the old one.")
    with engine().begin() as c:
        _set_password(c, user_id, new_password)
        record("password_changed", user_id=user_id, ip=ip, conn=c)
    if keep_token:                                       # the other devices are logged out, this one stays
        with engine().begin() as c:
            c.execute(SESSIONS.update().where(SESSIONS.c.token_hash == _token_hash(keep_token))
                      .values(revoked=False, created=time.time() + 2))
    return get_user(user_id)


def delete_account(user_id, password, ip=None):
    with engine().connect() as c:
        row = c.execute(sa.select(USERS).where(USERS.c.id == user_id)).first()
    if row is None or not _verify(row.password_hash, password):
        raise AuthError("Password is not correct.")
    _delete(user_id)
    record("account_deleted", user_id=user_id, ip=ip, detail="by user")


def _delete(user_id):
    with engine().begin() as c:
        for t, col in ((SESSIONS, SESSIONS.c.user_id), (CHATS, CHATS.c.user_id), (SETTINGS, SETTINGS.c.user_id), (RESETS, RESETS.c.user_id),
                       (USERS, USERS.c.id)):
            c.execute(t.delete().where(col == user_id))


# ------------------------------------------------------------------ password reset by email code
def _code_hash(code):
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


def new_reset_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"        # no 0/O, 1/I: easy to type from an email
    return "".join(secrets.choice(alphabet) for _ in range(8))


def request_reset(email, ip=None, send=None):
    """Email a one-time reset code if the account exists. Always behaves the same for the caller.
    send(to, subject, body) can be given by tests; by default the SMTP settings are used."""
    try:
        email = normalize_email(email)
    except AuthError:
        return
    with engine().begin() as c:
        allowed = _hit(c, "reset_ip", ip) and _hit(c, "reset_email", email)
        if not allowed:
            record("reset_limited", email=email, ip=ip, conn=c)
    if not allowed:
        raise AuthError(TOO_MANY)
    with engine().begin() as c:
        row = c.execute(sa.select(USERS).where(USERS.c.email == email)).first()
        if row is None or not row.is_active:
            record("reset_unknown", email=email, ip=ip, conn=c)
            return
        code = new_reset_code()
        c.execute(RESETS.update().where(RESETS.c.user_id == row.id).values(used=True))   # older codes stop working
        c.execute(RESETS.insert().values(user_id=row.id, code_hash=_code_hash(code),
                                         expires=time.time() + RESET_CODE_MIN * 60, used=False, tries=0))
        record("reset_requested", user_id=row.id, email=email, ip=ip, conn=c)
    body = (f"Hello {row.name},\n\nYour JalMitra password reset code is:\n\n    {code}\n\n"
            f"It works for {RESET_CODE_MIN} minutes. If you did not ask for this, you can ignore this email; your "
            "password stays the same.\n\n- JalMitra")
    (send or send_email)(email, "Your JalMitra password reset code", body)


def reset_password(email, code, new_password, ip=None):
    bad = "The code is wrong or has expired. Please ask for a new code."
    email = normalize_email(email)
    with engine().begin() as c:
        row = c.execute(sa.select(USERS).where(USERS.c.email == email)).first()
        rc = None if row is None else c.execute(
            sa.select(RESETS).where(RESETS.c.user_id == row.id, RESETS.c.used.is_(False))
            .order_by(RESETS.c.id.desc())).first()
        if rc is None or rc.expires < time.time() or rc.tries >= RESET_CODE_TRIES:
            good = False
        else:
            good = hmac.compare_digest(rc.code_hash, _code_hash(code or ""))
            if not good:                                # counted and committed before the error is raised
                c.execute(RESETS.update().where(RESETS.c.id == rc.id).values(tries=rc.tries + 1))
                record("reset_bad_code", user_id=row.id, email=email, ip=ip, conn=c)
    if not good:
        raise AuthError(bad)
    problems = password_problems(new_password, row.email, row.name)
    if problems:
        raise AuthError(" ".join(problems))
    with engine().begin() as c:
        c.execute(RESETS.update().where(RESETS.c.user_id == row.id).values(used=True))
        _set_password(c, row.id, new_password)
        record("password_reset", user_id=row.id, email=email, ip=ip, conn=c)
    return get_user(row.id)


def send_email(to, subject, body):
    c = config()["smtp"]
    if not (c["host"] and c["sender"]):
        raise AuthError("Password reset by email is not set up yet. Please ask the JalMitra admin to reset it.")
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = c["sender"], to, subject
    msg.set_content(body)
    ctx = ssl.create_default_context()
    try:
        if c["port"] == 465:
            with smtplib.SMTP_SSL(c["host"], c["port"], context=ctx, timeout=20) as s:
                if c["user"]:
                    s.login(c["user"], c["password"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(c["host"], c["port"], timeout=20) as s:
                s.starttls(context=ctx)
                if c["user"]:
                    s.login(c["user"], c["password"])
                s.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        log.error("email send failed: %s", type(e).__name__)
        raise AuthError("The email could not be sent right now. Please try again later.")



# ------------------------------------------------------------------ login sessions (server side)
# The browser keeps only a random token (256 bits) in a cookie; the database keeps its SHA-256 hash, so a copy of the
# database cannot be used to log in. Sessions end after `idle_minutes` without use, after `max_hours` in total, on
# logout, and when the password is changed or reset or the account is disabled.
def _token_hash(token):
    return hashlib.sha256((token or "").encode()).hexdigest()


def create_session(user_id):
    token = secrets.token_urlsafe(32)
    now = time.time()
    with engine().begin() as c:
        c.execute(SESSIONS.delete().where(SESSIONS.c.expires < now - 7 * 86400))          # tidy old rows
        c.execute(SESSIONS.insert().values(token_hash=_token_hash(token), user_id=user_id, created=now,
                                           last_seen=now, expires=now + config()["max_hours"] * 3600, revoked=False))
    return token


def resume_session(token):
    """The user for a valid session token (and the session's last use is updated), else None."""
    if not isinstance(token, str) or not token or len(token) > 100:
        return None
    th = _token_hash(token)
    now = time.time()
    idle = config()["idle_minutes"] * 60
    with engine().begin() as c:
        srow = c.execute(sa.select(SESSIONS).where(SESSIONS.c.token_hash == th)).first()
        if srow is None or srow.revoked or srow.expires < now or now - srow.last_seen > idle:
            return None
        urow = c.execute(sa.select(USERS).where(USERS.c.id == srow.user_id)).first()
        if urow is None or not urow.is_active or (urow.password_changed_at or 0) > srow.created + 1:
            c.execute(SESSIONS.update().where(SESSIONS.c.token_hash == th).values(revoked=True))
            return None
        c.execute(SESSIONS.update().where(SESSIONS.c.token_hash == th).values(last_seen=now))
    return _public(urow)


def revoke_session(token):
    with engine().begin() as c:
        c.execute(SESSIONS.update().where(SESSIONS.c.token_hash == _token_hash(token)).values(revoked=True))


def revoke_all(user_id, keep_token=None, conn=None):
    q = SESSIONS.update().where(SESSIONS.c.user_id == user_id)
    if keep_token:
        q = q.where(SESSIONS.c.token_hash != _token_hash(keep_token))
    q = q.values(revoked=True)
    if conn is not None:
        conn.execute(q)
    else:
        with engine().begin() as c:
            c.execute(q)


# ------------------------------------------------------------------ admin
def list_users():
    with engine().connect() as c:
        rows = c.execute(sa.select(USERS).order_by(USERS.c.created_at.desc())).fetchall()
    return [_public(r) for r in rows]


def admin_update(admin_id, user_id, action):
    """action: disable | enable | unlock | make_admin | make_user | delete. An admin cannot lock themself out."""
    admin = get_user(admin_id)
    if not admin or admin["role"] != "admin" or not admin["is_active"]:
        raise AuthError("Only an admin can do this.")
    if user_id == admin_id and action in ("disable", "make_user", "delete"):
        raise AuthError("You cannot do this to your own account.")
    values = {"disable": {"is_active": False}, "enable": {"is_active": True},
              "unlock": {"failed_logins": 0, "lock_count": 0, "locked_until": 0},
              "make_admin": {"role": "admin"}, "make_user": {"role": "user"}}
    if action == "delete":
        _delete(user_id)
    elif action == "disable":
        with engine().begin() as c:
            c.execute(USERS.update().where(USERS.c.id == user_id).values(**values[action]))
            revoke_all(user_id, conn=c)
    elif action in values:
        with engine().begin() as c:
            c.execute(USERS.update().where(USERS.c.id == user_id).values(**values[action]))
    else:
        raise AuthError("Unknown action.")
    record("admin_" + action, user_id=user_id, detail=f"by {admin_id}")


def admin_reset_password(admin_id, user_id):
    """Give a user a new random temporary password (shown once to the admin). Ends the user's sessions."""
    admin = get_user(admin_id)
    if not admin or admin["role"] != "admin":
        raise AuthError("Only an admin can do this.")
    temp = "-".join(secrets.token_urlsafe(6) for _ in range(3))
    with engine().begin() as c:
        _set_password(c, user_id, temp)
        record("admin_password_reset", user_id=user_id, detail=f"by {admin_id}", conn=c)
    return temp


def recent_events(limit=200):
    with engine().connect() as c:
        rows = c.execute(sa.select(EVENTS).order_by(EVENTS.c.id.desc()).limit(limit)).fetchall()
    return [dict(r._mapping) for r in rows]


def stats():
    day = time.time() - 86400
    with engine().connect() as c:
        def n(q):
            return c.execute(q).scalar_one()
        cnt = sa.select(sa.func.count())
        return {"users": n(cnt.select_from(USERS)),
                "active_24h": n(cnt.select_from(USERS).where(USERS.c.last_login_at >= day)),
                "signups_24h": n(cnt.select_from(USERS).where(USERS.c.created_at >= day)),
                "failed_24h": n(cnt.select_from(EVENTS).where(EVENTS.c.ts >= day,
                                                              EVENTS.c.kind.in_(["login_failed", "lockout"]))),
                "locked_now": n(cnt.select_from(USERS).where(USERS.c.locked_until > time.time())),
                "chats": n(cnt.select_from(CHATS)),
                "sessions_open": n(cnt.select_from(SESSIONS).where(SESSIONS.c.revoked.is_(False),
                                                                   SESSIONS.c.expires > time.time()))}


# ------------------------------------------------------------------ per-user chats and settings (used by chat_store)
def save_chat(user_id, chat_id, title, updated, data):
    payload = json.dumps(data, ensure_ascii=False)
    with engine().begin() as c:
        exists = c.execute(sa.select(CHATS.c.chat_id).where(CHATS.c.user_id == user_id,
                                                            CHATS.c.chat_id == chat_id)).first()
        values = {"title": (title or "")[:120], "updated": updated, "data": payload}
        if exists:
            c.execute(CHATS.update().where(CHATS.c.user_id == user_id, CHATS.c.chat_id == chat_id).values(**values))
        else:
            c.execute(CHATS.insert().values(user_id=user_id, chat_id=chat_id, **values))


def load_chats(user_id, limit=200):
    with engine().connect() as c:
        rows = c.execute(sa.select(CHATS.c.data).where(CHATS.c.user_id == user_id)
                         .order_by(CHATS.c.updated.desc()).limit(limit)).fetchall()
    out = []
    for r in rows:
        try:
            out.append(json.loads(r.data))
        except ValueError:
            continue
    return out


def get_chat(user_id, chat_id):
    with engine().connect() as c:
        r = c.execute(sa.select(CHATS.c.data).where(CHATS.c.user_id == user_id, CHATS.c.chat_id == chat_id)).first()
    return json.loads(r.data) if r else None


def delete_chat(user_id, chat_id):
    with engine().begin() as c:
        return c.execute(CHATS.delete().where(CHATS.c.user_id == user_id, CHATS.c.chat_id == chat_id)).rowcount > 0


def clear_chats(user_id):
    with engine().begin() as c:
        return c.execute(CHATS.delete().where(CHATS.c.user_id == user_id)).rowcount


def load_user_settings(user_id):
    with engine().connect() as c:
        r = c.execute(sa.select(SETTINGS.c.data).where(SETTINGS.c.user_id == user_id)).first()
    try:
        return json.loads(r.data) if r else {}
    except ValueError:
        return {}


def save_user_settings(user_id, data):
    payload = json.dumps(data, ensure_ascii=False)
    with engine().begin() as c:
        if c.execute(sa.select(SETTINGS.c.user_id).where(SETTINGS.c.user_id == user_id)).first():
            c.execute(SETTINGS.update().where(SETTINGS.c.user_id == user_id).values(data=payload))
        else:
            c.execute(SETTINGS.insert().values(user_id=user_id, data=payload))
