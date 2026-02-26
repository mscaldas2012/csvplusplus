"""
CSV++ main parser.

Two-phase parsing per Section 8 of the spec:
  1. Header row — parse column declarations into Field schemas.
  2. Data rows — for each field in each row, decode the raw CSV string
     into the appropriate Python value per the schema.

Public API:
    parse(text)       — parse a CSV++ string, return list[dict]
    parse_file(path)  — parse a CSV++ file, return list[dict]
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from .header_parser import parse_header_row
from .models import Field, SimpleField, CSVPPError
from .value_parser import parse_value


def parse(text: str, field_sep: str = ",") -> list[dict[str, Any]]:
    """Parse a CSV++ document string.

    Args:
        text: Full CSV++ document content.
        field_sep: Field separator character (default: comma).

    Returns:
        List of record dicts.  Values are:
            str          for simple fields
            list         for array fields
            dict         for struct fields
            list[dict]   for array-of-struct fields

    Raises:
        CSVPPError and subclasses on malformed input.
    """
    reader = _make_reader(text, field_sep)

    # Phase 1: header row
    try:
        raw_headers = next(reader)
    except StopIteration:
        raise CSVPPError("CSV++ document is empty — header row is required.")

    schemas: list[Field] = parse_header_row(raw_headers)

    # Phase 2: data rows
    records: list[dict[str, Any]] = []
    for row_num, (raw_row, quoted_row) in enumerate(
        _iter_rows_with_quoting(text, field_sep), start=2
    ):
        if len(raw_row) == 0:
            continue  # skip blank lines

        record: dict[str, Any] = {}
        for col_idx, schema in enumerate(schemas):
            if col_idx < len(raw_row):
                raw_val = raw_row[col_idx]
                was_quoted = quoted_row[col_idx]
            else:
                raw_val = ""
                was_quoted = False

            record[schema.name] = parse_value(raw_val, schema,
                                              was_quoted=was_quoted)
        records.append(record)

    return records


def parse_file(path: str | Path, field_sep: str = ",") -> list[dict[str, Any]]:
    """Parse a CSV++ file.

    Args:
        path: Path to the file.
        field_sep: Field separator character (default: comma).

    Returns:
        List of record dicts (same structure as parse()).
    """
    text = Path(path).read_text(encoding="utf-8-sig")  # handle optional BOM
    return parse(text, field_sep=field_sep)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_reader(text: str, field_sep: str) -> csv.reader:
    """Return a csv.reader over the text for the header row only."""
    return csv.reader(io.StringIO(text), delimiter=field_sep)


def _iter_rows_with_quoting(
    text: str,
    field_sep: str,
) -> list[tuple[list[str], list[bool]]]:
    """Parse all rows, returning (values, was_quoted) per field.

    We need to know whether each CSV field was enclosed in double-quotes
    so we can reject invalid non-leaf quoting.  Python's csv.reader strips
    the quotes without exposing that information, so we implement our own
    RFC 4180 row parser here.

    Skips the first (header) row.
    """
    rows = []
    lines = _split_csv_lines(text)
    if not lines:
        return rows

    # Skip header
    for line in lines[1:]:
        if line.strip() == "":
            continue
        fields, quoted_flags = _parse_csv_row(line, field_sep)
        rows.append((fields, quoted_flags))
    return rows


def _split_csv_lines(text: str) -> list[str]:
    """Split CSV text into logical lines, respecting quoted newlines."""
    lines: list[str] = []
    current: list[str] = []
    in_quotes = False
    i = 0

    while i < len(text):
        ch = text[i]
        if ch == '"':
            if in_quotes and i + 1 < len(text) and text[i + 1] == '"':
                current.append('"')
                i += 2
                continue
            in_quotes = not in_quotes
            current.append(ch)
        elif ch == '\r' and not in_quotes:
            if i + 1 < len(text) and text[i + 1] == '\n':
                i += 1
            lines.append("".join(current))
            current = []
        elif ch == '\n' and not in_quotes:
            lines.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1

    if current:
        lines.append("".join(current))

    return lines


def _parse_csv_row(
    line: str,
    field_sep: str,
) -> tuple[list[str], list[bool]]:
    """Parse one CSV line into (values, was_quoted) per RFC 4180.

    This is deliberately simple: a field either starts with '"' (quoted)
    or it doesn't (unquoted).  We track the was_quoted flag for each field.
    """
    values: list[str] = []
    quoted_flags: list[bool] = []

    current: list[str] = []
    was_quoted = False
    in_quotes = False
    i = 0

    while i < len(line):
        ch = line[i]

        if in_quotes:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    current.append('"')
                    i += 2
                else:
                    in_quotes = False
                    i += 1
            else:
                current.append(ch)
                i += 1
        else:
            if ch == '"' and not current:
                in_quotes = True
                was_quoted = True
                i += 1
            elif ch == field_sep:
                values.append("".join(current))
                quoted_flags.append(was_quoted)
                current = []
                was_quoted = False
                i += 1
            else:
                current.append(ch)
                i += 1

    values.append("".join(current))
    quoted_flags.append(was_quoted)
    return values, quoted_flags
