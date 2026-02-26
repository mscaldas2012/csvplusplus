"""
CSV++ header parser.

Converts a column header string (e.g. "address[~]^(street^city^state^zip)")
into a typed Field model.

Grammar (from Appendix A of draft-mscaldas-csvpp-02):

    field          = simple-field / array-field /
                     struct-field / array-struct-field
    simple-field   = name
    array-field    = name "[" [delimiter] "]"
    struct-field   = name [component-delim] "(" component-list ")"
    array-struct-field = name "[" [delimiter] "]"
                         [component-delim] "(" component-list ")"

    component-list = component *(component-delim component)
    component      = simple-field / array-field /
                     struct-field / array-struct-field

    name           = 1*field-char
    field-char     = ALPHA / DIGIT / "_" / "-"
"""

from __future__ import annotations

import re
import warnings
from typing import Optional

from .models import (
    Field, SimpleField, ArrayField, StructField,
    HeaderParseError, DelimiterConflictError, NestingDepthWarning,
)

# Valid name characters per the ABNF
_NAME_RE = re.compile(r'^[A-Za-z0-9_\-]+')

# Default delimiters
_DEFAULT_ARRAY_DELIM = "~"
_DEFAULT_COMP_DELIM = "^"

# Warn above this nesting depth
_NESTING_WARN_DEPTH = 4


def parse_field(header: str) -> Field:
    """Parse a single CSV++ column header string into a Field model.

    Args:
        header: The raw header string, e.g. "phone[]" or
                "items[~]^(sku^name^qty^price^opts[;]:(k:v))".

    Returns:
        A SimpleField, ArrayField, or StructField.

    Raises:
        HeaderParseError: If the header is syntactically invalid.
        DelimiterConflictError: If the same delimiter is reused at
            multiple nesting levels.
    """
    field_obj, consumed = _parse_field(
        header,
        pos=0,
        depth=0,
        used_delimiters=frozenset(),
    )
    if consumed != len(header):
        raise HeaderParseError(
            f"Unexpected characters after field declaration: "
            f"{header[consumed:]!r} in {header!r}"
        )
    return field_obj


def parse_header_row(headers: list[str]) -> list[Field]:
    """Parse a list of raw column header strings.

    Args:
        headers: List of header strings from the CSV header row.

    Returns:
        List of Field objects in the same order.
    """
    return [parse_field(h.strip()) for h in headers]


# ---------------------------------------------------------------------------
# Internal implementation
# ---------------------------------------------------------------------------


def _parse_field(
    s: str,
    pos: int,
    depth: int,
    used_delimiters: frozenset[str],
) -> tuple[Field, int]:
    """Parse one field starting at s[pos].

    Returns (Field, new_pos) where new_pos is the index of the first
    character NOT consumed by this field.
    """
    if depth > _NESTING_WARN_DEPTH:
        warnings.warn(
            f"Nesting depth {depth} exceeds recommended maximum of "
            f"{_NESTING_WARN_DEPTH}; consider using JSON/XML for deeply "
            f"nested structures.",
            NestingDepthWarning,
            stacklevel=4,
        )

    # --- Parse name ---
    m = _NAME_RE.match(s, pos)
    if not m:
        raise HeaderParseError(
            f"Expected a field name at position {pos} in {s!r}"
        )
    name = m.group()
    pos = m.end()

    # --- Optional array brackets ---
    array_delim: Optional[str] = None
    if pos < len(s) and s[pos] == "[":
        pos += 1  # consume "["
        bracket_close = s.find("]", pos)
        if bracket_close == -1:
            raise HeaderParseError(
                f"Unclosed '[' in field {name!r} of {s!r}"
            )
        delim_str = s[pos:bracket_close]
        if delim_str == "":
            if depth > 0:
                raise HeaderParseError(
                    f"Nested array field {name!r} must specify an explicit "
                    f"delimiter; empty [] is only allowed at top level."
                )
            array_delim = _DEFAULT_ARRAY_DELIM
        else:
            if len(delim_str) != 1:
                raise HeaderParseError(
                    f"Array delimiter must be a single character, got "
                    f"{delim_str!r} in {name!r}"
                )
            array_delim = delim_str
        pos = bracket_close + 1  # consume "]"

        # Validate delimiter is not already in use at an enclosing level
        if array_delim in used_delimiters:
            raise DelimiterConflictError(
                f"Array delimiter {array_delim!r} in field {name!r} is "
                f"already used at an enclosing level."
            )

    # --- Optional component-delim + struct body ---
    if pos < len(s) and s[pos] == "(":
        # No explicit component delimiter; use default "^"
        comp_delim = _DEFAULT_COMP_DELIM
    elif pos + 1 < len(s) and s[pos + 1] == "(":
        # Single character before "(" is the component delimiter
        comp_delim = s[pos]
        pos += 1
    else:
        # No struct body — done
        if array_delim is not None:
            return ArrayField(name=name, delimiter=array_delim,
                              element_type=SimpleField(name=name)), pos
        return SimpleField(name=name), pos

    # We have a "(" — parse the struct body
    if s[pos] != "(":
        raise HeaderParseError(
            f"Expected '(' for struct body in {name!r}, got {s[pos]!r}"
        )
    pos += 1  # consume "("

    # Validate component delimiter
    if comp_delim in used_delimiters:
        raise DelimiterConflictError(
            f"Component delimiter {comp_delim!r} in field {name!r} is "
            f"already used at an enclosing level."
        )
    if array_delim is not None and comp_delim == array_delim:
        raise DelimiterConflictError(
            f"Component delimiter {comp_delim!r} must differ from the "
            f"array delimiter {array_delim!r} in field {name!r}."
        )

    # Find the matching ")" (accounting for nested brackets)
    body_start = pos
    depth_count = 1
    while pos < len(s) and depth_count > 0:
        if s[pos] == "(":
            depth_count += 1
        elif s[pos] == ")":
            depth_count -= 1
        pos += 1
    if depth_count != 0:
        raise HeaderParseError(
            f"Unclosed '(' in struct field {name!r} of {s!r}"
        )
    body = s[body_start:pos - 1]  # exclude trailing ")"

    # Build the set of delimiters visible inside this struct
    inner_used = used_delimiters | {comp_delim}
    if array_delim is not None:
        inner_used = inner_used | {array_delim}

    # Parse component list
    components = _parse_component_list(body, comp_delim, depth + 1, inner_used)

    struct_type = StructField(
        name=name,
        component_delimiter=comp_delim,
        components=components,
    )

    if array_delim is not None:
        return ArrayField(name=name, delimiter=array_delim,
                          element_type=struct_type), pos
    return struct_type, pos


def _parse_component_list(
    body: str,
    comp_delim: str,
    depth: int,
    used_delimiters: frozenset[str],
) -> list[Field]:
    """Split the component-list body on comp_delim (bracket-depth-aware)
    and parse each component recursively."""
    raw_components = _bracket_aware_split(body, comp_delim)
    components: list[Field] = []
    for raw in raw_components:
        # A component starting with "(" means the bracket-aware split
        # swallowed a "name<delim>(...)" as two tokens, which only happens
        # when the inner struct reuses the outer component delimiter.
        if raw.startswith("("):
            raise DelimiterConflictError(
                f"A component in the struct body appears to start with '(' "
                f"after splitting on {comp_delim!r}. This indicates the "
                f"component delimiter {comp_delim!r} is being reused inside "
                f"a nested struct — each nesting level must use a distinct "
                f"delimiter."
            )
        comp_field, consumed = _parse_field(
            raw, pos=0, depth=depth, used_delimiters=used_delimiters
        )
        if consumed != len(raw):
            trailing = raw[consumed:]
            # Check if trailing chars start with a known enclosing delimiter
            for d in sorted(used_delimiters, key=len, reverse=True):
                if trailing.startswith(d):
                    raise DelimiterConflictError(
                        f"Delimiter {d!r} appears inside component {raw!r} "
                        f"but is already in use at an enclosing level."
                    )
            raise HeaderParseError(
                f"Unexpected trailing characters in component {raw!r}: "
                f"{trailing!r}"
            )
        components.append(comp_field)
    return components


def _bracket_aware_split(s: str, delimiter: str) -> list[str]:
    """Split s on delimiter, not splitting inside [] or ()."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in ("(", "["):
            depth += 1
            current.append(ch)
        elif ch in (")", "]"):
            depth -= 1
            current.append(ch)
        elif depth == 0 and s[i:i + len(delimiter)] == delimiter:
            parts.append("".join(current))
            current = []
            i += len(delimiter)
            continue
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return parts
