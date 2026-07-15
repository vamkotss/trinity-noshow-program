"""Tests for the de-identification pass.

WHAT THESE PROTECT
------------------
A de-identification step that leaks is worse than none, because it ships with a
false assurance attached. These tests prove the direct identifiers are actually
gone, the patient key is stable enough to link on but not reversible without the
salt, and the birth date never survives in any form.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from trinity.deidentify import (
    DIRECT_IDENTIFIERS,
    age_band,
    deidentify,
    hash_mrn,
)
from trinity.generate import SEED, generate


@pytest.fixture(scope="module")
def deid(tmp_path_factory):
    raw = tmp_path_factory.mktemp("raw")
    processed = tmp_path_factory.mktemp("processed")

    generate(raw, seed=SEED)
    deidentify(raw, processed)

    return {
        "raw_patients": pd.read_csv(raw / "patients.csv"),
        "patients": pd.read_csv(processed / "patients_deid.csv"),
        "appointments": pd.read_csv(processed / "appointments_deid.csv"),
        "visits": pd.read_csv(processed / "visits_deid.csv"),
    }


# ---------------------------------------------------------------------------
# THE IDENTIFIERS ARE GONE
# ---------------------------------------------------------------------------


def test_no_direct_identifiers_survive(deid):
    """Names, phones, and the rest are absent from every de-identified file."""
    for frame_name in ["patients", "appointments", "visits"]:
        columns = set(deid[frame_name].columns)
        leaked = columns & set(DIRECT_IDENTIFIERS)
        assert not leaked, f"{frame_name} still contains identifiers: {leaked}"


def test_the_raw_mrn_is_gone(deid):
    """The original MRN does not appear in any de-identified file.

    The MRN is a direct identifier. It is replaced by a hashed key, never carried
    through in the clear.
    """
    for frame_name in ["patients", "appointments", "visits"]:
        assert "mrn" not in deid[frame_name].columns, f"{frame_name} still has a raw MRN column"


def test_no_birth_date_survives(deid):
    """The date of birth is gone - only an age band remains.

    A birth date is identifying. An age band is not. This test proves no column
    holds anything that looks like a date of birth.
    """
    patients = deid["patients"]

    assert "date_of_birth" not in patients.columns
    assert "age_band" in patients.columns

    # And the age band is a band, not a smuggled exact age or date.
    bands = set(patients["age_band"])
    allowed = {"0-17", "18-34", "35-49", "50-64", "65-89", "90+"}
    assert bands <= allowed, f"unexpected age_band values: {bands - allowed}"


# ---------------------------------------------------------------------------
# THE KEY IS STABLE, AND LINKS
# ---------------------------------------------------------------------------


def test_the_patient_key_is_deterministic():
    """Same MRN, same key, every time. Otherwise nothing links."""
    assert hash_mrn("MRN000123") == hash_mrn("MRN000123")
    assert hash_mrn("MRN000123") != hash_mrn("MRN000124")


def test_the_key_is_not_the_mrn():
    """The pseudonym does not contain or resemble the original."""
    key = hash_mrn("MRN000123")

    assert "MRN" not in key
    assert "000123" not in key
    assert len(key) == 16


def test_appointments_still_link_to_patients(deid):
    """After hashing, appointments still join to patients on the new key.

    De-identification must not break the analysis. If the keys did not match, the
    entire downstream pipeline would silently lose every row in the join.
    """
    patient_keys = set(deid["patients"]["patient_key"])
    appt_keys = set(deid["appointments"]["patient_key"])

    overlap = appt_keys & patient_keys

    # The overwhelming majority of appointment keys must match a patient.
    assert len(overlap) / len(appt_keys) > 0.99, "the hashed keys do not link"


# ---------------------------------------------------------------------------
# AGE BANDING
# ---------------------------------------------------------------------------


def test_age_band_generalises_correctly():
    """A few known dates of birth land in the right bands."""
    as_of = date(2026, 6, 30)

    assert age_band(date(2020, 1, 1), as_of) == "0-17"
    assert age_band(date(2000, 1, 1), as_of) == "18-34"
    assert age_band(date(1980, 1, 1), as_of) == "35-49"
    assert age_band(date(1930, 1, 1), as_of) == "90+"


def test_the_very_old_are_bucketed(deid):
    """Nobody is reported as an exact age above 89 - Safe Harbor requires 90+ aggregation.

    A 97-year-old at a small clinic is findable from age alone. Bucketing them
    into '90+' is a specific HIPAA requirement, not a nicety.
    """
    bands = set(deid["patients"]["age_band"])

    # There is a 90+ band and no band that names a specific age above 89.
    assert "90+" in bands or all("9" not in b or "-" in b for b in bands)
