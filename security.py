"""
security.py - Safety checks for JalMitra.

Every SQL query that Gemini writes is checked here BEFORE it touches the
database. Only ONE read-only SELECT query on the groundwater table is allowed.

This is the first lock. The second lock is in database.py, which opens the
database file in read-only mode and blocks any write at the SQLite level.
"""

import re

# The only tables the chatbot is allowed to read.
ALLOWED_TABLES = {"groundwater"}

# Longest question we accept from the user (keeps prompts short and cheap).
MAX_QUESTION_LENGTH = 500

# Longest SQL query we accept from Gemini.
MAX_SQL_LENGTH = 2000

# Words that must never appear in a query (whole words, any case).
BANNED_WORDS = [
    "insert", "update", "delete", "drop", "alter", "create", "replace",
    "attach", "detach", "pragma", "vacuum", "reindex", "analyze", "begin",
    "commit", "rollback", "savepoint", "release", "truncate", "grant",
    "load_extension", "readfile", "writefile", "sqlite_master",
    "sqlite_schema", "sqlite_temp_master", "data_imports",
]

# Symbols used to hide extra commands or comments.
BANNED_SYMBOLS = [";", "--", "/*", "*/"]


class UnsafeQueryError(Exception):
    """Raised when a query is not a safe, read-only SELECT."""


def clean_sql(raw_text):
    """Remove markdown code fences and extra spaces that Gemini may add."""
    if raw_text is None:
        return ""
    text = raw_text.strip()
    text = re.sub(r"^```(?:sql|sqlite)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    # One trailing semicolon is normal; remove it. Any other ";" is rejected later.
    if text.endswith(";"):
        text = text[:-1].rstrip()
    return text


def _strip_string_literals(sql):
    """Replace text inside quotes with empty quotes, so a place name like
    'Drop Block' is not mistaken for the DROP command."""
    sql = re.sub(r"'(?:[^']|'')*'", "''", sql)
    sql = re.sub(r'"(?:[^"]|"")*"', '""', sql)
    return sql


def validate_sql(sql):
    """Check a query and return it if it is safe.

    Raises UnsafeQueryError with a simple reason if it is not safe.
    """
    if not sql or not sql.strip():
        raise UnsafeQueryError("The query is empty.")
    if len(sql) > MAX_SQL_LENGTH:
        raise UnsafeQueryError("The query is too long.")

    # Unbalanced quotes could hide commands; reject them.
    if sql.count("'") % 2 != 0:
        raise UnsafeQueryError("The query has an unclosed quote.")

    code_only = _strip_string_literals(sql)
    lowered = code_only.lower()

    if not (lowered.lstrip().startswith("select") or lowered.lstrip().startswith("with")):
        raise UnsafeQueryError("Only SELECT queries are allowed.")

    for symbol in BANNED_SYMBOLS:
        if symbol in code_only:
            raise UnsafeQueryError(f"The symbol {symbol!r} is not allowed.")

    for word in BANNED_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            raise UnsafeQueryError(f"The word {word.upper()!r} is not allowed.")

    # Every table after FROM or JOIN must be on the allowed list.
    # (Names defined inside a WITH clause are also accepted.)
    cte_names = set(re.findall(r"\b([a-z_][a-z0-9_]*)\s+as\s*\(", lowered))
    tables = re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_\.]*)", lowered)
    if not tables:
        raise UnsafeQueryError("The query does not read from any table.")
    for table in tables:
        if table not in ALLOWED_TABLES and table not in cte_names:
            raise UnsafeQueryError(f"Reading table {table!r} is not allowed.")

    return sql


def is_safe(sql):
    """True if the query passes validate_sql, otherwise False."""
    try:
        validate_sql(sql)
        return True
    except UnsafeQueryError:
        return False


def clean_question(question):
    """Tidy the user's question and check its length.

    Returns the cleaned question, or raises ValueError with a simple reason.
    """
    if question is None:
        raise ValueError("Please type a question.")
    # Remove invisible control characters but keep normal letters of every script.
    text = "".join(ch for ch in question if ch.isprintable() or ch in "\n\t")
    text = text.strip()
    if not text:
        raise ValueError("Please type a question.")
    if len(text) > MAX_QUESTION_LENGTH:
        raise ValueError(
            f"Your question is too long. Please keep it under {MAX_QUESTION_LENGTH} characters."
        )
    return text
