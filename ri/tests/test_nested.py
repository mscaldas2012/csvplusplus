import pytest
from csvpp.models import SimpleField, ArrayField, StructField
from csvpp.value_parser import parse_value


class TestArrayWithinStruct:
    """Figure 6: address[~]^(type^lines[;]^city^state^zip)"""
    def _schema(self):
        return ArrayField("address", "~", StructField("address", "^", [
            SimpleField("type"),
            ArrayField("lines", ";", SimpleField("lines")),
            SimpleField("city"),
            SimpleField("state"),
            SimpleField("zip"),
        ]))

    def test_two_addresses_with_array_lines(self):
        raw = "home^123 Main;Apt 4^LA^CA^90210~work^456 Oak^NY^NY^10001"
        result = parse_value(raw, self._schema())
        assert len(result) == 2
        assert result[0] == {
            "type": "home",
            "lines": ["123 Main", "Apt 4"],
            "city": "LA",
            "state": "CA",
            "zip": "90210",
        }
        assert result[1] == {
            "type": "work",
            "lines": ["456 Oak"],
            "city": "NY",
            "state": "NY",
            "zip": "10001",
        }


class TestStructWithinStruct:
    """Figure 7: location^(name^coords:(lat:lon))"""
    def _schema(self):
        return StructField("location", "^", [
            SimpleField("name"),
            StructField("coords", ":", [SimpleField("lat"), SimpleField("lon")]),
        ])

    def test_office(self):
        result = parse_value("Office^34.05:-118.24", self._schema())
        assert result == {"name": "Office", "coords": {"lat": "34.05", "lon": "-118.24"}}

    def test_home(self):
        result = parse_value("Home^40.71:-74.00", self._schema())
        assert result == {"name": "Home", "coords": {"lat": "40.71", "lon": "-74.00"}}


class TestEcommerceNested:
    """Appendix B: items[~]^(sku^name^qty^price^opts[;]:(k:v))"""
    def _schema(self):
        opts = ArrayField("opts", ";", StructField("opts", ":", [
            SimpleField("k"), SimpleField("v"),
        ]))
        return ArrayField("items", "~", StructField("items", "^", [
            SimpleField("sku"),
            SimpleField("name"),
            SimpleField("qty"),
            SimpleField("price"),
            opts,
        ]))

    def test_two_items(self):
        raw = "S1^Shirt^2^20^sz:M;col:blu~S2^Pant^1^50^sz:32"
        result = parse_value(raw, self._schema())
        assert len(result) == 2
        assert result[0] == {
            "sku": "S1",
            "name": "Shirt",
            "qty": "2",
            "price": "20",
            "opts": [{"k": "sz", "v": "M"}, {"k": "col", "v": "blu"}],
        }
        assert result[1] == {
            "sku": "S2",
            "name": "Pant",
            "qty": "1",
            "price": "50",
            "opts": [{"k": "sz", "v": "32"}],
        }
