# Discovery Interview Notes — Trinity No-Show Program

Four stakeholders, two sessions. Notes below are the analyst's synthesis, not
verbatim transcripts. Each finding is tagged with who it came from and what it
changes about the project.

---

## Dana Reyes — COO (Sponsor)

- Funding a **phased program**, not a product. Up to **$600k year one**, payback
  **≤ 18 months**, board presentation in **90 days**.
- Loss is a felt **$1–2M/yr** — undefended. Quantifying it defensibly is the
  first deliverable.
- A prior **reminder pilot ran in 3 clinics and was never measured.** [→ natural
  experiment]
- Named the imbalance directly: some providers overbooked while others sit idle.
- **Dr. Raghavan will contest any recommendation in the board room.** Every
  number must survive hostile clinical review.
- Signed the scope boundaries (see CHARTER.md). Billing, software replacement,
  clinical protocols, and the two newest clinics are OUT.

## Tom Whitlock — IT Lead (Data witness)

The data does not mean what the column headers say. Specifically:

- **`status` is free text — 14 distinct strings mean "no-show"** ('NS', 'no
  show', 'noshow', 'DNA', 'cancelled by pt', 'CXL', ...). No-show *rate* is
  undefined until these are mapped. [→ standardization ruling, M3]
- **Status contradicts the visit-notes file.** Some rows marked no-show have a
  billed visit attached — someone arrived, nobody updated the schedule. A rule
  is needed for which source wins. [→ ruling, M3]
- **Duplicate patients: same human, up to 3 MRNs** (name variants). Per-patient
  analysis is wrong until deduplicated. [→ MRN dedupe, M3]
- **Provider roster is an Excel file with FTE encoded as CELL BACKGROUND COLOR**
  (green = full-time, yellow = part-time, orange = per-diem). Must be extracted
  programmatically. [→ color-extraction task, M3]
- **Reminder call log covers only 3 of 7 clinics.** The 4 without it never
  logged. [→ selection-bias trap in the natural experiment, M5]
- Appointment types are free-typed. CPT-like codes in the billing extract have
  typos. Payer column mixes payer names and plan IDs.

## Marcus Ellery — Clinic Manager, Plano (Front-line reality) [synthesized]

- Front desk overbooks *informally already* — experienced staff double-book
  slots they "know" will no-show. It's undocumented tribal knowledge, not policy.
  [→ the to-be process formalizes what good staff already do]
- No-shows cluster: Monday mornings, new patients, long lead times between
  booking and appointment, and certain payer types.
- Reminder calls are made "when there's time" — which is why coverage is
  inconsistent. Not a clean experiment; the clinics that logged reminders may
  differ systematically from those that didn't. [→ reinforces M5 bias concern]
- Telehealth slots almost never no-show, but providers resist them.

## Dr. Priya Raghavan — Family Medicine (The adversary) [synthesized]

- Will attack any overbooking recommendation on **patient-safety** grounds: a
  double-booked slot that both patients attend means a sick person waits.
- Will demand the no-show *prediction* be good enough that overbooking targets
  genuine no-shows, not random patients. [→ the ROI model must bound the
  "both showed up" cost, not just the upside]
- Respects evidence. A defensible number and an honest error bound will move her;
  hand-waving will not.

---

## What discovery changed about the project

1. "No-show rate" is not a given — it is a **defined metric with rulings**, exactly
   like churn in P1. This becomes M3.
2. The natural experiment (reminders) has a **selection-bias problem** that must be
   named and bounded, not glossed. This shapes M5.
3. Utilization analysis is **blocked on a color-extraction task** before any SQL
   can run. This is the highest-risk technical dependency; do it early.
4. The ROI model must model the **downside** (overbooking collisions), because the
   adversary will attack there — not just the upside.
5. Scope is locked and signed. Billing, platform replacement, clinical protocols,
   and the two newest clinics are out.
