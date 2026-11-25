"""
soil_card.py - Read a Soil Health Card or soil lab report that the user uploads
(PDF with a text layer, CSV or Excel) and turn it into rows for the user to REVIEW.

Nothing extracted here is trusted: the app shows every row in an editable table,
and only rows the user confirms are explained. Scanned PDFs (no text layer) are not
OCR'd: JalMitra asks the user to type the values instead.

Uploads stay in the user's session. They are saved to disk only if the user presses
"Save on this computer" (user_data/, outside the repository), and can be deleted.
Nothing is sent to any external service.
"""

import csv
import hashlib
import io
import json
import re
import time
import uuid
from pathlib import Path

import knowledge as kn

MAX_BYTES = 5 * 1024 * 1024
ALLOWED = {".pdf": "pdf", ".csv": "csv", ".xlsx": "xlsx"}
USER_DIR = Path(__file__).resolve().parent / "user_data" / "soil_reports"

# Words used on cards and lab reports for the 12 Soil Health Card parameters (longest first when matching)
PARAM_WORDS = {
    "N": ["available nitrogen", "nitrogen", "avail. n", "n (kg/ha)"],
    "P": ["available phosphorus", "phosphorus", "phosphorous", "p2o5", "avail. p"],
    "K": ["available potassium", "potassium", "potash", "k2o", "avail. k"],
    "S": ["available sulphur", "sulphur", "sulfur"],
    "Zn": ["zinc"],
    "Fe": ["iron"],
    "Cu": ["copper"],
    "Mn": ["manganese"],
    "B": ["boron"],
    "pH": ["ph", "soil reaction"],
    "EC": ["electrical conductivity", "ec"],
    "OC": ["organic carbon", "oc"],
}
DEFAULT_UNIT = {"N": "kg/ha", "P": "kg/ha", "K": "kg/ha", "S": "ppm", "Zn": "ppm", "Fe": "ppm", "Cu": "ppm",
                "Mn": "ppm", "B": "ppm", "pH": "pH", "EC": "dS/m", "OC": "%"}
UNIT_RE = r"(kg\s*/\s*ha|kg ha-1|ppm|mg\s*/\s*kg|ds\s*/\s*m|mmhos\s*/\s*cm|ms\s*/\s*cm|%)"


class UploadError(ValueError):
    pass


# ------------------------------------------------------------------ validation

def validate_upload(name, data):
    """Check name, size and content type. Returns the kind ('pdf', 'csv', 'xlsx') or raises UploadError."""
    ext = Path(name or "").suffix.lower()
    if ext not in ALLOWED:
        raise UploadError("Only PDF, CSV or Excel (.xlsx) files are accepted.")
    if not data:
        raise UploadError("The file is empty.")
    if len(data) > MAX_BYTES:
        raise UploadError("The file is larger than 5 MB.")
    kind = ALLOWED[ext]
    if kind == "pdf" and not data[:5] == b"%PDF-":
        raise UploadError("This file does not look like a PDF.")
    if kind == "xlsx" and not data[:2] == b"PK":
        raise UploadError("This file does not look like an Excel .xlsx file.")
    if kind == "csv":
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise UploadError("The CSV file is not UTF-8 text.")
        if b"\x00" in data[:4096]:
            raise UploadError("The CSV file contains binary data.")
    return kind


# ------------------------------------------------------------------ extraction

def _row(parameter, value, unit, raw, how):
    return {"parameter": parameter, "value": value, "unit": unit or DEFAULT_UNIT.get(parameter, ""),
            "card_rating": "", "raw_text": raw[:120], "extracted_by": how, "confirmed": False}


def _match_param(label):
    t = " " + re.sub(r"[^a-z0-9%/ .()]", " ", label.lower()) + " "
    for pid, words in PARAM_WORDS.items():
        for w in sorted(words, key=len, reverse=True):
            if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", t):
                return pid
    return None


def _num(text):
    m = re.search(r"-?\d+(?:\.\d+)?", str(text).replace(",", ""))
    return float(m.group()) if m else None


def extract_table(records):
    """Rows from CSV/Excel. Accepts long form (parameter, value, unit[, rating]) or wide form (one column per parameter)."""
    rows = []
    if not records:
        return rows
    cols = {c.lower().strip(): c for c in records[0].keys() if c}
    if "parameter" in cols and "value" in cols:
        for r in records:
            pid = _match_param(str(r.get(cols["parameter"]) or ""))
            v = _num(r.get(cols["value"]))
            if pid and v is not None:
                row = _row(pid, v, str(r.get(cols.get("unit", ""), "") or "").strip(), str(r), "table")
                if "rating" in cols:
                    row["card_rating"] = str(r.get(cols["rating"]) or "")
                rows.append(row)
        return rows
    first = records[0]
    for col, val in first.items():
        pid = _match_param(col or "")
        v = _num(val) if val not in (None, "") else None
        if pid and v is not None:
            unit = re.search(UNIT_RE, (col or "").lower())
            rows.append(_row(pid, v, unit.group(1).replace(" ", "") if unit else "", f"{col}={val}", "table"))
    return rows


def extract_pdf_text(text):
    """Find '<parameter> ... <number> [unit]' on each line of a text-layer PDF."""
    rows, seen = [], set()
    for line in text.splitlines():
        pid = _match_param(line)
        if not pid or pid in seen:
            continue
        label_end = 0
        for w in sorted(PARAM_WORDS[pid], key=len, reverse=True):
            m = re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", line.lower())
            if m:
                label_end = m.end()
                break
        rest = line[label_end:]
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*" + UNIT_RE + "?", rest.lower())
        if not m:
            continue
        unit = (m.group(2) or "").replace(" ", "")
        if pid == "P" and "p2o5" in line.lower():
            unit = "kg P2O5/ha"
        if pid == "K" and "k2o" in line.lower():
            unit = "kg K2O/ha"
        rows.append(_row(pid, float(m.group(1)), unit, line.strip(), "pdf text"))
        seen.add(pid)
    return rows


def extract(name, data):
    """Return {"kind", "rows", "message", "sha256"} for an upload. Raises UploadError for invalid files."""
    kind = validate_upload(name, data)
    digest = hashlib.sha256(data).hexdigest()
    if kind == "csv":
        records = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        rows = extract_table(records)
    elif kind == "xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.worksheets[0]
        it = ws.iter_rows(values_only=True)
        header = [str(h) if h is not None else "" for h in next(it, [])]
        records = [dict(zip(header, r)) for r in it]
        wb.close()
        rows = extract_table(records)
    else:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            if len(pdf.pages) > 20:
                raise UploadError("The PDF has more than 20 pages; please upload only the soil report.")
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        if len(text.strip()) < 20:
            return {"kind": kind, "rows": [], "sha256": digest, "message": "scanned"}
        rows = extract_pdf_text(text)
    return {"kind": kind, "rows": rows, "sha256": digest, "message": "ok" if rows else "nothing_found"}


def blank_rows():
    """The 12 Soil Health Card parameters with empty values, for typing values by hand."""
    return [_row(p, None, DEFAULT_UNIT[p], "", "typed") for p in kn.SOIL_HEALTH_PARAMETERS]


# ------------------------------------------------------------------ private storage (user's own computer only)

def new_report(rows, meta):
    return {"report_id": uuid.uuid4().hex[:12], "created": time.strftime("%Y-%m-%d %H:%M"),
            "meta": dict(meta), "rows": [dict(r) for r in rows]}


def save_local(report):
    USER_DIR.mkdir(parents=True, exist_ok=True)
    path = USER_DIR / f"{report['report_id']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def list_local():
    if not USER_DIR.exists():
        return []
    out = []
    for p in sorted(USER_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out


def delete_local(report_id):
    if not re.fullmatch(r"[0-9a-f]{12}", report_id or ""):
        return False
    path = USER_DIR / f"{report_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
