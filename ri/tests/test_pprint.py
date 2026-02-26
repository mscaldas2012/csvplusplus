"""Tests for csvpp.pprint."""
import io
import pytest
from csvpp import parse, pprint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def render(records, top=None, color=False):
    """Capture pprint output as a string (no ANSI codes)."""
    buf = io.StringIO()
    pprint(records, top=top, file=buf, color=color)
    return buf.getvalue()


SIMPLE_CSV = "id,name\n1,Alice\n2,Bob\n3,Carol\n"

ARRAY_CSV = (
    "id,name,phone[|],email[;]\n"
    "1,John,555-1234|555-5678|555-9012,john@work.com;john@home.com\n"
    "2,Jane,555-4444,jane@company.com\n"
)

STRUCT_CSV = (
    "id,name,address[~]^(street^city^state^zip)\n"
    "1,John,123 Main St^Los Angeles^CA^90210~456 Oak Ave^New York^NY^10001\n"
    "2,Jane,789 Pine St^Boston^MA^02101\n"
)

NESTED_CSV = (
    "id,cust,items[~]^(sku^name^qty^price^opts[;]:(k:v))\n"
    "1,Alice,S1^Shirt^2^20^sz:M;col:blu~S2^Pant^1^50^sz:32\n"
)

STRUCT_IN_STRUCT_CSV = (
    "id,location^(name^coords:(lat:lon))\n"
    "1,Office^34.05:-118.24\n"
    "2,Home^40.71:-74.00\n"
)


# ---------------------------------------------------------------------------
# Smoke tests — just make sure it doesn't crash and produces output
# ---------------------------------------------------------------------------

class TestNoCrash:
    def test_simple_fields(self):
        out = render(parse(SIMPLE_CSV))
        assert len(out) > 0
       

    def test_array_fields(self):
        out = render(parse(ARRAY_CSV))
        assert len(out) > 0

    def test_struct_fields(self):
        out = render(parse(STRUCT_CSV))
        assert len(out) > 0

    def test_nested_complex(self):
        out = render(parse(NESTED_CSV))
        assert len(out) > 0

    def test_struct_in_struct(self):
        out = render(parse(STRUCT_IN_STRUCT_CSV))
        assert len(out) > 0

    def test_empty_records(self):
        out = render([])
        assert "no records" in out

    def test_empty_string_value(self):
        # An empty array element
        records = parse("id,tags[|]\n1,urgent||priority\n")
        out = render(records)
        assert len(out) > 0


# ---------------------------------------------------------------------------
# top= parameter
# ---------------------------------------------------------------------------

class TestTopParameter:
    def test_top_limits_records_shown(self):
        records = parse(SIMPLE_CSV)  # 3 records
        out = render(records, top=1)
        # "Record 1/3" should appear; "Record 2/3" should NOT
        assert "Record 1/3" in out
        assert "Record 2/3" not in out
        assert "Record 3/3" not in out

    def test_top_shows_omission_message(self):
        records = parse(SIMPLE_CSV)  # 3 records
        out = render(records, top=2)
        assert "omitted" in out or "Showing" in out

    def test_top_equal_to_total_shows_no_omission_message(self):
        records = parse(SIMPLE_CSV)  # 3 records
        out = render(records, top=3)
        assert "omitted" not in out

    def test_top_none_shows_all(self):
        records = parse(SIMPLE_CSV)  # 3 records
        out = render(records, top=None)
        assert "Record 1/3" in out
        assert "Record 2/3" in out
        assert "Record 3/3" in out

    def test_top_larger_than_total_shows_all(self):
        records = parse(SIMPLE_CSV)  # 3 records
        out = render(records, top=100)
        assert "Record 1/3" in out
        assert "Record 3/3" in out
        assert "omitted" not in out

    def test_top_zero_shows_nothing_but_omission(self):
        records = parse(SIMPLE_CSV)
        out = render(records, top=0)
        # Should say something about 3 total records being omitted
        assert "omitted" in out or "Showing 0" in out


# ---------------------------------------------------------------------------
# Content correctness — field values appear in output
# ---------------------------------------------------------------------------

class TestContent:
    def test_simple_field_values_present(self):
        records = parse(SIMPLE_CSV)
        out = render(records)
        assert "Alice" in out
        assert "Bob" in out
        assert "Carol" in out

    def test_array_items_present(self):
        records = parse(ARRAY_CSV)
        out = render(records)
        assert "555-1234" in out
        assert "john@work.com" in out

    def test_struct_components_present(self):
        records = parse(STRUCT_CSV)
        out = render(records)
        assert "Los Angeles" in out
        assert "CA" in out
        assert "90210" in out

    def test_nested_values_present(self):
        records = parse(NESTED_CSV)
        out = render(records)
        assert "Shirt" in out
        assert "sz" in out
        assert "blu" in out

    def test_all_keys_shown(self):
        records = parse(SIMPLE_CSV)
        out = render(records)
        assert "id" in out
        assert "name" in out

    def test_empty_tag_shown(self):
        records = parse("id,tags[|]\n1,urgent||priority\n")
        out = render(records)
        # Empty middle element should be represented
        assert "urgent" in out
        assert "priority" in out

    def test_none_value_for_missing_component(self):
        # A struct with fewer values than declared components → None component
        records = parse("id,geo^(lat^lon^alt)\n1,34.05^-118.24\n")
        out = render(records)
        assert "none" in out.lower()


# ---------------------------------------------------------------------------
# color=True path doesn't crash and contains ANSI sequences
# ---------------------------------------------------------------------------

class TestColor:
    def test_color_true_contains_ansi(self):
        records = parse(SIMPLE_CSV)
        buf = io.StringIO()
        pprint(records, file=buf, color=True)
        out = buf.getvalue()
        assert "\033[" in out

    def test_color_false_no_ansi(self):
        records = parse(SIMPLE_CSV)
        buf = io.StringIO()
        pprint(records, file=buf, color=False)
        out = buf.getvalue()
        assert "\033[" not in out


# ---------------------------------------------------------------------------
# Output to file=
# ---------------------------------------------------------------------------

class TestFileParameter:
    def test_writes_to_custom_stream(self):
        records = parse(SIMPLE_CSV)
        buf = io.StringIO()
        pprint(records, file=buf, color=False)
        assert "Alice" in buf.getvalue()

    def test_default_file_is_stdout(self, capsys):
        records = parse("id,name\n1,Alice\n")
        pprint(records, color=False)
        captured = capsys.readouterr()
        assert "Alice" in captured.out
