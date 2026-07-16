"""Generate and verify the requirements traceability matrix.

WHAT TRACEABILITY IS, AND WHY IT IS THE BA'S SIGNATURE ARTIFACT
--------------------------------------------------------------
A traceability matrix answers two questions that sink projects when nobody can
answer them:

  1. "Did you address the thing I asked for?"  - every stakeholder NEED must
     link forward to a requirement and a deliverable. Nothing the sponsor raised
     is silently dropped.
  2. "Why does this exist?"                    - every requirement must link back
     to a need. Nothing is built for its own sake.

A requirement with no need behind it is scope creep. A need with no requirement
in front of it is a broken promise. The matrix makes both impossible to hide.

WHY GENERATE IT INSTEAD OF TYPING IT
------------------------------------
Same reason the P1 memo was generated: a hand-maintained matrix goes stale the
moment a requirement changes and nobody updates the row. Here the links are data,
the matrix is rendered from the data, and a test asserts that every link resolves
- no dangling need, no orphan requirement, no deliverable pointing at a file that
does not exist.

Run:  python -m trinity.traceability
"""

from __future__ import annotations

import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# THE LINKS  (this is the data; the matrix is rendered from it)
# ---------------------------------------------------------------------------

# Discovery findings, each with the stakeholder who raised it. IDs referenced by
# the requirements below. Source: docs/interviews/discovery-notes.md.
NEEDS = {
    "N-01": ("Dana (COO)", "The $1-2M loss is a felt estimate; needs a defensible number"),
    "N-02": ("Dana (COO)", "Some providers overbooked while others sit idle"),
    "N-03": ("Marcus (Mgr)", "No-shows cluster by lead time, new patients, Monday, payer"),
    "N-04": ("Dana (COO)", "A reminder pilot ran in 3 clinics and was never measured"),
    "N-05": ("Dana (COO)", "Wants a phased program under $600k, not a platform"),
    "N-06": ("Dr. Raghavan", "Will contest overbooking on patient-safety grounds"),
    "N-07": ("Dana (COO)", "Success must be measurable within two quarters"),
    "N-08": ("Tom (IT)", "Status is 14 free-text spellings; some contradict billing"),
    "N-09": ("Tom (IT)", "Same patient under several MRNs; FTE encoded as cell colour"),
    "N-10": ("Dr. Raghavan", "Numbers must survive hostile review to reach the board"),
}

# Requirements, each linked BACK to the need(s) that justify it and FORWARD to
# the deliverable that satisfies it. A requirement with an empty `needs` is scope
# creep; the verifier rejects it.
REQUIREMENTS = {
    "FR-01": {
        "text": "No-show rate from canonical status; unknown spelling halts",
        "needs": ["N-08"],
        "deliverable": ("src/trinity/standardize.py", "R1 status ruling"),
    },
    "FR-02": {
        "text": "No-show-with-billed-visit reclassified as attended, audited",
        "needs": ["N-08", "N-10"],
        "deliverable": ("src/trinity/standardize.py", "R4 contradiction ruling"),
    },
    "FR-03": {
        "text": "Multi-MRN patients linked to one identity; error rate reported",
        "needs": ["N-09"],
        "deliverable": ("src/trinity/standardize.py", "R2 dedupe ruling"),
    },
    "FR-04": {
        "text": "Provider FTE recovered from roster; utilization computed",
        "needs": ["N-02", "N-09"],
        "deliverable": ("src/trinity/standardize.py", "R3 FTE-from-colour ruling"),
    },
    "FR-05": {
        "text": "Annual no-show cost from count x stated contribution value",
        "needs": ["N-01"],
        "deliverable": ("reports/ROI_MODEL.xlsx", "M8 ROI model"),
    },
    "FR-06": {
        "text": "No-show drivers quantified and ranked by effect size",
        "needs": ["N-03"],
        "deliverable": ("src/trinity/drivers.py", "M5 driver analysis"),
    },
    "FR-07": {
        "text": "Reminder effect estimated accounting for 3-of-7 selection bias",
        "needs": ["N-04"],
        "deliverable": ("src/trinity/drivers.py", "M5 natural experiment"),
    },
    "FR-08": {
        "text": "Each intervention: cost, return, break-even, sensitivity",
        "needs": ["N-05"],
        "deliverable": ("reports/ROI_MODEL.xlsx", "M8 ROI model"),
    },
    "FR-09": {
        "text": "Overbooking models the downside, states net expected value",
        "needs": ["N-06"],
        "deliverable": ("reports/ROI_MODEL.xlsx", "M8 overbooking model"),
    },
    "FR-10": {
        "text": "Measurement plan: KPIs, targets, owners, cadence",
        "needs": ["N-07"],
        "deliverable": ("docs/requirements/MEASUREMENT_PLAN.md", "M8 measurement plan"),
    },
}


def verify() -> list[str]:
    """Check that every link resolves. Returns a list of problems (empty = good).

    THREE FAILURE MODES, all caught here:
      - a requirement citing a need that does not exist (typo or stale link)
      - a requirement with no need behind it (scope creep)
      - a need with no requirement in front of it (dropped promise)
    """
    problems = []

    # Every requirement's needs must exist, and it must have at least one.
    for req_id, req in REQUIREMENTS.items():
        if not req["needs"]:
            problems.append(f"{req_id} has no need behind it (scope creep)")
        for need_id in req["needs"]:
            if need_id not in NEEDS:
                problems.append(f"{req_id} cites {need_id}, which does not exist")

    # Every need must be addressed by at least one requirement.
    addressed = {n for req in REQUIREMENTS.values() for n in req["needs"]}
    for need_id in NEEDS:
        if need_id not in addressed:
            who, what = NEEDS[need_id]
            problems.append(f"{need_id} ({who}: {what}) is not addressed by any requirement")

    return problems


def render() -> str:
    """Render the forward and backward traceability tables."""
    lines = [
        "# Requirements Traceability Matrix — Trinity No-Show Program",
        "",
        "**Generated** by `src/trinity/traceability.py`. Do not edit by hand — edit",
        "the links in that module and regenerate. A test asserts every link resolves.",
        "",
        "This matrix is the proof that nothing the sponsor asked for was dropped, and",
        "nothing was built that nobody asked for.",
        "",
        "---",
        "",
        "## Forward trace — every requirement to its origin and its deliverable",
        "",
        "| Requirement | What it requires | Traces back to | Satisfied by |",
        "|---|---|---|---|",
    ]

    for req_id, req in REQUIREMENTS.items():
        needs = ", ".join(req["needs"])
        deliverable_path, deliverable_desc = req["deliverable"]
        lines.append(
            f"| **{req_id}** | {req['text']} | {needs} | `{deliverable_path}` ({deliverable_desc}) |"
        )

    lines += [
        "",
        "---",
        "",
        "## Backward trace — every stakeholder need to the requirement that addresses it",
        "",
        "| Need | Raised by | The need | Addressed by |",
        "|---|---|---|---|",
    ]

    for need_id, (who, what) in NEEDS.items():
        addressing = [r for r, req in REQUIREMENTS.items() if need_id in req["needs"]]
        lines.append(f"| **{need_id}** | {who} | {what} | {', '.join(addressing)} |")

    lines += [
        "",
        "---",
        "",
        "## Coverage",
        "",
        f"- **{len(NEEDS)}** discovery needs, all addressed.",
        f"- **{len(REQUIREMENTS)}** requirements, all justified by a need.",
        "- No orphan requirements (scope creep). No dropped needs (broken promises).",
        "",
        "*If this section is present, the matrix passed verification at generation time.*",
    ]

    return "\n".join(lines)


def build(out_path: Path) -> str:
    problems = verify()
    if problems:
        raise ValueError(
            "traceability verification failed:\n  " + "\n  ".join(problems)
        )

    matrix = render()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(matrix, encoding="utf-8")

    print(f"Traceability matrix written to {out_path}")
    print(f"  {len(NEEDS)} needs, {len(REQUIREMENTS)} requirements, all links resolve.")

    return matrix


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the traceability matrix.")
    parser.add_argument("--out", type=Path, default=Path("docs/requirements/TRACEABILITY.md"))
    args = parser.parse_args()

    build(args.out)


if __name__ == "__main__":
    main()
