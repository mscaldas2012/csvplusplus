"""
csvpp.pprint — pretty-printer for parsed CSV++ records.

Usage:
    import csvpp

    records = csvpp.parse_file("orders.csvpp")
    csvpp.pprint(records)           # all records
    csvpp.pprint(records, top=5)    # first 5 only
    csvpp.pprint(records, color=False)  # plain text (no ANSI)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, TextIO


# ---------------------------------------------------------------------------
# ANSI colour palette
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Palette:
    RESET:   str = ""
    BOLD:    str = ""
    DIM:     str = ""
    CYAN:    str = ""
    YELLOW:  str = ""
    GREEN:   str = ""
    MAGENTA: str = ""
    BLUE:    str = ""


_ANSI = _Palette(
    RESET="\033[0m",
    BOLD="\033[1m",
    DIM="\033[2m",
    CYAN="\033[36m",
    YELLOW="\033[33m",
    GREEN="\033[32m",
    MAGENTA="\033[35m",
    BLUE="\033[34m",
)

_PLAIN = _Palette()   # all fields are empty strings → no ANSI


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def pprint(
    records: list[dict[str, Any]],
    top: int | None = None,
    *,
    file: TextIO | None = None,
    color: bool | None = None,
) -> None:
    """Pretty-print a list of parsed CSV++ records.

    Args:
        records: Output of ``csvpp.parse()`` or ``csvpp.parse_file()``.
        top:     Maximum number of records to display.  ``None`` = all.
        file:    Output stream (default: ``sys.stdout``).
        color:   Force ANSI colours on (``True``) or off (``False``).
                 ``None`` (default) auto-detects from the stream's TTY state.

    Example::

        records = csvpp.parse_file("orders.csvpp")
        csvpp.pprint(records, top=10)
    """
    out = file if file is not None else sys.stdout

    if color is None:
        color = getattr(out, "isatty", lambda: False)()
    c = _ANSI if color else _PLAIN

    total = len(records)
    shown = records[:top] if top is not None else records
    n_shown = len(shown)

    if total == 0:
        print(f"{c.DIM}(no records){c.RESET}", file=out)
        return

    # Widest field name across all shown records (sets the key column width)
    all_keys: list[str] = []
    for rec in shown:
        all_keys.extend(rec.keys())
    key_w = max((len(k) for k in all_keys), default=6)

    for i, record in enumerate(shown, start=1):
        _print_record(record, i, total, key_w, c, out)
        if i < n_shown:
            print(file=out)   # blank line between records

    if top is not None and n_shown < total:
        omitted = total - n_shown
        print(
            f"\n{c.DIM}Showing {n_shown} of {total} records "
            f"({omitted} omitted). Pass top={total} to see all.{c.RESET}",
            file=out,
        )


# ---------------------------------------------------------------------------
# Record-level rendering
# ---------------------------------------------------------------------------

def _print_record(
    record: dict[str, Any],
    index: int,
    total: int,
    key_w: int,
    c: _Palette,
    out: TextIO,
) -> None:
    label = f" Record {index}/{total} "
    inner_width = max(60, key_w + 4)
    bar = "─" * (inner_width - len(label))

    print(f"{c.BOLD}{c.CYAN}┌{label}{bar}┐{c.RESET}", file=out)

    for key, value in record.items():
        val_lines = _render_value(value, c)
        key_str = f"{c.BOLD}{key:<{key_w}}{c.RESET}"
        # First line: key  value
        print(f"{c.CYAN}│{c.RESET} {key_str}  {val_lines[0]}", file=out)
        # Continuation lines: aligned past the key column
        pad = " " * key_w
        for vl in val_lines[1:]:
            print(f"{c.CYAN}│{c.RESET} {pad}  {vl}", file=out)

    print(f"{c.BOLD}{c.CYAN}└{'─' * (len(label) + len(bar))}┘{c.RESET}", file=out)


# ---------------------------------------------------------------------------
# Recursive value renderer
# ---------------------------------------------------------------------------

def _render_value(value: Any, c: _Palette) -> list[str]:
    """Return a list of display lines for *value*.

    The first line is placed on the same line as the field key.
    Subsequent lines are continuations, already indented relative to the
    first.
    """
    if value is None:
        return [f"{c.DIM}(none){c.RESET}"]

    if isinstance(value, str):
        if value == "":
            return [f"{c.DIM}(empty){c.RESET}"]
        return [f"{c.GREEN}{value}{c.RESET}"]

    if isinstance(value, list):
        return _render_list(value, c)

    if isinstance(value, dict):
        return _render_struct(value, c)

    # Fallback for unexpected types
    return [repr(value)]


def _render_list(items: list[Any], c: _Palette) -> list[str]:
    if not items:
        return [f"{c.DIM}[]{c.RESET}"]

    # --- Array of plain strings ---
    if all(isinstance(v, str) for v in items):
        inline = ", ".join(f'"{v}"' if "," in v or not v else v for v in items)
        if len(inline) <= 45:
            return [f"{c.YELLOW}[{c.RESET}{inline}{c.YELLOW}]{c.RESET}"]
        # Too long → one item per line
        lines: list[str] = []
        for idx, item in enumerate(items):
            prefix = f"{c.DIM}[{idx}]{c.RESET} "
            lines.append(f"{prefix}{c.GREEN}{item}{c.RESET}")
        return lines

    # --- Array of structs (or mixed) ---
    lines = []
    for idx, item in enumerate(items):
        idx_str = f"{c.DIM}[{idx}]{c.RESET} "
        item_lines = _render_value(item, c)
        lines.append(f"{idx_str}{item_lines[0]}")
        # Continuation: indent to align past "[idx] "
        pad = " " * (len(f"[{idx}] "))
        for il in item_lines[1:]:
            lines.append(f"{pad}{il}")

    return lines


def _render_struct(struct: dict[str, Any], c: _Palette) -> list[str]:
    if not struct:
        return [f"{c.DIM}{{}}{c.RESET}"]

    sub_key_w = max(len(k) for k in struct)
    lines: list[str] = []

    for key, value in struct.items():
        key_str = f"{c.MAGENTA}{key:<{sub_key_w}}{c.RESET}"
        val_lines = _render_value(value, c)
        lines.append(f"{key_str}  {val_lines[0]}")
        pad = " " * sub_key_w
        for vl in val_lines[1:]:
            lines.append(f"{pad}  {vl}")

    return lines
