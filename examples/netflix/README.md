# CSV++ Example: Netflix Titles

> **Dataset:** [Netflix Movies and TV Shows](https://www.kaggle.com/datasets/shivamb/netflix-shows) (Kaggle)
> **Sample size:** 25 titles — representative of the full ~8,800-row dataset
> **Source format:** Standard CSV (RFC 4180)
> **Target format:** CSV++ ([draft-mscaldas-csvpp-02](https://csvplusplus.com))

---

## The Problem This Solves

The Netflix dataset is a textbook example of a very common data engineering pain point: **multi-valued fields stored as comma-separated strings inside a CSV field**.

Open `netflix_titles.csv` and look at these three columns:

```
cast      → "Ama Qamata, Khosi Ngema, Gail Mabalane, Thabang Molaba, Dillon Windvogel"
listed_in → "International TV Shows, TV Dramas, TV Mysteries"
country   → "United States, Germany"
```

These aren't text strings — they're **lists**. But because standard CSV has no way to declare a field as a list, every tool that consumes this dataset has to guess: split on commas? But what about titles with commas in them? What about trailing whitespace? What about empty values?

This is a solved problem in other domains (HL7v2 has had delimiter hierarchies since 1989), but CSV has never had a standard answer. So everyone invents their own convention — and it breaks everywhere differently.

**CSV++ is the standard answer.**

---

## What Changed

### Header declarations (the only structural change)

| Original header | CSV++ header  | Meaning                              |
|-----------------|---------------|--------------------------------------|
| `director`      | `director[]`  | This field is an array               |
| `cast`          | `cast[]`      | This field is an array               |
| `country`       | `country[]`   | This field is an array               |
| `listed_in`     | `genres[]`    | This field is an array (also renamed for clarity) |

The `[]` suffix in the header is the **entire CSV++ extension**. Nothing else in the file changes structurally.

### Value encoding

Array values are separated by `~` (tilde), the CSV++ default array separator — chosen specifically because it never appears in natural language text and doesn't conflict with shell, SQL, or CSV special characters.

**Before (original CSV):**
```csv
cast,listed_in,country
"Ama Qamata, Khosi Ngema, Gail Mabalane",International TV Shows,South Africa
"Luna Wedler, Jannis Niewöhner, Milan Peschel","Dramas, International Movies, Thrillers","Germany, Czech Republic"
```

**After (CSV++):**
```csv
cast[],genres[],country[]
Ama Qamata~Khosi Ngema~Gail Mabalane,International TV Shows,South Africa
Luna Wedler~Jannis Niewöhner~Milan Peschel,Dramas~International Movies~Thrillers,Germany~Czech Republic
```

---

## Conversion Stats (this sample)

| Metric                       | Value |
|------------------------------|-------|
| Rows converted               | 25    |
| Fields with multiple values  | 40    |
| Array separators introduced  | 179   |
| Columns converted to arrays  | 4     |

In the full dataset (8,807 titles), almost every row has multi-valued `cast` and `genres` fields — the scale of the ambiguity problem is enormous.

---

## Why This Matters for Consumers

### Standard CSV parsers (Excel, pandas, etc.)
They read `netflix_titles.csvpp` without errors or warnings. The `[]` suffix in headers is legal column name syntax. Values appear as tilde-separated strings, exactly as entered. **Zero breakage.**

```python
import pandas as pd
df = pd.read_csv("netflix_titles.csvpp")  # works fine
df["cast[]"].iloc[1]  # → "Ama Qamata~Khosi Ngema~Gail Mabalane~..."
```

### CSV++ parsers
They read the `[]` declaration and automatically parse array fields into proper lists.

```python
import csvpp  # hypothetical CSV++ parser
df = csvpp.read("netflix_titles.csvpp")
df["cast"].iloc[1]  # → ["Ama Qamata", "Khosi Ngema", "Gail Mabalane", ...]
df["genres"].iloc[1]  # → ["International TV Shows", "TV Dramas", "TV Mysteries"]
```

No split-on-comma logic. No strip-whitespace boilerplate. No regex. **The schema is in the header.**

---

## What the Original Dataset Forces You To Do

Every team consuming the Netflix dataset today writes something like this:

```python
# Parse genres — but watch out for the edge cases
df["genres"] = df["listed_in"].str.split(",").apply(
    lambda x: [g.strip() for g in x] if isinstance(x, list) else []
)

# Parse cast — same thing, hope for no commas in names
df["cast_list"] = df["cast"].str.split(",").apply(
    lambda x: [c.strip() for c in x] if isinstance(x, list) else []
)

# Parse country — same thing again
df["countries"] = df["country"].str.split(",").apply(
    lambda x: [c.strip() for c in x] if isinstance(x, list) else []
)
```

This code is written thousands of times across thousands of notebooks, pipelines, and scripts consuming this one dataset. It's fragile (actor name with comma → silent data corruption), undocumented (the schema is not in the file), and inconsistent (each team handles edge cases differently).

CSV++ eliminates this entire class of problem at the source.

---

## Files in This Folder

| File                       | Description                                              |
|----------------------------|----------------------------------------------------------|
| `netflix_titles.csv`       | Original format — comma-separated values in cast/genres/country fields |
| `netflix_titles.csvpp`     | CSV++ format — proper array declarations in headers, tilde-separated values |
| `convert_to_csvpp.py`      | The converter script — see the transformation logic      |
| `README.md`                | This file                                                |

---

## Run the Converter Yourself

```bash
python convert_to_csvpp.py
```

Requires Python 3.6+ and no external dependencies (uses stdlib `csv` only).

---

## Learn More

- **Spec:** [csvplusplus.com](https://csvplusplus.com)
- **IETF Draft:** [draft-mscaldas-csvpp-02](https://datatracker.ietf.org/doc/draft-mscaldas-csvpp/)
- **Original dataset:** [Netflix Movies and TV Shows on Kaggle](https://www.kaggle.com/datasets/shivamb/netflix-shows)
