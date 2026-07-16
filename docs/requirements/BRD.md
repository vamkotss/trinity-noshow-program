# Business Requirements Document — Trinity No-Show & Capacity Program

**Version:** 1.0
**Author:** Sri Vamsi Kota, Business Analyst
**Sponsor:** Dana Reyes, COO
**Status:** Draft — pending sponsor review
**Related:** `CHARTER.md`, `interviews/discovery-notes.md`, `requirements/TRACEABILITY.md`

---

## 1. Purpose

This document translates the needs elicited during discovery into explicit,
testable requirements. It is the bridge between *what stakeholders said they
need* and *what the analysis and program will deliver*. Every requirement here
traces backward to a discovery finding and forward to a deliverable — see the
traceability matrix.

## 2. Background

Trinity Family Health, a 7-clinic DFW primary-care network, is losing an
estimated $1–2M per year to appointment no-shows and imbalanced provider
schedules. The COO will present a board funding request within 90 days for a
phased program of interventions under a $600k year-one ceiling. This project
produces the business case.

## 3. Stakeholders

| Stakeholder | Role | Primary concern |
|---|---|---|
| Dana Reyes | COO / Sponsor | A defensible business case and board-ready funding request |
| Marcus Ellery | Clinic Manager | Front-line workability; already overbooks informally |
| Dr. Priya Raghavan | Physician | Patient safety; will contest overbooking in the board room |
| Tom Whitlock | IT Lead | Data accuracy and its real limits |

---

## 4. User stories

Written in the standard form. Each carries an ID used by the traceability matrix.

### Quantifying the problem

**US-01** — As the **COO**, I want the annual cost of no-shows quantified with a
stated method, so that I can present a defensible number to the board instead of
a guess.

**US-02** — As the **COO**, I want the cost of idle provider capacity quantified
separately from no-shows, so that I can tell whether the bigger problem is
patients not showing or schedules being built badly.

### Understanding the drivers

**US-03** — As a **clinic manager**, I want to know which appointments are most
likely to no-show, so that the front desk can focus reminders and overbooking
where they matter instead of guessing.

**US-04** — As the **COO**, I want to know whether reminder calls actually reduce
no-shows, so that I do not fund a reminder program on the strength of a pattern
that turns out to be coincidence.

### Designing interventions

**US-05** — As the **COO**, I want a ranked, costed set of interventions that
fits under $600k, so that I can fund the highest-return combination rather than a
single expensive platform.

**US-06** — As a **physician**, I want any overbooking recommendation to target
genuine no-show risk and to bound the cost of a mistake, so that I can be
confident it will not routinely put attending patients in a crowded waiting room.

### Measuring success

**US-07** — As the **COO**, I want a measurement plan with KPIs and targets, so
that I can tell within two quarters whether the program is working and report
that to the board.

---

## 5. Functional requirements

What the analysis and its deliverables must *do*. Each is testable.

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | The no-show rate shall be computed from a canonical status derived from all known free-text spellings; an unknown spelling shall halt processing rather than default. | Must |
| FR-02 | Appointments marked no-show but with a billed visit shall be reclassified as attended, and each such correction shall be recorded and auditable. | Must |
| FR-03 | Patients appearing under multiple record numbers shall be linked to a single identity before any per-patient metric is computed; the linkage error rate shall be measured and reported. | Must |
| FR-04 | Provider full-time-equivalent capacity shall be recovered from the roster and used to compute per-provider and per-clinic utilization. | Must |
| FR-05 | The annual dollar cost of no-shows shall be estimated from the no-show count and a stated per-visit contribution value, with the assumptions listed. | Must |
| FR-06 | No-show drivers (lead time, patient type, day/time, payer) shall be quantified and ranked by effect size. | Must |
| FR-07 | The effect of reminder calls shall be estimated in a way that accounts for the fact that only three clinics logged them, and any confounding shall be stated. | Must |
| FR-08 | Each recommended intervention shall carry an estimated cost, an estimated return, and a break-even, with sensitivity to the key assumptions. | Must |
| FR-09 | An overbooking recommendation shall model the downside (both patients attend) as well as the upside, and shall state the net expected value. | Must |
| FR-10 | A measurement plan shall define KPIs, targets, owners, and the cadence at which each is reviewed. | Should |

## 6. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | All patient data shall be de-identified per HIPAA Safe Harbor before analysis; the handling approach and its limits shall be documented. |
| NFR-02 | Every headline number shall be reproducible from raw data by running the documented pipeline; the generator shall be seeded. |
| NFR-03 | Every metric definition and cleaning ruling shall be documented with its rationale and its cost. |
| NFR-04 | The business case shall survive hostile review: each number shall be traceable to the code and the ruling that produced it. |

## 7. Assumptions and constraints

- **Budget:** ~$600k year one; payback within 18 months.
- **Timeline:** board presentation within 90 days.
- **Data:** four clinics have full history; three are partial; two newest are out
  of scope (per charter).
- **Contribution value per attended visit** is an input to the cost model and
  will be sourced from Finance; until then a stated placeholder is used and
  flagged in sensitivity analysis.

## 8. Out of scope

Per the signed charter: billing/denials, scheduling-software replacement,
clinical protocols, and the two newest clinics.
