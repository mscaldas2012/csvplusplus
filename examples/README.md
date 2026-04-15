# CSV++ Examples

Real-world datasets converted to CSV++ to demonstrate how the format solves genuine data engineering pain points. Each example includes the original source files, a converter script, and the generated CSV++ output.

---

## The Core Problem

Standard CSV (RFC 4180) has no way to express one-to-many relationships or structured sub-fields. When data has these shapes, teams are forced into one of three bad choices:

- **Flatten** — lose meaning, create data bloat, make updates painful
- **Multiple files** — break atomicity, require JOINs to reassemble what was one thing
- **Ad-hoc delimiters** — stuff `"Drama, Thriller, Action"` into a cell and hope downstream parsers agree on how to split it

CSV++ fixes this with two additions declared in column headers:
- `field[]` — an array field, values separated by `~`
- `field^(comp1^comp2)` — a structured field with named components
- `field[](comp1^comp2)` — an array of structs (both combined)

Both are 100% backward-compatible: any standard CSV parser opens a `.csvpp` file without errors.

---

## Examples

### 1. `netflix/` — The Ad-hoc Delimiter Problem

**Dataset:** [Netflix Movies and TV Shows](https://www.kaggle.com/datasets/shivamb/netflix-shows) (Kaggle, ~8,800 titles)
**Source:** 1 CSV file
**Output:** 1 CSV++ file

The Netflix dataset stores genres, cast members, and countries of origin as comma-separated strings inside CSV fields — a homegrown workaround with no schema, no contract, and no standard. Every consumer re-implements the same fragile `split(",")` logic independently.

**CSV++ fix:** Four column headers renamed with `[]` declarations. Values switched from comma-separated to tilde-separated. The schema is now in the file.

| Original header | CSV++ header  |
|-----------------|---------------|
| `director`      | `director[]`  |
| `cast`          | `cast[]`      |
| `country`       | `country[]`   |
| `listed_in`     | `genres[]`    |

**Key stat:** 25 rows → 40 multi-valued fields, 179 array separators. At full dataset scale (~8,800 rows), this represents millions of ad-hoc comma splits replaced by a single declared schema.

**Best for:** Explaining CSV++ to a general technical audience. Simple, instantly relatable.

---

### 2. `ecommerce/` — The Multiple-Files Problem

**Dataset:** Inspired by [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle, 100k orders, 9 files)
**Source:** 5 separate CSV files
**Output:** 1 CSV++ file

An e-commerce order is one business concept. In the Olist dataset it lives across 9 separate CSV files — orders, line items, payments, reviews, customers, products, sellers, geolocation, and category translations — because flat CSV cannot represent one-to-many relationships. Every analysis requires a multi-table JOIN to reconstruct a single order.

**CSV++ fix:** 5 source files merged into one. Each order becomes one row. Line items and payments become arrays of structured fields. Review becomes an embedded struct.

| CSV++ column | What it replaces |
|---|---|
| `items[](product_id^seller_id^category^price^freight)` | `order_items.csv` (many rows per order) |
| `payments[](type^installments^value)` | `order_payments.csv` (many rows per order, split payments) |
| `review^(score^title^comment)` | `order_reviews.csv` (joined separately) |

**Key stat:** 5 files, 17 item rows, 12 payment rows → 10 output rows, one per order. Zero JOINs required.

**Best for:** Data engineers. The "multiple files" pain is universally felt.

---

### 3. `healthcare/` — The HL7v2 Parallel

**Dataset:** Schema from [Synthea™ Synthetic Patient Population Simulator](https://synthetichealth.github.io/synthea/) by MITRE
**Source:** 6 separate CSV files
**Output:** 1 CSV++ file
**Standards used:** SNOMED CT (diagnoses), RxNorm (medications), LOINC (labs & vitals)

> *"HL7v2 has encoded clinical data using delimiter-hierarchical fields since 1989. CSV++ applies the same proven idea to general-purpose CSV."*

Clinical data is the most structurally complex of the three examples. A single patient encounter spans 6 files — demographics, visit records, diagnoses, prescriptions, observations, and allergies. The Synthea schema even exhibits a telling anti-pattern: `Reaction1 / Description1 / Severity1 / Reaction2 / Description2 / Severity2` column duplication, because flat CSV has no array type.

**CSV++ fix:** 6 source files merged into one encounter-centric file. Real medical coding standards are preserved in structured fields. The Reaction1/Reaction2 anti-pattern is replaced with a proper `allergies[]` array.

| CSV++ column | What it replaces |
|---|---|
| `conditions[](snomed^description^onset)` | `conditions.csv` (SNOMED coded diagnoses, many per encounter) |
| `medications[](rxnorm^description^reason)` | `medications.csv` (RxNorm coded prescriptions, many per encounter) |
| `vitals^(systolic^diastolic^heart_rate^temp_cel^bmi^o2_sat)` | 6 rows in `observations.csv` |
| `labs[](loinc^description^value^units)` | remaining rows in `observations.csv` (LOINC coded) |
| `allergies[](allergen^reaction^severity)` | `allergies.csv` (fixing the Reaction1/Reaction2 anti-pattern) |

**Key stat:** 6 files, 70 observation rows, 22 medication rows, 16 condition rows → 8 output rows, one per encounter. Real Synthea CSV exports are a direct drop-in — just download from [synthea.mitre.org/downloads](https://synthea.mitre.org/downloads).

**Best for:** Healthcare IT audience and IETF reviewers. The HL7v2 connection gives CSV++ a 35-year precedent.

---

## CSV++ Feature Coverage

| Feature | Netflix | E-Commerce | Healthcare |
|---|:---:|:---:|:---:|
| Simple array `field[]` | ✓ | | |
| Array of structs `field[](a^b^c)` | | ✓ | ✓ |
| Single struct `field^(a^b^c)` | | ✓ | ✓ |
| Multi-file consolidation | | ✓ | ✓ |
| Real-world coding standards | | | ✓ (SNOMED/RxNorm/LOINC) |
| Anti-pattern fix | ✓ (comma-in-field) | | ✓ (column duplication) |

---

## Running the Converters

All converters use Python 3.6+ standard library only — no pip install required.

```bash
python examples/netflix/convert_to_csvpp.py
python examples/ecommerce/convert_to_csvpp.py
python examples/healthcare/convert_to_csvpp.py
```

---

## Learn More

- **Spec:** [csvplusplus.com](https://csvplusplus.com)
- **IETF Draft:** [draft-mscaldas-csvpp-02](https://datatracker.ietf.org/doc/draft-mscaldas-csvpp/)
