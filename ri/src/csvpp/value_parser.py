"""
CSV++ value parser.

Given a raw field string (already extracted from the CSV row by the outer
csv-module pass) and a Field schema, produces the Python value:

    SimpleField  ->  str
    ArrayField   ->  list[str | dict]
    StructField  ->  dict[str, str | list | dict]

Quoting rules (Section 7 of the spec):
  - RFC 4180 double-quote quoting MUST only be applied to *leaf* elements.
  - Quoting at a level that still contains unprocessed delimiters is invalid
    and MUST be rejected.
"""

from __future__ import annotations

from typing import Any

from .models import (
    Field, SimpleField, ArrayField, StructField,
    InvalidQuotingError, ValueParseError,
)


def parse_value(raw: str, schema: Field, was_quoted: bool = False) -> Any:
    """Parse a raw field string according to its schema.

    Args:
        raw: The raw string value extracted from a CSV field (outer CSV
             quoting has already been stripped by the csv module).
        schema: The Field describing how to interpret the value.
        was_quoted: True if the outer CSV field was double-quoted.
                    Used to detect invalid non-leaf quoting.

    Returns:
        str for SimpleField, list for ArrayField, dict for StructField.

    Raises:
        InvalidQuotingError: If quoting is applied to a non-leaf element.
        ValueParseError: If the value cannot be parsed per its schema.
    """
    if isinstance(schema, SimpleField):
        # Leaf node — just return the string as-is.
        return raw

    # Non-leaf: quoting the entire field at the CSV level is invalid.
    if was_quoted:
        raise InvalidQuotingError(
            f"Field {schema.name!r} is a non-leaf field "
            f"({type(schema).__name__}) but its value was enclosed in "
            f"outer CSV double-quotes, which prevents delimiter splitting. "
            f"Only individual leaf elements may be quoted."
        )

    if isinstance(schema, ArrayField):
        return _parse_array(raw, schema)

    if isinstance(schema, StructField):
        return _parse_struct(raw, schema)

    raise ValueParseError(f"Unknown schema type: {type(schema)}")


# ---------------------------------------------------------------------------
# Array parsing
# ---------------------------------------------------------------------------


def _parse_array(raw: str, schema: ArrayField) -> list[Any]:
    if raw == "":
        return []

    elements, quoted_flags = quote_aware_split(raw, schema.delimiter)

    result = []
    for elem, elem_quoted in zip(elements, quoted_flags):
        # If this element is quoted AND is not a leaf, it's invalid.
        if elem_quoted and not isinstance(schema.element_type, SimpleField):
            raise InvalidQuotingError(
                f"Array element in field {schema.name!r} was quoted, but "
                f"its element type is {type(schema.element_type).__name__} "
                f"(non-leaf). Only leaf elements may be quoted."
            )
        result.append(parse_value(elem, schema.element_type,
                                  was_quoted=False))
    return result


# ---------------------------------------------------------------------------
# Struct parsing
# ---------------------------------------------------------------------------


def _parse_struct(raw: str, schema: StructField) -> dict[str, Any]:
    if not schema.components:
        return {}

    elements, quoted_flags = quote_aware_split(raw, schema.component_delimiter)

    if len(elements) > len(schema.components):
        raise ValueParseError(
            f"Struct field {schema.name!r} has {len(schema.components)} "
            f"declared components but {len(elements)} values were found."
        )

    result: dict[str, Any] = {}
    for i, comp_schema in enumerate(schema.components):
        if i < len(elements):
            elem = elements[i]
            elem_quoted = quoted_flags[i]

            # If this component is quoted AND is not a leaf, it's invalid.
            if elem_quoted and not isinstance(comp_schema, SimpleField):
                raise InvalidQuotingError(
                    f"Component {comp_schema.name!r} in struct "
                    f"{schema.name!r} was quoted, but it is a non-leaf "
                    f"({type(comp_schema).__name__}). "
                    f"Only leaf elements may be quoted."
                )
            result[comp_schema.name] = parse_value(
                elem, comp_schema, was_quoted=False
            )
        else:
            # Fewer values than declared components — fill with None.
            result[comp_schema.name] = None

    return result


# ---------------------------------------------------------------------------
# Quote-aware splitting
# ---------------------------------------------------------------------------


def quote_aware_split(s: str, delimiter: str) -> tuple[list[str], list[bool]]:
    """Split *s* on *delimiter*, respecting RFC 4180-style inner quoting.

    Returns two parallel lists:
        values      — the split strings (with surrounding quotes stripped)
        was_quoted  — whether each element was surrounded by double-quotes

    RFC 4180 quoting rules applied:
      - A token beginning with '"' is quoted; it ends at the next unescaped '"'.
      - '""' inside a quoted token represents a literal '"'.
      - Quoted tokens may span the delimiter character.
    """
    values: list[str] = []
    quoted_flags: list[bool] = []

    current: list[str] = []
    this_quoted = False
    in_quotes = False
    i = 0

    while i < len(s):
        ch = s[i]

        if in_quotes:
            if ch == '"':
                # Check for escaped quote ""
                if i + 1 < len(s) and s[i + 1] == '"':
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
                # Start of a quoted token (only valid at token boundary)
                in_quotes = True
                this_quoted = True
                i += 1
            elif s[i:i + len(delimiter)] == delimiter:
                values.append("".join(current))
                quoted_flags.append(this_quoted)
                current = []
                this_quoted = False
                i += len(delimiter)
            else:
                current.append(ch)
                i += 1

    values.append("".join(current))
    quoted_flags.append(this_quoted)
    return values, quoted_flags
