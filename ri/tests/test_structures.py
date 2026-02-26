import pytest
from csvpp.models import SimpleField, ArrayField, StructField
from csvpp.value_parser import parse_value


class TestSimpleStructParsing:
    def test_geo_two_components(self):
        schema = StructField("geo", "^", [SimpleField("lat"), SimpleField("lon")])
        result = parse_value("34.0522^-118.2437", schema)
        assert result == {"lat": "34.0522", "lon": "-118.2437"}

    def test_address_four_components(self):
        schema = StructField("address", "^", [
            SimpleField("street"), SimpleField("city"),
            SimpleField("state"), SimpleField("zip"),
        ])
        result = parse_value("123 Main St^LA^CA^90210", schema)
        assert result == {"street": "123 Main St", "city": "LA", "state": "CA", "zip": "90210"}

    def test_colon_delimiter(self):
        schema = StructField("coords", ":", [SimpleField("lat"), SimpleField("lon")])
        result = parse_value("34.05:-118.24", schema)
        assert result == {"lat": "34.05", "lon": "-118.24"}

    def test_fewer_components_than_declared(self):
        schema = StructField("address", "^", [
            SimpleField("street"), SimpleField("city"), SimpleField("state"), SimpleField("zip"),
        ])
        # Only 3 values provided
        result = parse_value("Main St^LA^CA", schema)
        assert result == {"street": "Main St", "city": "LA", "state": "CA", "zip": None}

    def test_from_spec_figure4_geo(self):
        """Figure 4: Simple Structure — geo^(lat^lon)"""
        schema = StructField("geo", "^", [SimpleField("lat"), SimpleField("lon")])
        assert parse_value("34.0522^-118.2437", schema) == {"lat": "34.0522", "lon": "-118.2437"}
        assert parse_value("40.7128^-74.0060", schema) == {"lat": "40.7128", "lon": "-74.0060"}
