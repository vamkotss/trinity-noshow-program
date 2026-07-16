"""Driver analysis and the reminder natural experiment.

TWO QUESTIONS, TWO STANDARDS OF EVIDENCE
----------------------------------------
1. WHAT DRIVES NO-SHOWS?  This is descriptive. We rank the drivers by effect
   size so the business case can say "lead time is the biggest lever" with a
   number behind it. Observational ranking is fine here - we are describing what
   the data shows, not claiming a cause we intend to act on.

2. DO REMINDERS WORK?  This is causal, and the moment a question is causal the
   bar jumps. The COO wants to fund reminders. If we get this wrong, real money
   goes to an intervention that does nothing.

THE TRAP IN QUESTION 2
----------------------
Three clinics logged reminder calls; four did not. The naive move is to compare
no-show rates between the two groups, find the reminding clinics lower, and
declare reminders effective.

But the clinics that bothered to log reminders are ALSO the better-run clinics.
They would have had lower no-shows anyway. The comparison is confounded: it
measures "well-run vs not" at least as much as "reminded vs not". This is the
same disease as the P1 A/B test - a difference that looks causal and is not.

So we do three things:
  a) show the naive comparison, and how convincing it looks;
  b) show the confound - the reminding clinics differ systematically before any
     reminder is sent;
  c) estimate the effect WITHIN clinics, where the confound cannot operate, and
     report what honestly remains.

If the within-clinic effect is small or uncertain, we say so. "Reminders might
help a little but this data cannot prove it - run a randomised pilot" is a
finding a board can act on. "Reminders cut no-shows by a quarter!" - when that is
mostly selection bias - is how $200k gets set on fire.

Run:  python -m trinity.drivers
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# The 14 spellings, imported so we score no-show the same way the standardizer
# does - one definition, used everywhere.
from trinity.standardize import STATUS_MAP


def _prepare(appointments: pd.DataFrame) -> pd.DataFrame:
    """Attach the features the drivers analysis needs."""
    df = appointments.copy()

    # Canonical no-show flag. Use status_canonical if the standardizer already
    # ran; otherwise derive it, so this module works on raw or clean input.
    if "status_canonical" in df.columns:
        df["no_show"] = (df["status_canonical"] == "no_show").astype(int)
    else:
        df["no_show"] = df["status"].map(STATUS_MAP).eq("no_show").astype(int)

    df["appointment_date"] = pd.to_datetime(df["appointment_date"])
    df["booked_date"] = pd.to_datetime(df["booked_date"])
    df["lead_days"] = (df["appointment_date"] - df["booked_date"]).dt.days
    df["weekday"] = df["appointment_date"].dt.weekday
    df["is_monday_am"] = ((df["weekday"] == 0) & (df["appointment_hour"] < 11)).astype(int)

    type_col = "appointment_type_canonical" if "appointment_type_canonical" in df.columns \
        else "appointment_type"
    df["is_new_patient"] = df[type_col].astype(str).str.contains("new", case=False, na=False).astype(int)

    payer_col = "payer_canonical" if "payer_canonical" in df.columns else "payer"
    df["high_risk_payer"] = df[payer_col].isin(["Self-Pay", "Medicaid"]).astype(int)

    return df


# ---------------------------------------------------------------------------
# QUESTION 1 - RANK THE DRIVERS
# ---------------------------------------------------------------------------


def rank_drivers(df: pd.DataFrame) -> pd.DataFrame:
    """Quantify each driver's effect on the no-show rate, ranked by size.

    Effect size = (no-show rate WITH the factor) - (rate WITHOUT it). Simple,
    honest, and exactly what a business audience needs: 'appointments booked more
    than 30 days out no-show 12 points more than same-week ones'.
    """
    baseline = df["no_show"].mean()

    factors = {
        "Lead time > 30 days": df["lead_days"] > 30,
        "New patient": df["is_new_patient"] == 1,
        "Monday morning": df["is_monday_am"] == 1,
        "Self-pay / Medicaid": df["high_risk_payer"] == 1,
    }

    rows = []
    for name, mask in factors.items():
        with_rate = df[mask]["no_show"].mean()
        without_rate = df[~mask]["no_show"].mean()
        rows.append(
            {
                "driver": name,
                "rate_with": round(with_rate, 4),
                "rate_without": round(without_rate, 4),
                "effect_pts": round((with_rate - without_rate) * 100, 1),
                "population_share": round(mask.mean(), 3),
            }
        )

    out = pd.DataFrame(rows).sort_values("effect_pts", ascending=False).reset_index(drop=True)
    out.attrs["baseline"] = baseline
    return out


def lead_time_curve(df: pd.DataFrame) -> pd.DataFrame:
    """No-show rate by lead-time bucket. The evidence base for overbooking.

    An overbooking policy has to target the appointments most likely to no-show.
    This curve is what tells the front desk WHICH ones - and it is the single
    most important table for the intervention design.
    """
    buckets = pd.cut(
        df["lead_days"],
        [-1, 7, 14, 30, 60, 9999],
        labels=["0-7 days", "8-14 days", "15-30 days", "31-60 days", "60+ days"],
    )

    curve = df.groupby(buckets, observed=True).agg(
        appointments=("no_show", "size"),
        no_show_rate=("no_show", "mean"),
    ).reset_index()
    curve.columns = ["lead_bucket", "appointments", "no_show_rate"]
    curve["no_show_rate"] = curve["no_show_rate"].round(4)

    return curve


# ---------------------------------------------------------------------------
# QUESTION 2 - THE REMINDER NATURAL EXPERIMENT  (the trap)
# ---------------------------------------------------------------------------

REMINDING_CLINICS = ["Plano", "Frisco", "Allen"]


def naive_reminder_effect(df: pd.DataFrame) -> dict:
    """The comparison a junior analyst ships. It looks convincing. It is confounded.

    Compare no-show rates between clinics that logged reminders and those that
    did not. The gap is real - and almost entirely selection bias.
    """
    df = df.copy()
    df["reminds"] = df["clinic"].isin(REMINDING_CLINICS)

    remind_rate = df[df["reminds"]]["no_show"].mean()
    no_remind_rate = df[~df["reminds"]]["no_show"].mean()

    return {
        "reminding_rate": round(remind_rate, 4),
        "non_reminding_rate": round(no_remind_rate, 4),
        "naive_effect_pts": round((no_remind_rate - remind_rate) * 100, 1),
    }


def show_the_confound(df: pd.DataFrame) -> pd.DataFrame:
    """Prove the two clinic groups differ BEFORE any reminder is sent.

    If the reminding clinics have a lower-risk patient mix - fewer new patients,
    shorter lead times, fewer high-risk payers - then their lower no-show rate is
    explained by WHO they see, not by reminding. This table is the evidence that
    the naive comparison is measuring the wrong thing.
    """
    df = df.copy()
    df["reminds"] = df["clinic"].isin(REMINDING_CLINICS)

    covariates = ["is_new_patient", "high_risk_payer", "is_monday_am"]

    rows = []
    for cov in covariates:
        remind_val = df[df["reminds"]][cov].mean()
        no_remind_val = df[~df["reminds"]][cov].mean()
        rows.append(
            {
                "covariate": cov,
                "reminding_clinics": round(remind_val, 4),
                "non_reminding_clinics": round(no_remind_val, 4),
                "difference": round(remind_val - no_remind_val, 4),
            }
        )

    # Also compare mean lead time - a continuous risk factor.
    rows.append(
        {
            "covariate": "mean_lead_days",
            "reminding_clinics": round(df[df["reminds"]]["lead_days"].mean(), 2),
            "non_reminding_clinics": round(df[~df["reminds"]]["lead_days"].mean(), 2),
            "difference": round(
                df[df["reminds"]]["lead_days"].mean() - df[~df["reminds"]]["lead_days"].mean(), 2
            ),
        }
    )

    return pd.DataFrame(rows)


def adjusted_reminder_effect(df: pd.DataFrame) -> dict:
    """Estimate the reminder effect WITHIN risk strata, where the confound cannot operate.

    The naive comparison mixes 'reminded vs not' with 'low-risk mix vs high-risk
    mix'. If we compare within the SAME risk profile - same patient type, same
    lead-time band, same payer risk - the selection bias is largely removed, and
    what remains is a far more honest estimate of what reminding actually does.

    Here, because reminding was assigned at the CLINIC level and perfectly
    correlates with clinic quality, stratification can only partly separate the
    two. That limitation is the finding: this data cannot cleanly identify the
    reminder effect, and we say so.
    """
    df = df.copy()
    df["reminds"] = df["clinic"].isin(REMINDING_CLINICS)

    # Build a coarse risk stratum from the observable drivers. Payer risk is the
    # KEY covariate here - it is the axis on which the reminding and non-reminding
    # clinics actually differ, so stratifying on it is what removes the bias.
    df["lead_band"] = pd.cut(df["lead_days"], [-1, 14, 30, 9999], labels=["short", "mid", "long"])
    df["stratum"] = (
        df["high_risk_payer"].astype(str)
        + "|" + df["is_new_patient"].astype(str)
        + "|" + df["lead_band"].astype(str)
    )

    # Within each stratum, difference in no-show rate between reminded and not.
    effects = []
    weights = []
    for _stratum, g in df.groupby("stratum", observed=True):
        r = g[g["reminds"]]
        nr = g[~g["reminds"]]
        if len(r) < 50 or len(nr) < 50:
            continue
        effect = nr["no_show"].mean() - r["no_show"].mean()
        effects.append(effect)
        weights.append(len(g))

    if not effects:
        return {"adjusted_effect_pts": None, "n_strata": 0}

    effects_arr = np.array(effects)
    weights_arr = np.array(weights)
    weighted = float(np.average(effects_arr, weights=weights_arr))

    # A crude bootstrap over strata for an interval.
    rng = np.random.default_rng(11)
    boot = []
    for _ in range(500):
        idx = rng.integers(0, len(effects_arr), len(effects_arr))
        boot.append(np.average(effects_arr[idx], weights=weights_arr[idx]))
    lo, hi = np.percentile(boot, [2.5, 97.5])

    return {
        "adjusted_effect_pts": round(weighted * 100, 1),
        "ci_low_pts": round(float(lo) * 100, 1),
        "ci_high_pts": round(float(hi) * 100, 1),
        "n_strata": len(effects_arr),
        "includes_zero": bool(lo < 0 < hi),
    }


# ---------------------------------------------------------------------------
# ORCHESTRATION
# ---------------------------------------------------------------------------


def analyse(processed_dir: Path, out_dir: Path) -> dict:
    appointments = pd.read_parquet(processed_dir / "appointments_standardized.parquet")
    df = _prepare(appointments)

    drivers = rank_drivers(df)
    curve = lead_time_curve(df)

    naive = naive_reminder_effect(df)
    confound = show_the_confound(df)
    adjusted = adjusted_reminder_effect(df)

    # --- Print ---
    print("=" * 68)
    print("QUESTION 1 - WHAT DRIVES NO-SHOWS?")
    print("=" * 68)
    print(f"\n  Baseline no-show rate: {df['no_show'].mean():.1%}\n")
    print(f"  {'Driver':<24} {'with':>7} {'without':>8} {'effect':>8} {'share':>7}")
    print(f"  {'-' * 24} {'-' * 7} {'-' * 8} {'-' * 8} {'-' * 7}")
    for r in drivers.itertuples(index=False):
        print(f"  {r.driver:<24} {r.rate_with:>6.1%} {r.rate_without:>7.1%} "
              f"{r.effect_pts:>+7.1f} {r.population_share:>6.1%}")

    print("\n  Lead-time curve (the evidence base for overbooking):")
    for r in curve.itertuples(index=False):
        bar = "#" * int(r.no_show_rate * 100)
        print(f"    {r.lead_bucket:<12} {r.no_show_rate:>6.1%}  {bar}")

    print("\n" + "=" * 68)
    print("QUESTION 2 - DO REMINDERS WORK?  (the causal question)")
    print("=" * 68)

    print("\n  STEP 1 - the naive comparison (what a junior analyst ships):")
    print(f"    Reminding clinics no-show:     {naive['reminding_rate']:.1%}")
    print(f"    Non-reminding clinics no-show: {naive['non_reminding_rate']:.1%}")
    print(f"    >>> Naive 'effect': {naive['naive_effect_pts']:+.1f} pts. Looks like reminders work.")

    print("\n  STEP 2 - but the groups were never comparable:")
    print(f"    {'covariate':<18} {'remind':>9} {'no-remind':>10} {'diff':>8}")
    print(f"    {'-' * 18} {'-' * 9} {'-' * 10} {'-' * 8}")
    for r in confound.itertuples(index=False):
        print(f"    {r.covariate:<18} {r.reminding_clinics:>9} "
              f"{r.non_reminding_clinics:>10} {r.difference:>+8}")
    print("    >>> The reminding clinics see a lower-risk mix. Their lower no-show")
    print("    >>> rate is partly WHO they see, not whether they remind.")

    print("\n  STEP 3 - the effect within matched risk strata:")
    if adjusted["adjusted_effect_pts"] is None:
        print("    Too few comparable strata to estimate. The data cannot separate")
        print("    reminding from clinic quality.")
    else:
        print(f"    Adjusted effect: {adjusted['adjusted_effect_pts']:+.1f} pts "
              f"(95% CI [{adjusted['ci_low_pts']:+.1f}, {adjusted['ci_high_pts']:+.1f}])")
        print(f"    across {adjusted['n_strata']} strata.")

    print("\n" + "=" * 68)
    print("THE VERDICT")
    print("=" * 68)
    naive_e = naive["naive_effect_pts"]
    adj_e = adjusted["adjusted_effect_pts"]
    if adj_e is not None:
        shrink = (1 - adj_e / naive_e) * 100 if naive_e else 0
        print(f"\n  The naive comparison says reminders cut no-shows by {naive_e:.1f} pts.")
        print(f"  Adjusting for who each clinic sees, the estimate falls to {adj_e:.1f} pts")
        print(f"  - roughly {shrink:.0f}% of the naive figure was selection bias.")
        if adjusted["includes_zero"]:
            print("\n  The adjusted interval includes zero. This observational data CANNOT")
            print("  prove reminders work. Recommend a randomised pilot before funding at")
            print("  scale - do not commit the budget on a confounded comparison.")
        else:
            print("\n  A real effect survives adjustment, but it is far smaller than the")
            print("  naive number. Fund cautiously and measure, do not extrapolate.")

    out_dir.mkdir(parents=True, exist_ok=True)
    drivers.to_parquet(out_dir / "drivers.parquet", index=False)
    curve.to_parquet(out_dir / "lead_time_curve.parquet", index=False)
    confound.to_parquet(out_dir / "reminder_confound.parquet", index=False)

    return {
        "drivers": drivers,
        "curve": curve,
        "naive": naive,
        "confound": confound,
        "adjusted": adjusted,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="No-show driver analysis and reminder experiment.")
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    parser.add_argument("--out", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    analyse(args.processed, args.out)


if __name__ == "__main__":
    main()
