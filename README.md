# Trinity Family Health — No-Show & Capacity Program

[![CI](https://github.com/vamkotss/trinity-noshow-program/actions/workflows/ci.yml/badge.svg)](https://github.com/vamkotss/trinity-noshow-program/actions/workflows/ci.yml)

**A 7-clinic health network is losing an estimated $1–2M a year to no-shows and badly balanced schedules. The COO wants a board-ready funding request in 90 days. This repository is the business case — from the first stakeholder interview to the ROI model that survives a hostile physician in the board room.**

> **The finding that would have cost them $45k:**
>
> A clinic-level comparison said reminder calls cut no-shows by 2.3 points. Fund it, obviously. **Except it was wrong.** The three clinics that logged reminders also served a far lower-risk patient mix — 11% self-pay/Medicaid vs 34% elsewhere. Adjusting for that, the real effect was **0.7 points with a confidence interval spanning zero.** ~70% of the "reminders work" signal was selection bias. The recommendation: run a randomised pilot, don't fund a rollout on a confounded number.

📊 **[Board deck](reports/BOARD_DECK.pptx)** · 📈 **[ROI model](reports/ROI_MODEL.xlsx)** · 📋 **[Project charter](docs/CHARTER.md)** · 🔗 **[Requirements traceability](docs/requirements/TRACEABILITY.md)**

---

## Why this is a Business Analyst project, not a data project

The analysis feeds the business case. It is not the deliverable. What a BA is actually hired to do is here:

| | |
|---|---|
| **Scope an ambiguous ask.** | The COO opened with "we need a better scheduling system" — a *solution*, before anyone had seen the data. The [charter](docs/CHARTER.md) reframes it as an outcome, sets the $600k ceiling and 18-month payback, and — critically — has the sponsor **sign an explicit out-of-scope list** so week-8 scope creep gets declined by reference to a document, not an opinion. |
| **Translate needs into requirements.** | 7 user stories, 10 functional requirements, and a [traceability matrix](docs/requirements/TRACEABILITY.md) linking every requirement backward to a stakeholder need and forward to the deliverable that satisfies it. It is *generated and tested* — a build fails if any link dangles. |
| **Redesign the process.** | [As-is and to-be process maps](docs/process/PROCESS_MAPS.md) showing where no-show risk goes unmanaged today and where each intervention slots in. Every new step traces to a requirement. |
| **Build a defensible financial model.** | An [ROI model](reports/ROI_MODEL.xlsx) where every figure is a live formula. The board can change one assumption cell and watch every ROI recompute. |
| **Handle PHI responsibly.** | A HIPAA Safe Harbor [de-identification pass](docs/DATA_HANDLING.md) — and an honest note that hashing MRNs is *pseudonymisation, not anonymisation*. |

**71 tests. Green CI on every commit.**

---

## The data was deliberately broken — the way real clinic data is

A seeded, tested generator builds four operational sources with the defects an IT lead actually warns you about in discovery:

- **14 free-text spellings of "no-show"** — `NS`, `no show`, `DNA`, `cancelled by pt`, `CXL`… all meaning the same thing.
- **The same patient under three medical record numbers**, with name variants (`Sarah Jones` / `S. Jones` / `Sara Jones `).
- **A provider roster where each doctor's FTE is encoded as the *background colour* of a spreadsheet cell** — green = full-time, yellow = 0.8, orange = 0.6. There is no FTE column. It has to be read out of the cell formatting.
- **A billing extract that contradicts the schedule** — some appointments marked "no-show" have a paid visit attached.
- **A reminder log covering only 3 of 7 clinics** — the natural experiment, with its selection bias baked in.

Knowing exactly what is wrong — because it was injected on purpose — is what lets the cleaning layer be *tested* rather than eyeballed.

---

## Four rulings, each with its cost stated

Every transformation from raw to analysable is a decision, documented in [`STANDARDIZATION_RULINGS.md`](docs/requirements/STANDARDIZATION_RULINGS.md) with its rationale **and what it costs**:

| Ruling | Decision | The honest cost |
|---|---|---|
| **R1** Status | 14 spellings → 3 states; an unknown spelling **halts the pipeline** rather than defaulting | The mapping must be maintained |
| **R2** Dedupe | Link patients on date-of-birth + name | ~15 false merges per 8,000 patients — **measured and reported**, not hidden |
| **R3** FTE | Recover the fraction from the cell's fill colour | Coupled to the roster's exact layout |
| **R4** Contradiction | **Billing wins** — a paid claim documents a real visit; reclassify, but quarantine every change with a receipt | Overrides the schedule of record |

> *An analyst who claims their dedupe is exact is either not measuring it or not telling you. This one measures it — and states the false-merge rate in the rulings doc.*

---

## What the analysis found

**No-shows have real, rankable drivers** — and lead time is the biggest lever:

| Lead time | No-show rate |
|---|---|
| 0–7 days | 10% |
| 15–30 days | 16% |
| 31–60 days | 23% |
| 60+ days | 26% |

That curve is the evidence base for overbooking: apply it **only** to the long-lead, high-risk slots.

**Capacity is badly balanced.** Single-provider clinics are drowning while two-provider clinics coast:

- Denton (1 provider, 0.6 FTE): **135% utilized** — turning patients away
- Eight providers at 2-provider clinics: **50–68%** — idle capacity being paid for
- **27 appointments/week could move from overbooked to idle providers at zero hiring cost**

---

## The funding request — ranked, and honest about what doesn't work

| Intervention | Benefit/yr | Cost/yr | Net/yr | ROI |
|---|---|---|---|---|
| **1. Rebalance providers** | $194k | $15k | **+$179k** | **12.0x** |
| 2. Overbook high-risk slots | $5k | $20k | –$15k | marginal |
| 3. Reminder pilot | $32k | $45k | –$13k | pilot only |

**Only one intervention is a clear win — and saying so is the point.** A weaker business case makes everything look fundable. This one shows that overbooking nets just **$3.95 per slot** once the collision cost (a patient waiting when both show up) is priced in, and that reminders don't clear their cost at the *honest* 0.7-point effect.

That is the model that survives the board room. The physician who was going to attack overbooking on safety grounds finds the model already **agrees with her** — it prices her objection and shows the intervention is thin, applied only to high-risk slots, with collision rate as a monitored KPI.

---

## Run it

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
python -m pip install -r requirements.txt

$env:PYTHONPATH = "src"

python -m trinity.generate --out data/raw
python -m trinity.deidentify --raw data/raw --processed data/processed
python -m trinity.standardize --raw data/raw --processed data/processed
python -m trinity.drivers --processed data/processed
python -m trinity.capacity --processed data/processed
python -m trinity.roi_model

python -m pytest tests/ -v          # 71 tests
```

The generator is seeded — your output will match this repo's.

---

## Layout

| Path | |
|---|---|
| [`docs/CHARTER.md`](docs/CHARTER.md) | Project charter with sponsor-signed scope boundaries |
| [`docs/interviews/`](docs/interviews/) | Discovery synthesis from four stakeholders |
| [`docs/requirements/BRD.md`](docs/requirements/BRD.md) | User stories and functional requirements |
| [`docs/requirements/TRACEABILITY.md`](docs/requirements/TRACEABILITY.md) | Generated, tested traceability matrix |
| [`docs/requirements/STANDARDIZATION_RULINGS.md`](docs/requirements/STANDARDIZATION_RULINGS.md) | The four data rulings, each with its cost |
| [`docs/process/PROCESS_MAPS.md`](docs/process/PROCESS_MAPS.md) | As-is and to-be process redesign |
| [`docs/DATA_HANDLING.md`](docs/DATA_HANDLING.md) | HIPAA de-identification note |
| [`reports/ROI_MODEL.xlsx`](reports/ROI_MODEL.xlsx) | The formula-driven financial model |
| [`reports/BOARD_DECK.pptx`](reports/BOARD_DECK.pptx) | The board presentation |
| `src/trinity/` | The pipeline |
| `tests/` | 71 tests, run on every push |

---

## Stack

Python 3.13 · pandas · openpyxl · scipy · pytest · ruff · GitHub Actions · Excel · PowerPoint

---

## Author

**Sri Vamsi Kota** — MS Business Analytics & AI, UT Dallas
[github.com/vamkotss](https://github.com/vamkotss)
