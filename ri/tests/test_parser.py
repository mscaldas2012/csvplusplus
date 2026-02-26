import pytest
from csvpp import parse, parse_file


class TestBasicParsing:
    def test_simple_fields(self):
        text = "id,name\n1,Alice\n2,Bob\n"
        records = parse(text)
        assert records == [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]

    def test_crlf_line_endings(self):
        text = "id,name\r\n1,Alice\r\n"
        records = parse(text)
        assert records == [{"id": "1", "name": "Alice"}]

    def test_empty_document_raises(self):
        from csvpp import CSVPPError
        with pytest.raises(CSVPPError):
            parse("")

    def test_header_only_no_records(self):
        records = parse("id,name\n")
        assert records == []

    def test_simple_array(self):
        text = "id,name,phone[|]\n1,John,555-1234|555-5678\n"
        records = parse(text)
        assert records[0]["phone"] == ["555-1234", "555-5678"]

    def test_simple_struct(self):
        text = "id,geo^(lat^lon)\n1,34.05^-118.24\n"
        records = parse(text)
        assert records[0]["geo"] == {"lat": "34.05", "lon": "-118.24"}

    def test_outer_csv_quoting_for_simple_field(self):
        """Outer CSV quoting is valid for simple (leaf) fields."""
        text = 'id,name\n1,"Alice, Jr."\n'
        records = parse(text)
        assert records[0]["name"] == "Alice, Jr."
