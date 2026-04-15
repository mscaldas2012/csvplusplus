"""
Netflix CSV → CSV++ Converter
==============================
Demonstrates how three columns in the original Netflix dataset that use
ad-hoc comma-separated values inside a field get converted to proper
CSV++ array declarations:

  Original column  │  Problem                        │  CSV++ column
  ─────────────────┼─────────────────────────────────┼─────────────────────
  cast             │  "Actor A, Actor B, Actor C"    │  cast[]
  listed_in        │  "Dramas, Thrillers, Action"    │  genres[]
  country          │  "United States, Germany"       │  country[]

The director column is also converted to director[] because some titles
have multiple directors stored as "Director A, Director B".

Array values are separated with ~ (tilde), the CSV++ default array delimiter.
All other columns pass through unchanged.

Usage:
    python convert_to_csvpp.py
"""

import csv
import re
import os

INPUT_FILE  = os.path.join(os.path.dirname(__file__), "netflix_titles.csv")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "netflix_titles.csvpp")

# Columns that contain comma-separated lists and should become CSV++ arrays.
# Maps original column name → new CSV++ header name.
ARRAY_COLUMNS = {
    "cast":      "cast[]",
    "listed_in": "genres[]",
    "country":   "country[]",
    "director":  "director[]",
}

# The CSV++ array separator (default per spec)
ARRAY_SEP = "~"


def csv_list_to_csvpp_array(value: str) -> str:
    """
    Convert a comma-separated string like "Drama, Thriller, Action"
    into a CSV++ tilde-separated array like "Drama~Thriller~Action".

    Empty strings return empty strings (no array value).
    """
    if not value.strip():
        return ""
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return ARRAY_SEP.join(parts)


def convert(input_path: str, output_path: str) -> dict:
    stats = {"rows": 0, "array_values_converted": 0, "multi_value_fields": 0}

    with open(input_path, newline="", encoding="utf-8") as fin, \
         open(output_path, "w", newline="", encoding="utf-8") as fout:

        reader = csv.DictReader(fin)
        original_fieldnames = reader.fieldnames

        # Build new header list — rename array columns
        new_fieldnames = []
        for col in original_fieldnames:
            new_fieldnames.append(ARRAY_COLUMNS.get(col, col))

        writer = csv.DictWriter(fout, fieldnames=new_fieldnames,
                                quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for row in reader:
            new_row = {}
            for original_col, new_col in zip(original_fieldnames, new_fieldnames):
                val = row[original_col]
                if original_col in ARRAY_COLUMNS:
                    converted = csv_list_to_csvpp_array(val)
                    new_row[new_col] = converted
                    if ARRAY_SEP in converted:
                        stats["multi_value_fields"] += 1
                        stats["array_values_converted"] += converted.count(ARRAY_SEP)
                else:
                    new_row[new_col] = val

            writer.writerow(new_row)
            stats["rows"] += 1

    return stats


if __name__ == "__main__":
    print(f"Reading:  {INPUT_FILE}")
    print(f"Writing:  {OUTPUT_FILE}\n")

    stats = convert(INPUT_FILE, OUTPUT_FILE)

    print("✓ Conversion complete!")
    print(f"  Rows converted          : {stats['rows']}")
    print(f"  Multi-value array fields: {stats['multi_value_fields']}")
    print(f"  Array separators added  : {stats['array_values_converted']}")
    print()
    print("Column mapping applied:")
    for orig, new in ARRAY_COLUMNS.items():
        print(f"  {orig:12s} → {new}")
    print()
    print("What changed in the file:")
    print('  Header "cast"      → "cast[]"      (CSV++ array declaration)')
    print('  Header "listed_in" → "genres[]"    (CSV++ array declaration)')
    print('  Header "country"   → "country[]"   (CSV++ array declaration)')
    print('  Header "director"  → "director[]"  (CSV++ array declaration)')
    print('  Values  "A, B, C"  → "A~B~C"       (tilde-delimited array values)')
    print()
    print("The output file is 100% readable by any standard CSV parser.")
    print("CSV++ parsers additionally understand the [] header declarations")
    print("and return cast, genres, country, and director as proper lists.")
