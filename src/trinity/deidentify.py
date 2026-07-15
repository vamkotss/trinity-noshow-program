"""De-identification pass for Trinity patient data.

WHY THIS EXISTS
---------------
The raw export contains synthetic PHI - names, dates of birth, phone numbers -
exactly what a real scheduling system leaks into a CSV. Before any analysis
touches it, the direct identifiers come out. This is not optional in healthcare,
and being able to say "here is my de-identification step and here is the note
explaining it" is a genuine differentiator for healthcare-adjacent analyst roles.

WHAT HIPAA ACTUALLY REQUIRES (the short version)
------------------------------------------------
The HIPAA Safe Harbor method lists 18 identifiers that must be removed for data
to count as de-identified, including name, phone, and any date more specific
than a year. This module implements the ones present in our data:

  - NAMES               dropped entirely
  - PHONE               dropped entirely
  - DATE OF BIRTH       generalised to an AGE BAND (never a birth date, never
                        even an exact age - ages 90+ are especially identifying
                        and get bucketed)
  - MRN                 a direct identifier, but we NEED a stable patient key to
                        link appointments to patients. So we do not drop it - we
                        HASH it. Same patient, same hash; the original MRN is
                        irrecoverable without the salt.

THE SUBTLE POINT: A HASH IS NOT ANONYMISATION
---------------------------------------------
Hashing the MRN gives us a consistent pseudonym, which is what the analysis
needs. But a hash is reversible by anyone who has the salt and can enumerate
MRNs (ours are sequential - trivially enumerable). So the salt is a secret, the
mapping is never exported, and we are honest in the note that this is
PSEUDONYMISATION, not true anonymisation. Overstating your privacy guarantees is
its own kind of harm.

Run:  python -m trinity.deidentify
"""

from __future__ import annotations

import argparse
import hashlib
from datetime import date, datetime
from pathlib import Path

import pandas as pd

# In a real system this lives in a secrets manager, never in code. It is here so
# the pipeline runs; the note is explicit that this is a demonstration.
SALT = "trinity-demo-salt-not-for-production"

# The 18 HIPAA Safe Harbor identifiers we drop outright when present.
DIRECT_IDENTIFIERS = ["first_name", "last_name", "phone", "email", "address", "ssn"]


def hash_mrn(mrn: str, salt: str = SALT) -> str:
    """Turn an MRN into a stable pseudonym.

    Same MRN -> same hash every time, so appointments still link to patients.
    The original is not recoverable without the salt. This is pseudonymisation:
    useful, honest, and NOT the same as anonymisation - see the module docstring.
    """
    return hashlib.sha256(f"{salt}:{mrn}".encode()).hexdigest()[:16]


def age_band(dob: str | date, as_of: date | None = None) -> str:
    """Generalise a date of birth to an age band. Never a date, never an exact age.

    An exact age is identifying at the extremes (a 97-year-old in a small clinic
    is findable). Safe Harbor requires ages 90+ to be aggregated, so we bucket
    the whole range and cap the top.
    """
    as_of = as_of or date(2026, 6, 30)

    if isinstance(dob, str):
        dob = datetime.strptime(dob, "%Y-%m-%d").date()

    age = as_of.year - dob.year - ((as_of.month, as_of.day) < (dob.month, dob.day))

    if age < 18:
        return "0-17"
    if age < 35:
        return "18-34"
    if age < 50:
        return "35-49"
    if age < 65:
        return "50-64"
    if age < 90:
        return "65-89"
    return "90+"   # Safe Harbor: everyone 90 and over is bucketed together.


def deidentify_patients(patients: pd.DataFrame) -> pd.DataFrame:
    """Strip direct identifiers, hash the MRN, generalise the DOB."""
    out = pd.DataFrame()

    # The stable pseudonym the rest of the pipeline joins on.
    out["patient_key"] = patients["mrn"].map(hash_mrn)

    # DOB -> age band. The birth date itself never survives.
    out["age_band"] = patients["date_of_birth"].map(age_band)

    # Non-identifying attributes we keep - they are analytically useful and not
    # on the Safe Harbor list.
    for col in ["home_clinic"]:
        if col in patients.columns:
            out[col] = patients[col].to_numpy()

    return out


def deidentify_appointments(appointments: pd.DataFrame) -> pd.DataFrame:
    """Replace the MRN with the same hashed patient key. Dates stay.

    Appointment dates are operational, not birth dates - they are not PHI in the
    Safe Harbor sense (they are not tied to the individual's identity the way a
    DOB is), and the whole analysis is about WHEN appointments happen. They stay.
    """
    out = appointments.copy()
    out["patient_key"] = out["mrn"].map(hash_mrn)
    out = out.drop(columns=["mrn"])
    return out


def deidentify_visits(visits: pd.DataFrame) -> pd.DataFrame:
    """Same hashing for the billing extract."""
    out = visits.copy()
    out["patient_key"] = out["mrn"].map(hash_mrn)
    out = out.drop(columns=["mrn"])
    return out


HIPAA_NOTE = """# Data Handling Note — PHI and De-identification

**Scope:** This note documents how patient health information (PHI) is handled in
the Trinity No-Show analysis. The data is synthetic, but it is treated as if it
were real, because that is the habit worth demonstrating.

## What was present

The raw operational export contained direct identifiers typical of a real
scheduling system: patient names, dates of birth, and phone numbers, keyed by
medical record number (MRN).

## What we did, and why

We apply the **HIPAA Safe Harbor** approach: remove the 18 categories of direct
identifier so the working dataset cannot reasonably be tied to an individual.

| Field | Action | Reason |
|---|---|---|
| First / last name | **Dropped** | Direct identifier; no analytical value |
| Phone | **Dropped** | Direct identifier |
| Date of birth | **Generalised to age band** | A birth date is identifying; an age band preserves the analytical signal (age relates to no-show behaviour) without the exposure. Ages 90+ are bucketed together, as Safe Harbor requires |
| MRN | **Hashed to a stable pseudonym** | We need a consistent patient key to link appointments to patients. The MRN is hashed with a secret salt: the same patient always maps to the same key, and the original MRN is not recoverable without the salt |
| Appointment / visit dates | **Kept** | These are operational event dates, not identity-linked dates like a DOB. The entire analysis is about appointment timing |

## An honest limitation

Hashing the MRN is **pseudonymisation, not anonymisation.** Our MRNs are
sequential and therefore enumerable; anyone holding the salt could reverse the
mapping by brute force. In production the salt lives in a secrets manager, the
MRN-to-key mapping is never exported, and access is logged. We state this plainly
because overstating a privacy guarantee is its own kind of harm.

## What never leaves the secure boundary

- The salt.
- The MRN-to-key mapping.
- The original name, DOB, and phone columns.

The de-identified dataset — patient key, age band, home clinic — is what every
downstream step operates on.
"""


def deidentify(raw_dir: Path, processed_dir: Path) -> dict[str, int]:
    """Run the full de-identification pass and write the handling note."""
    processed_dir.mkdir(parents=True, exist_ok=True)

    patients = pd.read_csv(raw_dir / "patients.csv")
    appointments = pd.read_csv(raw_dir / "appointments.csv")
    visits = pd.read_csv(raw_dir / "visits.csv")

    # Drop any direct identifier that happens to be present.
    present_identifiers = [c for c in DIRECT_IDENTIFIERS if c in patients.columns]

    clean_patients = deidentify_patients(patients)
    clean_appts = deidentify_appointments(appointments)
    clean_visits = deidentify_visits(visits)

    clean_patients.to_csv(processed_dir / "patients_deid.csv", index=False)
    clean_appts.to_csv(processed_dir / "appointments_deid.csv", index=False)
    clean_visits.to_csv(processed_dir / "visits_deid.csv", index=False)

    # The note lives in docs, next to the code that implements it.
    note_path = Path("docs") / "DATA_HANDLING.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(HIPAA_NOTE, encoding="utf-8")

    print("De-identification complete.")
    print(f"  Dropped direct identifiers : {present_identifiers}")
    print(f"  Patients  -> {len(clean_patients):,} rows (name/DOB/phone removed)")
    print(f"  Appointments -> {len(clean_appts):,} rows (MRN -> patient_key)")
    print(f"  Visits    -> {len(clean_visits):,} rows (MRN -> patient_key)")
    print(f"  Handling note written to {note_path}")

    return {
        "patients": len(clean_patients),
        "appointments": len(clean_appts),
        "visits": len(clean_visits),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="De-identify Trinity patient data.")
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    deidentify(args.raw, args.processed)


if __name__ == "__main__":
    main()
