# CSV++ Reference Implementation — Kanban Board

## Backlog

## In Progress

## Done

| # | Task | Notes |
|---|------|-------|
| 1 | Project setup (ri/ directory, pyproject.toml, README) | |
| 2 | Kanban board (this file) | |

---

## Phases

### Phase 1 — Header Parsing
**Goal:** Parse CSV++ column headers into typed field models.

| Status | Task |
|--------|------|
| ✅ Done | Define data models (`models.py`) |
| ✅ Done | Implement `header_parser.py` |
| ✅ Done | Write `tests/test_header_parser.py` |

### Phase 2 — Simple Array Parsing
**Goal:** Parse array field values using declared delimiters.

| Status | Task |
|--------|------|
| ✅ Done | Implement `value_parser.py` (array logic) |
| ✅ Done | Write `tests/test_arrays.py` |

### Phase 3 — Structure Parsing
**Goal:** Parse structured field values (components).

| Status | Task |
|--------|------|
| ✅ Done | Implement struct parsing in `value_parser.py` |
| ✅ Done | Write `tests/test_structures.py` |

### Phase 4 — Array of Structures
**Goal:** Parse repeated structures (array + struct combo).

| Status | Task |
|--------|------|
| ✅ Done | Implement array-of-struct parsing |
| ✅ Done | Write `tests/test_arrays.py` (extended) |

### Phase 5 — Nested Structures
**Goal:** Arrays within structures, structures within structures.

| Status | Task |
|--------|------|
| ✅ Done | Implement recursive nested parsing |
| ✅ Done | Write `tests/test_nested.py` |

### Phase 6 — Quoting and Escaping
**Goal:** RFC 4180 leaf-level quoting; reject invalid non-leaf quoting.

| Status | Task |
|--------|------|
| ✅ Done | Quote-aware split in `value_parser.py` |
| ✅ Done | Non-leaf quoting detection and rejection |
| ✅ Done | Write `tests/test_quoting.py` |

### Phase 7 — Full Parser Integration
**Goal:** Wire everything together via `parser.py`.

| Status | Task |
|--------|------|
| ✅ Done | Implement `parser.py` with `parse()` / `parse_file()` |
| ✅ Done | Write `tests/test_parser.py` |
| ✅ Done | Write `tests/test_examples.py` (all spec examples) |

### Phase 8 — Validation & Error Handling
**Goal:** Robust error messages and spec compliance validation.

| Status | Task |
|--------|------|
| ✅ Done | Reject nested `[]` without explicit delimiter |
| ✅ Done | Reject same delimiter at multiple nesting levels |
| ✅ Done | Warn on deep nesting (>3–4 levels) |
| ✅ Done | Reject invalid non-leaf quoting |
| ✅ Done | Write `tests/test_validation.py` |

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Use Python `csv` module only for outer comma-level parsing | Spec says "Use Python's built-in csv module for initial CSV parsing, then layer CSV++ semantics on top" |
| 2026-02-26 | Track `was_quoted` flag at CSV field level | Required to detect invalid non-leaf quoting |
| 2026-02-26 | Quote-aware split for inner array/struct delimiters | Leaf quoting must be respected at each nesting level |
| 2026-02-26 | Pass `used_delimiters: frozenset` through recursive header parsing | Required to enforce "distinct delimiter at each level" rule |
