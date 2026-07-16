# Standardization Rulings — Trinity No-Show Analysis

**Version:** 1.0
**Status:** Draft — pending analyst sign-off
**Applies to:** all downstream analysis and the ROI model

Every transformation between the raw operational export and the analysable
dataset is a decision. This document records each decision, why it was made, and
**what it costs** — because a ruling with no stated cost is a ruling nobody has
thought hard enough about.

Each ruling is implemented in `src/trinity/standardize.py` and enforced by a test
in `tests/test_standardize.py`.

---

## R1 — Status standardization

**The situation.** The `status` field is free text. Fourteen distinct strings
mean the patient did not show: `NS`, `no show`, `noshow`, `no-show`, `No Show`,
`DNA`, `dna`, `cancelled by pt`, `CXL`, `cxl`, `did not attend`, `n/s`,
`No-Show`, `NOSHOW`.

**The ruling.** Map every known string to one of three canonical states —
`no_show`, `arrived`, `cancelled` — via an explicit table. **An unmapped string
raises an error; it is never defaulted.**

**Why raise instead of default.** A silent default is the most dangerous option.
If a new spelling appeared next quarter and quietly became `arrived`, the
no-show rate — the number the entire business case rests on — would deflate with
no warning and no error. A loud failure forces a human to make a ruling. That is
correct: a new spelling *is* a new decision.

**The cost.** The mapping must be maintained. When the front desk invents a
fifteenth spelling, the pipeline stops until someone adds it. We accept that
cost, because the alternative is a wrong number that looks right.

---

## R2 — Patient deduplication

**The situation.** The same human appears under multiple medical record numbers,
with name variants (`Sarah Jones`, `S. Jones`, `Sara Jones `). Un-deduplicated,
a patient who no-shows repeatedly under three MRNs looks like three occasional
no-show patients, and per-patient analysis is wrong.

**The ruling.** Link records on **date of birth plus a normalised name
signature** (first initial + cleaned surname). Records matching both are the
same person; the analysis operates on the canonical patient.

**Why DOB is the anchor.** Names drift — people shorten them, add spaces,
mistype. A date of birth does not. Anchoring on the stable field and refining
with a loose name match catches the realistic variants without over-merging.

**The cost — stated honestly.** This method **cannot be perfect**, because there
is no true unique key. Two genuinely different people who share a birth date
*and* a name signature will be wrongly merged. In this dataset that is roughly
15 false merges across 8,000 patients — about 0.2%. We **measure and report**
this rather than claiming a precision the method does not have. For the headline
no-show numbers it is immaterial; for any per-patient claim it is a stated
limitation, not a hidden one.

*An analyst who claims their dedupe is exact is either not measuring it or not
telling you. We measure it.*

---

## R3 — FTE from cell colour

**The situation.** The provider roster is a hand-maintained spreadsheet. Each
provider's full-time-equivalent fraction is not in a column — it is the
**background colour of a cell**. Green = 1.0, yellow = 0.8, orange = 0.6. The FTE
text cell is blank.

**The ruling.** Read the cell fill colour with `openpyxl`, map the hex value back
to a fraction via the legend, and fail loudly on any colour the legend does not
cover.

**Why this matters.** Provider utilization — a core input to the capacity half
of the business case — cannot be computed without knowing how much each provider
works. That number exists only as colour. Extracting it is not optional, and it
is not something a spreadsheet formula can do.

**The cost.** The extraction is coupled to the roster's exact layout and colour
scheme. If Brenda changes the colours or moves the columns, the extractor breaks
— loudly, by design. A roster we cannot fully decode is not one we quietly
half-decode.

---

## R4 — The schedule / billing contradiction

**The situation.** Some appointments the schedule marks as `no_show` have a
**billed visit** attached in the billing extract. The two systems disagree about
whether the patient showed up.

**The ruling. Billing wins.** A contradicted appointment is reclassified to
`arrived`. Every reclassified row is **quarantined with its billed amount and a
note** — the change is never silent.

**Why billing wins.** A submitted claim documents a real, audited, face-to-face
encounter. An un-updated scheduling status is a routine clerical miss — the front
desk gets slammed, a patient walks in, the visit happens, nobody clicks the
dropdown back. When the two disagree, the billed visit is near-certainly the real
event.

**Why this ruling is load-bearing.** The entire business case is *"no-shows cost
Trinity $X."* If the schedule won, X would be inflated by people who
demonstrably attended. The first time a physician pulls a chart in the board room
and finds a billed visit on a "no-show," the number dies — and every number
beside it dies with it. One visible contradiction discredits the whole analysis.

**Why quarantine rather than just fix.** Silently flipping the rows would hide a
real operational finding: the schedule is wrong in a knowable direction, a
fraction of the time. The quarantine is the receipt. When challenged, the answer
is a list — *"these N appointments showed as no-shows but had billed visits; here
they are"* — not a shrug.

**The cost.** We are overriding the no-show system of record with a source built
for a different purpose. We accept that, because billing is the more trustworthy
witness and because the override is fully auditable.

---

## Summary

| Ruling | Decision | Failure mode it prevents | Stated cost |
|---|---|---|---|
| R1 | 14 spellings → 3 states; unknown raises | A new spelling silently deflating the no-show rate | Mapping must be maintained |
| R2 | Dedupe on DOB + name | Split patient histories | ~0.2% false merges, measured |
| R3 | FTE from cell colour | No utilization analysis at all | Coupled to roster layout |
| R4 | Billing wins, quarantined | Inflated no-show cost, discredited in the board room | Overrides the schedule of record |
