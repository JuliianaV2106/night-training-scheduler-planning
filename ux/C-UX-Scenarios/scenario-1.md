# 01: Kavita's Afternoon Submission — Annex Scenario 1: Daytime Submission & Queuing

**Project:** Proyecto final — Module 9, Night Training Scheduler
**Created:** 2026-09-28
**Method:** WDS Phase 3 (UX scenario outline), trigger document = `planning/prd.md`
**Journey:** UJ-1
**State path:** — → `QUEUED_PENDING_WINDOW`
**Design references:** `ux/DESIGN.md` (theme, tokens, component specs) · `ux/EXPERIENCE.md` (IA, state patterns, voice)

> **Trigger-document substitution.** WDS Phase 3 normally derives scenarios from a Trigger Map produced in Phase 2. No Trigger Map exists for this project — Phases 1 and 2 were never run. The substitute is `planning/prd.md`, which supplies the same three things a Trigger Map would: named personas (§2.1), stated jobs-to-be-done, and a success-metric set (§13). Sections that would have cited a Trigger Map objective instead cite the PRD metric. This is recorded rather than papered over; see Open Question S1-Q1.

---

## Transaction

**What this scenario covers:** Kavita submits a LoRA Job Spec during the afternoon, and the system either parks it in the Pending Set with a name, a position and a projected first-start time, or refuses it naming the specific rule that refused it. It never admits a Job Spec it cannot later place, and it never refuses one without saying which field and which rule failed.

---

## Business Goal

**Goal:** A student who cannot act on a vague refusal stops routing around the scheduler. Every refusal arrives as a per-field `rule_id` plus a human-readable message, and every admission arrives with a checkable justification.

**PRD objective reference:** `SM-5` (Explainability — 100% of decisions presented to a user carry a citation and a one-sentence summary a reader can check against the delegated authority) · `SM-1` (Mandated-path fidelity — Annex Scenario 1 executes end-to-end with asserted state transitions, citations and Node allocation counts)

---

## User & Situation

**Persona:** Kavita, senior research student. *(§2.1; role disclosure F-33 — Ines Okonkwo is the team-added persona, Kavita is named in the Annex.)*

**Situation:** She has held a laptop-open SSH session all afternoon waiting for a free GPU that never appeared. Her thesis fine-tune will not fit in one night and she knows it, which is precisely the case the module exists to serve.

**Trigger:** 14:30. She has the container digest in her clipboard and a `checkpoint_interval_minutes` she has already reasoned about.

**Hope:** Submit it, be told plainly it will run across at least four nights, and then close the laptop and stop thinking about it until Monday.

**Worry:** Being parked somewhere invisible with no idea when her job runs — and, if refused, being told "policy violation" and having no way to tell which rule stopped her.

> **Driving forces addressed**
> - ✅ *Want* (§2.1): "I want to submit my LoRA run in the afternoon and stop thinking about it, and I want to know on Monday morning exactly how far it got and when it will finish."
> - ✅ *Want* (§2.1): "When I am denied or deferred, I want the actual rule that did it, not a generic 'policy violation'."
> - ❌ *Fear* (§2.1): The current alternative is a spreadsheet and a group chat — a held-open SSH session that is ungoverned, unobserved, and silently lost overnight.

---

## Device & Starting Point

**Device:** Desktop. The submission surface is light-themed (`{colors.surface-base-light}`) because Kavita is working at 14:30, not on a night shift — see `DESIGN.md` "Surfaces and ink (light, submission)".

**Entry:** She navigates to the submission surface and presses `n` (new job). FR-1 qualifies the *submission* surface as "desktop"; the status board's viewport is a separate, unresolved question (Open Question S1-Q2).

---

## Best Outcome

**User Success:** HTTP 201, state `QUEUED_PENDING_WINDOW`, and on screen — before she closes the laptop — a state with a name, a position in the Pending Set, a projected first-start time, and a Retention Deadline. `requires_multiple_nights: true` and `estimated_completion_nights: 4` stated plainly against the 38.75 h ceiling they are measured against. (FR-1 testable condition; FR-4(b), F-15.)

**Business Success:** The Pending Set gains exactly one `QUEUED_PENDING_WINDOW` entry with a durable `ADMIT` Decision Record carrying `self:JOBSPEC-VALIDATION-v1` plus every delegated verdict consulted — so the admission itself is auditable before a single GPU is allocated. (FR-24(e): emission is durable before the transition is committed.)

---

## Shortest Path

1. **Submission** — Kavita opens the light submission surface at 14:30 and enters the LoRA Job Spec: pinned container image digest, 1 GPU, 24 GB class node selector, a `checkpoint_interval_minutes`, and `declared_intent: THESIS`.
2. **Submission** — Spec validation returns instantly. The estimate comes back as 31 hours, which exceeds the 7 h 45 min Usable Night Duration but fits the 5-night Max Night Span of 38.75 h, so the response sets `requires_multiple_nights: true` and returns `estimated_completion_nights: 4`. The surface states that this job will run across at least four nights and names the span ceiling it is measured against.
3. **Submission** — Granted Priority is rendered read-only, read from the Policy Engine (Module 2). Her self-declared `THESIS` is stored as a `PENDING_REVIEW` request, visible to the administrator and visibly **not** applied.
4. **Job detail** — She lands on her own job, not on the queue: the `QUEUED_PENDING_WINDOW` badge (colour + `◷` glyph + the label "Queued"), her Pending Set position, her projected first-start, her Retention Deadline, and the one `ADMIT` Decision Record with its full citation row. She closes the laptop. ✓

> **Why step 4 is Job detail and not the Pending Set.** FR-4's response carries the position and the estimate, and UJ-1's climax is those two numbers attached to *her* job. Routing her to a 500-row list (`QUEUE_DEPTH_CAP = 500`, FR-7(a)) would bury the one thing she came for. The `QUEUE_DEPTH_CAP` counter beside that list is fleet-wide and is labelled as such — a student who believes her own three jobs are 312 deep has been lied to. (Per `EXPERIENCE.md` Information Architecture.)

---

## Requirement Traceability

### Primary — `planning/prd.md` §14 row 1

| FR | What it constrains in this scenario |
|---|---|
| **FR-1** | Submit a Training Job. Outputs `job_id`, admitted state, Pending Set position, projected first-start estimate, Retention Deadline, and a Decision Record with `ADMIT` or `DENY`. HTTP 201 on success. |
| **FR-2** | Validate the Job Spec. Per-field `pass` or `rule_id` + human-readable message, rules (a)–(j). |
| **FR-4** | Estimate duration, enforce Max Night Span, required VRAM. Produces `estimated_duration_s`, `estimated_completion_nights`, `required_vram_gb`, `admitted_nights`, `max_night_span`, `confidence`. |

### Supporting

| FR / NFR | Bearing |
|---|---|
| **FR-3** | Scope boundary. Short-circuits *before* FR-2 — see NP-1.1. |
| **FR-5** | Idempotent submission. Same key + identical digest → HTTP 200, same `job_id`, no state change. See NP-1.4. |
| **FR-6** | Consume delegated verdicts from Modules 1, 2, 5, 8. All four present; any missing verdict is a blocking error, never a default ALLOW. See NP-1.5. |
| **FR-7** | Bound the Pending Set. `QUEUE_DEPTH_CAP = 500`; Retention Deadline assigned at admission. See NP-1.6 (cap) and **NP-1.8** (the Retention Deadline passing, T-15, and the 7-day expiry grace). |
| **FR-24** | Emit a cited Decision Record for every transition. Injectivity, fail-closed emitter, §6.1 `summary` rules. |
| **NFR-4** | Citation completeness — 100% absolute, tolerance zero. |
| **NFR-11** | Secret hygiene — no token, key, or credential in any response body; display names resolved by the UI, never stored. |
| **NFR-13** | Checkpoint store bound. See NP-1.7. |
| **NFR-15** | Accessibility. WCAG 2.1 AA; every one of the nine states carries a distinct glyph *and* a text label. |

### State machine

| Transition | From → To | Decision | Reason | Citations (§6.4) |
|---|---|---|---|---|
| **T-1** | — → `QUEUED_PENDING_WINDOW` | `ADMIT` | — | `self:JOBSPEC-VALIDATION-v1`; every delegated submission verdict consulted — `entitlement:M1/…`, `policy:M2/…`, `catalog:M5/…`, `quota:M8/…` |
| **T-2** | — → `REJECTED` | `DENY` | `VALIDATION_FAILED` | `self:JOBSPEC-VALIDATION-v1` alone only for a module-owned failure; the delegated verdict otherwise (F-1 split rule) |
| **T-15** | `QUEUED_PENDING_WINDOW` → `EXPIRED` | `EXPIRE` | `RETENTION_DEADLINE` | `self:RETENTION-DEADLINE-v1` — **module-owned rule, permitted alone per the §6.2 split rule** (see NP-1.8) |

**States reached:** `QUEUED_PENDING_WINDOW` (terminal: no · node held: no). `REJECTED` and `EXPIRED` in the non-happy paths.
**Decisions reached:** `ADMIT`, `DENY`, `EXPIRE`, `DEFER` (NFR-13 escalation only).
**Screens:** Submission → Job detail. Status strip present throughout.

---

## Scenario Steps

### Step 1 — Submission: enter the Job Spec

- **Screen:** Submission. Light theme. Field-level validation; the form is never disabled wholesale, because a student mid-entry at 14:30 must not lose their work to a background poll.
- **Fields, per the §3 Job Spec definition:** container image digest, `gpus_per_node`, VRAM class, `node_selector`, storage request, `checkpoint_interval_minutes`, `restart_policy`, `declared_intent`, idempotency key. There is exactly one Job Spec per Training Job.
- **Kavita's entry:** digest pinned (not `:latest`), `gpus_per_node: 1`, 24 GB class, `node_selector` naming a 24 GB Node, `checkpoint_interval_minutes: 30`, `declared_intent: THESIS`, `worker_count: 1`.
- **Rendered:** the A-3 simulation disclaimer, permanently and un-dismissably. v1 models no real GPU, no container execution, no telemetry and no model weights; every Training Job is a simulated process. An operator must never mistake a prototype run for a production fleet.
- **Copy discipline (§6.1):** the console's own surrounding copy obeys the same ban the daemon's summaries do — no "Policy violation", no "Invalid request", no "Forbidden". A UI that says "Policy violation" next to a carefully-cited summary destroys the summary's credibility.

### Step 2 — Submission: validation returns, the estimate is stated

- **Instant.** Spec validation returns instantly; the estimate comes back as 31 hours.
- **FR-2 checks that pass, each surfaced individually:** (a) digest pinned not tag; (b) `gpus_per_node` is 1; (c) 24 GB ≤ the largest single-Node VRAM class of 48 GB; (d) `requests` equals `limits` for GPU and memory; (e) `node_selector` names a Node matching the declared 24 GB class; (f) `restart_policy` does not request a restart that would silently re-enter a Night Window without re-admission; (g) `checkpoint_interval_minutes` is a positive integer ≤ 30; (h) the Module 5 model record exists and is not deprecated; (i) an estimated duration is declared; (j) 31 h does not exceed 38.75 h.
- **FR-4 outputs, all six named:** `estimated_duration_s: 111600` · `estimated_completion_nights: 4` · `required_vram_gb: 24` · `admitted_nights: 0` · `max_night_span: 5` · `confidence` (a stated confidence, never a bare number).
- **The critical rendering:** 31 h exceeds the 7 h 45 min Usable Night Duration, so `requires_multiple_nights: true` is set — **unconditionally**, per FR-4(b), which admits no exception. This is *not* a rejection. A 31 h estimate is the case the module exists to serve, and a surface that made it feel like a problem would invert the module's thesis.
- **FR-7(b):** a Retention Deadline is assigned at admission and travels with the response.

### Step 3 — Submission: priority is read, not declared

- **FR-17(c):** the self-declared `THESIS` is stored as a *request* — visible to the administrator, and **never applied**. This is what the `prd-addendum.md` §A.3 "Reject self-declared priority" decision buys: priority is the only resource in this module that can destroy someone else's work, so making it self-service would make Annex Scenario 4 a no-op.
- **Rendered:** Granted Priority read-only, sourced from Module 2. The student's declaration renders as `PENDING_REVIEW` and is visibly *not* the applied value.
- **What the PRD does not pin:** the Granted Priority this particular job receives. FR-17's testable condition states that a `declared_intent: THESIS` submission receives `granted_priority: EXPLORATION` until an administrator grants otherwise, while UJ-1 states only that her priority is read from the Policy Engine. The surface renders whatever Module 2 returned and never derives it. (Open Question S1-Q3.)

### Step 4 — Job detail: the three numbers she came for ✓

- **Screen:** Job detail for her `job_id`. Landing route by design, not the Pending Set.
- **The `QUEUED_PENDING_WINDOW` badge:** `{colors.state-queued-pending-window}`, glyph `◷`, label "Queued". Colour + glyph + text label, always all three — NFR-15 forbids an icon-only state indicator outright. Non-terminal, so no 1px `{colors.border-structure}` ring.
- **The payload:**
  - state `QUEUED_PENDING_WINDOW`
  - position in the Pending Set, with `aria-posinset` / `aria-setsize` on the virtualised list — UJ-1's climax is a position, and a screen-reader user arrowing the list must hear it
  - projected first-start instant
  - Retention Deadline
  - `admitted_nights` against `max_night_span`
  - the Effective Priority decomposition (granted + aged) — readable now, before she closes the laptop
  - how many verified Checkpoints she already holds, if any (`QUEUED_PENDING_WINDOW` "may hold one or more verified Checkpoints")
- **The one `ADMIT` Decision Record:** group glyph `✓`, group word "admit", `decision` as the eyebrow, the `summary` at `{typography.body}`, then the full `citations` row as `citation-chip` elements — `self:JOBSPEC-VALIDATION-v1` in `{colors.citation-ink}` beside the delegated verdicts. **A quieter `ADMIT` is a de-emphasis, never a citation-stripped summary** (SM-5, FR-25(b)).
- **The `self:` / non-`self:` split is visible.** `self:` citations render in `{colors.citation-ink}`, delegated authorities in the same channel weighted heavier; neither uses `{colors.accent}`, which is reserved for interactive affordance. A citation is evidence, not a control. §6.2's F-1 split is satisfied by a `DENY`-free `ADMIT`, and the reader can see which part of the admission rested on this module's own Job Spec rules and which rested on Module 1, 2, 5 and 8.
- **`decision_id` and `sim_timestamp`** render as a mono metadata line under the summary, `decision_id` first — it is the handle the reader quotes.
- **Exit:** she closes the laptop. The emotional payload of the journey is that she can now stop thinking about it.

---

## Non-Happy Paths

Seven. The PRD makes this surface the module's most refusal-dense: four distinct refusal taxonomies plus per-field rejections, none of which may be collapsed into a generic message.

### NP-1.1 — Multi-worker Job Spec → refused at the scope boundary

- **Trigger:** `worker_count: 2`.
- **Outcome:** `REJECTED`. Decision `DENY`. Reason `OUT_OF_SCOPE_DISTRIBUTED`. Citation `self:SCOPE-BOUNDARY-v1`, naming **Module 10** as the owning module. Pending Set length unchanged; **no GPU allocation attempted**.
- **Critical behaviour:** the scope check **short-circuits before FR-2 runs** (F-28). FR-2 is never evaluated, so no field-level rejections appear alongside it. This is why FR-2's own testable condition must be run with `worker_count = 1` — otherwise the short-circuit swallows the three rejections it is testing for.
- **Rendering:** one reason, one rule, one referral. A 4-worker PyTorchJob-style spec is refused whole, because the request is not a Training Job this module can ever place.

### NP-1.2 — Three simultaneous field rejections, reported individually

- **Trigger:** the FR-2 testable Job Spec — pinned to `:latest`, `worker_count: 1`, requesting **64 GB** VRAM, `checkpoint_interval_minutes: 240`.
- **Outcome:** `REJECTED`. Decision `DENY`. Reason `VALIDATION_FAILED`. **Exactly three** rejections, each naming its field and its rule identifier:
  | Rule | Field | Message carries |
  |---|---|---|
  | (a) | container image | must be pinned by digest, not tag |
  | (c) | requested VRAM | 64 GB requested against the largest single-Node VRAM class of 48 GB — **both classes named** |
  | (g) | `checkpoint_interval_minutes` | must be a positive integer ≤ 30 |
- **Critical behaviour:** reported **individually**, never as a single generic "invalid spec". Rule (c) exists because a 70B-class job on a 24 GB workstation is infeasible for a reason the reader needs both halves of; and a 240-minute interval would let progress since the last Checkpoint exceed what the Checkpoint Budget can plausibly flush at the Ramp, which is the whole reason rule (g) exists.
- **Rendering:** per-field, at the field. Not a banner and not a toast. A form that collapses three actionable problems into one sentence has made the reader do the diagnosis the system already did.

### NP-1.3 — Estimated duration over the Max Night Span

- **Trigger:** the same Job Spec with `estimated_duration_s` declared as 52 h instead of 31 h.
- **Outcome:** `REJECTED`. Decision `DENY`. Reason `VALIDATION_FAILED` (FR-2(j)). Citation `self:MAX-NIGHT-SPAN-v1`. Pending Set length unchanged.
- **The message must name both numbers** — 52 h and the 38.75 h ceiling (5 × 7 h 45 min) — **and propose at least one concrete scope reduction**: lower `epochs`, raise `gradient_accumulation_steps` to trade compute for memory, reduce the dataset size, or target a smaller base model.
- **Why `self:` alone is legitimate here (F-1):** Max Night Span is a module-owned rule with no delegated authority to name. A `DENY` may cite `self:` alone *only* for a module-owned rule — scope boundary, Max Night Span, queue cap, or Job Spec validation.
- **Contrast with step 2 of the sunshine path:** 52 h is refused; 31 h is admitted with `estimated_completion_nights: 4`. The 38.75 h line is the only difference, and the surface must make that legible rather than presenting both as "too long".

### NP-1.4 — Repeated idempotency key with a different payload

- **Trigger:** same idempotency key, different payload digest.
- **Outcome:** **HTTP 409**, client error, **no job created**. The Pending Set length does not change.
- **Contrast:** same key + identical payload digest → HTTP 200, the **original** `job_id`, no state change. The surface must say *which* of the two happened, because "409" alone does not tell Kavita whether her first submission succeeded.
- **Rendering:** states that no job was created. Silent idempotency is a data-loss bug wearing a feature.

### NP-1.5 — A delegated verdict is missing

- **Trigger:** the Module 2 quota source returns 503 (FR-6 testable condition).
- **Outcome:** **refusal.** FR-6(b): a missing verdict is a blocking error, **never a default ALLOW**. 100 consecutive submissions under a 503 produce 100 refusals and 0 admissions.
- **Rendering:** the `DENY` names the missing authority. This is a `DENY` on a **delegated verdict**, so under F-1 it **may not cite `self:` alone** — it needs at least one non-`self:` citation naming the verdict that is absent or non-ALLOW.
- **Why this matters to the design:** it is the one refusal where the correct product behaviour is to look broken. The surface's obligation is to be *specific* about what it is waiting for, not to soften the failure.

### NP-1.6 — The Pending Set is at the cap

- **Trigger:** Pending Set length at or above `QUEUE_DEPTH_CAP = 500`.
- **Outcome:** `REJECTED` at submission. Decision `DENY`. Reason `QUEUE_FULL`. Citation `self:QUEUE-DEPTH-CAP-v1` — module-owned, so `self:` alone is legitimate (F-1).
- **Must carry:** a **next-available-slot estimate** (FR-7(a) outputs "admission or refusal with an estimate").
- **Contrast with the board rendering:** on the board this same condition is a **capacity banner, not an error** — the fleet is not in trouble, the queue is simply full. The same underlying fact is a refusal to a submitter and a capacity notice to an operator.

### NP-1.7 — Checkpoint store pressure

- **Trigger:** Checkpoint store usage exceeds `CHECKPOINT_STORE_BUDGET` `[ASSUMPTION: A-10]`, which the PRD sizes from Σ over non-terminal jobs (2 × checkpoint_size) rather than fixing a number.
- **Outcome, two records, not one (NFR-13):**
  1. `DENY` / `STORE_FULL` / `self:CHECKPOINT-STORE-BUDGET-v1` — the submission is refused, citing the reason.
  2. `DEFER` / `DISK_PRESSURE_ESCALATION` / `self:CHECKPOINT-STORE-BUDGET-v1` — escalation to a human, **within 1 simulated minute**.
- **Invariant that must be visible in the behaviour:** **zero protected Checkpoints deleted**, where protected means one of the 2 most recent verified Checkpoints of a non-terminal job (FR-22(b)) or any Quarantined Checkpoint. A single protected deletion fails the build.
- **Why this is a separate path and not a variant of NP-1.6:** it has its own Decision Record *and* its own escalation record, so a designer who folds it into the queue-full banner has removed a branch the PRD requires. (The PRD names no surface for store pressure — Open Question S1-Q4.)

### NP-1.8 — The Retention Deadline passes without admission (T-15)

The one path in this scenario that outlives the session it is written in. Everything else in scenario 1 is resolved at 14:30; this one resolves days later, or never, and it is the only path in the module where a job the student submitted simply stops being something the module will run.

- **Trigger:** the job has been in `QUEUED_PENDING_WINDOW` and its **Retention Deadline passes without admission.** No Eligible Node was ever free for it, or its rank in the Admission Order was never good enough. FR-7(b) assigns every admitted job a Retention Deadline at admission, and the PRD fixes no numeric value for it — the deadline's length is a deployment parameter, not a rule, and the surface must render the value it was given rather than a constant of its own.
- **Outcome:** **T-15** fires. `QUEUED_PENDING_WINDOW` → **`EXPIRED`**. Decision `EXPIRE`, reason `RETENTION_DEADLINE`, citation **`self:RETENTION-DEADLINE-v1`**.
- **The citation is legitimately `self:`-alone**, and this is one of only two places in the module where that is true for a transition that ends a job's life: retention is a module-owned bookkeeping rule with no delegated authority to name, which is exactly the reasoning the F-1 split rule states and which the PRD's T-15 row records. The contrast with FR-16's refusals is the point — a *module-owned* rule may stand alone, a *stop* never may. A designer who reaches for `self:`-alone out of habit here is right by accident, and one who reaches for it on a `PREEMPT` is wrong on purpose.
- **`EXPIRED` is terminal** (terminal: yes · non-terminal: no), so the badge takes the 1px `{colors.border-structure}` ring. It is the **only** state rendered in near-neutral `{colors.state-expired}` / `{colors.state-expired-light}` with the `⊗` glyph and the fixed label "Expired," and the design reason is worth holding onto: it is an absence. The Retention Deadline passed and nothing happened. A saturated red here would be a lie about severity, and a badge that looked like `FAILED` would be a worse one, because `FAILED` says something is unrecoverable while this says nothing ever started.
- **The EXPIRE banner** names the job, the outcome, the Retention Deadline that passed, and the next eligible action. "Next eligible action" for an expired job is **"none — resubmit"**, and it must be said as that rather than left blank. FR-27 lists Expiry among its triggers, and FR-27(a) requires the last verified Checkpoint step in every payload, so the notification states the step whether or not one exists.
- **How many notifications, and to whom, the PRD does not say.** FR-27's testable condition pins exact counts for an **Eviction** (one to the submitter, none to the administrator) and a **Checkpoint failure** (one to each) and is silent on Expiry. The reading that matches the pattern — one to the submitter, none to the administrator, since an expiry requires no operator action — is a design decision, not a requirement. Recorded as Open Question S1-Q6.
- **Job detail states the Checkpoint position, and this is the part that must not be got wrong.** Invariant S-2 names `EXPIRED` as one of only three exits that end a Training Job with admitted work incomplete while **retaining the last verified Checkpoint** for a human to recover — and for `EXPIRED` the retention window is a **7-day expiry grace** after expiry, after which the artifact is garbage-collection eligible (F-2). FR-7(c) is the collection rule: the 03:00 sweep removes Checkpoints only from `EXPIRED` jobs whose 7-day grace has elapsed, and **never** the 2 most recent verified Checkpoints of a non-terminal job. FR-22's own testable condition is the paired case — with the store over budget and one `EXPIRED` job past its grace alongside pending jobs, collection removes the expired artifacts and the pending jobs' Checkpoints stay byte-identical.
- **So the surface has to show a countdown to a second deadline, and must not grey the Checkpoint out.** A terminal job whose Checkpoint is *live, retained and recoverable for another six days* is the hardest thing in this set to render honestly. The rendering rules: the `EXPIRED` badge is terminal and inert, and **the Checkpoint listing beside it is not** — the digest, byte count and step stay fully legible, with the date on which they become garbage-collection eligible stated. Dimming the artifact to match the badge would tell a student her work is gone when it is sitting on disk.
- **The cross-scenario consequence, which is the reason this path exists here.** NP-3.9 in scenario 3 and FR-22(d) both depend on it: when the store exceeds `CHECKPOINT_STORE_BUDGET`, the **oldest eligible `EXPIRED`-job Checkpoints are removed first.** Garbage collection needs expired jobs to exist, and this is the path that makes them. The other half of that rule — collection halts and escalates rather than deleting when only non-terminal or quarantined Checkpoints remain — is NP-3.9.
- **Why it belongs in scenario 1 and not in a scenario of its own:** the Retention Deadline is assigned at **admission** by FR-7(b) and surfaced in the HTTP 201 response, so the reader meets it in this flow. Its resolution is late, but its cause and its promise are not.

---

## Open Questions

Gaps in `planning/prd.md` that this scenario deliberately did not fill. Each is a question for the PRD owner, not a design decision.

**S1-Q1 — The trigger document is a PRD, not a Trigger Map.** WDS Phase 3 reads persona driving forces and business objectives from a Phase 2 Trigger Map. None exists. Personas, jobs-to-be-done and success metrics were taken from PRD §2.1 and §13 instead. If Phase 1 and Phase 2 are ever run, this scenario's Business Goal and Driving Forces sections should be re-anchored to the real objective ids.

**S1-Q2 — The submission surface has a viewport basis; the board does not.** FR-1 calls the *submission* surface "desktop". Nothing in the PRD describes a viewport, breakpoint or minimum size for the status board, and FR-25's testable condition requires it to display all 32 Nodes and 33 GPU slots. The desktop floor asserted for the console is a design decision with no requirement behind it, and the WCAG 2.1 AA claim holds at and above that floor only. (Carried from `EXPERIENCE.md` OQ-5 / OQ-15.)

**S1-Q3 — Which Granted Priority does this particular job receive?** FR-17's testable condition says a `declared_intent: THESIS` submission receives `granted_priority: EXPLORATION` until an administrator grants otherwise. UJ-1 says only that the priority is read from Module 2. UJ-4 places a *different* Kavita job at `THESIS`. The surface renders whatever Module 2 returned; no scenario asserts a value.

**S1-Q4 — No named surface for Checkpoint store pressure.** NFR-13 mandates a refusal, an escalation record within 1 simulated minute and zero protected deletions; FR-22(d) says the pressure "is reported" without saying where. NP-1.7 is rendered as a submission refusal plus a Board capacity banner. That placement is a design decision, not a PRD requirement.

**S1-Q5 — The rate control's initial state is unstated.** FR-28(a) fixes the rate *set* (1×, 60×, 360×, 1440× plus pause) and FR-11(c) establishes that pause is a real state. What a run *starts* at, and whether a rate survives a page reload mid-window, is unspecified — and a board that opens at 1440× and one that opens paused are very different first impressions of the same module. Not exercised in this scenario (it belongs to scenario 2) but it lands on the same status strip.

**S1-Q6 — FR-27's notification counts are pinned for Eviction and Checkpoint failure only.** Its testable condition states exact recipient counts for those two triggers and lists **Expiry** among its triggers without giving a count. NP-1.8 renders one notification to the submitter and none to the administrator, on the reasoning that an expiry requires no operator action — a design decision consistent with the Eviction case, not a requirement. The same silence covers a **refused Preemption** (S4-Q3) and a **resume** trigger.

**S1-Q7 — The Retention Deadline has no value.** ~~Open~~ **RESOLVED 2026-09-28:** PRD Glossary now sets `JOB_TTL = 14 days` (A-22), extended by 14 days from each admitted night. FR-7(b) requires one on every admitted job and FR-1 carries it in the HTTP 201 response, and §7.3 models every other duration the simulation depends on — Checkpoint write time, job estimated duration, node health evaluation, digest verification — but the Retention Deadline is absent from that table and given no number anywhere. NP-1.8 therefore renders the value it was handed, and the 7-day figure in that path is the **expiry grace** (F-2, A-21), a different quantity that must not be mistaken for it.
