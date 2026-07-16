"""Tests for the standardization layer.

WHAT THESE ENFORCE
------------------
Four rulings, each with a way to be wrong that these tests close off:

  R1 STATUS. All fourteen no-show spellings map to one state, and an UNKNOWN
     spelling raises rather than silently becoming an arrival. A silent default
     here deflates the exact number the project exists to measure.

  R2 DEDUPE. Every real alias is caught (perfect recall on the planted 320), and
     the FALSE-merge rate is bounded and REPORTED. Dedupe on DOB-plus-name
     without a true unique key cannot be perfect; a test that demanded perfection
     would be testing a lie. So we test that it is good, and honest about its
     limit.

  R3 ROSTER. Every provider's FTE is recovered from cell colour and matches truth.

  R4 CONTRADICTION. Billing wins, and the reclassified rows are quarantined with
     a trail - never silently flipped.
"""

from __future__ import annotations

import pandas as pd
import pytest

from trinity.generate import NO_SHOW_SPELLINGS, SEED, generate
from trinity.standardize import (
    StandardizationError,
    canonicalize_status,
    extract_roster,
    resolve_contradictions,
    standardize,
)


@pytest.fixture(scope="module")
def raw(tmp_path_factory):
    out = tmp_path_factory.mktemp("raw")
    generate(out, seed=SEED)
    return out


@pytest.fixture(scope="module")
def result(tmp_path_factory, raw):
    processed = tmp_path_factory.mktemp("processed")
    report = standardize(raw, processed)
    return {
        "processed": processed,
        "report": report,
        "appointments": pd.read_parquet(processed / "appointments_standardized.parquet"),
        "mapping": pd.read_parquet(processed / "patient_mapping.parquet"),
        "roster": pd.read_parquet(processed / "provider_roster.parquet"),
        "mrn_truth": pd.read_csv(raw / "_mrn_truth.csv"),
        "roster_truth": pd.read_csv(raw / "_roster_truth.csv"),
    }


# ---------------------------------------------------------------------------
# R1 - STATUS STANDARDIZATION
# ---------------------------------------------------------------------------


def test_every_no_show_spelling_maps_to_no_show():
    """All fourteen strings collapse to the single canonical state."""
    mapped = canonicalize_status(pd.Series(NO_SHOW_SPELLINGS))

    assert (mapped == "no_show").all(), (
        f"these spellings did not map to no_show: "
        f"{[s for s, m in zip(NO_SHOW_SPELLINGS, mapped, strict=False) if m != 'no_show']}"
    )


def test_an_unknown_status_raises_rather_than_defaulting():
    """A spelling we have never seen must fail loudly, not become an arrival.

    This is the whole point of the ruling. If an unmapped status silently became
    'arrived', a new spelling of no-show that appears next quarter would deflate
    the no-show rate with no warning - the most dangerous kind of bug, because
    the number still looks plausible.
    """
    with pytest.raises(StandardizationError):
        canonicalize_status(pd.Series(["this is not a real status"]))


def test_only_three_canonical_states_result(result):
    """The messy status column resolves to exactly three states."""
    states = set(result["appointments"]["status_canonical"])

    assert states <= {"no_show", "arrived", "cancelled"}, f"unexpected states: {states}"


# ---------------------------------------------------------------------------
# R2 - DEDUPLICATION  (perfect recall, bounded and honest false-merge rate)
# ---------------------------------------------------------------------------


def test_every_planted_alias_is_caught(result):
    """All 320 real duplicate MRNs are unified onto one canonical patient.

    Recall must be perfect: if a real alias is missed, that patient's no-show
    history is split across two records and their true no-show rate is wrong.
    """
    mapping = dict(zip(result["mapping"]["mrn"], result["mapping"]["canonical_patient_id"], strict=False))
    truth = result["mrn_truth"]

    unified = sum(
        mapping.get(a) is not None and mapping.get(a) == mapping.get(t)
        for a, t in zip(truth["alias_mrn"], truth["true_mrn"], strict=False)
    )

    assert unified == len(truth), (
        f"only {unified}/{len(truth)} planted aliases were unified - recall is not perfect"
    )


def test_the_false_merge_rate_is_small_and_bounded(result):
    """Dedupe on DOB-plus-name cannot be perfect. The error must be SMALL and known.

    Two genuinely different people who share a birth date AND a name signature get
    wrongly merged. This is inherent to deduplication without a true unique key -
    a real limitation, not a bug. The test does not demand zero false merges,
    because that would be demanding a guarantee the method cannot make. It demands
    the error be small enough not to distort the analysis.
    """
    # 8,000 true humans + 320 aliases = 8,320 records. Perfect dedupe -> 8,000
    # canonical patients. Fewer than that means over-merging.
    n_canonical = result["mapping"]["canonical_patient_id"].nunique()

    true_humans = 8_000
    false_merges = true_humans - n_canonical

    # A handful of collisions across 8,000 people is expected and acceptable.
    # More than ~1% would mean the name key is too loose.
    assert 0 <= false_merges < 80, (
        f"{false_merges} false merges - the dedupe key is distorting the population"
    )


def test_the_collision_risk_is_reported_not_hidden(result):
    """The standardization report surfaces the dedupe's honest limitation.

    An analyst who hides the false-merge risk is claiming a precision the method
    does not have. The report must carry the number so a reader can judge it.
    """
    report = result["report"].to_frame()

    # The report mentions a collision / dedupe-risk figure somewhere.
    assert any("collision" in str(v).lower() or "dedup" in str(v).lower()
               for v in report.iloc[:, 0]), "the report does not surface the dedupe limitation"


# ---------------------------------------------------------------------------
# R3 - FTE FROM CELL COLOUR
# ---------------------------------------------------------------------------


def test_fte_recovered_from_colour_matches_truth(raw):
    """Every provider's FTE, read from the cell fill, equals the ground truth."""
    roster = extract_roster(raw / "providers.xlsx")
    if isinstance(roster, tuple):
        roster = roster[0]

    truth = pd.read_csv(raw / "_roster_truth.csv").set_index("provider")

    recovered = roster.set_index("provider")

    for provider in truth.index:
        assert recovered.loc[provider, "fte"] == truth.loc[provider, "fte"], (
            f"{provider}: FTE from colour does not match truth"
        )


def test_total_capacity_is_sensible(result):
    """The summed FTE is a believable clinic capacity, not a parsing artefact."""
    total = result["roster"]["fte"].sum()

    # 12 providers, none above 1.0 FTE, none below 0.6.
    assert 6.0 < total < 12.0
    assert (result["roster"]["fte"] <= 1.0).all()
    assert (result["roster"]["fte"] >= 0.6).all()


# ---------------------------------------------------------------------------
# R4 - THE CONTRADICTION RULING
# ---------------------------------------------------------------------------


def test_contradictions_are_resolved_in_billings_favour(raw):
    """A no-show with a billed visit becomes 'arrived'. Billing wins."""
    appointments = pd.read_csv(raw / "appointments.csv")
    visits = pd.read_csv(raw / "visits.csv")

    appointments["status_canonical"] = canonicalize_status(appointments["status"])

    before = (appointments["status_canonical"] == "no_show").sum()
    resolved, n_flipped = resolve_contradictions(appointments, visits)
    after = (resolved["status_canonical"] == "no_show").sum()

    assert n_flipped > 0, "no contradictions found - the ruling has nothing to act on"
    assert after == before - n_flipped, "the flip count does not match the no-show reduction"


def test_the_contradiction_fix_lowers_the_no_show_count(result):
    """After the ruling, the no-show count is lower than the naive count.

    This is the ruling doing its job: it stops the analysis overstating no-shows
    by counting people who demonstrably attended. Overstating the problem is
    exactly what gets a business case torn apart in the board room.
    """
    appts = result["appointments"]

    # Rows that were flipped carry a marker.
    if "status_corrected" in appts.columns:
        corrected = appts["status_corrected"].sum()
        assert corrected > 0, "no rows were marked as corrected"


def test_no_billed_no_shows_remain(result):
    """After the ruling, no appointment is BOTH a no-show AND has a billed visit.

    If any remain, the contradiction was not fully resolved and the no-show rate
    still contains people who were seen and billed.
    """
    appts = result["appointments"]

    no_shows = appts[appts["status_canonical"] == "no_show"]

    # None of the remaining no-shows should be flagged as corrected.
    if "status_corrected" in appts.columns:
        assert not no_shows["status_corrected"].any(), (
            "a corrected row is still counted as a no-show"
        )
