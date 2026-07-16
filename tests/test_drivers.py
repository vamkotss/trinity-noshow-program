"""Tests for the driver analysis and the reminder natural experiment.

WHAT THESE PROTECT
------------------
Two things, one descriptive and one causal, held to two different standards.

The driver ranking must find the real, planted drivers and rank lead time first
- that ranking is the evidence base for the overbooking recommendation.

The reminder experiment must NOT fall for the confound. The naive comparison
looks convincing; the honest conclusion is that this data cannot prove reminders
work. The most important test in this file asserts that the analysis reaches the
humble conclusion rather than the flattering one - because the flattering one is
how the budget gets spent on nothing.
"""

from __future__ import annotations

import pandas as pd
import pytest

from trinity.drivers import (
    _prepare,
    adjusted_reminder_effect,
    lead_time_curve,
    naive_reminder_effect,
    rank_drivers,
    show_the_confound,
)
from trinity.generate import SEED, generate
from trinity.standardize import standardize


@pytest.fixture(scope="module")
def df(tmp_path_factory):
    raw = tmp_path_factory.mktemp("raw")
    processed = tmp_path_factory.mktemp("processed")
    generate(raw, seed=SEED)
    standardize(raw, processed)

    appts = pd.read_parquet(processed / "appointments_standardized.parquet")
    return _prepare(appts)


# ---------------------------------------------------------------------------
# QUESTION 1 - THE DRIVERS
# ---------------------------------------------------------------------------


def test_lead_time_is_the_top_driver(df):
    """Lead time has the largest effect - it is what justifies overbooking.

    If some other driver ranked first, the central intervention (overbook the
    appointments most likely to no-show, which are the long-lead ones) would
    rest on the wrong evidence.
    """
    drivers = rank_drivers(df)

    top = drivers.iloc[0]["driver"]

    assert "Lead time" in top, f"the top driver is {top}, not lead time"


def test_the_lead_time_curve_climbs_monotonically(df):
    """No-show rate rises with every lead-time bucket.

    A clean monotonic climb is what makes the curve usable as an overbooking
    policy: 'the longer the wait, the more you can safely overbook'.
    """
    curve = lead_time_curve(df)

    rates = curve["no_show_rate"].to_numpy()

    assert all(rates[i] <= rates[i + 1] for i in range(len(rates) - 1)), (
        f"lead-time curve is not monotonic: {rates}"
    )

    # And the effect is large - the far end is at least double the near end.
    assert rates[-1] > rates[0] * 1.8


def test_all_planted_drivers_have_positive_effect(df):
    """Every driver we built in shows the direction we built it in."""
    drivers = rank_drivers(df).set_index("driver")

    for name in drivers.index:
        assert drivers.loc[name, "effect_pts"] > 0, f"{name} does not raise no-show risk"


# ---------------------------------------------------------------------------
# QUESTION 2 - THE NATURAL EXPERIMENT
# The tests that matter most.
# ---------------------------------------------------------------------------


def test_the_naive_comparison_looks_convincing(df):
    """The naive reminder effect is real and sizeable - that is why it is a trap.

    If the naive number were zero, there would be nothing to be fooled by. The
    danger exists precisely because the confounded comparison is persuasive.
    """
    naive = naive_reminder_effect(df)

    assert naive["naive_effect_pts"] > 1.0, (
        "the naive reminder effect is too small to be a convincing trap"
    )


def test_the_confound_is_visible(df):
    """The reminding and non-reminding clinics differ on an OBSERVABLE covariate.

    Specifically, the reminding clinics serve a lower-risk payer mix. This is the
    evidence that the naive comparison is confounded - and, crucially, it is
    visible in a column the analyst has, so it can be adjusted for.
    """
    confound = show_the_confound(df).set_index("covariate")

    payer_gap = confound.loc["high_risk_payer", "difference"]

    assert abs(payer_gap) > 0.10, (
        f"the payer-mix confound is only {payer_gap:.3f} - too small to drive the bias"
    )
    # The reminding clinics have FEWER high-risk payers.
    assert payer_gap < 0, "reminding clinics do not have the lower-risk mix we planted"


def test_adjustment_shrinks_the_effect_toward_zero(df):
    """Stratifying on the confounder collapses most of the naive effect.

    This is the payoff. When you compare within matched risk strata, the reminder
    'effect' largely disappears - proving the naive number was mostly selection
    bias, not causation.
    """
    naive = naive_reminder_effect(df)
    adjusted = adjusted_reminder_effect(df)

    assert adjusted["adjusted_effect_pts"] is not None, "no strata were comparable"

    # The adjusted effect is much smaller than the naive one.
    assert abs(adjusted["adjusted_effect_pts"]) < abs(naive["naive_effect_pts"]) * 0.6, (
        f"adjustment barely moved the estimate: naive {naive['naive_effect_pts']} "
        f"-> adjusted {adjusted['adjusted_effect_pts']}"
    )


def test_the_analysis_refuses_to_claim_reminders_work(df):
    """THE TEST. The honest conclusion is 'this data cannot prove it'.

    After adjustment, the confidence interval includes zero. That means the
    observational data cannot distinguish a real reminder effect from no effect.
    The correct output is a recommendation to run a randomised pilot - NOT a
    claim that reminders work.

    An analyst who ships the naive number funds an intervention on the strength
    of selection bias. This test is the guardrail against a future version of the
    analysis quietly becoming more confident than the evidence allows.
    """
    adjusted = adjusted_reminder_effect(df)

    assert adjusted["includes_zero"], (
        f"the adjusted CI [{adjusted['ci_low_pts']}, {adjusted['ci_high_pts']}] "
        "excludes zero - the analysis is claiming a causal effect this "
        "observational data cannot support"
    )
