---
name: launch-readiness
description: >-
  Evaluates whether a product or feature is safe to release by auditing six
  Amazon-sourced readiness components (operational, CX, security, legal/compliance,
  metrics instrumentation, and post-launch monitoring) and gates the release
  decision through Robert G. Cooper's four-outcome Stage-Gate taxonomy: Go, Kill,
  Hold, or Recycle. Use at the end of the build cycle — before any release to
  production — to confirm that Day 1 measurement, on-call runbooks, legal sign-off,
  and incident response protocols are in place. Produces a structured gate decision
  with component-level status, kill metrics thresholds, and a mandatory COE template
  if a post-launch incident occurs within 30 days.
---

# Skill — Launch Readiness Review (Cooper Stage-Gate · Amazon 6-Component)

Launch readiness is a structured pre-release gate that separates the question "is
it safe to release?" from both "is it worth building?" (assumption testing) and
"can users operate it?" (usability testing). The six-component framework is sourced
from Amazon's internal Launch Readiness Review practice, documented by Colin Bryar
and Bill Carr in Working Backwards (2021): operational readiness, CX readiness,
security review, legal and compliance sign-off, metrics instrumentation, and
definition of the post-launch monitoring window. These six components are evaluated
in parallel, not in sequence — no single component outranks another in the gate
checklist. The gate decision uses Robert G. Cooper's four-outcome Stage-Gate
taxonomy (Stage-Gate International), supported by 60+ industrial studies: Go
(release as planned), Kill (cancel — with as much process discipline as Go),
Hold (pause pending a specific resolution), and Recycle (rework one or more
components and re-gate). Three kill metrics are adapted from NielsenIQ/BASES CPG
methodology into software analogs — activation velocity, trial-to-paid conversion,
and D30 retention — and must be instrumented before launch, not after.

> **Doctrine:** Cite Bryar and Carr (Working Backwards, 2021) for the six Amazon
> components. Cite Cooper (Stage-Gate International) for the four-outcome gate
> taxonomy; do not reduce it to binary go/no-go — Kill and Recycle require equal
> process discipline. Cite Amazon COE (Correction of Errors) for the post-launch
> incident artifact. Cite NielsenIQ/BASES for the CPG kill-metric analogs.
> Never cite "50% of features never used," NPS as a sole growth driver, or the
> 40% PMF Ellis threshold as a universal law. Never invent a quote, statistic,
> or benchmark — research every external fact and cite it. Unknown → "unknown"
> or "[assumption — verify]".

## Procedure

1. **Frame the gate context.** Identify the product or feature, the release scope
   (GA, limited beta, flag-gated rollout), and the intended customer segment.
   Confirm which officer owns this gate decision (O5 — Delivery) and who holds
   sign-off authority for each component. Record the target release date and any
   hard external deadlines (regulatory, contractual, marketing event) that may
   create pressure to compress the gate process.

2. **Audit all six Amazon components in parallel.** For each of the six components,
   assess status as Green (ready), Amber (at-risk — named owner, named resolution
   date), or Red (blocking — release must not proceed): (a) Operational readiness —
   runbooks written, on-call rotation confirmed, rollback procedure tested, capacity
   plan validated; (b) CX readiness — support documentation published, customer-facing
   error messages reviewed, help-center articles live or scheduled; (c) Security
   review — threat model completed, pen-test or security scan results reviewed,
   data classification confirmed, GDPR/CCPA/HIPAA obligations checked where
   applicable; (d) Legal and compliance — terms of service updated, privacy policy
   current, export controls checked, IP clearance confirmed; (e) Metrics
   instrumentation — every Day 1 metric is event-tracked and flowing to the analytics
   system before launch; (f) Post-launch monitoring window — alerting thresholds set,
   monitoring duration defined (minimum 7 days recommended; 30 days for major
   releases), escalation path named. Per Amazon doctrine (Bryar & Carr, Working
   Backwards, 2021), a launch without Day 1 metrics instrumentation is incomplete —
   treat it as a Red blocking item with equal weight to security review and legal
   sign-off.

3. **Define and instrument kill metrics before launch.** Adapted from NielsenIQ/BASES
   CPG methodology, three software analogs must be defined and threshold-set prior to
   release: (a) Activation velocity — the rate at which new users complete the
   activation event within the first session (CPG analog: retail velocity / distribution
   rate); (b) Trial-to-paid conversion — the percentage of trial or freemium users who
   convert to a paying plan within a defined window (CPG analog: trial rate); (c) D30
   retention — the proportion of activated users returning and performing the core
   action at Day 30 (CPG analog: repeat purchase rate). For each metric, document the
   pre-launch threshold below which the product will trigger a Hold or Recycle decision.
   If any kill metric lacks a defined threshold, mark metrics instrumentation Red.

4. **Apply Cooper's four-outcome gate decision.** Using the six-component audit and
   kill metric thresholds, assign one of four Stage-Gate outcomes (Cooper, Stage-Gate
   International): Go — all six components Green, kill metric thresholds defined,
   release proceeds as planned; Kill — the product or feature is cancelled; record the
   Kill decision with the same rigor as a Go — document rationale, sunset timeline,
   and customer communication plan; Hold — release is paused pending resolution of a
   specific named blocker (e.g., legal sign-off pending, security scan in progress);
   set a resolution date and a re-gate date; Recycle — one or more components fail
   and require substantive rework before re-gating; specify which components must be
   reworked and what "done" means. Do not compress Kill into a silent cancellation or
   collapse Hold and Recycle into a single "not ready" label.

5. **Draft the COE template for post-launch incident response.** For any launch incident
   occurring within 30 days of release, Amazon mandates a Correction of Errors (COE)
   artifact — an 8-component post-mortem that closes the Delivery-to-Measurement loop
   (Bryar & Carr, Working Backwards, 2021). Pre-draft the COE template at gate time:
   incident description, customer impact, root cause (5-Whys), detection method,
   resolution steps, time-to-detect, time-to-resolve, and corrective actions with
   owners and dates. The existence of a pre-drafted COE template is itself a
   readiness signal — teams that cannot describe their incident response process
   before launch have not completed operational readiness.

6. **Define the monitoring window and escalation path.** Specify the start and end date
   of the post-launch monitoring window, the metrics to be watched daily, the alert
   thresholds that will trigger an escalation, and the named individuals in the
   escalation chain. Minimum monitoring window: 7 days for flag-gated features,
   30 days for GA releases. If kill metrics fall below threshold during the monitoring
   window, the gate re-opens automatically — Hold or Recycle decisions at this stage
   feed back into the build cycle.

7. **Produce the output block and cite all sources.** Format using the template below.
   Every component status must be traceable to a named owner. Every kill metric must
   have a defined threshold. Every gate decision must reference the Cooper four-outcome
   taxonomy. End with a SOURCES section — every external fact cited; nothing invented.

## Output format

```
LAUNCH READINESS REVIEW — <product / feature / release>
Context detected: <B2B/B2C · sector · stage>
Gate owner: O5 — Delivery
Target release date: <date or "TBD">

SIX-COMPONENT AUDIT (Bryar & Carr, Working Backwards, 2021)
  Operational readiness:    <Green | Amber | Red> — <key detail or blocker>
  CX readiness:             <Green | Amber | Red> — <key detail or blocker>
  Security review:          <Green | Amber | Red> — <key detail or blocker>
  Legal / compliance:       <Green | Amber | Red> — <key detail or blocker>
  Metrics instrumentation:  <Green | Amber | Red> — <key detail or blocker>
  Post-launch monitoring:   <Green | Amber | Red> — <key detail or blocker>
  Blocking items:           <list all Red items with named owner and resolution date>

KILL METRICS (NielsenIQ/BASES CPG analogs — software-adapted)
  Activation velocity:       threshold <X%> within <N> sessions — instrumented: <Yes | No>
  Trial-to-paid conversion:  threshold <X%> within <N> days — instrumented: <Yes | No>
  D30 retention:             threshold <X%> at Day 30 — instrumented: <Yes | No>
  Kill trigger:              <If any metric falls below threshold during monitoring window → Hold or Recycle>

STAGE-GATE DECISION (Cooper, Stage-Gate International)
  Decision:   <Go | Kill | Hold | Recycle>
  Rationale:  <1-2 sentences — which components drove the decision>
  If Kill:    <Sunset timeline, customer communication plan, rationale on record>
  If Hold:    <Named blocker, resolution owner, re-gate date>
  If Recycle: <Components to rework, definition of done, re-gate criteria>

POST-LAUNCH COE TEMPLATE (Amazon — Bryar & Carr, 2021 — mandatory if incident within 30 days)
  Incident description:  <pre-drafted placeholder>
  Customer impact:       <pre-drafted placeholder>
  Root cause (5-Whys):   <pre-drafted placeholder>
  Detection method:      <pre-drafted placeholder>
  Resolution steps:      <pre-drafted placeholder>
  Time-to-detect:        <SLA target>
  Time-to-resolve:       <SLA target>
  Corrective actions:    <owner + date for each>

MONITORING WINDOW
  Start: <launch date>   End: <date — min 7 days flag-gated / 30 days GA>
  Daily metrics watched: <list>
  Alert thresholds:      <values that trigger escalation>
  Escalation chain:      <named individuals>

SO-WHAT / NEXT STEPS
  - <Gate decision and immediate action required>
  - <Any Amber items: owner, resolution date, and re-check schedule>
  - <Kill metric thresholds to validate with data lead before release>
  - <Handoff if strategy or roadmap realignment needed: O5 Delivery officer>

SOURCES (every external fact cited; nothing invented)
  - Bryar, C., & Carr, B. Working Backwards: Insights, Stories, and Secrets
    from Inside Amazon. St. Martin's Press, 2021.
  - Cooper, R. G. Stage-Gate International. Stage-Gate model and four-decision
    taxonomy (Go / Kill / Hold / Recycle). https://www.stage-gate.com/
    [assumption — verify URL currency]
  - NielsenIQ / BASES. CPG launch metrics methodology (retail velocity, trial rate,
    repeat purchase). https://nielseniq.com/global/en/solutions/bases/
    [assumption — verify URL currency]
  - [Additional sources as needed — author, title, year, URL or [assumption — verify]]
```
