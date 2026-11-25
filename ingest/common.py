"""
ingest/common.py - shared helpers for the JalMitra 4.0 groundwater monitoring ingest.

Standard library only, so the download scripts run with any Python 3.9+ on Windows or Linux.

Safety rules enforced here:
  * nothing under data/groundwater.db is ever opened for writing,
  * write_new() never overwrites an existing file (originals are preserved),
  * every network request is logged with its outcome.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # project root (E:\JalMitra)
DATA = ROOT / "data"
MON = DATA / "monitoring"                                # everything new lives here
RAW = MON / "raw"
CATALOG = MON / "catalog"
EXTRACTED = MON / "extracted"
REPORTS = MON / "reports"
SCRATCH = MON / "scratch"
LOGS = MON / "logs"
EXISTING_DB = DATA / "groundwater.db"                    # read-only, never modified
MONITORING_DB = DATA / "groundwater_monitoring.db"

USER_AGENT = "JalMitra-groundwater-ingest/1.0 (non-commercial research; python-urllib)"

_lock = threading.Lock()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_dirs() -> None:
    for d in (MON, RAW, CATALOG, EXTRACTED, REPORTS, SCRATCH, LOGS):
        d.mkdir(parents=True, exist_ok=True)


def slug(s: str, n: int = 60) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", (s or "").strip()).strip("_").lower()
    return s[:n] or "x"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_new(path: Path, data: bytes) -> bool:
    """Write data to path only if path does not exist. Returns True if written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    tmp = path.with_name(path.name + ".part")
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)          # atomic; path did not exist
    return True


def write_json_gz_new(path: Path, obj) -> bool:
    return write_new(path, gzip.compress(json.dumps(obj, ensure_ascii=False).encode("utf-8")))


def read_json_gz(path: Path):
    with gzip.open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def append_csv(path: Path, row: dict, fields: list[str]) -> None:
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        new = not path.exists()
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if new:
                w.writeheader()
            w.writerow(row)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def http(url: str, method: str = "GET", params: dict | None = None, timeout: int = 90,
         retries: int = 3, backoff: float = 4.0, accept: str = "*/*") -> tuple[int, dict, bytes]:
    """Plain HTTP(S) request with retries on network errors and 5xx. Returns (status, headers, body)."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT, "Accept": accept})
        if method == "POST":
            req.data = b""
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, "read") else b""
            if e.code < 500 or attempt == retries:
                return e.code, dict(e.headers or {}), body
            last = e
        except Exception as e:  # timeouts, resets
            last = e
            if attempt == retries:
                raise
        time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"unreachable: {last}")


def assert_existing_db_untouched(expected_sha: str) -> str:
    got = sha256_file(EXISTING_DB)
    if got != expected_sha:
        raise SystemExit(f"STOP: data/groundwater.db SHA256 changed: {got} != {expected_sha}")
    return got


EXPECTED_EXISTING_DB_SHA256 = "9eeaee1533b478c1e649b86a56b56f4415e5255e0a3311e37a466f20bdeaa46a"
