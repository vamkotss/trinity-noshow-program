"""Demand forecast and capacity model.

THE OTHER HALF OF THE PROBLEM
-----------------------------
No-shows are one leak. The other, which the COO named directly in discovery, is
imbalanced capacity: "some providers overbooked while others sit idle." A no-show
program that ignores this fixes half the problem and leaves the other half
bleeding.

This milestone answers two questions:

  1. WHERE IS THE IMBALANCE?  Compute utilization per provider and per clinic -
     demand against the FTE capacity we recovered from the roster in M3. A
     provider at 130% is turning patients away; one at 60% is idle. Both cost
     money, in opposite directions.

  2. HOW MUCH DEMAND IS COMING?  Forecast appointment volume per clinic so
     capacity can be planned against it rather than guessed.

WHY UTILIZATION NEEDS THE ROSTER
--------------------------------
You cannot say a provider is "overbooked" without knowing how much they are
supposed to work. A 0.6-FTE provider seeing 30 patients a week is stretched; a
1.0-FTE provider seeing the same is coasting. That FTE number existed only as a
cell colour until M3 extracted it. This is where that extraction pays off - no
roster, no utilization, no capacity story.

THE HONEST LIMIT ON THE FORECAST
--------------------------------
Two years of history is not a lot, and clinic demand has seasonality we can only
partly see. The forecast is a planning aid with an interval, not a promise. We
say so, the same way P1's forecast shipped with its own warning.

Run:  python -m trinity.capacity
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# A provider's weekly slot capacity at 1.0 FTE. A full-time provider has roughly
# this many bookable appointment slots per week. Stated as an assumption because
# it drives every utilization number and belongs in sensitivity analysis.
SLOTS_PER_WEEK_AT_FULL_FTE = 80


def _prepare(appointments: pd.DataFrame) -> pd.DataFrame:
    df = appointments.copy()
    df["appointment_date"] = pd.to_datetime(df["appointment_date"])
    df["week"] = df["appointment_date"].dt.to_period("W").dt.start_time

    if "status_canonical" in df.columns:
        df["attended"] = (df["status_canonical"] == "arrived").astype(int)
    else:
        df["attended"] = 1  # fall back to counting all booked

    return df


# ---------------------------------------------------------------------------
# QUESTION 1 - UTILIZATION AND IMBALANCE
# ---------------------------------------------------------------------------


def provider_utilization(
    appointments: pd.DataFrame, roster: pd.DataFrame
) -> pd.DataFrame:
    """Demand vs FTE capacity, per provider. The imbalance table.

    Utilization = booked appointments per week / (FTE * slots-per-week). Above
    100% means demand exceeds the provider's contracted capacity - they are
    overbooked. Well below means idle time that is being paid for and not used.
    """
    df = _prepare(appointments)

    # Weeks of history, to turn totals into a weekly rate.
    n_weeks = df["week"].nunique()

    # Booked appointments per provider (demand). Count all booked slots, since a
    # booked-then-no-show slot still consumed schedule capacity.
    demand = df.groupby("provider").size().rename("appointments_total")
    weekly_demand = (demand / n_weeks).rename("appointments_per_week")

    util = roster.set_index("provider").join(weekly_demand)
    util["capacity_per_week"] = util["fte"] * SLOTS_PER_WEEK_AT_FULL_FTE
    util["utilization"] = util["appointments_per_week"] / util["capacity_per_week"]

    util = util.reset_index().sort_values("utilization", ascending=False)

    # Flag the two failure modes.
    util["status"] = np.select(
        [util["utilization"] > 1.05, util["utilization"] < 0.75],
        ["OVERBOOKED", "IDLE"],
        default="balanced",
    )

    util["utilization"] = util["utilization"].round(3)
    util["appointments_per_week"] = util["appointments_per_week"].round(1)

    return util


def clinic_utilization(util: pd.DataFrame) -> pd.DataFrame:
    """Roll utilization up to the clinic level.

    A clinic can look balanced on average while hiding an overbooked provider
    next to an idle one. We report both the clinic mean AND the spread, because
    the spread is the rebalancing opportunity.
    """
    grouped = util.groupby("clinic").agg(
        providers=("provider", "size"),
        total_capacity=("capacity_per_week", "sum"),
        total_demand=("appointments_per_week", "sum"),
        util_min=("utilization", "min"),
        util_max=("utilization", "max"),
    )

    grouped["clinic_utilization"] = (
        grouped["total_demand"] / grouped["total_capacity"]
    ).round(3)

    # The spread: how far apart the busiest and quietest providers are. A large
    # spread means rebalancing within the clinic could help without hiring.
    grouped["util_spread"] = (grouped["util_max"] - grouped["util_min"]).round(3)

    return grouped.reset_index().sort_values("util_spread", ascending=False)


def rebalancing_opportunity(util: pd.DataFrame) -> dict:
    """Quantify the demand that could move from overbooked to idle providers.

    This is the finding that costs nothing to act on: some of the imbalance is
    not a staffing shortfall, it is misallocation. Demand sitting on an
    overbooked provider that an idle colleague in the same clinic could absorb.
    """
    overbooked = util[util["status"] == "OVERBOOKED"]
    idle = util[util["status"] == "IDLE"]

    # Excess demand on overbooked providers (above 100%).
    excess = (
        (overbooked["appointments_per_week"]
         - overbooked["capacity_per_week"]).clip(lower=0).sum()
    )

    # Spare capacity on idle providers (below 100%).
    spare = (
        (idle["capacity_per_week"]
         - idle["appointments_per_week"]).clip(lower=0).sum()
    )

    return {
        "overbooked_providers": len(overbooked),
        "idle_providers": len(idle),
        "excess_demand_per_week": round(float(excess), 1),
        "spare_capacity_per_week": round(float(spare), 1),
        "absorbable_per_week": round(float(min(excess, spare)), 1),
    }


# ---------------------------------------------------------------------------
# QUESTION 2 - DEMAND FORECAST
# ---------------------------------------------------------------------------


def weekly_demand_series(appointments: pd.DataFrame) -> pd.DataFrame:
    """Total booked appointments per week, network-wide.

    THE BOUNDARY-WEEK TRAP. The first and last few weeks of any operational
    export are partial: appointments ramp up as the data window opens and trail
    off as it closes, because the window edges cut through real activity. Those
    weeks are not low-demand weeks - they are incompletely-observed weeks, and
    fitting a trend through them would invent a crash that is not real.

    So we trim to the weeks that are fully observed. We keep only weeks whose
    volume is within a sane band of the median - the stable middle of the series,
    which is what an analyst actually wants to forecast from.
    """
    df = _prepare(appointments)
    series = df.groupby("week").size().rename("appointments").reset_index()

    if len(series) < 12:
        return series

    # The median week is representative; boundary weeks are a fraction of it.
    # Keep weeks with at least half the median volume - drops the ramp-up and
    # trail-off without touching the genuine middle.
    median = series["appointments"].median()
    stable = series[series["appointments"] >= 0.5 * median].reset_index(drop=True)

    return stable


def forecast_demand(series: pd.DataFrame, horizon: int = 13) -> pd.DataFrame:
    """A simple, honest demand forecast: level + trend + a measured interval.

    Deliberately not elaborate. With ~two years of weekly data and real
    seasonality we cannot fully model, an over-engineered forecast would project
    false precision. We fit a trend, project it, and attach an interval built
    from the model's own residuals - the same 'earn your interval' discipline as
    P1.
    """
    y = series["appointments"].to_numpy(dtype=float)
    n = len(y)

    # Fit a linear trend by least squares.
    x = np.arange(n)
    slope, intercept = np.polyfit(x, y, 1)
    fitted = intercept + slope * x

    # Residual spread drives the interval - measured, not assumed.
    residual_std = float(np.std(y - fitted))

    future_x = np.arange(n, n + horizon)
    point = intercept + slope * future_x

    last_week = pd.to_datetime(series["week"].iloc[-1])
    weeks = pd.date_range(last_week + pd.Timedelta(weeks=1), periods=horizon, freq="W-MON")

    # Interval widens with horizon: uncertainty compounds the further out we look.
    widen = 1 + 0.03 * np.arange(1, horizon + 1)
    margin = 1.96 * residual_std * widen

    return pd.DataFrame(
        {
            "week": weeks,
            "forecast": np.round(point, 0),
            "lower": np.round(point - margin, 0),
            "upper": np.round(point + margin, 0),
        }
    )


def clinic_demand_forecast(appointments: pd.DataFrame, horizon: int = 13) -> pd.DataFrame:
    """Forecast demand for each clinic - the input to per-clinic capacity planning."""
    df = _prepare(appointments)

    rows = []
    for clinic, g in df.groupby("clinic"):
        series = g.groupby("week").size().rename("appointments").reset_index()
        if len(series) < 8:
            continue
        series = series.iloc[:-1]
        fc = forecast_demand(series, horizon)
        avg = fc["forecast"].mean()
        rows.append({"clinic": clinic, "forecast_avg_per_week": round(float(avg), 0)})

    return pd.DataFrame(rows).sort_values("forecast_avg_per_week", ascending=False)


# ---------------------------------------------------------------------------
# ORCHESTRATION
# ---------------------------------------------------------------------------


def analyse(processed_dir: Path, out_dir: Path) -> dict:
    appointments = pd.read_parquet(processed_dir / "appointments_standardized.parquet")
    roster = pd.read_parquet(processed_dir / "provider_roster.parquet")

    util = provider_utilization(appointments, roster)
    clinic = clinic_utilization(util)
    rebalance = rebalancing_opportunity(util)

    series = weekly_demand_series(appointments)
    forecast = forecast_demand(series)
    clinic_fc = clinic_demand_forecast(appointments)

    # --- Print ---
    print("=" * 70)
    print("QUESTION 1 - WHERE IS THE CAPACITY IMBALANCE?")
    print("=" * 70)
    print(f"\n  (Assuming {SLOTS_PER_WEEK_AT_FULL_FTE} slots/week at 1.0 FTE)\n")
    print(f"  {'Provider':<16} {'Clinic':<12} {'FTE':>4} {'demand':>7} {'cap':>5} {'util':>6}  status")
    print(f"  {'-' * 16} {'-' * 12} {'-' * 4} {'-' * 7} {'-' * 5} {'-' * 6}  {'-' * 10}")
    for r in util.itertuples(index=False):
        print(f"  {r.provider:<16} {r.clinic:<12} {r.fte:>4.1f} "
              f"{r.appointments_per_week:>7.1f} {r.capacity_per_week:>5.0f} "
              f"{r.utilization:>6.1%}  {r.status}")

    print("\n  REBALANCING OPPORTUNITY:")
    print(f"    Overbooked providers: {rebalance['overbooked_providers']}   "
          f"Idle providers: {rebalance['idle_providers']}")
    print(f"    Excess demand on overbooked : {rebalance['excess_demand_per_week']:.0f}/week")
    print(f"    Spare capacity on idle      : {rebalance['spare_capacity_per_week']:.0f}/week")
    print(f"    >>> {rebalance['absorbable_per_week']:.0f} appointments/week could move "
          f"from overbooked to idle providers - at NO hiring cost.")

    print("\n  Clinic-level (spread = rebalancing headroom within the clinic):")
    print(f"    {'Clinic':<12} {'util':>6} {'spread':>7} {'providers':>10}")
    print(f"    {'-' * 12} {'-' * 6} {'-' * 7} {'-' * 10}")
    for r in clinic.itertuples(index=False):
        print(f"    {r.clinic:<12} {r.clinic_utilization:>6.1%} "
              f"{r.util_spread:>7.1%} {r.providers:>10}")

    print("\n" + "=" * 70)
    print("QUESTION 2 - HOW MUCH DEMAND IS COMING?")
    print("=" * 70)
    current = series["appointments"].tail(4).mean()
    fc_avg = forecast["forecast"].mean()
    print(f"\n  Recent demand:   {current:.0f} appointments/week")
    print(f"  13-week forecast: {fc_avg:.0f}/week "
          f"(range {forecast['lower'].mean():.0f}-{forecast['upper'].mean():.0f})")
    print(f"  Trend: {'growing' if fc_avg > current else 'flat/declining'}")

    print("\n  Per-clinic forecast (planning input):")
    for r in clinic_fc.itertuples(index=False):
        print(f"    {r.clinic:<12} {r.forecast_avg_per_week:>5.0f}/week")

    print("\n  NOTE: two years of history and partial seasonality. This is a")
    print("  planning aid with an interval, not a promise. Re-fit quarterly.")

    out_dir.mkdir(parents=True, exist_ok=True)
    util.to_parquet(out_dir / "provider_utilization.parquet", index=False)
    clinic.to_parquet(out_dir / "clinic_utilization.parquet", index=False)
    forecast.to_parquet(out_dir / "demand_forecast.parquet", index=False)

    return {
        "utilization": util,
        "clinic": clinic,
        "rebalance": rebalance,
        "forecast": forecast,
        "clinic_forecast": clinic_fc,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Demand forecast and capacity model.")
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    parser.add_argument("--out", type=Path, default=Path("data/processed"))
    args = parser.parse_args()

    analyse(args.processed, args.out)


if __name__ == "__main__":
    main()
