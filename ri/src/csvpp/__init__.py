"""
csvpp — CSV++ reference implementation.

CSV++ extends RFC 4180 with support for array fields and structured fields.
See draft-mscaldas-csvpp-02 for the full specification.

Quick start:

    import csvpp

    records = csvpp.parse('''id,name,phone[|],email[;]
    1,John,555-1234|555-5678,john@work.com;john@home.com
    ''')
    # records[0]['phone'] == ['555-1234', '555-5678']

    records = csvpp.parse_file('orders.csvpp')
"""

from .parser import parse, parse_file
from .header_parser import parse_field, parse_header_row
from .models import (
    Field,
    SimpleField,
    ArrayField,
    StructField,
    CSVPPError,
    HeaderParseError,
    ValueParseError,
    InvalidQuotingError,
    DelimiterConflictError,
    NestingDepthWarning,
)

__all__ = [
    "parse",
    "parse_file",
    "parse_field",
    "parse_header_row",
    "Field",
    "SimpleField",
    "ArrayField",
    "StructField",
    "CSVPPError",
    "HeaderParseError",
    "ValueParseError",
    "InvalidQuotingError",
    "DelimiterConflictError",
    "NestingDepthWarning",
]

__version__ = "0.1.0"
