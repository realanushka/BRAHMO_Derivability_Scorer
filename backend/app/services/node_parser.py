"""
Node Parser — Parses uploaded node files (CSV or SQL) into plain dicts.

Supports two formats:
  - CSV: header row maps to knowledge_nodes columns (Excel/Sheets export).
  - SQL: INSERT INTO knowledge_nodes (...) VALUES (...), (...);  statements
         like ASSESSMENT_08_SETUP_GUIDE.md / seed.sql.

IMPORTANT: For SQL, we do NOT execute the uploaded SQL. We only read the
column list and VALUES tuples, so an uploaded file can never run arbitrary
statements against the database.
"""

from __future__ import annotations

import csv
import io
import re


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def parse_csv(text: str) -> list[dict]:
    """Parse CSV text into a list of raw node dicts (values as strings/None)."""
    reader = csv.DictReader(io.StringIO(text))
    nodes: list[dict] = []
    for row in reader:
        clean: dict = {}
        for key, value in row.items():
            if key is None:
                continue
            k = key.strip()
            if isinstance(value, str):
                v = value.strip()
                clean[k] = v if v != "" else None
            else:
                clean[k] = value
        # Skip fully-empty rows
        if any(v is not None for v in clean.values()):
            nodes.append(clean)
    return nodes


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+knowledge_nodes\s*\(([^)]*)\)\s*VALUES\s*(.*?);",
    re.IGNORECASE | re.DOTALL,
)

_UPDATE_RE = re.compile(
    r"UPDATE\s+knowledge_nodes\s+SET\s+non_derivable_portion\s*=\s*"
    r"('(?:[^']|'')*')\s+WHERE\s+id\s*=\s*('(?:[^']|'')*')\s*;",
    re.IGNORECASE | re.DOTALL,
)


def parse_sql(text: str) -> list[dict]:
    """
    Parse INSERT INTO knowledge_nodes statements into raw node dicts.
    Also applies any `UPDATE ... SET non_derivable_portion ...` statements.
    Tuple order is preserved; later inserts for the same id overwrite earlier.
    """
    nodes_by_id: dict[str, dict] = {}
    order: list[str] = []

    for match in _INSERT_RE.finditer(text):
        columns = [c.strip().strip('"').strip("`") for c in match.group(1).split(",")]
        for tup in _extract_tuples(match.group(2)):
            values = _split_tuple(tup)
            if len(values) != len(columns):
                continue  # malformed row — skip rather than guess
            row = {col: _coerce(val) for col, val in zip(columns, values)}
            node_id = row.get("id")
            key = node_id if node_id is not None else f"__noid_{len(order)}"
            if key not in nodes_by_id:
                order.append(key)
            nodes_by_id[key] = row

    # Apply UPDATE ... SET non_derivable_portion = '...' WHERE id = '...'
    for match in _UPDATE_RE.finditer(text):
        portion = _unquote(match.group(1))
        target_id = _unquote(match.group(2))
        for row in nodes_by_id.values():
            if row.get("id") == target_id:
                row["non_derivable_portion"] = portion

    return [nodes_by_id[k] for k in order]


def _extract_tuples(s: str) -> list[str]:
    """
    Extract top-level (...) groups from a VALUES region, skipping SQL line
    comments (-- ...) and respecting single-quoted string literals.
    """
    tuples: list[str] = []
    current: list[str] = []
    depth = 0
    in_str = False
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if in_str:
            current.append(c)
            if c == "'":
                if i + 1 < n and s[i + 1] == "'":  # escaped ''
                    current.append("'")
                    i += 2
                    continue
                in_str = False
            i += 1
            continue
        if c == "-" and i + 1 < n and s[i + 1] == "-":  # line comment
            nl = s.find("\n", i)
            if nl == -1:
                break
            i = nl + 1
            continue
        if c == "'":
            in_str = True
            current.append(c)
        elif c == "(":
            if depth == 0:
                current = []
            else:
                current.append(c)
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                tuples.append("".join(current))
                current = []
            else:
                current.append(c)
        elif depth > 0:
            current.append(c)
        i += 1
    return tuples


def _split_tuple(s: str) -> list[str]:
    """Split one tuple's body by top-level commas, respecting strings/parens."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_str = False
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if in_str:
            current.append(c)
            if c == "'":
                if i + 1 < n and s[i + 1] == "'":
                    current.append("'")
                    i += 2
                    continue
                in_str = False
            i += 1
            continue
        if c == "'":
            in_str = True
            current.append(c)
        elif c == "(":
            depth += 1
            current.append(c)
        elif c == ")":
            depth -= 1
            current.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(c)
        i += 1
    if current:
        parts.append("".join(current).strip())
    return parts


def _coerce(raw: str):
    """Convert a raw SQL token into a Python value."""
    raw = raw.strip()
    if raw == "" or raw.upper() == "NULL":
        return None
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    try:
        return float(raw) if "." in raw else int(raw)
    except ValueError:
        return raw


def _unquote(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    return raw
