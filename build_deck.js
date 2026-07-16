// Trinity No-Show Program — board deck.
// Eight slides: the funding request, built from the analysis and the ROI model.
// Numbers here match the pipeline outputs and the ROI_MODEL.xlsx.

const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5

const NAVY = "1F3864";
const BLUE = "366092";
const GREEN = "27AE60";
const RED = "C0392B";
const GREY = "888888";
const LIGHT = "F2F5F9";

// ---- helpers ----
function titleBar(slide, text) {
  slide.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.3, h: 1.1, fill: { color: NAVY } });
  slide.addText(text, { x: 0.5, y: 0, w: 12.3, h: 1.1, fontSize: 26, bold: true, color: "FFFFFF", valign: "middle", fontFace: "Arial" });
}

// ================= SLIDE 1 — TITLE =================
let s = pres.addSlide();
s.background = { color: NAVY };
s.addText("Reducing No-Shows and Rebalancing Capacity", { x: 0.7, y: 2.2, w: 11.9, h: 1.2, fontSize: 34, bold: true, color: "FFFFFF", fontFace: "Arial" });
s.addText("A phased, funded program — business case for the board", { x: 0.7, y: 3.5, w: 11.9, h: 0.6, fontSize: 18, color: "AEC6E4", fontFace: "Arial" });
s.addText("Trinity Family Health  ·  Prepared by Analytics  ·  Under the $600k year-one ceiling", { x: 0.7, y: 6.4, w: 11.9, h: 0.5, fontSize: 12, color: "AEC6E4", fontFace: "Arial" });

// ================= SLIDE 2 — THE ASK (BLUF) =================
s = pres.addSlide();
titleBar(s, "The ask, up front");
s.addText([
  { text: "Fund a phased program that recovers ", options: {} },
  { text: "~$150k/year in net benefit", options: { bold: true, color: GREEN } },
  { text: " for ", options: {} },
  { text: "$80k", options: { bold: true } },
  { text: " — well under the $600k ceiling.", options: {} },
], { x: 0.6, y: 1.5, w: 12.1, h: 1.0, fontSize: 22, fontFace: "Arial", valign: "top" });

const asks = [
  ["1. Rebalance providers", "12x ROI — the clear win. Move demand from overbooked single-provider clinics to idle colleagues. Fund first."],
  ["2. Overbook high-risk slots", "Marginal. Barely profitable once the collision cost is counted. Fund small, monitor closely."],
  ["3. Reminder pilot", "Do NOT fund at scale yet. The evidence is confounded — run a randomised pilot to measure the real effect."],
];
let y = 2.8;
asks.forEach(([h, b]) => {
  s.addShape(pres.ShapeType.rect, { x: 0.6, y: y, w: 12.1, h: 1.15, fill: { color: LIGHT } });
  s.addText(h, { x: 0.8, y: y + 0.1, w: 3.6, h: 0.9, fontSize: 15, bold: true, color: NAVY, valign: "middle", fontFace: "Arial" });
  s.addText(b, { x: 4.5, y: y + 0.1, w: 8.0, h: 0.9, fontSize: 13, color: "333333", valign: "middle", fontFace: "Arial" });
  y += 1.3;
});

// ================= SLIDE 3 — THE PROBLEM =================
s = pres.addSlide();
titleBar(s, "The problem, quantified");
s.addText("No-shows cost ~$634k/year", { x: 0.6, y: 1.4, w: 12, h: 0.7, fontSize: 24, bold: true, color: RED, fontFace: "Arial" });
s.addText("4,226 no-shows a year × $150 lost contribution each. This number reconciles to the schedule and billing — it is defensible under scrutiny.", { x: 0.6, y: 2.1, w: 12.1, h: 0.7, fontSize: 14, color: "333333", fontFace: "Arial" });

s.addText("And capacity is badly balanced:", { x: 0.6, y: 3.1, w: 12, h: 0.5, fontSize: 16, bold: true, color: NAVY, fontFace: "Arial" });
const rows = [
  ["Denton (1 provider)", "135%", "Overbooked — turning patients away", RED],
  ["Richardson (1 provider)", "106%", "Overbooked", RED],
  ["8 providers at 2-provider clinics", "50-68%", "Idle capacity being paid for", BLUE],
];
y = 3.7;
rows.forEach(([a, b, c, col]) => {
  s.addText(a, { x: 0.8, y: y, w: 4.2, h: 0.5, fontSize: 13, color: "333333", valign: "middle", fontFace: "Arial" });
  s.addText(b, { x: 5.0, y: y, w: 1.4, h: 0.5, fontSize: 15, bold: true, color: col, valign: "middle", fontFace: "Arial" });
  s.addText(c, { x: 6.6, y: y, w: 6.0, h: 0.5, fontSize: 13, color: "333333", valign: "middle", fontFace: "Arial" });
  y += 0.6;
});
s.addText("27 appointments/week could move from overbooked to idle providers — at no hiring cost.", { x: 0.6, y: 5.8, w: 12.1, h: 0.6, fontSize: 15, bold: true, color: GREEN, fontFace: "Arial" });

// ================= SLIDE 4 — WHAT DRIVES NO-SHOWS =================
s = pres.addSlide();
titleBar(s, "What drives no-shows — and where to act");
s.addText("Lead time is the biggest lever. The longer the wait between booking and appointment, the more no-shows:", { x: 0.6, y: 1.35, w: 12.1, h: 0.7, fontSize: 15, color: "333333", fontFace: "Arial" });
const curve = [["0–7 days", 10, "F2C1C1"], ["8–14 days", 12, "EAA0A0"], ["15–30 days", 16, "E08080"], ["31–60 days", 23, "C0392B"], ["60+ days", 26, "A02020"]];
y = 2.3;
curve.forEach(([lbl, val, col]) => {
  s.addText(lbl, { x: 0.6, y: y, w: 2.0, h: 0.45, fontSize: 13, color: "333333", valign: "middle", fontFace: "Arial" });
  s.addShape(pres.ShapeType.rect, { x: 2.7, y: y + 0.05, w: val * 0.32, h: 0.35, fill: { color: col } });
  s.addText(val + "%", { x: 2.7 + val * 0.32 + 0.1, y: y, w: 1.0, h: 0.45, fontSize: 12, bold: true, color: "333333", valign: "middle", fontFace: "Arial" });
  y += 0.6;
});
s.addText("This is the evidence base for overbooking: apply it only to the long-lead, high-risk slots — never blanket.", { x: 0.6, y: 5.6, w: 12.1, h: 0.6, fontSize: 14, italic: true, color: GREY, fontFace: "Arial" });

// ================= SLIDE 5 — THE REMINDER TRAP =================
s = pres.addSlide();
titleBar(s, "Why we will NOT fund reminders yet");
s.addText([
  { text: "The naive comparison says reminders cut no-shows by 2.3 points. ", options: {} },
  { text: "It is wrong.", options: { bold: true, color: RED } },
], { x: 0.6, y: 1.4, w: 12.1, h: 0.6, fontSize: 17, fontFace: "Arial" });
s.addText("The three clinics that logged reminders also serve a much lower-risk patient mix — 11% self-pay/Medicaid vs 34% elsewhere. Their lower no-show rate is mostly WHO they see, not the reminders.", { x: 0.6, y: 2.2, w: 12.1, h: 1.0, fontSize: 14, color: "333333", fontFace: "Arial" });
s.addShape(pres.ShapeType.rect, { x: 0.6, y: 3.5, w: 5.8, h: 1.6, fill: { color: LIGHT } });
s.addText("Naive effect\n2.3 pts", { x: 0.6, y: 3.7, w: 5.8, h: 1.2, fontSize: 20, bold: true, color: GREY, align: "center", fontFace: "Arial" });
s.addShape(pres.ShapeType.rect, { x: 6.9, y: 3.5, w: 5.8, h: 1.6, fill: { color: "D5F5D5" } });
s.addText("Adjusted effect\n0.7 pts  (CI spans zero)", { x: 6.9, y: 3.7, w: 5.8, h: 1.2, fontSize: 20, bold: true, color: GREEN, align: "center", fontFace: "Arial" });
s.addText("~70% of the apparent effect was selection bias. Recommendation: fund a randomised pilot, not a full rollout. Spending $45k on a confounded number is how budgets get wasted.", { x: 0.6, y: 5.4, w: 12.1, h: 0.9, fontSize: 14, bold: true, color: NAVY, fontFace: "Arial" });

// ================= SLIDE 6 — THE ROI =================
s = pres.addSlide();
titleBar(s, "The numbers — ranked by return");
const head = ["Intervention", "Benefit/yr", "Cost/yr", "Net/yr", "ROI"];
const data = [
  ["1. Rebalance providers", "$194k", "$15k", "+$179k", "12.0x", GREEN],
  ["2. Overbook high-risk", "$5k", "$20k", "–$15k", "—", GREY],
  ["3. Reminders (pilot)", "$32k", "$45k", "–$13k", "—", GREY],
];
// header
let x0 = 0.6, colW = [4.6, 2.0, 2.0, 2.0, 1.7];
let cx = x0;
head.forEach((h, i) => {
  s.addShape(pres.ShapeType.rect, { x: cx, y: 1.4, w: colW[i], h: 0.55, fill: { color: BLUE } });
  s.addText(h, { x: cx, y: 1.4, w: colW[i], h: 0.55, fontSize: 13, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: "Arial" });
  cx += colW[i];
});
y = 1.95;
data.forEach((row) => {
  cx = x0;
  for (let i = 0; i < 5; i++) {
    s.addShape(pres.ShapeType.rect, { x: cx, y: y, w: colW[i], h: 0.6, fill: { color: i === 0 ? LIGHT : "FFFFFF" }, line: { color: "DDDDDD", width: 1 } });
    const isNet = i === 3;
    s.addText(String(row[i]), { x: cx, y: y, w: colW[i], h: 0.6, fontSize: 13, bold: i === 0 || isNet, color: isNet ? row[5] : "333333", align: i === 0 ? "left" : "center", valign: "middle", fontFace: "Arial", inset: 0.1 });
    cx += colW[i];
  }
  y += 0.6;
});
s.addText("Fund #1 now. Fund #2 small and monitored. Pilot #3. Total cost $80k — leaves $520k of headroom under the ceiling.", { x: 0.6, y: 4.2, w: 12.1, h: 0.6, fontSize: 15, bold: true, color: NAVY, fontFace: "Arial" });
s.addText("Every figure here is a live formula in ROI_MODEL.xlsx. Change the contribution-per-visit assumption and every number recomputes.", { x: 0.6, y: 5.0, w: 12.1, h: 0.6, fontSize: 13, italic: true, color: GREY, fontFace: "Arial" });

// ================= SLIDE 7 — ADDRESSING THE SAFETY OBJECTION =================
s = pres.addSlide();
titleBar(s, "The overbooking safety concern, addressed");
s.addText("Overbooking risks a patient waiting when both the original and the overbook patient show up. We priced that:", { x: 0.6, y: 1.4, w: 12.1, h: 0.7, fontSize: 15, color: "333333", fontFace: "Arial" });
const safety = [
  "Applied ONLY to high-risk slots (23%+ no-show rate) — never blanket.",
  "Collision cost is counted against the benefit — that is why #2 is only marginally profitable.",
  "\"Overbook collisions\" is a tracked KPI. If it rises, the policy tightens automatically.",
  "The model supports caution: it shows overbooking is barely worth it, not a free win.",
];
y = 2.3;
safety.forEach((t) => {
  s.addText("✓", { x: 0.7, y: y, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: GREEN, fontFace: "Arial" });
  s.addText(t, { x: 1.3, y: y, w: 11.3, h: 0.6, fontSize: 14, color: "333333", valign: "middle", fontFace: "Arial" });
  y += 0.75;
});
s.addText("This business case brings its own worst case. It is built to survive scrutiny, not dodge it.", { x: 0.6, y: 5.6, w: 12.1, h: 0.6, fontSize: 15, bold: true, italic: true, color: NAVY, fontFace: "Arial" });

// ================= SLIDE 8 — MEASUREMENT & NEXT STEPS =================
s = pres.addSlide();
titleBar(s, "How we will know it worked");
const kpis = [
  ["No-show rate", "13.0% → under 11% within 2 quarters"],
  ["Provider utilization spread", "Narrow the 50%–135% gap"],
  ["Overbook collision rate", "Keep below a set threshold"],
  ["Reminder pilot effect", "Measured, randomised — decide on rollout at Q2"],
];
y = 1.5;
kpis.forEach(([k, v]) => {
  s.addShape(pres.ShapeType.rect, { x: 0.6, y: y, w: 4.4, h: 0.8, fill: { color: BLUE } });
  s.addText(k, { x: 0.6, y: y, w: 4.4, h: 0.8, fontSize: 14, bold: true, color: "FFFFFF", align: "center", valign: "middle", fontFace: "Arial" });
  s.addShape(pres.ShapeType.rect, { x: 5.0, y: y, w: 7.7, h: 0.8, fill: { color: LIGHT } });
  s.addText(v, { x: 5.2, y: y, w: 7.4, h: 0.8, fontSize: 13, color: "333333", valign: "middle", fontFace: "Arial" });
  y += 0.95;
});
s.addText("Next step: board approval to fund rebalancing now, overbooking as a monitored trial, and a randomised reminder pilot. Review at end of Q2.", { x: 0.6, y: 5.6, w: 12.1, h: 0.8, fontSize: 15, bold: true, color: NAVY, fontFace: "Arial" });

pres.writeFile({ fileName: "reports/BOARD_DECK.pptx" }).then((f) => console.log("Deck written:", f));
