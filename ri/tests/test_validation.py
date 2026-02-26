"""Tests for Phase 8: Validation & Error Handling."""
import pytest
import warnings
from csvpp import parse
from csvpp.header_parser import parse_field
from csvpp.models import (
    HeaderParseError, DelimiterConflictError,
    InvalidQuotingError, NestingDepthWarning,
)


class TestHeaderValidation:
    def test_nested_empty_brackets_rejected(self):
        """Nested arrays must specify explicit delimiter."""
        with pytest.raises(HeaderParseError):
            parse_field("address[~]^(lines[]^city)")

    def test_same_delimiter_at_two_levels_rejected(self):
        """Component delimiter must not equal enclosing array delimiter."""
        with pytest.raises(DelimiterConflictError):
            parse_field("address[~]^(street~city)")

    def test_same_component_delimiters_nested(self):
        """Inner struct must use different component delimiter."""
        with pytest.raises(DelimiterConflictError):
            parse_field("location^(name^coords^(lat^lon))")  # both use ^

    def test_empty_name_raises(self):
        with pytest.raises(HeaderParseError):
            parse_field("")

    def test_unclosed_bracket(self):
        with pytest.raises(HeaderParseError):
            parse_field("phone[|")

    def test_unclosed_paren(self):
        with pytest.raises(HeaderParseError):
            parse_field("geo^(lat^lon")


class TestDataValidation:
    def test_outer_quoted_array_field_raises(self):
        """Quoting entire array value at CSV field level is invalid."""
        csv_text = 'id,notes[|]\n1,"First note|Second note|Third note"\n'
        with pytest.raises(InvalidQuotingError):
            parse(csv_text)

    def test_outer_quoted_struct_field_raises(self):
        """Quoting entire struct value at CSV field level is invalid."""
        csv_text = 'id,address^(street^city)\n1,"Main St^Boston"\n'
        with pytest.raises(InvalidQuotingError):
            parse(csv_text)

    def test_simple_field_outer_quoted_is_valid(self):
        """Outer CSV quoting of a simple (leaf) field is always valid."""
        csv_text = 'id,name\n1,"Alice, Jr."\n'
        records = parse(csv_text)
        assert records[0]["name"] == "Alice, Jr."


class TestNestingDepthWarning:
    def test_deep_nesting_warns(self):
        """Fields nested beyond 4 levels should issue NestingDepthWarning."""
        # 5 levels deep using distinct delimiters at every level:
        # a[~] -> struct^ -> struct; -> struct: -> struct@ -> struct$
        # delimiters: ~, ^, ;, :, @, $ — all distinct, no conflicts
        header = "a[~]^(b;(c:(d@(e$(f)))))"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                parse_field(header)
            except Exception:
                pass  # may also raise; we only care about the warning
            depth_warns = [x for x in w if issubclass(x.category, NestingDepthWarning)]
            assert len(depth_warns) > 0
