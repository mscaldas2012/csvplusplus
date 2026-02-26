import pytest
from csvpp.models import SimpleField, ArrayField, StructField
from csvpp.value_parser import parse_value, quote_aware_split
from csvpp.models import InvalidQuotingError


class TestQuoteAwareSplit:
    def test_simple_no_quotes(self):
        vals, flags = quote_aware_split("a|b|c", "|")
        assert vals == ["a", "b", "c"]
        assert flags == [False, False, False]

    def test_quoted_middle_element(self):
        vals, flags = quote_aware_split('First note|"Second note with | pipe"|Third note', "|")
        assert vals == ["First note", "Second note with | pipe", "Third note"]
        assert flags == [False, True, False]

    def test_quoted_element_with_escaped_quote(self):
        vals, flags = quote_aware_split('a|"say ""hi"""|c', "|")
        assert vals == ["a", 'say "hi"', "c"]
        assert flags == [False, True, False]

    def test_empty_elements(self):
        vals, flags = quote_aware_split("a||c", "|")
        assert vals == ["a", "", "c"]

    def test_single_element_quoted(self):
        vals, flags = quote_aware_split('"hello world"', "|")
        assert vals == ["hello world"]
        assert flags == [True]


class TestLeafQuoting:
    """Valid quoting at the leaf (individual element) level."""

    def test_quoted_array_item_with_delimiter(self):
        """Spec: id,notes[|] / 1,First note|"Second note with | pipe"|Third note"""
        schema = ArrayField("notes", "|", SimpleField("notes"))
        # The raw value as delivered after outer CSV parsing
        raw = 'First note|"Second note with | pipe"|Third note'
        result = parse_value(raw, schema)
        assert result == ["First note", "Second note with | pipe", "Third note"]

    def test_quoted_component_with_comma(self):
        """Spec: Quoting an Individual Component Value (Leaf)
        id,address^(street^city^state^zip)
        1,"123 Main St, Apt 4"^Springfield^IL^62701
        The outer CSV strips the street quote — the raw arrives as the quoted section
        NOTE: In this case the outer CSV reader handles the field-level quoting.
        Here we test component-level inner quoting."""
        schema = StructField("address", "^", [
            SimpleField("street"), SimpleField("city"),
            SimpleField("state"), SimpleField("zip"),
        ])
        # After outer CSV parsing, the street component may still carry inner quotes
        # e.g., the raw field is: "123 Main St, Apt 4"^Springfield^IL^62701
        # (not outer-quoted; the "..." wraps just the street component within the field)
        raw = '"123 Main St, Apt 4"^Springfield^IL^62701'
        result = parse_value(raw, schema)
        assert result == {
            "street": "123 Main St, Apt 4",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
        }


class TestInvalidNonLeafQuoting:
    """Quoting non-leaf elements MUST be rejected."""

    def test_outer_quoted_array_raises(self):
        """If was_quoted=True for an array field, raise InvalidQuotingError."""
        schema = ArrayField("notes", "|", SimpleField("notes"))
        with pytest.raises(InvalidQuotingError):
            parse_value("First note|Second note|Third note", schema, was_quoted=True)

    def test_outer_quoted_struct_raises(self):
        """If was_quoted=True for a struct field, raise InvalidQuotingError."""
        schema = StructField("address", "^", [
            SimpleField("street"), SimpleField("city"),
        ])
        with pytest.raises(InvalidQuotingError):
            parse_value("123 Main^Springfield", schema, was_quoted=True)

    def test_quoted_struct_element_within_array_raises(self):
        """Array element that is a struct and is quoted -> InvalidQuotingError."""
        schema = ArrayField("address", "~", StructField("address", "^", [
            SimpleField("street"), SimpleField("city"),
        ]))
        # The first element is quoted but it's a struct (non-leaf)
        raw = '"123 Main^Springfield"~456 Oak^New York'
        with pytest.raises(InvalidQuotingError):
            parse_value(raw, schema)
