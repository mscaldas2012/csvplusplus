"""
Synthea-style Clinical Data → CSV++ Converter
===============================================
Merges 6 source CSV files into ONE encounter-centric CSV++ file.

CSV++ features demonstrated
────────────────────────────
  1. Arrays of structured fields (conditions, medications, labs)

     conditions[](snomed^description^onset)
       → "44054006^Type 2 diabetes mellitus^2015-06-01~59621000^Essential hypertension^2012-03-15"

     medications[](rxnorm^description^reason)
       → "860975^Metformin 500 MG Oral Tablet^Type 2 diabetes mellitus~314076^Lisinopril 10 MG Oral Tablet^Essential hypertension"

     labs[](loinc^description^value^units)
       → "4548-4^Hemoglobin A1c^7.8^%~2339-0^Glucose^168^mg/dL"

  2. Single structured fields (vitals, which travel as a unit)

     vitals^(systolic^diastolic^heart_rate^temp_cel^bmi^o2_sat)
       → "138^88^76^37.0^31.2^"

  3. Allergies — fixing Synthea's Reaction1/Reaction2 anti-pattern

     In the source, Synthea encodes up to two reactions per allergy by
     duplicating columns (Reaction1, Description1, Severity1, Reaction2, ...).
     This is exactly the "add more columns" workaround that CSV++ replaces.

     CSV++ output:
     allergies[](allergen^reaction^severity)
       → "Penicillin^Urticaria^MODERATE~Penicillin^Angioedema^MILD~Sulfonamide^Drug eruption^MILD"

     Each reaction becomes its own array element — no column duplication needed.

Source files
────────────
  source/patients.csv      → demographics (joined by patient ID)
  source/encounters.csv    → one row per encounter (the output grain)
  source/conditions.csv    → many rows per encounter → conditions[]
  source/medications.csv   → many rows per encounter → medications[]
  source/observations.csv  → many rows per encounter → vitals^() + labs[]
  source/allergies.csv     → many rows per patient   → allergies[]

Usage:
    python convert_to_csvpp.py
"""

import csv
import os
from collections import defaultdict

HERE   = os.path.dirname(os.path.abspath(__file__))
SRC    = os.path.join(HERE, "source")
OUTPUT = os.path.join(HERE, "clinical_encounters.csvpp")

ARRAY_SEP = "~"
COMP_SEP  = "^"

# LOINC codes that are vital signs — everything else is a lab result
VITAL_LOINCS = {
    "8480-6":  "systolic",
    "8462-4":  "diastolic",
    "8867-4":  "heart_rate",
    "8310-5":  "temp_cel",
    "39156-5": "bmi",
    "59408-5": "o2_sat",
}


def read_csv(filename):
    with open(os.path.join(SRC, filename), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe(value):
    """Escape any stray component or array separators in a value."""
    return str(value).strip().replace(COMP_SEP, ",").replace(ARRAY_SEP, ",")


# ── load & index ─────────────────────────────────────────────────────────────

patients   = {r["Id"]: r for r in read_csv("patients.csv")}
encounters = read_csv("encounters.csv")

conditions_by_enc  = defaultdict(list)
medications_by_enc = defaultdict(list)
obs_by_enc         = defaultdict(list)
allergies_by_pat   = defaultdict(list)

for r in read_csv("conditions.csv"):
    conditions_by_enc[r["Encounter"]].append(r)

for r in read_csv("medications.csv"):
    medications_by_enc[r["Encounter"]].append(r)

for r in read_csv("observations.csv"):
    obs_by_enc[r["Encounter"]].append(r)

for r in read_csv("allergies.csv"):
    allergies_by_pat[r["Patient"]].append(r)


# ── builder helpers ───────────────────────────────────────────────────────────

def build_conditions(rows):
    elements = []
    for r in rows:
        elements.append(COMP_SEP.join([
            safe(r["Code"]),
            safe(r["Description"]),
            safe(r["Start"]),
        ]))
    return ARRAY_SEP.join(elements)


def build_medications(rows):
    elements = []
    for r in rows:
        elements.append(COMP_SEP.join([
            safe(r["Code"]),
            safe(r["Description"]),
            safe(r["ReasonDescription"]),
        ]))
    return ARRAY_SEP.join(elements)


def build_vitals_and_labs(rows):
    """
    Split observations into vitals struct and labs array.
    Vitals: fixed set of LOINC codes → one structured field with named slots.
    Labs:   everything else → array of (loinc^description^value^units).
    """
    vital_map = {}   # slot_name → value
    lab_elements = []

    for r in rows:
        loinc = r["Code"]
        if loinc in VITAL_LOINCS:
            vital_map[VITAL_LOINCS[loinc]] = safe(r["Value"])
        else:
            lab_elements.append(COMP_SEP.join([
                safe(loinc),
                safe(r["Description"]),
                safe(r["Value"]),
                safe(r["Units"]),
            ]))

    # vitals struct — empty string for any slot not recorded this encounter
    vitals = COMP_SEP.join([
        vital_map.get("systolic",   ""),
        vital_map.get("diastolic",  ""),
        vital_map.get("heart_rate", ""),
        vital_map.get("temp_cel",   ""),
        vital_map.get("bmi",        ""),
        vital_map.get("o2_sat",     ""),
    ])

    labs = ARRAY_SEP.join(lab_elements)
    return vitals, labs


def build_allergies(rows):
    """
    Flatten Synthea's Reaction1/Reaction2 column-duplication pattern into a
    proper CSV++ array. Each reaction (regardless of whether it's Reaction1 or
    Reaction2) becomes its own array element: allergen^reaction^severity.
    """
    elements = []
    for r in rows:
        allergen = safe(r["Description"])
        # Reaction 1
        if r.get("Description1", "").strip():
            elements.append(COMP_SEP.join([
                allergen,
                safe(r["Description1"]),
                safe(r["Severity1"]),
            ]))
        # Reaction 2 — in flat CSV this required an extra pair of columns
        if r.get("Description2", "").strip():
            elements.append(COMP_SEP.join([
                allergen,
                safe(r["Description2"]),
                safe(r["Severity2"]),
            ]))
    return ARRAY_SEP.join(elements)


# ── CSV++ header ──────────────────────────────────────────────────────────────
#
#   conditions[](snomed^description^onset)
#   medications[](rxnorm^description^reason)
#   vitals^(systolic^diastolic^heart_rate^temp_cel^bmi^o2_sat)
#   labs[](loinc^description^value^units)
#   allergies[](allergen^reaction^severity)

FIELDNAMES = [
    "encounter_id",
    "encounter_class",
    "encounter_date",
    "patient_id",
    "patient_name",
    "patient_dob",
    "patient_gender",
    "patient_city",
    "patient_state",
    "reason",
    "conditions[](snomed^description^onset)",
    "medications[](rxnorm^description^reason)",
    "vitals^(systolic^diastolic^heart_rate^temp_cel^bmi^o2_sat)",
    "labs[](loinc^description^value^units)",
    "allergies[](allergen^reaction^severity)",
]

stats = {
    "encounters": 0,
    "condition_rows": 0,
    "medication_rows": 0,
    "observation_rows": 0,
    "allergy_reactions": 0,
    "encounters_no_allergies": 0,
    "encounters_no_labs": 0,
}

with open(OUTPUT, "w", newline="", encoding="utf-8") as fout:
    writer = csv.DictWriter(fout, fieldnames=FIELDNAMES, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()

    for enc in encounters:
        eid = enc["Id"]
        pid = enc["Patient"]
        pat = patients.get(pid, {})

        conds = conditions_by_enc.get(eid, [])
        meds  = medications_by_enc.get(eid, [])
        obs   = obs_by_enc.get(eid, [])
        allgs = allergies_by_pat.get(pid, [])

        vitals_val, labs_val = build_vitals_and_labs(obs)
        allergies_val = build_allergies(allgs)

        writer.writerow({
            "encounter_id":    eid,
            "encounter_class": enc["EncounterClass"],
            "encounter_date":  enc["Start"][:10],
            "patient_id":      pid,
            "patient_name":    f"{pat.get('First','')} {pat.get('Last','')}".strip(),
            "patient_dob":     pat.get("BirthDate", ""),
            "patient_gender":  pat.get("Gender", ""),
            "patient_city":    pat.get("City", ""),
            "patient_state":   pat.get("State", ""),
            "reason":          enc.get("ReasonDescription", ""),
            "conditions[](snomed^description^onset)":                       build_conditions(conds),
            "medications[](rxnorm^description^reason)":                     build_medications(meds),
            "vitals^(systolic^diastolic^heart_rate^temp_cel^bmi^o2_sat)":   vitals_val,
            "labs[](loinc^description^value^units)":                        labs_val,
            "allergies[](allergen^reaction^severity)":                      allergies_val,
        })

        stats["encounters"]        += 1
        stats["condition_rows"]    += len(conds)
        stats["medication_rows"]   += len(meds)
        stats["observation_rows"]  += len(obs)
        stats["allergy_reactions"] += allergies_val.count(ARRAY_SEP) + (1 if allergies_val else 0)
        if not allergies_val:
            stats["encounters_no_allergies"] += 1
        if not labs_val:
            stats["encounters_no_labs"] += 1


# ── report ────────────────────────────────────────────────────────────────────

print(f"\n✓ Conversion complete → {OUTPUT}\n")
print(f"  Source files merged        : 6")
print(f"  Encounters written         : {stats['encounters']}")
print(f"  Condition rows collapsed   : {stats['condition_rows']}  → conditions[] arrays")
print(f"  Medication rows collapsed  : {stats['medication_rows']}  → medications[] arrays")
print(f"  Observation rows split     : {stats['observation_rows']}  → vitals^() struct + labs[] arrays")
print(f"  Allergy reactions flattened: {stats['allergy_reactions']}  → allergies[] (fixing Reaction1/Reaction2 anti-pattern)")
print(f"  Encounters with no allergies: {stats['encounters_no_allergies']}")
print()
print("  CSV++ features used:")
print("    conditions[](snomed^description^onset)                        — array of structs (SNOMED codes)")
print("    medications[](rxnorm^description^reason)                      — array of structs (RxNorm codes)")
print("    vitals^(systolic^diastolic^heart_rate^temp_cel^bmi^o2_sat)    — single struct field")
print("    labs[](loinc^description^value^units)                         — array of structs (LOINC codes)")
print("    allergies[](allergen^reaction^severity)                       — array of structs")
print()
print("  HL7v2 parallel:")
print("    HL7v2 OBX segments encode observations with exactly this delimiter hierarchy.")
print("    CSV++ brings the same proven pattern to general-purpose CSV.")
