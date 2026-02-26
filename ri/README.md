# csvpp — CSV++ Reference Implementation

Python reference implementation of [draft-mscaldas-csvpp-02](../spec/draft-mscaldas-csvpp-02.xml), the IETF Internet-Draft extending RFC 4180 CSV with support for array fields and structured/nested fields.

## Quick Start

```python
import csvpp

# Array fields
records = csvpp.parse("""id,name,phone[|],email[;]
1,John,555-1234|555-5678|555-9012,john@work.com;john@home.com
2,Jane,555-4444,jane@company.com
""")
records[0]["phone"]   # ["555-1234", "555-5678", "555-9012"]
records[0]["email"]   # ["john@work.com", "john@home.com"]

# Structured fields
records = csvpp.parse("""id,name,geo^(lat^lon)
1,Location A,34.0522^-118.2437
""")
records[0]["geo"]     # {"lat": "34.0522", "lon": "-118.2437"}

# Array of structures
records = csvpp.parse("""id,name,address[~]^(street^city^state^zip)
1,John,123 Main St^Los Angeles^CA^90210~456 Oak Ave^New York^NY^10001
""")
records[0]["address"][0]  # {"street": "123 Main St", "city": "Los Angeles", ...}

# Parse from file
records = csvpp.parse_file("examples/appendixB_ecommerce.csvpp")
```

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Project Structure

```
ri/
├── src/csvpp/
│   ├── __init__.py        — public API (parse, parse_file, + model types)
│   ├── models.py          — field type data models + exceptions
│   ├── header_parser.py   — parse CSV++ column header declarations
│   ├── value_parser.py    — parse data values per header schema
│   └── parser.py          — main two-phase parser (orchestration)
├── tests/
│   ├── test_header_parser.py  — Phase 1: header parsing
│   ├── test_arrays.py         — Phase 2: array value parsing
│   ├── test_structures.py     — Phase 3: struct value parsing
│   ├── test_nested.py         — Phase 5: nested structures
│   ├── test_quoting.py        — Phase 6: RFC 4180 leaf quoting
│   ├── test_parser.py         — Phase 7: full parser integration
│   ├── test_examples.py       — all spec figures (Figs 1–7 + Appendix B)
│   └── test_validation.py     — Phase 8: error handling & validation
└── examples/                  — sample .csvpp files from the spec
```

## CSV++ Syntax Summary

| Feature | Header syntax | Example value |
|---------|--------------|---------------|
| Simple field | `name` | `Alice` |
| Array (explicit delim) | `phone[|]` | `555-1234|555-5678` |
| Array (default `~`) | `phone[]` | `555-1234~555-5678` |
| Struct (explicit delim) | `geo^(lat^lon)` | `34.05^-118.24` |
| Struct (default `^`) | `address(street^city)` | `Main St^Boston` |
| Array of structs | `address[~]^(street^city^state^zip)` | `Main^LA^CA^90210~Oak^NY^NY^10001` |
| Nested (array in struct) | `address[~]^(type^lines[;]^city)` | `home^Main;Apt 4^LA` |
| Nested (struct in struct) | `loc^(name^coords:(lat:lon))` | `Office^34.05:-118.24` |

## Return Value Structure

`parse()` / `parse_file()` return `list[dict]`. Values in each dict:

| Field type | Python value |
|------------|-------------|
| `SimpleField` | `str` |
| `ArrayField[simple]` | `list[str]` |
| `ArrayField[struct]` | `list[dict]` |
| `StructField` | `dict[str, str | list | dict]` |

## Spec Compliance

- Header row is **required** (no headerless files)
- Default array delimiter: `~` (top-level arrays only; nested arrays must specify explicit delimiter)
- Default component delimiter: `^`
- RFC 4180 quoting applies **only to leaf elements** (innermost atomic values); quoting non-leaf elements raises `InvalidQuotingError`
- Same delimiter at multiple nesting levels raises `DelimiterConflictError`
- Nesting depth >4 issues `NestingDepthWarning`

## Exceptions

| Exception | When raised |
|-----------|-------------|
| `HeaderParseError` | Malformed column header |
| `DelimiterConflictError` | Same delimiter reused at multiple nesting levels |
| `InvalidQuotingError` | RFC 4180 quoting applied to a non-leaf element |
| `ValueParseError` | Value cannot be parsed per its schema |
| `NestingDepthWarning` | Nesting depth exceeds recommended 3–4 levels |

All inherit from `csvpp.CSVPPError`.
