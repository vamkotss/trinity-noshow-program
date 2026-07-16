# Process Maps — Appointment Lifecycle

**Author:** Sri Vamsi Kota, Business Analyst
**Related:** `BRD.md`, `TRACEABILITY.md`, `interviews/discovery-notes.md`

This document maps the appointment lifecycle two ways: **as-is** (how it works
today, with the points where no-shows go unmanaged) and **to-be** (the redesigned
flow with the program's interventions in place).

The gap between the two diagrams is the program. Every new box in the to-be map
traces to a requirement, and every requirement traces to a stakeholder need —
see the traceability note at the end.

---

## 1. As-is — the current appointment lifecycle

What happens today. The red-flagged steps are where the process fails to manage
no-show risk — not because anyone is doing anything wrong, but because nothing in
the flow is designed to catch it.

```mermaid
flowchart TD
    A[Patient requests appointment] --> B[Front desk books a slot]
    B --> C{Reminder call made?}
    C -->|"Only if there's time<br/>(3 of 7 clinics)"| D[Reminder attempted]
    C -->|"No — most appointments"| E[No reminder]
    D --> F[Appointment day]
    E --> F
    F --> G{Patient arrives?}
    G -->|Yes| H[Visit happens, billed]
    G -->|No| I[No-show]
    I --> J[Slot sits empty]
    J --> K[Provider idle for that slot]
    H --> L[End]
    K --> L

    style C fill:#ffd7d7,stroke:#c0392b
    style E fill:#ffd7d7,stroke:#c0392b
    style I fill:#ffd7d7,stroke:#c0392b
    style J fill:#ffd7d7,stroke:#c0392b
    style K fill:#ffd7d7,stroke:#c0392b
```

### Where it fails today

| # | Failure point | What it costs |
|---|---|---|
| F1 | **Reminders are ad-hoc** — made "when there's time", and only 3 of 7 clinics log them at all | High-risk appointments go un-reminded; the effect is unmeasured and unmanaged |
| F2 | **Booking ignores no-show risk** — a 60-day-out new-patient Monday slot is booked exactly like a same-week established one, despite ~2.5x the no-show rate | The most predictable no-shows are the least protected against |
| F3 | **An empty slot is a dead loss** — nothing fills it, nothing overbooks against it | Provider time is unbilled; capacity is wasted |
| F4 | **No feedback loop** — no-shows are not tracked, so nothing learns | The problem is invisible to the people who could fix it |

---

## 2. To-be — the redesigned lifecycle

The same flow, with four interventions inserted. Each new (green) step maps to a
requirement in the BRD.

```mermaid
flowchart TD
    A[Patient requests appointment] --> B[Front desk books a slot]
    B --> RISK[Score no-show risk<br/>lead time, patient type,<br/>day/time, payer]
    RISK --> DEC{Risk tier?}

    DEC -->|High risk| OB[Flag slot for<br/>controlled overbooking]
    DEC -->|Any tier| REM[Send reminder<br/>via preferred channel]

    OB --> DAY[Appointment day]
    REM --> DAY

    DAY --> ARR{Patient arrives?}
    ARR -->|Yes| VISIT[Visit happens, billed]
    ARR -->|No, but slot was overbooked| FILL[Overbook patient seen<br/>— slot recovered]
    ARR -->|No, not overbooked| NS[No-show recorded]

    VISIT --> TRACK[Log outcome to<br/>no-show tracker]
    FILL --> TRACK
    NS --> TRACK
    TRACK --> KPI[Weekly KPI review<br/>no-show rate, utilization,<br/>overbook collisions]
    KPI --> LEARN[Adjust risk model<br/>and overbook rules]
    LEARN -.->|feeds back into| RISK

    style RISK fill:#d5f5d5,stroke:#27ae60
    style OB fill:#d5f5d5,stroke:#27ae60
    style REM fill:#d5f5d5,stroke:#27ae60
    style FILL fill:#d5f5d5,stroke:#27ae60
    style TRACK fill:#d5f5d5,stroke:#27ae60
    style KPI fill:#d5f5d5,stroke:#27ae60
    style LEARN fill:#d5f5d5,stroke:#27ae60
```

### What each new step does, and where it comes from

| New step | Fixes | Requirement | Need |
|---|---|---|---|
| **Score no-show risk** at booking | F2 | FR-06 (drivers ranked) | N-03 (Marcus: no-shows cluster) |
| **Controlled overbooking** for high-risk slots | F3 | FR-09 (overbook w/ downside) | N-02, N-06 (idle capacity; safety) |
| **Structured reminders** for all appointments | F1 | FR-07 (reminder effect) | N-04 (Dana: did reminders work?) |
| **No-show tracker + KPI review + feedback** | F4 | FR-10 (measurement plan) | N-07 (measurable in 2 quarters) |

---

## 3. The one step that needs the most care

**Controlled overbooking** is the intervention Dr. Raghavan will attack, and the
process map is deliberately honest about its risk. Note the branch:

> *"No, but slot was overbooked" → Overbook patient seen — slot recovered*
> *"Yes" (both the original and overbook patient arrive) → both are seen*

The second case is the danger: if you overbook a slot and **both** patients show,
someone waits. That is exactly Raghavan's objection. The to-be process manages it
two ways:

1. **Overbooking is applied only to high-risk slots** — the ones the driver
   analysis shows have ~23-26% no-show rates, not blanket-applied. You overbook
   where a no-show is likely, not everywhere.
2. **The KPI review tracks "overbook collisions"** — the rate at which both
   patients attend — as a first-class metric. If collisions climb, the overbook
   rules tighten automatically via the feedback loop.

This is why the ROI model (M8) must price the *downside* of overbooking, not just
the upside. The process map and the ROI model tell the same honest story: the
intervention works *because* it is targeted and monitored, not despite being
reckless.

---

## 4. Traceability

Every green box above traces to a requirement and a stakeholder need. Nothing in
the redesign exists because it seemed like a good idea — each step closes a
specific, documented failure in the as-is flow. That is the difference between a
process redesign and a wish list.
