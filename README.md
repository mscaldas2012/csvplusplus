# CSV++

**CSV with arrays and structured fields — backward-compatible with every CSV tool you already use.**

[![IETF Draft](https://img.shields.io/badge/IETF-draft--mscaldas--csvpp--02-blue)](https://datatracker.ietf.org/doc/draft-mscaldas-csvpp/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](ri/)
[![No dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)](ri/pyproject.toml)
[![Website](https://img.shields.io/badge/website-csvplusplus.com-informational)](https://csvplusplus.com)

---

## The problem

Every time your data has one-to-many relationships, flat CSV forces a bad tradeoff:

- **Flatten it** → lose meaning, create bloat, make updates painful
- **Split into multiple files** → break atomicity, require JOINs to reassemble one thing
- **Stuff it into a field** → `"Drama, Thriller, Action"` — ad-hoc, unspecified, fragile

The Netflix dataset stores genres as `"Dramas, International Movies, Thrillers"`. Every consumer re-implements the same fragile `split(",")`. The Olist e-commerce dataset stores one order across 9 separate CSV files. Every analysis starts with a 5-way JOIN. These aren't edge cases — they're the normal shape of relational data, and CSV has never had a standard answer.

**CSV++ is that answer.**

---

## The fix — two additions to column headers

```csv
# Before — ad-hoc, no schema, every consumer guesses
title,cast,genres
Inception,"Leonardo DiCaprio, Joseph Gordon-Levitt","Action, Sci-Fi, Thriller"

# After — schema declared in the header, values unambiguous
title,cast[],genres[]
Inception,Leonardo DiCaprio~Joseph Gordon-Levitt,Action~Sci-Fi~Thriller
```

That's it. Add `[]` to a column header to declare it an array. Use `~` to separate values. **Any standard CSV parser opens the file without errors** — the `[]` suffix is just a column name to tools that don't understand it.

For structured sub-fields (like order line items or clinical vitals), use `^`:

```csv
order_id,items[](product^qty^price),review^(score^comment)
ORD-001,Widget^2^19.99~Gadget^1^49.99,5^Arrived ahead of schedule
ORD-002,Sprocket^1^8.50,4^Good quality
```

---

## Try it in 30 seconds

```bash
pip install -e "ri/[dev]"
```

```python
import csvpp

# Array fields → lists
records = csvpp.parse("""title,cast[],genres[]
Inception,Leonardo DiCaprio~Joseph Gordon-Levitt,Action~Sci-Fi~Thriller
The Matrix,Keanu Reeves~Laurence Fishburne,Action~Sci-Fi
""")

records[0]["cast"]    # ["Leonardo DiCaprio", "Joseph Gordon-Levitt"]
records[0]["genres"]  # ["Action", "Sci-Fi", "Thriller"]

# Array of structs → list of dicts
records = csvpp.parse("""order_id,items[](product^qty^price)
ORD-001,Widget^2^19.99~Gadget^1^49.99
""")

records[0]["items"]
# [{"product": "Widget", "qty": "2", "price": "19.99"},
#  {"product": "Gadget", "qty": "1", "price": "49.99"}]

# Struct field → dict
records = csvpp.parse("""patient_id,vitals^(systolic^diastolic^heart_rate)
PAT-001,138^88^76
""")

records[0]["vitals"]  # {"systolic": "138", "diastolic": "88", "heart_rate": "76"}
```

The reference implementation has **no runtime dependencies** — pure Python standard library.

---

## Syntax

| Feature | Header | Example value | Parsed as |
|---|---|---|---|
| Simple field | `name` | `Alice` | `str` |
| Array (default `~`) | `tags[]` | `python~csv~data` | `list[str]` |
| Array (custom delimiter) | `phone[\]` | `555-1234\555-5678` | `list[str]` |
| Struct | `geo^(lat^lon)` | `34.05^-118.24` | `dict` |
| Array of structs | `items[](sku^qty^price)` | `A1^2^9.99~B2^1^4.99` | `list[dict]` |
| Nested struct | `loc^(name^coords:(lat:lon))` | `HQ^37.77:-122.41` | `dict` |

**Delimiter hierarchy** (inspired by HL7v2): `~` (arrays) → `^` (components) → `;` → `:` → `,`

---

## Real-world examples

Three real datasets converted to CSV++ — source files, converter scripts, and output included.

### [`examples/netflix/`](examples/netflix/) — The ad-hoc delimiter problem

The Netflix dataset stores cast, genres, and country as comma-separated strings inside CSV fields. Every consumer writes the same fragile `split(",")`. CSV++ declares the schema in four header renames — zero other changes.

```csv
# Original
cast,listed_in
"Ama Qamata, Khosi Ngema, Gail Mabalane","International TV Shows, TV Dramas"

# CSV++
cast[],genres[]
Ama Qamata~Khosi Ngema~Gail Mabalane,International TV Shows~TV Dramas
```

### [`examples/ecommerce/`](examples/ecommerce/) — The multiple-files problem

Inspired by the [Brazilian Olist e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (100k orders, 9 CSV files). One order with 3 items and a split payment spans 8 rows across 5 files. CSV++ collapses it to one row.

```csv
order_id,items[](product^seller^price^freight),payments[](type^installments^value),review^(score^comment)
ORD-0003,PROD-C01^SELL-Z30^39.90^6.50~PROD-C02^SELL-Z30^59.90^6.50,credit_card^6^150.30~voucher^1^51.50,3^Delivery took longer than expected
```

**5 files → 1 file. Zero JOINs required.**

### [`examples/healthcare/`](examples/healthcare/) — The HL7v2 parallel

Inspired by [Synthea™](https://synthetichealth.github.io/synthea/) synthetic patient data (SNOMED, RxNorm, LOINC coded). 6 source files per encounter, including Synthea's own `Reaction1/Reaction2` column-duplication anti-pattern. CSV++ fixes both.

```csv
conditions[](snomed^description^onset),medications[](rxnorm^description^reason),vitals^(systolic^diastolic^heart_rate^temp_cel^bmi^o2_sat)
84114007^Heart failure^2017-08-12~49436004^Atrial fibrillation^2016-02-28,310429^Furosemide 20 MG^Heart failure~855332^Warfarin 5 MG^Atrial fibrillation,158^96^110^37.2^28.1^91
```

> *HL7v2 has encoded clinical data with delimiter-hierarchical fields since 1989. CSV++ applies the same proven pattern to general-purpose CSV.*

---

## Backward compatibility

CSV++ files are valid RFC 4180 CSV. Open them in Excel, pandas, or any standard CSV tool — they work. The `[]` and `^()` syntax in column headers is just a column name to tools that don't know about it. CSV++ parsers additionally read the declarations and return structured data.

```python
import pandas as pd

# Works fine — genres column is a string like "Action~Sci-Fi~Thriller"
df = pd.read_csv("examples/netflix/netflix_titles.csvpp")

# CSV++ parser returns it as a proper list
import csvpp
records = csvpp.parse_file("examples/netflix/netflix_titles.csvpp")
records[0]["genres"]  # ["Action", "Sci-Fi", "Thriller"]
```

---

## Repository layout

```
csvplusplus/
├── spec/
│   └── draft-mscaldas-csvpp-02.xml   ← IETF draft (source of truth)
├── ri/                                ← Python reference implementation
│   ├── src/csvpp/                     ← parser (no dependencies)
│   ├── tests/                         ← 88 tests
│   └── demo.py                        ← visual tour of the parser
├── examples/
│   ├── README.md                      ← examples overview
│   ├── netflix/                       ← ad-hoc delimiter → array headers
│   ├── ecommerce/                     ← 5 files → 1 file
│   └── healthcare/                    ← 6 files → 1 file (HL7v2 parallel)
└── website/
    └── index.html                     ← csvplusplus.com (self-contained)
```

---

## Spec & status

CSV++ is an IETF Internet-Draft extending [RFC 4180](https://www.rfc-editor.org/rfc/rfc4180).

- **Current draft:** [`draft-mscaldas-csvpp-02`](https://datatracker.ietf.org/doc/draft-mscaldas-csvpp/)
- **Website:** [csvplusplus.com](https://csvplusplus.com)
- **Status:** Individual submission, seeking community review

The draft is looking for real-world feedback. If you use CSV++ in a project, encounter an edge case, or have thoughts on the delimiter choices or syntax — open a [GitHub Discussion](https://github.com/mscaldas/csvplusplus/discussions) or comment on the IETF datatracker.

---

## Contributing & feedback

The most valuable contributions right now are:

- **Try it** — run the converter on your own CSV data, report friction
- **Review the spec** — open an issue if you find ambiguity or missing cases
- **IETF review** — comment on [`apps-discuss@ietf.org`](mailto:apps-discuss@ietf.org) or the datatracker
- **Share examples** — PRs adding real-world conversions to `examples/` are very welcome

```bash
git clone https://github.com/mscaldas/csvplusplus
cd csvplusplus/ri
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest          # 88 tests
python demo.py  # visual tour
```

---

*CSV++: same simplicity, more power, zero barriers to adoption.*
