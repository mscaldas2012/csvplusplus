# CSV++ Example: Clinical Encounters (Healthcare)

> **Schema inspired by:** [Synthea™ Synthetic Patient Population Simulator](https://synthetichealth.github.io/synthea/) by MITRE
> **Sample:** 5 patients, 8 clinical encounters
> **Source format:** 6 separate CSV files (standard RFC 4180)
> **Target format:** 1 CSV++ file ([draft-mscaldas-csvpp-02](https://csvplusplus.com))
> **Standards used:** SNOMED CT (diagnoses), RxNorm (medications), LOINC (labs & vitals)

---

## The HL7v2 Connection

> *"HL7v2 has encoded clinical data using delimiter-hierarchical fields since 1989.
> CSV++ applies the same proven idea to general-purpose CSV."*

HL7v2 — the messaging standard running in virtually every hospital system worldwide — encodes a patient observation like this:

```
OBX|1|NM|4548-4^Hemoglobin A1c^LN||7.8|%|4.0-5.6||||F
```

Those `^` carets separating `4548-4`, `Hemoglobin A1c`, and `LN` are component separators. The `~` tilde separates repeated values. This is exactly CSV++'s delimiter hierarchy — not invented, but **standardised from a 35-year proven precedent**.

CSV++ doesn't compete with HL7v2. It generalises its best idea — structured delimiters declared in headers — to work with any CSV data, in any domain, readable by any spreadsheet.

---

## The Problem: 6 Files, One Clinical Visit

A single patient encounter involves data spread across 6 tables in Synthea (and in most EHR systems):

```
source/
├── patients.csv       ← demographics
├── encounters.csv     ← visit record (the output grain)
├── conditions.csv     ← diagnoses (SNOMED) — MANY per encounter
├── medications.csv    ← prescriptions (RxNorm) — MANY per encounter
├── observations.csv   ← vitals + labs (LOINC) — MANY per encounter
└── allergies.csv      ← allergy reactions — MANY per patient
```

A single encounter for a complex patient (e.g., heart failure + atrial fibrillation) produces:
- 1 row in `encounters.csv`
- 3 rows in `conditions.csv`
- 4 rows in `medications.csv`
- 10 rows in `observations.csv`
- 1 row in `allergies.csv`

**19 rows across 5 files** to describe one 90-minute clinic visit. Every analysis, every dashboard, every downstream system must reassemble this with JOINs.

### The allergies anti-pattern

Synthea's `allergies.csv` has a particularly telling design: `Reaction1`, `Description1`, `Severity1`, `Reaction2`, `Description2`, `Severity2`. When a patient has two reactions to the same allergen, **columns were duplicated** because there was no array type. This is the exact workaround CSV++ eliminates.

---

## CSV++ Features Used

### 1. Arrays of structured fields — conditions, medications, labs

Each uses the pattern `fieldname[](component1^component2^...)`:

**Diagnoses** (SNOMED coded):
```
conditions[](snomed^description^onset)
44054006^Type 2 diabetes mellitus^2015-06-01~59621000^Essential hypertension^2012-03-15~55822004^Hyperlipidemia^2018-09-20
```

**Medications** (RxNorm coded):
```
medications[](rxnorm^description^reason)
860975^Metformin 500 MG Oral Tablet^Type 2 diabetes mellitus~314076^Lisinopril 10 MG Oral Tablet^Essential hypertension
```

**Lab results** (LOINC coded):
```
labs[](loinc^description^value^units)
4548-4^Hemoglobin A1c^7.8^%~2339-0^Glucose^168^mg/dL~2160-0^Creatinine^1.2^mg/dL
```

### 2. Single structured field — vitals

Vitals are not a list — they're always a fixed set of measurements recorded together. A struct (not an array) is the right model:

```
vitals^(systolic^diastolic^heart_rate^temp_cel^bmi^o2_sat)
138^88^76^37.0^31.2^
```

The trailing `^` means O2 saturation wasn't recorded this visit. The structure is declared in the header — consumers know exactly what each position means without guessing.

### 3. Fixing the Reaction1/Reaction2 anti-pattern

Synthea's source CSV had to duplicate columns for multiple reactions:

```csv
Description,Reaction1,Description1,Severity1,Reaction2,Description2,Severity2
Penicillin,126485001,Urticaria,MODERATE,41291007,Angioedema,MILD
```

CSV++ flattens this into one array — no column count limit, no duplication:

```
allergies[](allergen^reaction^severity)
Penicillin^Urticaria^MODERATE~Penicillin^Angioedema^MILD~Sulfonamide^Drug eruption^MILD
```

---

## Before and After: ENC-005 (Emergency Admission)

Carlos Mendes, 72M, acute decompensated heart failure. **19 source rows → 1 CSV++ row.**

### Source: 5 files, 19 rows

**encounters.csv (1 row):**
```
ENC-005,2023-06-22T22:15:00Z,2023-06-23T18:00:00Z,PAT-003,emergency,...,Acute decompensated heart failure
```

**conditions.csv (3 rows):**
```
2017-08-12,,PAT-003,ENC-005,84114007,Heart failure (disorder)
2016-02-28,,PAT-003,ENC-005,49436004,Atrial fibrillation
2009-11-05,,PAT-003,ENC-005,59621000,Essential hypertension
```

**medications.csv (4 rows):**
```
PAT-003,ENC-005,310429,Furosemide 20 MG Oral Tablet,...
PAT-003,ENC-005,855332,Warfarin Sodium 5 MG Oral Tablet,...
PAT-003,ENC-005,866514,Metoprolol Succinate 25 MG...,...
PAT-003,ENC-005,314076,Lisinopril 10 MG Oral Tablet,...
```

**observations.csv (10 rows):**
```
2023-06-22,PAT-003,ENC-005,vital-signs,8480-6,Systolic Blood Pressure,158,mmHg,...
2023-06-22,PAT-003,ENC-005,vital-signs,8462-4,Diastolic Blood Pressure,96,mmHg,...
2023-06-22,PAT-003,ENC-005,vital-signs,59408-5,Oxygen saturation,91,%,...
2023-06-22,PAT-003,ENC-005,laboratory,33762-6,NT-proBNP,1200,ng/L,...
... (6 more rows)
```

**allergies.csv (1 row):**
```
PAT-003,ENC-004,387458008,SNOMED,Aspirin,allergy,medication,74474003,Gastrointestinal hemorrhage,SEVERE,,,
```

### Output: 1 CSV++ row

```
ENC-005,emergency,2023-06-22,PAT-003,Carlos Mendes,1951-11-08,M,Porto Alegre,RS,
Acute decompensated heart failure,
84114007^Heart failure (disorder)^2017-08-12~49436004^Atrial fibrillation^2016-02-28~59621000^Essential hypertension^2009-11-05,
310429^Furosemide 20 MG Oral Tablet^Heart failure (disorder)~855332^Warfarin Sodium 5 MG Oral Tablet^Atrial fibrillation — held for emergency~866514^Metoprolol Succinate 25 MG...~314076^Lisinopril 10 MG Oral Tablet^Essential hypertension,
158^96^110^37.2^28.1^91,
34714-6^INR^1.9^{INR}~33762-6^NT-proBNP^1200^ng/L~2160-0^Creatinine^1.7^mg/dL~2951-2^Sodium^135^mmol/L,
Aspirin^Gastrointestinal hemorrhage^SEVERE
```

The clinical story is right there in one row: BP 158/96, O2 sat down to 91%, NT-proBNP up to 1,200 ng/L, warfarin held. Readable, auditable, portable.

---

## Conversion Stats

| Metric | Value |
|--------|-------|
| Source files merged | 6 |
| Encounters in output | 8 |
| Condition rows collapsed | 16 → `conditions[]` arrays |
| Medication rows collapsed | 22 → `medications[]` arrays |
| Observation rows split | 70 → `vitals^()` struct + `labs[]` arrays |
| Allergy reactions flattened | 10 → `allergies[]` (fixing Reaction1/Reaction2) |

---

## Why This Matters for Healthcare IT

**Portability.** A single CSV++ encounter file can be emailed, version-controlled, diffed, and opened in Excel. A 6-file relational export cannot.

**Auditability.** Each row is a complete, self-describing clinical record. Changes between visits are visible in a plain diff.

**HL7v2 migration.** Teams moving from HL7v2 to flat-file exports lose the structured delimiter encoding. CSV++ preserves it in a format that's universally readable.

**FHIR alignment.** FHIR encodes the same concepts (conditions, medications, observations) as separate resources that must be assembled. CSV++ provides a flat, portable alternative for bulk export scenarios.

---

## Files in This Folder

```
healthcare/
├── source/
│   ├── patients.csv        ← patient demographics
│   ├── encounters.csv      ← clinical visits
│   ├── conditions.csv      ← diagnoses (SNOMED CT coded)
│   ├── medications.csv     ← prescriptions (RxNorm coded)
│   ├── observations.csv    ← vitals + lab results (LOINC coded)
│   └── allergies.csv       ← allergy reactions (note Reaction1/Reaction2 pattern)
├── clinical_encounters.csvpp   ← OUTPUT: one row per encounter
├── convert_to_csvpp.py         ← converter (stdlib only, no dependencies)
└── README.md                   ← this file
```

## Run It

```bash
python convert_to_csvpp.py
```

To use with real Synthea data, download a sample from [synthea.mitre.org/downloads](https://synthea.mitre.org/downloads) and point the converter at those CSV files — the schema is identical.

---

## Learn More

- **CSV++ Spec:** [csvplusplus.com](https://csvplusplus.com)
- **IETF Draft:** [draft-mscaldas-csvpp-02](https://datatracker.ietf.org/doc/draft-mscaldas-csvpp/)
- **Synthea:** [synthetichealth.github.io/synthea](https://synthetichealth.github.io/synthea/)
- **Synthea CSV Schema:** [CSV File Data Dictionary](https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary)
- **HL7v2:** [HL7 International](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185)
