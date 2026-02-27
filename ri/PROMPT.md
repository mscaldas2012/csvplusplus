# CSV++ Reference Implementation - Claude Code Prompt

## Overview

Implement a **reference implementation** of the CSV++ (CSV Plus Plus) specification defined in `draft-mscaldas-csvpp-02.xml` (included in this repository). CSV++ extends RFC 4180 CSV with support for repeating fields (arrays), structured fields (components/subcomponents), and nested combinations of both.

This is a **reference implementation** — correctness and clarity are the priority, not performance. Use Python's built-in `csv` module for initial CSV parsing, then layer CSV++ semantics on top.

## Specification Reference

Read and follow `draft-mscaldas-csvpp-02.xml` in this repository. Key sections:
- **Section 4 (Array Fields):** `column_name[delimiter]` and `column_name[]` syntax. Default array delimiter is `~` for top-level only. Nested arrays MUST specify explicit delimiters.
- **Section 5 (Structured Fields):** `column_name(comp1^comp2)` syntax. Default component delimiter is `^`.
- **Section 6 (Nested Structures):** Recursive composition — arrays within structures, structures within structures.
- **Section 7 (Quoting and Escaping):** RFC 4180 quoting applies ONLY to leaf elements. Quoting non-leaf values is invalid.
- **Appendix A (ABNF Grammar):** Formal grammar for headers and values.

## Approach

### Use TDD (Test-Driven Development)

For **every feature**, follow this cycle strictly:
1. **Write failing tests first** that define the expected behavior
2. **Implement the minimum code** to make those tests pass
3. **Refactor** if needed while keeping tests green

Organize tests in a `tests/` directory using `pytest`. Group tests logically by feature area.

### Use Subagents

Use subagents (`@subagent`) for well-scoped, parallelizable tasks such as:
- Writing test suites for a specific feature while you work on another
- Implementing independent modules simultaneously
- Reviewing/validating against the spec

### Token Management

This is a large implementation. **Pause your work when you are running low on tokens.** Before pausing:
1. Summarize what has been completed
2. List what remains to be done
3. Note any open questions or decisions
4. Ensure all code is committed/saved

When more tokens are available, resume from where you left off.

## Project Structure

```
csvpp/
├── src/
│   └── csvpp/
│       ├── __init__.py
│       ├── header_parser.py    # Parse CSV++ header declarations
│       ├── value_parser.py     # Parse data values per header type
│       ├── parser.py           # Main CSV++ parser (orchestrates everything)
│       └── models.py           # Data models (Field types, parsed records)
├── tests/
│   ├── test_header_parser.py
│   ├── test_value_parser.py
│   ├── test_parser.py
│   ├── test_arrays.py
│   ├── test_structures.py
│   ├── test_nested.py
│   ├── test_quoting.py
│   └── test_examples.py        # All examples from the spec
├── examples/                    # Sample .csvpp files from the spec
├── pyproject.toml
└── README.md
```

## Features to Implement (in order)

### Phase 1: Header Parsing

Build the header parser that analyzes column headers and determines field types.

**Test cases to cover:**
- Simple fields: `id`, `name` → simple field type
- Array fields with explicit delimiter: `phone[|]`, `email[;]` → array with specified delimiter
- Array fields with default delimiter: `phone[]` → array with `~` delimiter
- Structured fields with explicit delimiter: `geo^(lat^lon)` → structure with `^` delimiter
- Structured fields with default delimiter: `address(street^city^state)` → structure with `^` default
- Array of structures: `address[~]^(street^city^state^zip)` → array of structures
- Nested structures: `location^(name^coords:(lat:lon))` → structure containing structure
- Arrays within structures: `address[~]^(type^lines[;]^city^state^zip)` → structure with array component
- Complex nested: `items[~]^(sku^name^qty^price^opts[;]:(k:v))` → the e-commerce example from spec

**Produce a data model** (in `models.py`) that represents each field type:
- `SimpleField(name)`
- `ArrayField(name, delimiter, element_type)` where element_type can be simple or structured
- `StructField(name, component_delimiter, components: list[Field])`

### Phase 2: Simple Array Parsing

Parse data values for array fields.

**Test cases:**
- `phone[|]` with value `555-1234|555-5678|555-9012` → `["555-1234", "555-5678", "555-9012"]`
- `email[;]` with value `john@work.com;john@home.com` → `["john@work.com", "john@home.com"]`
- `phone[]` with value `555-1234~555-5678` → `["555-1234", "555-5678"]` (default `~`)
- Single value (no delimiter present): `555-4444` → `["555-4444"]`
- Empty values between delimiters: `urgent||priority` → `["urgent", "", "priority"]`
- Empty field: `` → `[]`

### Phase 3: Structure Parsing

Parse data values for structured fields.

**Test cases:**
- `geo^(lat^lon)` with value `34.0522^-118.2437` → `{"lat": "34.0522", "lon": "-118.2437"}`
- `address^(street^city^state^zip)` with value `123 Main St^LA^CA^90210` → dict with 4 keys
- Component count mismatch: fewer components than declared → handle gracefully (fill with None or empty)
- Component count mismatch: more components than declared → handle gracefully (warn or error)

### Phase 4: Array of Structures

Parse repeated structures.

**Test cases:**
- `address[~]^(street^city^state^zip)` with value `123 Main St^Los Angeles^CA^90210~456 Oak Ave^New York^NY^10001` → list of 2 address dicts
- Single structure (no repetition delimiter): `789 Pine St^Boston^MA^02101` → list of 1 dict
- From spec Figure 6: the John example with 2 addresses

### Phase 5: Nested Structures

Parse structures within structures and arrays within structures.

**Test cases:**
- Array within structure: `address[~]^(type^lines[;]^city^state^zip)` with value `home^123 Main;Apt 4^LA^CA^90210~work^456 Oak^NY^NY^10001`
- Structure within structure: `location^(name^coords:(lat:lon))` with value `Office^34.05:-118.24`
- The e-commerce example from Appendix B: `items[~]^(sku^name^qty^price^opts[;]:(k:v))`

### Phase 6: Quoting and Escaping

Handle RFC 4180 quoting at leaf level.

**Test cases:**
- Quoted leaf in array: `notes[|]` with value `First note|"Second note with | pipe"|Third note` → 3 items, second contains literal `|`
- Quoted leaf in structure: `address^(street^city^state^zip)` with value `"123 Main St, Apt 4"^Springfield^IL^62701` → street contains comma
- **Invalid quoting (must reject):** entire array value quoted: `"First note|Second note|Third note"` for `notes[|]`
- **Invalid quoting (must reject):** entire structure value quoted: `"123 Main St^Springfield^IL^62701"` for `address^(street^city^state^zip)`

### Phase 7: Full Parser Integration

Wire everything together into a main `parse()` function.

**Test cases — use every example from the spec:**
1. Figure 1: Arrays with explicit delimiters
2. Figure 2: Arrays with default delimiters
3. Figure 3: Empty values in arrays
4. Figure 4: Simple structure (geo)
5. Figure 5: Repeated structures (address)
6. Figure 6: Array within structure
7. Figure 7: Structure within structure
8. Appendix B: E-commerce order (complex nested)

**API should look roughly like:**
```python
import csvpp

# Parse a CSV++ string
records = csvpp.parse(csvpp_string)
# records is a list of dicts, where values are:
#   - str for simple fields
#   - list[str] for arrays
#   - dict for structures
#   - list[dict] for array of structures
#   - nested combinations thereof

# Parse a CSV++ file
records = csvpp.parse_file("orders.csvpp")
```

### Phase 8: Validation & Error Handling

- Reject nested arrays with empty brackets `[]` (must specify explicit delimiter)
- Reject same delimiter used at multiple nesting levels
- Warn on deep nesting (>3-4 levels)
- Reject invalid quoting of non-leaf elements
- Handle malformed headers gracefully with clear error messages

## Key Rules from the Spec

1. Header row is **REQUIRED** in all CSV++ documents
2. Default array delimiter: `~` (top-level only)
3. Default component delimiter: `^`
4. Nested arrays **MUST** use explicit, distinct delimiters
5. RFC 4180 quoting applies **ONLY** to leaf elements
6. Delimiters at each nesting level **MUST** be different
7. Use Python's `csv` module for initial field-level parsing, then apply CSV++ parsing on each field's value based on its header declaration

## What NOT to Focus On

- Performance optimization
- Streaming/incremental parsing
- Writing/serialization (parsing only for now)
- Field separator auto-detection (assume comma)
- BOM handling
- MIME type handling
