import pytest
from csvpp.header_parser import parse_field
from csvpp.models import (
    SimpleField, ArrayField, StructField,
    HeaderParseError, DelimiterConflictError, NestingDepthWarning,
)


class TestSimpleField:
    def test_simple_name(self):
        assert parse_field("id") == SimpleField("id")

    def test_simple_with_underscore(self):
        assert parse_field("user_id") == SimpleField("user_id")

    def test_simple_with_hyphen(self):
        assert parse_field("user-id") == SimpleField("user-id")

    def test_simple_with_digits(self):
        assert parse_field("field123") == SimpleField("field123")


class TestArrayField:
    def test_explicit_delimiter_pipe(self):
        assert parse_field("phone[|]") == ArrayField("phone", "|", SimpleField("phone"))

    def test_explicit_delimiter_semicolon(self):
        assert parse_field("email[;]") == ArrayField("email", ";", SimpleField("email"))

    def test_default_delimiter_empty_brackets(self):
        assert parse_field("phone[]") == ArrayField("phone", "~", SimpleField("phone"))

    def test_default_delimiter_tilde(self):
        result = parse_field("phone[]")
        assert result.delimiter == "~"


class TestStructField:
    def test_explicit_component_delim(self):
        assert parse_field("geo^(lat^lon)") == StructField(
            "geo", "^", [SimpleField("lat"), SimpleField("lon")]
        )

    def test_default_component_delim(self):
        assert parse_field("address(street^city^state^zip)") == StructField(
            "address", "^", [SimpleField("street"), SimpleField("city"), SimpleField("state"), SimpleField("zip")]
        )

    def test_colon_component_delim(self):
        assert parse_field("coords:(lat:lon)") == StructField(
            "coords", ":", [SimpleField("lat"), SimpleField("lon")]
        )

    def test_four_components(self):
        result = parse_field("address^(street^city^state^zip)")
        assert len(result.components) == 4


class TestArrayOfStructField:
    def test_array_of_struct(self):
        assert parse_field("address[~]^(street^city^state^zip)") == ArrayField(
            "address",
            "~",
            StructField(
                "address",
                "^",
                [SimpleField("street"), SimpleField("city"), SimpleField("state"), SimpleField("zip")],
            ),
        )

    def test_array_with_nested_array_component(self):
        result = parse_field("address[~]^(type^lines[;]^city^state^zip)")
        expected = ArrayField(
            "address",
            "~",
            StructField(
                "address",
                "^",
                [
                    SimpleField("type"),
                    ArrayField("lines", ";", SimpleField("lines")),
                    SimpleField("city"),
                    SimpleField("state"),
                    SimpleField("zip"),
                ],
            ),
        )
        assert result == expected

    def test_struct_in_struct(self):
        assert parse_field("location^(name^coords:(lat:lon))") == StructField(
            "location",
            "^",
            [
                SimpleField("name"),
                StructField("coords", ":", [SimpleField("lat"), SimpleField("lon")]),
            ],
        )

    def test_complex_ecommerce(self):
        result = parse_field("items[~]^(sku^name^qty^price^opts[;]:(k:v))")
        expected = ArrayField(
            "items",
            "~",
            StructField(
                "items",
                "^",
                [
                    SimpleField("sku"),
                    SimpleField("name"),
                    SimpleField("qty"),
                    SimpleField("price"),
                    ArrayField(
                        "opts",
                        ";",
                        StructField("opts", ":", [SimpleField("k"), SimpleField("v")]),
                    ),
                ],
            ),
        )
        assert result == expected


class TestValidation:
    def test_nested_array_empty_brackets_raises(self):
        with pytest.raises(HeaderParseError):
            parse_field("address[~]^(lines[]^city)")

    def test_delimiter_conflict_raises(self):
        with pytest.raises(DelimiterConflictError):
            parse_field("address[~]^(street~city)")

    def test_invalid_name_raises(self):
        with pytest.raises(HeaderParseError):
            parse_field("")

    def test_unclosed_bracket_raises(self):
        with pytest.raises(HeaderParseError):
            parse_field("phone[|")

    def test_unclosed_paren_raises(self):
        with pytest.raises(HeaderParseError):
            parse_field("geo^(lat^lon")
