"""
CSV++ data models.

Represents the typed field declarations parsed from CSV++ headers.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union


# Field type union — any header field resolves to one of these.
Field = Union["SimpleField", "ArrayField", "StructField"]


@dataclass
class SimpleField:
    """A plain scalar field (no arrays, no components)."""
    name: str

    def __repr__(self) -> str:
        return f"SimpleField({self.name!r})"


@dataclass
class ArrayField:
    """A repeating field whose elements share a common type.

    element_type is either SimpleField (array of scalars) or StructField
    (array of structured records).
    """
    name: str
    delimiter: str
    element_type: Union[SimpleField, "StructField"]

    def __repr__(self) -> str:
        return (
            f"ArrayField({self.name!r}, delimiter={self.delimiter!r}, "
            f"element_type={self.element_type!r})"
        )


@dataclass
class StructField:
    """A structured field composed of named components.

    Each component is itself a Field (simple, array, or nested struct).
    """
    name: str
    component_delimiter: str
    components: list[Field] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"StructField({self.name!r}, "
            f"component_delimiter={self.component_delimiter!r}, "
            f"components={self.components!r})"
        )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CSVPPError(Exception):
    """Base class for all CSV++ errors."""


class HeaderParseError(CSVPPError):
    """Raised when a column header cannot be parsed."""


class ValueParseError(CSVPPError):
    """Raised when a field value cannot be parsed per its declared type."""


class InvalidQuotingError(CSVPPError):
    """Raised when RFC 4180 quoting is applied to a non-leaf element."""


class DelimiterConflictError(CSVPPError):
    """Raised when the same delimiter is used at multiple nesting levels."""


class NestingDepthWarning(UserWarning):
    """Issued when nesting depth exceeds the recommended 3–4 levels."""
