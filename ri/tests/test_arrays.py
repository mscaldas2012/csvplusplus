import pytest
from csvpp.models import SimpleField, ArrayField, StructField
from csvpp.value_parser import parse_value


class TestSimpleArrayParsing:
    def test_explicit_pipe_delimiter(self):
        assert parse_value(
            "555-1234|555-5678|555-9012",
            ArrayField("phone", "|", SimpleField("phone")),
        ) == ["555-1234", "555-5678", "555-9012"]

    def test_explicit_semicolon(self):
        assert parse_value(
            "john@work.com;john@home.com",
            ArrayField("email", ";", SimpleField("email")),
        ) == ["john@work.com", "john@home.com"]

    def test_default_tilde(self):
        assert parse_value(
            "555-1234~555-5678",
            ArrayField("phone", "~", SimpleField("phone")),
        ) == ["555-1234", "555-5678"]

    def test_single_value_no_delimiter(self):
        assert parse_value(
            "555-4444",
            ArrayField("phone", "|", SimpleField("phone")),
        ) == ["555-4444"]

    def test_empty_values_between_delimiters(self):
        assert parse_value(
            "urgent||priority",
            ArrayField("tags", "|", SimpleField("tags")),
        ) == ["urgent", "", "priority"]

    def test_empty_field(self):
        assert parse_value(
            "",
            ArrayField("phone", "|", SimpleField("phone")),
        ) == []

    def test_from_spec_figure1(self):
        # Header: id,name,phone[|],email[;]  — data row 1
        assert parse_value(
            "555-1234|555-5678|555-9012",
            ArrayField("phone", "|", SimpleField("phone")),
        ) == ["555-1234", "555-5678", "555-9012"]

    def test_from_spec_figure2_default_delim(self):
        assert parse_value(
            "555-1234~555-5678~555-9012",
            ArrayField("phone", "~", SimpleField("phone")),
        ) == ["555-1234", "555-5678", "555-9012"]

    def test_from_spec_figure3_empty(self):
        assert parse_value(
            "urgent||priority",
            ArrayField("tags", "|", SimpleField("tags")),
        ) == ["urgent", "", "priority"]


class TestArrayOfStructParsing:
    def test_two_addresses(self):
        field = ArrayField(
            "address",
            "~",
            StructField(
                "address",
                "^",
                [SimpleField("street"), SimpleField("city"), SimpleField("state"), SimpleField("zip")],
            ),
        )
        result = parse_value(
            "123 Main St^Los Angeles^CA^90210~456 Oak Ave^New York^NY^10001",
            field,
        )
        assert result == [
            {"street": "123 Main St", "city": "Los Angeles", "state": "CA", "zip": "90210"},
            {"street": "456 Oak Ave", "city": "New York", "state": "NY", "zip": "10001"},
        ]

    def test_single_address(self):
        field = ArrayField(
            "address",
            "~",
            StructField(
                "address",
                "^",
                [SimpleField("street"), SimpleField("city"), SimpleField("state"), SimpleField("zip")],
            ),
        )
        result = parse_value("789 Pine St^Boston^MA^02101", field)
        assert result == [
            {"street": "789 Pine St", "city": "Boston", "state": "MA", "zip": "02101"},
        ]
