"""Tests for the demand forecast and capacity model.

WHAT THESE PROTECT
------------------
Two findings the business case leans on:

  1. The utilization imbalance is REAL and correctly computed against roster FTE.
     A provider's "overbooked" or "idle" status is meaningless unless it is
     measured against how much they are contracted to work - which is the FTE we
     extracted from cell colour in M3. If utilization silently ignored FTE, a
     0.6-FTE provider and a 1.0-FTE provider seeing the same volume would look
     identical, and the whole rebalancing argument would collapse.

  2. The forecast is SANE. The boundary-week trap - partial weeks at the edges of
     the data window masquerading as a demand crash - would make the forecast
     project a collapse that is not real. One test exists purely to keep that
     trap sprung shut.
"""

from __future__ import annotations

import pandas as pd
import pytest

from trinity.capacity import (
    SLOTS_PER_WEEK_AT_FULL_FTE,
    clinic_utilization,
    forecast_demand,
    provider_utilization,
    rebalancing_opportunity,
    weekly_demand_series,
)
from trinity.generate import SEED, generate
from trinity.standardize import standardize


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    raw = tmp_path_factory.mktemp("raw")
    processed = tmp_path_factory.mktemp("processed")
    generate(raw, seed=SEED)
    standardize(raw, processed)

    appts = pd.read_parquet(processed / "appointments_standardized.parquet")
    roster = pd.read_parquet(processed / "provider_roster.parquet")

    util = provider_utilization(appts, roster)
    return {
        "appointments": appts,
        "roster": roster,
        "utilization": util,
        "clinic": clinic_utilization(util),
        "rebalance": rebalancing_opportunity(util),
        "series": weekly_demand_series(appts),
    }


# ---------------------------------------------------------------------------
# UTILIZATION IS COMPUTED AGAINST FTE
# ---------------------------------------------------------------------------


def test_utilization_uses_the_roster_fte(data):
    """Capacity is FTE x slots-per-week, not a flat number for everyone.

    This is the payoff of the M3 colour extraction. A 0.6-FTE provider has 60% of
    the capacity of a 1.0-FTE one; utilization must reflect that. If it did not,
    the part-time providers would look permanently overbooked and the story would
    be wrong.
    """
    util = data["utilization"]

    for r in util.itertuples(index=False):
        expected_capacity = r.fte * SLOTS_PER_WEEK_AT_FULL_FTE
        assert r.capacity_per_week == pytest.approx(expected_capacity), (
            f"{r.provider}: capacity does not reflect FTE {r.fte}"
        )


def test_the_imbalance_is_real(data):
    """Some providers are overbooked and others idle - the imbalance the COO named.

    If every provider came out near 100%, there would be no rebalancing story and
    half the business case would evaporate. The spread is the finding.
    """
    util = data["utilization"]

    statuses = set(util["status"])

    assert "OVERBOOKED" in statuses, "no overbooked providers - the imbalance is missing"
    assert "IDLE" in statuses, "no idle providers - the imbalance is missing"

    # And the spread is material: the busiest is well above the quietest.
    assert util["utilization"].max() > util["utilization"].min() * 1.8


def test_the_single_provider_clinics_are_the_overbooked_ones(data):
    """The structural finding: clinics with one provider are drowning.

    This is what turns 'some providers are busy' into an actionable diagnosis -
    the overbooked providers are the ones with no colleague to share load with.
    """
    util = data["utilization"]

    overbooked = util[util["status"] == "OVERBOOKED"]

    # The overbooked providers are at clinics with only one provider in the roster.
    provider_counts = util.groupby("clinic").size()
    for clinic in overbooked["clinic"]:
        assert provider_counts[clinic] == 1, (
            f"{clinic} is overbooked but has more than one provider - "
            "the single-provider diagnosis does not hold"
        )


def test_rebalancing_opportunity_is_quantified(data):
    """The model states how much demand could move at no hiring cost."""
    rebalance = data["rebalance"]

    assert rebalance["overbooked_providers"] > 0
    assert rebalance["idle_providers"] > 0
    assert rebalance["absorbable_per_week"] > 0, (
        "no absorbable demand found - the free rebalancing win is missing"
    )

    # The absorbable amount cannot exceed either the excess or the spare.
    assert rebalance["absorbable_per_week"] <= rebalance["excess_demand_per_week"]
    assert rebalance["absorbable_per_week"] <= rebalance["spare_capacity_per_week"]


def test_clinic_spread_surfaces_within_clinic_headroom(data):
    """Clinic-level utilization reports the spread, not just the average.

    A clinic averaging 90% might hide a provider at 130% next to one at 50%. The
    spread is the rebalancing headroom that exists WITHOUT hiring - the cheapest
    fix available - so it must be surfaced.
    """
    clinic = data["clinic"]

    assert "util_spread" in clinic.columns
    # At least one clinic has a meaningful internal spread.
    assert clinic["util_spread"].max() > 0.1


# ---------------------------------------------------------------------------
# THE FORECAST IS SANE
# ---------------------------------------------------------------------------


def test_the_demand_series_excludes_boundary_weeks(data):
    """Partial weeks at the data edges are trimmed, not forecast from.

    THE TRAP. The first and last weeks of the export are incompletely observed -
    they look like low-demand weeks and are not. Left in, they would drag a trend
    line into projecting a demand crash that is a data artefact, not reality.
    """
    series = data["series"]

    # No week in the kept series is a tiny fraction of the median - the boundary
    # weeks (which are) have been removed.
    median = series["appointments"].median()
    assert (series["appointments"] >= 0.4 * median).all(), (
        "a boundary week survived into the demand series"
    )


def test_the_forecast_is_close_to_recent_demand(data):
    """The forecast is in the same ballpark as recent actuals.

    A 13-week forecast that is 10x or 0.1x recent demand is not a forecast, it is
    a bug. This catches the boundary-week contamination that made an early version
    project ~14x reality.
    """
    series = data["series"]
    forecast = forecast_demand(series)

    recent = series["appointments"].tail(8).mean()
    projected = forecast["forecast"].mean()

    ratio = projected / recent
    assert 0.6 < ratio < 1.6, (
        f"forecast ({projected:.0f}) is implausible against recent demand ({recent:.0f})"
    )


def test_the_forecast_interval_brackets_the_point(data):
    """Every forecast point sits inside its own interval, and the interval widens."""
    forecast = forecast_demand(data["series"])

    assert (forecast["lower"] <= forecast["forecast"]).all()
    assert (forecast["forecast"] <= forecast["upper"]).all()

    # Uncertainty grows with horizon.
    first_width = forecast.iloc[0]["upper"] - forecast.iloc[0]["lower"]
    last_width = forecast.iloc[-1]["upper"] - forecast.iloc[-1]["lower"]
    assert last_width > first_width, "the interval does not widen with the horizon"
