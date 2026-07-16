# Requirements Traceability Matrix — Trinity No-Show Program

**Generated** by `src/trinity/traceability.py`. Do not edit by hand — edit
the links in that module and regenerate. A test asserts every link resolves.

This matrix is the proof that nothing the sponsor asked for was dropped, and
nothing was built that nobody asked for.

---

## Forward trace — every requirement to its origin and its deliverable

| Requirement | What it requires | Traces back to | Satisfied by |
|---|---|---|---|
| **FR-01** | No-show rate from canonical status; unknown spelling halts | N-08 | `src/trinity/standardize.py` (R1 status ruling) |
| **FR-02** | No-show-with-billed-visit reclassified as attended, audited | N-08, N-10 | `src/trinity/standardize.py` (R4 contradiction ruling) |
| **FR-03** | Multi-MRN patients linked to one identity; error rate reported | N-09 | `src/trinity/standardize.py` (R2 dedupe ruling) |
| **FR-04** | Provider FTE recovered from roster; utilization computed | N-02, N-09 | `src/trinity/standardize.py` (R3 FTE-from-colour ruling) |
| **FR-05** | Annual no-show cost from count x stated contribution value | N-01 | `reports/ROI_MODEL.xlsx` (M8 ROI model) |
| **FR-06** | No-show drivers quantified and ranked by effect size | N-03 | `src/trinity/drivers.py` (M5 driver analysis) |
| **FR-07** | Reminder effect estimated accounting for 3-of-7 selection bias | N-04 | `src/trinity/drivers.py` (M5 natural experiment) |
| **FR-08** | Each intervention: cost, return, break-even, sensitivity | N-05 | `reports/ROI_MODEL.xlsx` (M8 ROI model) |
| **FR-09** | Overbooking models the downside, states net expected value | N-06 | `reports/ROI_MODEL.xlsx` (M8 overbooking model) |
| **FR-10** | Measurement plan: KPIs, targets, owners, cadence | N-07 | `docs/requirements/MEASUREMENT_PLAN.md` (M8 measurement plan) |

---

## Backward trace — every stakeholder need to the requirement that addresses it

| Need | Raised by | The need | Addressed by |
|---|---|---|---|
| **N-01** | Dana (COO) | The $1-2M loss is a felt estimate; needs a defensible number | FR-05 |
| **N-02** | Dana (COO) | Some providers overbooked while others sit idle | FR-04 |
| **N-03** | Marcus (Mgr) | No-shows cluster by lead time, new patients, Monday, payer | FR-06 |
| **N-04** | Dana (COO) | A reminder pilot ran in 3 clinics and was never measured | FR-07 |
| **N-05** | Dana (COO) | Wants a phased program under $600k, not a platform | FR-08 |
| **N-06** | Dr. Raghavan | Will contest overbooking on patient-safety grounds | FR-09 |
| **N-07** | Dana (COO) | Success must be measurable within two quarters | FR-10 |
| **N-08** | Tom (IT) | Status is 14 free-text spellings; some contradict billing | FR-01, FR-02 |
| **N-09** | Tom (IT) | Same patient under several MRNs; FTE encoded as cell colour | FR-03, FR-04 |
| **N-10** | Dr. Raghavan | Numbers must survive hostile review to reach the board | FR-02 |

---

## Coverage

- **10** discovery needs, all addressed.
- **10** requirements, all justified by a need.
- No orphan requirements (scope creep). No dropped needs (broken promises).

*If this section is present, the matrix passed verification at generation time.*