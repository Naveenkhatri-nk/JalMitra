"""
chat_store.py - local chat history and settings for the JalMitra chat (UI redesign, 24 Nov 2026).

Everything stays on this computer as plain JSON files in data/chat_history/ (never inside groundwater.db,
never uploaded):
  * chat_<id>.json   one conversation: title, times, messages (incl. the official data cards shown with each reply)
                     and the conversation context (places discussed), so a reopened chat can continue
  * settings.json    the user's settings: theme (day / night / system), interface and answer language, default
                     location, answer style and length, voice

Folder: JALMITRA_HISTORY_DIR if set; when the app runs inside Streamlit's AppTest (the test suites) and no folder
is set, each test session gets its own temporary folder, so tests never touch the real history or settings.
"""

import atexit
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_DIR = BASE / "data" / "chat_history"
SETTINGS_FILE = "settings.json"
SETTING_KEYS = ["theme", "ui_lang", "answer_lang", "loc_state", "loc_district", "loc_unit", "style", "detail",
                "voice_on", "voice_lang"]
THEMES = ["day", "night", "system"]
_ID = re.compile(r"^[0-9a-f]{6,32}$")
_TEST_DIRS = []


def _cleanup_test_dirs():
    for d in _TEST_DIRS:
        shutil.rmtree(d, ignore_errors=True)


atexit.register(_cleanup_test_dirs)


def base_dir():
    """The folder that holds the history and settings (created on first use)."""
    env = os.environ.get("JALMITRA_HISTORY_DIR")
    if env:
        d = Path(env)
    elif "streamlit.testing.v1" in sys.modules:          # test run: a private folder per AppTest session
        try:
            import streamlit as st
            d = st.session_state.get("_jm_test_store")
            if not d:
                d = tempfile.mkdtemp(prefix="jalmitra_test_history_")
                _TEST_DIRS.append(d)
                st.session_state["_jm_test_store"] = d
            d = Path(d)
        except Exception:                                 # noqa: BLE001 - outside a script run
            d = Path(tempfile.gettempdir()) / "jalmitra_test_history"
    else:
        d = DEFAULT_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------------------------ JSON helpers
def _plain(o):
    """json.dumps default: database rows -> dict, numpy numbers -> Python numbers, sets -> lists, else text."""
    if hasattr(o, "keys") and callable(o.keys):
        try:
            return {k: o[k] for k in o.keys()}
        except Exception:                                 # noqa: BLE001
            pass
    if hasattr(o, "item") and callable(o.item):
        try:
            return o.item()
        except Exception:                                 # noqa: BLE001
            pass
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def _write(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, default=_plain, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def _state_dict(state):
    """The conversation context as JSON-safe values (keys that cannot be stored are left out)."""
    out = {}
    for k, v in (getattr(state, "__dict__", None) or {}).items():
        try:
            json.dumps(v)
            out[k] = v
        except (TypeError, ValueError):
            continue
    return out


def restore_state(saved, new_state):
    """A fresh engine state with the stored context put back (unknown keys ignored)."""
    state = new_state()
    for k, v in (saved or {}).items():
        if hasattr(state, k):
            setattr(state, k, v)
    return state


# ------------------------------------------------------------------ conversations
def _chat_path(cid):
    if not _ID.match(cid or ""):
        raise ValueError(f"bad conversation id: {cid!r}")
    return base_dir() / f"chat_{cid}.json"


def save_conversation(conv):
    """Store one conversation (only finished messages; an answer still being written is skipped)."""
    if not conv.get("messages"):
        return None
    msgs = []
    for m in conv["messages"]:
        if m.get("ai_pending"):
            continue
        msgs.append({k: v for k, v in m.items() if not k.startswith("_")})
    data = {"version": 1, "id": conv["id"], "title": conv.get("title") or "",
            "created": conv.get("created_ts") or time.time(), "updated": conv.get("updated") or time.time(),
            "messages": msgs, "state": _state_dict(conv.get("state"))}
    path = _chat_path(conv["id"])
    _write(path, data)
    return path


def load_conversations():
    """All stored conversations, most recently used first (unreadable files are skipped)."""
    out = []
    for p in base_dir().glob("chat_*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, dict) and _ID.match(d.get("id") or "") and isinstance(d.get("messages"), list):
                out.append(d)
        except (OSError, ValueError):
            continue
    return sorted(out, key=lambda d: d.get("updated") or 0, reverse=True)


def delete_conversation(cid):
    try:
        _chat_path(cid).unlink()
        return True
    except (FileNotFoundError, ValueError):
        return False


def rename_conversation(cid, title):
    p = _chat_path(cid)
    if not p.exists():
        return False
    d = json.loads(p.read_text(encoding="utf-8"))
    d["title"] = (title or "").strip()[:80]
    _write(p, d)
    return True


def clear_conversations():
    """Delete every stored conversation (settings are kept). Returns how many were deleted."""
    n = 0
    for p in base_dir().glob("chat_*.json"):
        try:
            p.unlink()
            n += 1
        except OSError:
            pass
    return n


def group_label(ts, now=None):
    """'Today', 'Yesterday' or 'Earlier' for a time stamp (local time)."""
    now = now or time.time()
    day = time.localtime(ts)[:3]
    if day == time.localtime(now)[:3]:
        return "Today"
    if day == time.localtime(now - 86400)[:3]:
        return "Yesterday"
    return "Earlier"


# ------------------------------------------------------------------ settings
def load_settings():
    """Stored settings (only known keys; a missing or broken file gives {})."""
    try:
        d = json.loads((base_dir() / SETTINGS_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(d, dict):
        return {}
    d = {k: v for k, v in d.items() if k in SETTING_KEYS}
    if d.get("theme") not in THEMES:
        d.pop("theme", None)
    return d


def save_settings(values):
    """Merge `values` (known keys only) into the settings file."""
    d = load_settings()
    d.update({k: v for k, v in values.items() if k in SETTING_KEYS})
    _write(base_dir() / SETTINGS_FILE, d)
    return d
