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

The library has **no runtime dependencies** — it uses only the Python standard library.
Test tooling (`pytest`, `pytest-cov`) is listed in `requirements.txt`.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

# 2a. Install with pip (editable, includes test deps)
pip install -e ".[dev]"

# 2b. Or install test deps directly from requirements.txt
pip install -r requirements.txt
pip install -e .
```

## Running Tests

```bash
# Run all 88 tests
pytest

# Run with coverage report
pytest --cov=csvpp --cov-report=term-missing

# Run a specific test file
pytest tests/test_examples.py

# Run a specific test class or case
pytest tests/test_examples.py::TestAppendixBEcommerce
pytest tests/test_examples.py::TestAppendixBEcommerce::test_shirt
```

## Using the Library

### Parsing a string

```python
import csvpp

# Simple fields — values are plain strings
records = csvpp.parse("id,name\n1,Alice\n2,Bob\n")
# [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]

# Array fields — values are lists
records = csvpp.parse("""id,name,phone[|],email[;]
1,John,555-1234|555-5678|555-9012,john@work.com;john@home.com
2,Jane,555-4444,jane@company.com
""")
records[0]["phone"]   # ["555-1234", "555-5678", "555-9012"]
records[1]["email"]   # ["jane@company.com"]

# Structured fields — values are dicts
records = csvpp.parse("""id,name,geo^(lat^lon)
1,Location A,34.0522^-118.2437
""")
records[0]["geo"]     # {"lat": "34.0522", "lon": "-118.2437"}

# Array of structures
records = csvpp.parse("""id,name,address[~]^(street^city^state^zip)
1,John,123 Main St^Los Angeles^CA^90210~456 Oak Ave^New York^NY^10001
""")
records[0]["address"][0]  # {"street": "123 Main St", "city": "Los Angeles", "state": "CA", "zip": "90210"}
records[0]["address"][1]  # {"street": "456 Oak Ave", "city": "New York", "state": "NY", "zip": "10001"}

# Complex nesting (array within struct, struct within struct)
records = csvpp.parse("""id,cust,items[~]^(sku^name^qty^price^opts[;]:(k:v))
1,Alice,S1^Shirt^2^20^sz:M;col:blu~S2^Pant^1^50^sz:32
""")
records[0]["items"][0]
# {"sku": "S1", "name": "Shirt", "qty": "2", "price": "20",
#  "opts": [{"k": "sz", "v": "M"}, {"k": "col", "v": "blu"}]}
```

### Parsing a file

```python
import csvpp

records = csvpp.parse_file("examples/appendixB_ecommerce.csvpp")
```

### Pretty-printing records

`csvpp.pprint()` renders any parsed result with aligned keys, box borders, and
recursive indentation for arrays and nested structs.  Use `top=N` to cap the
number of rows displayed.

```python
import csvpp

records = csvpp.parse_file("examples/figure5_repeated_structs.csvpp")
csvpp.pprint(records)           # all records, ANSI colour if terminal
csvpp.pprint(records, top=1)    # first record only
csvpp.pprint(records, color=False)  # plain text (no ANSI escape codes)
```

**Example output** — `figure5_repeated_structs.csvpp` (array of structs):

```
┌ Record 1/2 ────────────────────────────────────────────────┐
│ id       1
│ name     John
│ address  [0] street  123 Main St
│              city    Los Angeles
│              state   CA
│              zip     90210
│          [1] street  456 Oak Ave
│              city    New York
│              state   NY
│              zip     10001
└────────────────────────────────────────────────────────────┘

┌ Record 2/2 ────────────────────────────────────────────────┐
│ id       2
│ name     Jane
│ address  [0] street  789 Pine St
│              city    Boston
│              state   MA
│              zip     02101
└────────────────────────────────────────────────────────────┘
```

**Example output** — `appendixB_ecommerce.csvpp` (4-level nesting):

```
┌ Record 1/1 ────────────────────────────────────────────────┐
│ id     1
│ cust   Alice
│ items  [0] sku    S1
│            name   Shirt
│            qty    2
│            price  20
│            opts   [0] k  sz
│                       v  M
│                   [1] k  col
│                       v  blu
│        [1] sku    S2
│            name   Pant
│            qty    1
│            price  50
│            opts   [0] k  sz
│                       v  32
└────────────────────────────────────────────────────────────┘
```

**`top=N`** — shows N records and prints an omission note:

```
┌ Record 1/5 ───...
...
┌ Record 2/5 ───...
...

Showing 2 of 5 records (3 omitted). Pass top=5 to see all.
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `records` | `list[dict]` | — | Output of `parse()` / `parse_file()` |
| `top` | `int \| None` | `None` | Max rows to display; `None` = all |
| `file` | `TextIO` | `sys.stdout` | Output stream |
| `color` | `bool \| None` | `None` | ANSI colour: `True`/`False`/auto-detect |

### Working with field schemas directly

```python
from csvpp import parse_field, parse_header_row

# Parse a single header
field = parse_field("address[~]^(street^city^state^zip)")
# ArrayField('address', delimiter='~',
#   element_type=StructField('address', component_delimiter='^',
#     components=[SimpleField('street'), SimpleField('city'), ...]))

# Parse a full header row
schemas = parse_header_row(["id", "phone[|]", "address[~]^(street^city)"])
```

### Error handling

```python
import csvpp

try:
    records = csvpp.parse(my_csv_text)
except csvpp.HeaderParseError as e:
    print(f"Bad column header: {e}")
except csvpp.DelimiterConflictError as e:
    print(f"Reused delimiter: {e}")
except csvpp.InvalidQuotingError as e:
    print(f"Non-leaf element was quoted: {e}")
except csvpp.CSVPPError as e:
    print(f"Other CSV++ error: {e}")
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
