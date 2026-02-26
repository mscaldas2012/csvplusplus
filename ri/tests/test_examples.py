"""Tests for every example in draft-mscaldas-csvpp-02.xml."""
import pytest
from csvpp import parse


class TestFigure1ArraysExplicitDelimiters:
    """Figure 1: Arrays with Explicit Delimiters
    id,name,phone[|],email[;]
    1,John,555-1234|555-5678|555-9012,john@work.com;john@home.com
    2,Jane,555-4444,jane@company.com
    """
    CSV = (
        "id,name,phone[|],email[;]\n"
        "1,John,555-1234|555-5678|555-9012,john@work.com;john@home.com\n"
        "2,Jane,555-4444,jane@company.com\n"
    )

    def test_records_count(self):
        assert len(parse(self.CSV)) == 2

    def test_john_phones(self):
        r = parse(self.CSV)[0]
        assert r["phone"] == ["555-1234", "555-5678", "555-9012"]

    def test_john_emails(self):
        r = parse(self.CSV)[0]
        assert r["email"] == ["john@work.com", "john@home.com"]

    def test_jane_single_phone(self):
        r = parse(self.CSV)[1]
        assert r["phone"] == ["555-4444"]

    def test_jane_single_email(self):
        r = parse(self.CSV)[1]
        assert r["email"] == ["jane@company.com"]


class TestFigure2ArraysDefaultDelimiters:
    """Figure 2: Arrays with Default Delimiters
    id,name,phone[],email[]
    1,John,555-1234~555-5678~555-9012,john@work.com~john@home.com
    2,Jane,555-4444,jane@company.com
    """
    CSV = (
        "id,name,phone[],email[]\n"
        "1,John,555-1234~555-5678~555-9012,john@work.com~john@home.com\n"
        "2,Jane,555-4444,jane@company.com\n"
    )

    def test_john_phones(self):
        r = parse(self.CSV)[0]
        assert r["phone"] == ["555-1234", "555-5678", "555-9012"]

    def test_jane_single(self):
        r = parse(self.CSV)[1]
        assert r["phone"] == ["555-4444"]
        assert r["email"] == ["jane@company.com"]


class TestFigure3EmptyValues:
    """Figure 3: Empty Values in Arrays
    id,tags[|]
    1,urgent||priority
    """
    CSV = "id,tags[|]\n1,urgent||priority\n"

    def test_three_tags_middle_empty(self):
        r = parse(self.CSV)[0]
        assert r["tags"] == ["urgent", "", "priority"]


class TestFigure4SimpleStructure:
    """Figure 4: Simple Structure — geo^(lat^lon)
    id,name,geo^(lat^lon)
    1,Location A,34.0522^-118.2437
    2,Location B,40.7128^-74.0060
    """
    CSV = (
        "id,name,geo^(lat^lon)\n"
        "1,Location A,34.0522^-118.2437\n"
        "2,Location B,40.7128^-74.0060\n"
    )

    def test_location_a(self):
        r = parse(self.CSV)[0]
        assert r["geo"] == {"lat": "34.0522", "lon": "-118.2437"}

    def test_location_b(self):
        r = parse(self.CSV)[1]
        assert r["geo"] == {"lat": "40.7128", "lon": "-74.0060"}


class TestFigure5RepeatedStructures:
    """Figure 5: Repeated Structures — address[~]^(street^city^state^zip)
    id,name,address[~]^(street^city^state^zip)
    1,John,123 Main St^Los Angeles^CA^90210~456 Oak Ave^New York^NY^10001
    2,Jane,789 Pine St^Boston^MA^02101
    """
    CSV = (
        "id,name,address[~]^(street^city^state^zip)\n"
        "1,John,123 Main St^Los Angeles^CA^90210~456 Oak Ave^New York^NY^10001\n"
        "2,Jane,789 Pine St^Boston^MA^02101\n"
    )

    def test_john_two_addresses(self):
        r = parse(self.CSV)[0]
        assert len(r["address"]) == 2
        assert r["address"][0] == {
            "street": "123 Main St", "city": "Los Angeles",
            "state": "CA", "zip": "90210",
        }
        assert r["address"][1] == {
            "street": "456 Oak Ave", "city": "New York",
            "state": "NY", "zip": "10001",
        }

    def test_jane_one_address(self):
        r = parse(self.CSV)[1]
        assert len(r["address"]) == 1
        assert r["address"][0] == {
            "street": "789 Pine St", "city": "Boston",
            "state": "MA", "zip": "02101",
        }


class TestFigure6ArrayWithinStruct:
    """Figure 6: Array Within Structure
    id,name,address[~]^(type^lines[;]^city^state^zip)
    1,John,home^123 Main;Apt 4^LA^CA^90210~work^456 Oak^NY^NY^10001
    """
    CSV = (
        "id,name,address[~]^(type^lines[;]^city^state^zip)\n"
        "1,John,home^123 Main;Apt 4^LA^CA^90210~work^456 Oak^NY^NY^10001\n"
    )

    def test_home_address(self):
        r = parse(self.CSV)[0]
        assert r["address"][0] == {
            "type": "home",
            "lines": ["123 Main", "Apt 4"],
            "city": "LA",
            "state": "CA",
            "zip": "90210",
        }

    def test_work_address(self):
        r = parse(self.CSV)[0]
        assert r["address"][1] == {
            "type": "work",
            "lines": ["456 Oak"],
            "city": "NY",
            "state": "NY",
            "zip": "10001",
        }


class TestFigure7StructWithinStruct:
    """Figure 7: Structure Within Structure
    id,location^(name^coords:(lat:lon))
    1,Office^34.05:-118.24
    2,Home^40.71:-74.00
    """
    CSV = (
        "id,location^(name^coords:(lat:lon))\n"
        "1,Office^34.05:-118.24\n"
        "2,Home^40.71:-74.00\n"
    )

    def test_office(self):
        r = parse(self.CSV)[0]
        assert r["location"] == {
            "name": "Office",
            "coords": {"lat": "34.05", "lon": "-118.24"},
        }

    def test_home(self):
        r = parse(self.CSV)[1]
        assert r["location"] == {
            "name": "Home",
            "coords": {"lat": "40.71", "lon": "-74.00"},
        }


class TestAppendixBEcommerce:
    """Appendix B: E-commerce Order
    id,cust,items[~]^(sku^name^qty^price^opts[;]:(k:v))
    1,Alice,S1^Shirt^2^20^sz:M;col:blu~S2^Pant^1^50^sz:32
    """
    CSV = (
        "id,cust,items[~]^(sku^name^qty^price^opts[;]:(k:v))\n"
        "1,Alice,S1^Shirt^2^20^sz:M;col:blu~S2^Pant^1^50^sz:32\n"
    )

    def test_record_basics(self):
        r = parse(self.CSV)[0]
        assert r["id"] == "1"
        assert r["cust"] == "Alice"

    def test_two_items(self):
        r = parse(self.CSV)[0]
        assert len(r["items"]) == 2

    def test_shirt(self):
        r = parse(self.CSV)[0]
        shirt = r["items"][0]
        assert shirt == {
            "sku": "S1",
            "name": "Shirt",
            "qty": "2",
            "price": "20",
            "opts": [{"k": "sz", "v": "M"}, {"k": "col", "v": "blu"}],
        }

    def test_pant(self):
        r = parse(self.CSV)[0]
        pant = r["items"][1]
        assert pant == {
            "sku": "S2",
            "name": "Pant",
            "qty": "1",
            "price": "50",
            "opts": [{"k": "sz", "v": "32"}],
        }
