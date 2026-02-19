# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CSV++ is an IETF Internet-Draft specification extending RFC 4180 (CSV) to support arrays and structured/nested fields while remaining backward compatible with standard CSV parsers. This is a **documentation/specification project** — there is no source code to build or test.

## Repository Structure

- `spec/` — RFC specification documents
  - `draft-mscaldas-csvpp-02.xml` — **Source of truth.** Current IETF draft (RFC XML v3). All other spec files are generated from this.
  - `change.log` — Version history between drafts
  - `generated/` — Generated outputs (ignored by git): rendered TXT, HTML, PDF of previous drafts
- `website/index.html` — Single-page marketing/info site (self-contained HTML/CSS/JS)
- `docs/one-pager-marketing.txt` — Executive summary and positioning

## CSV++ Format Design

**Core syntax extensions over RFC 4180:**
- **Array fields**: Declared in column header as `field[]` or `field[delimiter]`; values separated by `~` (tilde, default array separator)
- **Structured fields**: Declared as `field^(comp1^comp2)`; components separated by `^` (caret, default component separator)
- **Nesting**: Arrays and structures compose recursively (recommended max depth: 3–4 levels)

**Delimiter hierarchy** (inspired by HL7v2): `~` (repetitions) → `^` (components) → `;` (sub-components) → `:` (sub-sub-components) → `,` (deeper)

**Key design constraints:**
- Backward compatibility: standard CSV parsers must read CSV++ files without errors
- Structure is declared in column headers, not in data cells
- Default delimiters are chosen to avoid shell/SQL/CSV control characters
- Injection protection via RFC 4180 quoting rules; depth/size limits for complexity attack mitigation
- Encoding: UTF-8 recommended; BOM supported

## Working with Spec Files

The only source file is `spec/draft-mscaldas-csvpp-02.xml` (RFC XML v3). All rendered outputs (TXT, HTML, PDF) are generated from it and live in `spec/generated/` (gitignored). When updating the spec:
1. Edit `spec/draft-mscaldas-csvpp-02.xml`
2. Log changes in `spec/change.log`

The current IETF draft identifier is `draft-mscaldas-csvpp-02`. The next version would be `draft-mscaldas-csvpp-03`.

## Website

`website/index.html` is a fully self-contained single-file site (no external build step). It includes an interactive radar chart comparing CSV++ with CSV, JSON, and XML, and a contact form pointing to the project email.
