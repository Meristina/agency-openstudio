---
name: feature-flags
description: >-
  Audits a team's feature flag practice against the four-type taxonomy
  (release/experiment/ops/permission), enforces hard expiry policy and lifecycle
  governance, designs progressive delivery sequences (canary → 100%), and
  establishes the structural dependency between trunk-based development and
  feature flags. Use when introducing flags for the first time, cleaning up flag
  debt, or designing a rollout strategy for a multi-sprint feature. Produces a
  flag inventory, lifecycle governance plan, progressive delivery sequence, and
  deployment/release decoupling audit.
---

# Skill — Feature Flag Lifecycle and Progressive Delivery

Feature flags (also called feature toggles) are the mechanism by which deployment
and release are decoupled into two fully independent events: deployment moves code
into production; release grants user access to that code. Treating them as synonyms
produces false DORA metrics — conflating Deployment Frequency with Feature Release
Rate — and generates organisational resistance to continuous integration. The four-type
taxonomy, standardised by LaunchDarkly's engineering practice and the OpenFeature CNCF
specification (2022), classifies every flag into one of four failure modes: release
toggles (temporary, removed after full rollout), experiment toggles (A/B and multivariate
instrumentation), ops toggles (circuit breakers and graceful degradation), and permission
toggles (feature rights and beta access). Forsgren, Humble, and Kim identify trunk-based
development (TBD) as one of the three architectural prerequisites for elite DORA performance
(Accelerate, 2018); feature flags are TBD's structural enabler — without them, every
merged commit must be production-ready within a single sprint, forcing either long-lived
branches (merge debt) or scope truncation. Spotify's blast-radius architecture is the
operational instantiation: a 1% canary release with flag-mediated rollback in minutes
structurally contains the failure scope of any bad deploy [assumption — verify exact
Spotify source].

> **Doctrine:** Cite OpenFeature (CNCF, 2022) for vendor-neutral SDK standards and
> provider abstraction. Cite Forsgren, Humble, Kim — Accelerate (2018) for trunk-based
> development as an architectural prerequisite. Cite LaunchDarkly's engineering blog or
> documentation for the four-type flag taxonomy; never invent taxonomy labels. The
> deployment/release lexical distinction is constitutionally mandatory — any metric or
> process conflating them must be flagged as invalid within this framework. Never cite
> "50% of features never used" — that figure is untraceable. Hard expiry dates are
> non-negotiable for release and experiment flags; ops and permission flags require
> explicit lifecycle ownership rather than a fixed date.

## Procedure

1. **Audit the deployment/release lexicon.** Before touching any flag, confirm the team
   holds a crisp distinction: deployment = code in production; release = user access to
   that code. If these are conflated in the team's DORA reporting, Jira workflow, or
   sprint ceremonies, flag the conflation explicitly. A team that calls every deployment
   a release cannot measure Deployment Frequency accurately, cannot implement trunk-based
   development safely, and cannot use progressive delivery — the entire flag practice is
   built on this lexical foundation. Document the current state and whether the team's
   tooling (CI/CD dashboards, incident trackers) reflects the distinction.

2. **Inventory all existing flags and classify into the four-type taxonomy.** Pull the
   current flag list from the feature management platform (LaunchDarkly, Unleash,
   OpenFeature-compliant provider, or homegrown). For each flag, assign exactly one type
   using the LaunchDarkly taxonomy: (a) Release toggle — temporary flag gating a feature
   from users during development and early rollout; intended to be removed after full
   rollout is complete. (b) Experiment toggle — instruments an A/B or multivariate test;
   controls which variant a user sees; tied to an analytics event schema. (c) Ops toggle
   — circuit breaker or graceful degradation switch; allows disabling a capability under
   load or incident; typically permanent or long-lived with explicit ownership. (d)
   Permission toggle — controls feature rights, beta access, or tier-based entitlements;
   permanent with ownership by a product or entitlements team. Flag any flag that cannot
   be classified as a candidate for immediate deletion.

3. **Enforce hard expiry policy on release and experiment flags.** Every release toggle
   and experiment toggle must carry a hard expiration date set at creation. Forsgren,
   Humble, and Kim identify accumulated flag debt — stale flags with no owner and no
   expiry — as a form of technical debt that degrades deployment confidence and increases
   Change Failure Rate (Accelerate, 2018, ch. 4). Apply the following policy: release
   flags expire at the end of the rollout sprint (maximum one quarter from creation);
   experiment flags expire when statistical significance is reached or at a maximum fixed
   window (typically four to eight weeks). Flags past their expiry date with no removal
   PR open are escalated to the owning squad as flag debt. Ops and permission flags
   require an explicit owner and quarterly lifecycle review in lieu of a fixed expiry.

4. **Establish the trunk-based development dependency.** Feature flags are the structural
   prerequisite for trunk-based development at any scale beyond a single-sprint feature.
   Without flags, merging a multi-sprint feature to trunk exposes incomplete work in
   production; the alternative — a long-lived branch — accrues merge debt and blocks
   Deployment Frequency from reaching elite band. Document the current branching strategy:
   how many active branches exist beyond trunk, their age, and the features they shelter.
   For each long-lived branch, design a flag that allows the feature to be merged to trunk
   immediately behind a release toggle, with the toggle controlling exposure. Cite
   Forsgren, Humble, Kim (Accelerate, 2018) for trunk-based development as an elite DORA
   architectural prerequisite.

5. **Design the progressive delivery sequence.** For every release toggle, specify the
   rollout sequence before the flag is created — not after the feature ships. The standard
   canary pattern is: 1% (internal users / canary segment) → 10% → 50% → 100%, with a
   defined dwell time and success metric at each stage. Define at each stage: (a) the
   rollout percentage and target segment (internal, beta cohort, random sample); (b) the
   success metric and threshold (e.g., error rate < 0.5%, p99 latency < 200ms, task
   success rate > 85%); (c) the rollback trigger — the specific signal that fires an
   automatic or manual flag-off; (d) the dwell time before advancing (minimum 24 hours
   for production signal collection). For dark launches (traffic without UI exposure) and
   blue/green deployments, document which flag type controls each layer. Spotify's
   blast-radius architecture treats the 1% stage as the structural containment mechanism:
   a bad deploy affects at most 1% of users, and rollback is a flag flip, not a
   redeployment [assumption — verify exact Spotify source].

6. **Assess vendor coupling risk and OpenFeature alignment.** The OpenFeature specification
   (CNCF, 2022) defines a vendor-neutral SDK standard with a provider abstraction layer,
   allowing teams to switch flag management backends (LaunchDarkly, Unleash, Flagsmith,
   homegrown) without rewriting application code. Audit the team's current SDK usage:
   are flag evaluations called through a vendor-specific SDK directly (tight coupling) or
   through an OpenFeature-compliant provider interface (portable)? Tight coupling to a
   single vendor's SDK is a migration risk and a lock-in cost. Recommend OpenFeature
   adoption for any team on a vendor-specific SDK with more than 50 active flags, or any
   team considering platform migration. Cite: OpenFeature specification,
   https://openfeature.dev, CNCF, 2022.

7. **Identify and remediate flag debt.** Flag debt is the accumulation of expired,
   unowned, or unclassifiable flags that increase cognitive load, slow flag evaluation
   (on platforms that evaluate all flags per request), and reduce confidence in the flag
   system. Quantify debt: count flags past expiry, flags with no owner, flags in
   production for more than one quarter without a removal PR. Prioritise removal by age
   and type: release flags older than one quarter with 100% rollout are the highest
   priority for deletion (the toggle is permanent-on; remove the branch in code). Provide
   a debt remediation backlog: flag name, type, age, owner, removal action, and deadline.

8. **Produce the flag governance output and next steps.** Deliver the full flag inventory
   with type classification, expiry status, and progressive delivery sequence for active
   release flags. Identify the single highest-priority flag debt item and the single most
   impactful missing governance control. Connect the flag practice to its DORA impact:
   flags that enable trunk-based development improve Deployment Frequency; flags that
   enable rollback reduce Change Failure Rate and Mean Time to Recover. Cite every
   external benchmark; nothing in the output may be invented.

## Output format

```
FEATURE FLAG LIFECYCLE — <product / team / context>
Context detected: <B2B/B2C · sector · stage · flag platform>

DEPLOYMENT / RELEASE AUDIT
  Lexical distinction held by team: <Yes | No | Partial>
  DORA metric conflation detected:  <Yes — Deployment Frequency mislabelled as Release Rate | No>
  Tooling reflects distinction:     <CI/CD dashboard | incident tracker | sprint workflow — Yes | No>

FLAG INVENTORY (by type)
  Type            | Count | Avg age | Expired (past SLA) | Owner coverage
  ────────────────┼───────┼─────────┼────────────────────┼────────────────
  Release         |   n   |  n days |        n           |    n%
  Experiment      |   n   |  n days |        n           |    n%
  Ops             |   n   |  n days |   N/A (no fixed)   |    n%
  Permission      |   n   |  n days |   N/A (no fixed)   |    n%
  Unclassified    |   n   |    —    |        —           |    —
  Total flag debt:  <n flags past expiry or unowned — removal backlog below>

LIFECYCLE GOVERNANCE
  Hard expiry policy (release flags):    <Enforced | Absent | Partial — SLA: 1 quarter>
  Hard expiry policy (experiment flags): <Enforced | Absent | Partial — SLA: 4–8 weeks>
  Ops/permission flag ownership:         <Quarterly review in place | Absent>
  Flag debt backlog:
    Flag name | Type | Age | Owner | Action | Deadline

TBD DEPENDENCY AUDIT  [Forsgren, Humble, Kim — Accelerate, 2018]
  Active long-lived branches:  <n — names and age>
  Features sheltered in branches: <list>
  Flag adoption blocks TBD gap: <Yes — n features need a release toggle to merge to trunk | No>
  TBD architectural prerequisite: <Met | Partial | Absent>

PROGRESSIVE DELIVERY SEQUENCE (active release flags)
  Flag: <flag name>
  Feature: <feature description>
  Stage 1 — Canary 1%:   segment=<internal/canary>, metric=<threshold>, dwell=<hours>, rollback trigger=<signal>
  Stage 2 — 10%:         segment=<random sample>, metric=<threshold>, dwell=<hours>, rollback trigger=<signal>
  Stage 3 — 50%:         metric=<threshold>, dwell=<hours>
  Stage 4 — 100%:        removal PR deadline=<date>

OPENFEATURE / VENDOR COUPLING AUDIT  [OpenFeature, CNCF, 2022]
  Current SDK:            <vendor name — direct or OpenFeature provider>
  Coupling risk:          <Low (OpenFeature provider) | High (vendor-direct SDK)>
  Migration recommendation: <OpenFeature adoption | Maintain current>

SO-WHAT / NEXT STEPS
  - Priority 1 (flag debt): <highest-urgency removal — flag name, owner, deadline>
  - Priority 2 (TBD gap):   <long-lived branch to collapse behind a release toggle>
  - Priority 3 (governance): <missing policy to implement first>
  - DORA impact: <which DORA metrics improve when this flag practice is implemented>

SOURCES (every external fact cited; nothing invented)
  - OpenFeature Specification. CNCF, 2022. https://openfeature.dev
  - Forsgren, N., Humble, J., & Kim, G. Accelerate: The Science of Lean Software and
    DevOps. IT Revolution Press, 2018. [Trunk-based development as elite prerequisite]
  - LaunchDarkly. "Feature Flag Types." LaunchDarkly Engineering Blog.
    https://launchdarkly.com/blog/feature-flag-types/ [assumption — verify exact URL]
  - [Additional sources as needed — author, title, year, URL or [assumption — verify]]
```
