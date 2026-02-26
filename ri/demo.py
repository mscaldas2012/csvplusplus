#!/usr/bin/env python3
"""
demo.py — visual tour of csvpp.pprint()

Run with:
    python demo.py
    python demo.py | less      # page through it
    python demo.py --no-color  # force plain text
"""

import sys
import csvpp

color = "--no-color" not in sys.argv


def header(title: str) -> None:
    width = 66
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


# ---------------------------------------------------------------------------
# 1. Simple fields
# ---------------------------------------------------------------------------
header("1. Simple fields")

records = csvpp.parse(
    "id,name\n"
    "1,Alice\n"
    "2,Bob\n"
    "3,Carol\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 2. Array fields — explicit delimiters  (Figure 1)
# ---------------------------------------------------------------------------
header("2. Array fields — explicit delimiters  (spec Figure 1)")

records = csvpp.parse(
    "id,name,phone[|],email[;]\n"
    "1,John,555-1234|555-5678|555-9012,john@work.com;john@home.com\n"
    "2,Jane,555-4444,jane@company.com\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 3. Array fields — default ~ delimiter  (Figure 2)
# ---------------------------------------------------------------------------
header("3. Array fields — default ~ delimiter  (spec Figure 2)")

records = csvpp.parse(
    "id,name,phone[],email[]\n"
    "1,John,555-1234~555-5678~555-9012,john@work.com~john@home.com\n"
    "2,Jane,555-4444,jane@company.com\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 4. Empty values in an array  (Figure 3)
# ---------------------------------------------------------------------------
header("4. Empty values in an array  (spec Figure 3)")

records = csvpp.parse(
    "id,tags[|]\n"
    "1,urgent||priority\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 5. Simple structure  (Figure 4)
# ---------------------------------------------------------------------------
header("5. Simple structure — geo^(lat^lon)  (spec Figure 4)")

records = csvpp.parse(
    "id,name,geo^(lat^lon)\n"
    "1,Location A,34.0522^-118.2437\n"
    "2,Location B,40.7128^-74.0060\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 6. Array of structures  (Figure 5)
# ---------------------------------------------------------------------------
header("6. Array of structures — address[~]^(...)  (spec Figure 5)")

records = csvpp.parse(
    "id,name,address[~]^(street^city^state^zip)\n"
    "1,John,123 Main St^Los Angeles^CA^90210~456 Oak Ave^New York^NY^10001\n"
    "2,Jane,789 Pine St^Boston^MA^02101\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 7. Array within structure  (Figure 6)
# ---------------------------------------------------------------------------
header("7. Array within structure — lines[;] inside address  (spec Figure 6)")

records = csvpp.parse(
    "id,name,address[~]^(type^lines[;]^city^state^zip)\n"
    "1,John,home^123 Main;Apt 4^LA^CA^90210~work^456 Oak^NY^NY^10001\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 8. Structure within structure  (Figure 7)
# ---------------------------------------------------------------------------
header("8. Structure within structure — coords:(lat:lon)  (spec Figure 7)")

records = csvpp.parse(
    "id,location^(name^coords:(lat:lon))\n"
    "1,Office^34.05:-118.24\n"
    "2,Home^40.71:-74.00\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 9. E-commerce — 4-level nesting  (Appendix B)
# ---------------------------------------------------------------------------
header("9. E-commerce order — 4-level nesting  (spec Appendix B)")

records = csvpp.parse(
    "id,cust,items[~]^(sku^name^qty^price^opts[;]:(k:v))\n"
    "1,Alice,S1^Shirt^2^20^sz:M;col:blu~S2^Pant^1^50^sz:32\n"
)
csvpp.pprint(records, color=color)

# ---------------------------------------------------------------------------
# 10. top= parameter demo
# ---------------------------------------------------------------------------
header("10. top=2 — show only first 2 of 5 records")

records = csvpp.parse(
    "id,name,role\n"
    "1,Alice,engineer\n"
    "2,Bob,designer\n"
    "3,Carol,manager\n"
    "4,Dave,engineer\n"
    "5,Eve,analyst\n"
)
csvpp.pprint(records, top=2, color=color)

print()
