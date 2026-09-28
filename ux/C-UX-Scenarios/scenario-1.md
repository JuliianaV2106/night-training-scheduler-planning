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
| **FR-2** | Validate the Job Spec. Per-field `pass` or `rule_id` + human-readable message, rules (a)–(k). |
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

---

## Page Specifications

> **Phase 4 — WDS UX design.** This file is the **canonical specification** for three surfaces, per the registry in `ux/_progress/00-design-log.md` §2: **SURF-01** (Submission form), **SURF-04** (Job detail) and **SURF-04b** (Decision Record detail). `scenario-2.md`, `scenario-3.md` and `scenario-4.md` use all three and reference this section rather than restating it. Read `ux/_progress/00-design-log.md` §3 (precedence) and §4 (four resolved `DESIGN.md` token conflicts) before implementing.
>
> Sources, in precedence order: `planning/prd.md` → `ux/EXPERIENCE.md` → `ux/DESIGN.md` → this section.

### Specification conventions

| Convention | Rule |
|---|---|
| **Tokens** | Every colour, font, radius and spacing value is a `DESIGN.md` token reference. No literal hex, px, or named substitute appears in this section. The 2px half-step is written `spacing['0.5']`, in bracket form, because a dotted token path cannot carry a dotted key unambiguously. |
| **Ids and codes** | Rendered **verbatim** from `planning/prd.md`. States, reason codes, decision values, citation ids, `FR-`/`NFR-`/`UJ-`/`F-`/`A-` ids, node identifiers and persona names are never paraphrased, re-cased or shortened. |
| **Prose values** | A `summary` shown as a specimen is a **rendered value from a Decision Record** — the console renders the string the daemon emitted and never authors one. Specimens are marked *specimen* and are shaped to §6.1 (one sentence, ≤ 200 characters, actor + action + reason, no "policy"/"invalid"/"forbidden"/"error" alone). They are not console-authored copy. |
| **Unknown values** | Where the source names no value, the spec says so and points at the scenario's open question. It does not supply one. `‹angle-bracket›` marks a metavariable, not a placeholder to be invented — with one deliberate exception, `JOB-0417` on `ws-gpu-12` at `2026-10-04T05:45:00-05:00`, which is verbatim from `planning/prd.md` §6.3 and may be used concretely. |
| **State encoding** | Every one of the 9 job states and 5 slot states renders **colour + glyph + text label** (NFR-15). Colour is the third channel, never the first. Terminality is carried by the label and a 1px `{colors.border-structure}` ring on the four terminal badges — never by a background fill, never by desaturation. |
| **Citation ink** | Both `self:` and non-`self:` citations render in `{colors.citation-ink}` / `{colors.citation-ink-light}`, `self:` at base weight and delegated authorities at a heavier weight, per design log §4 conflict **2**. Neither uses `{colors.accent}`, which is reserved for interactive affordance and the clock controls. |

---

## SURF-01 — Submission form

**Route:** `n` (bare key) — new job. `EXPERIENCE.md` Interaction Primitives: `n` is a standalone key and `g n` is a two-key sequence, so after `g` the `n` is consumed as a prefix and the two never collide.
**Persona:** `Kavita` (`STUDENT`).
**Theme:** light. `{colors.surface-base-light}` ground, `{colors.surface-raised-light}` field groups, `{colors.border-structure-light}` on every field border.
**PRD basis:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-17(c), FR-24, NFR-4, NFR-11, NFR-13, NFR-15. Realises UJ-1. Specimens: `ux/wireframes/03-submission-form.md`.

### SURF-01.1 Frame

Single column, work region. It is a route inside the console's three-region frame, not a separate origin — the status strip stays mounted and readable, because the strip is the surface that says which clock she is submitting against.

- Field groups sit on `{colors.surface-raised-light}`; padding `{spacing.3}` (12px); stack gap `{spacing.panel-gap}` (12px) inside the group, `{spacing.6}` (24px) between groups. `{spacing.panel-gap}` is one step tighter than the `{spacing.gutter}` (16px) region gutter deliberately, so nesting reads.
- Group label `{typography.label}` (12px/500) in `{colors.text-secondary-light}`; field label `{typography.label}`; value `{typography.body}` (13px/400) in `{colors.text-primary-light}`; helper text `{typography.caption}` (11px) in `{colors.text-muted-light}`; error text `{typography.caption}` in `{colors.ui-adverse-light}`.
- **Evidence is set in monospace.** The container digest, `node_id` values in the selector, `checkpoint_interval_minutes`, the idempotency key and every timestamp render `{typography.mono-data}` (12px, JetBrains Mono) in `{colors.text-primary-light}` — `DESIGN.md` Commitment 2: a `job_id` in Inter is a bug. The digest field is the sharpest case: a 64-character hex string, where the reader must be able to distinguish two characters at a glance before submitting.
- Focus: 2px `{colors.focus-ring-light}` outline at 2px offset (`{components.focus-ring}`), drawn outside the border box.
- **Single-key shortcuts are inert while any field has focus.** `1`–`4`, `Space`, `0`, `g`, `n`, `j` and `?` do nothing; `Esc` leaves the field rather than closing anything; the rate control stays reachable by `Tab`. `EXPERIENCE.md` is explicit and the reason is this surface in particular: a hex digest contains `0`–`5`, so typing a digest would otherwise fire the rate control four times on a live run.

### SURF-01.2 The A-3 simulation disclaimer

Permanently mounted, un-dismissable, above the first field group. `{typography.caption}` on `{colors.surface-raised-light}` with a 1px `{colors.border-subtle-light}` hairline.

> **This prototype simulates every Training Job.** v1 models no real GPU hardware, no container execution, no telemetry and no model weights (PRD §5, `A-3`). Nothing you submit will reach a physical machine.

No dismiss control, no "got it" affordance, no hover-reveal. `EXPERIENCE.md` OQ-8 records the dismissal semantics as unspecified; the surface resolves it as permanent because an operator must never be able to mistake a prototype run for a production fleet. **Flagged:** that resolution is a design decision, and it is the kind of thing a PRD owner may want to overturn.

### SURF-01.3 Field inventory

Twelve fields, all grounded in the §3 Job Spec definition plus the FRs that name them. There is exactly one Job Spec per Training Job (§3).

| # | Field | Type | FR-2 rule | Notes |
|---|---|---|---|---|
| 1 | `container_image` | text, digest | **(a)** | Must be pinned by digest, not tag. `sha256:` + 64 hex. `:latest` fails (NP-1.2). |
| 2 | `worker_count` | integer | FR-1(d), FR-3(a) | `= 1`. `replicas = 1` in the same group. **Checked first** — see SURF-01.4. |
| 3 | `gpus_per_node` | select | **(b), (k)** | `1` or `2`. **`2` is legal only with a 48 GB-class target — `server-gpu-01` is the only Node with two slots** (A-19, F-42). The 2-GPU option is offered, not hidden, because FR-2(b) admits it; what the surface refuses is the **combination**, and that refusal is a field error on this field. See rule (k) below. |
| 4 | `required_vram_gb` | select | **(c)** | Must not exceed the largest single-Node VRAM class, **48 GB**. `server-gpu-01` carries two 48 GB slots; each `ws-gpu-NN` carries one 24 GB slot (§3, F-42). |
| 5 | `resources` | paired `requests` / `limits` | **(d)** | Must be **equal** for GPU and memory, because quota accounting reads `requests`. Rendered as two inputs with an inline "must match" rule; a mismatch is a per-field rejection, never a silent normalisation. |
| 6 | `node_selector` | select | **(e)** | Optional. If present it must name a Node matching the declared VRAM class. Renders the 32 fixed ids, `ws-gpu-01` … `ws-gpu-31` and `server-gpu-01` (`A-4`), in `{typography.mono-data}`. |
| 7 | `storage_request` | text | — | Named in the §3 Job Spec. No validation rule is attached to it by the PRD, so the surface renders it with no invented constraint. |
| 8 | `checkpoint_interval_minutes` | integer | **(g)** | Positive integer **≤ 30** (F-17). Helper text states why: a longer interval would let progress since the last Checkpoint exceed what the Checkpoint Budget can plausibly flush at the Ramp. |
| 9 | `restart_policy` | select | **(f)** | Must not request a restart that would silently re-enter a Night Window without re-admission. |
| 10 | `model_id` | text | **(h)** | Resolved against the Module 5 catalog. Must exist and must not be deprecated. |
| 11 | `estimated_duration_s` | integer, seconds | **(i), (j)** | Declared or derived from the model record (A-11: declared is trusted as given). Rendered in `{typography.mono-column}` with tabular numerals so seconds align. |
| 12 | `declared_intent` | select | FR-17(c) | A **request**, never a Granted Priority. Renders with a `PENDING_REVIEW` marker. See SURF-01.6. |

Plus, read-only and not editable here:

| Read-only field | Source | Why |
|---|---|---|
| `granted_priority` | Module 2 (Policy Engine) | FR-17(b): Granted Priority is read-only to this module. A student's self-declared intent never contributes (FR-14(c)). |
| `idempotency_key` | generated by the surface, shown | FR-1(a), FR-5. Visible so the 409 case (NP-1.4) is diagnosable. |

### SURF-01.4 Validation model

**The scope check runs first, and that ordering is the spec.** FR-3 short-circuits **before** FR-2 field validation (F-28), so on a multi-worker Job Spec the response carries `OUT_OF_SCOPE_DISTRIBUTED` and **no per-field FR-2 rejections appear beside it**. This is why FR-2's own testable condition must be run with `worker_count = 1` — otherwise the short-circuit swallows the three rejections it exists to test. A form that showed all four errors at once would be lying about what the daemon evaluated.

Two rendering classes, never merged:

**(a) Per-field rejections** — NP-1.2. At the field, never a banner and never a toast. Each carries its field name, its `rule_id` and one human sentence. Three simultaneous rejections render as three separate messages on three separate fields:

| Rule | Field | Message carries |
|---|---|---|
| (a) | `container_image` | must be pinned by digest, not tag |
| (c) | `required_vram_gb` | **64 GB requested against the largest single-Node VRAM class of 48 GB** — both classes named |
| (g) | `checkpoint_interval_minutes` | must be a positive integer ≤ 30 |

Rule (c) names both halves on purpose: a 70B-class job on a 24 GB workstation is infeasible for a reason the reader needs in full. Rule (g) carries its reason in helper text, because the 30-minute ceiling is the Checkpoint Budget's arithmetic and not an arbitrary limit. `reason: VALIDATION_FAILED`, `decision: DENY`, citation `self:JOBSPEC-VALIDATION-v1`.

**Rule (k) is a fourth per-field rejection, and it is the one that exists because of edge-case review E-3.** It is stated as a field error on `gpus_per_node` rather than as a banner, because it is a Job Spec field rule like (a) and (c), and a reader who typed it can fix it by typing something else.

| Rule | Field | Message carries |
|---|---|---|
| **(k)** | **`gpus_per_node`** | **`2 GPUs` is valid only with a 48 GB-class target — `server-gpu-01`. `server-gpu-01` has 2 slots; `ws-gpu-NN` has 1.** Citation `self:JOBSPEC-VALIDATION-v1`, naming rule (k). |

**Why the field is not merely constrained by the selector.** `gpus_per_node = 2` with `required_vram_gb = 24` satisfies FR-2(b) and FR-2(c) individually, and the only thing that makes it unplaceable is the **`node_selector` pinning** — `ws-gpu-14`, which has one slot. Before rule (k) that job was admitted into the Pending Set and then silently unplaceable: it aged, it was promoted by FR-14(d), it appeared in the Admission Order as a `DEFER` with `CAPACITY_EXHAUSTED`, and **no reason ever surfaced on the form, because the form had already returned 201**. A job that is refused at 14:30 costs a student one edit; a job that is admitted at 14:30 and never runs costs her a night, and tells her nothing. The message names the **slot count of the specific Node pinned**, not just the class, because the class is what she has already read in the selector and the slot count is the fact that is actually blocking her.

**Rule (k) is deliberately *not* one of the three simultaneous rejections in FR-2's testable condition** — that condition is (a), (c) and (g) on a `worker_count = 1` spec and is left exactly as the PRD states it. Rule (k) is an additional branch in the same class, and the surface must therefore be able to render (a) + (c) + (g) + (k) at once without collapsing any of them.

**(b) Whole-request refusals** — a `decision-banner` at the top of the work region, in the form's light theme. Five distinct branches, none of which may be folded into another:

| Branch | `reason` | Citation | Why it is its own branch |
|---|---|---|---|
| **Scope** | `OUT_OF_SCOPE_DISTRIBUTED` | `self:SCOPE-BOUNDARY-v1` | Module-owned, so `self:` alone is legitimate (F-1). Names **Module 10** as the owning module. Short-circuits FR-2. |
| **Span** | `VALIDATION_FAILED` (FR-2(j)) | `self:MAX-NIGHT-SPAN-v1` | Module-owned. Must name **both** 52 h and the 38.75 h ceiling (5 × 7 h 45 min) **and propose a concrete scope reduction** (FR-4(c)). |
| **Capacity — queue** | `QUEUE_FULL` | `self:QUEUE-DEPTH-CAP-v1` | Module-owned. Carries a **next-available-slot estimate** (FR-7(a) outputs a refusal *with* an estimate). |
| **Capacity — store** | `STORE_FULL` | `self:CHECKPOINT-STORE-BUDGET-v1` | Its **own** branch, not a variant of the queue one: NFR-13 mandates a second record — `DEFER` / `DISK_PRESSURE_ESCALATION`, within 1 simulated minute. A designer who folds this into the queue banner has removed a branch the PRD requires. |
| **Missing verdict** | the non-ALLOW or absent authority, named | a **non-`self:`** citation naming that authority | FR-6(b): a missing verdict is a blocking error, never a default ALLOW. A `DENY` on a delegated verdict may **not** cite `self:` alone (F-1). 100 submissions against a 503 produce 100 refusals and 0 admissions. |

Plus a sixth, non-banner outcome:

**(c) HTTP 409** — same idempotency key, different payload digest. No job created, Pending Set length unchanged (FR-5). Renders as its own message and **states that no job was created**; silent idempotency is a data-loss bug wearing a feature. The contrast case — same key, identical digest → HTTP 200, the original `job_id`, no state change — must also be stated, because "409" alone does not tell Kavita whether her first submission succeeded.

### SURF-01.5 Dynamic feedback

Field-level validation, debounced on blur and on submit. **The form is never disabled wholesale** — a student mid-entry at 14:30 must not lose her work to a background poll, and the delegated-verdict round trip is a network call that can be slow.

**The estimate readout** is the surface's one piece of live feedback, and it is where the module's thesis is won or lost. When validation returns, all six FR-4 outputs render together, in `{typography.mono-column}` with tabular numerals:

```
estimated_duration_s        111600        (31 h 00 m 00 s)
estimated_completion_nights 4
required_vram_gb            24
admitted_nights             0
max_night_span              5
confidence                  <as stated — never a bare number>   (FR-4(a))
requires_multiple_nights    true
```

- **`requires_multiple_nights: true` is set unconditionally** when the estimate exceeds the 7 h 45 min Usable Night Duration. FR-4(b) admits no exception, and it **must never be treated as a rejection on its own**. It renders in the neutral/positive channel — this is the case the module exists to serve, and a surface that made it feel like a problem would invert the module's thesis.
- The line beneath it names the ceiling it is measured against: *"Requires at least 4 Night Windows. Max Night Span is 5."* (`EXPERIENCE.md` Voice — the approved phrasing, and its banned counterpart "This will take a while 🙂".)
- **The scope-reduction proposal is a distinct element, not part of the summary.** FR-4(c) requires a concrete proposal, and §6.1 caps `summary` at 200 characters; the two do not fit in one line honestly. It renders as a named list under the banner: lower `epochs`, raise `gradient_accumulation_steps` to trade compute for memory, reduce the dataset size, target a smaller base model.
- Confidence renders as a stated value, never a bare number (FR-4(a)). The PRD supplies no vocabulary for it, so the surface renders whatever the daemon returned and adds no band names of its own.

### SURF-01.6 Granted Priority is read, never declared

Rendered read-only above the form, from Module 2. Her `declared_intent: THESIS` renders **as a request**, with a `PENDING_REVIEW` marker and a line stating that it is not the applied value and that only an administrator can set Granted Priority.

This is the whole of FR-17(c), and it is load-bearing: priority is the only resource in this module that can destroy someone else's work, so making it self-service would make Annex Scenario 4 a no-op. The UI must make that visible rather than merely correct — a student who believes her declaration was honoured has been misled by a form that looks like it took her word.

**Not pinned by any source:** which Granted Priority this particular job receives. FR-17's testable condition says a `declared_intent: THESIS` submission receives `granted_priority: EXPLORATION` until an administrator grants otherwise; UJ-1 says only that it is read from Module 2. The surface renders whatever Module 2 returned and never derives it (**S1-Q3**).

### SURF-01.7 Controls and triggers

| Control | Type | Trigger | Result | Emits |
|---|---|---|---|---|
| **Submit** | primary, `{colors.accent-light}` fill, `{colors.text-on-accent-light}` text, `{rounded.sm}` | click, or `Ctrl`+`Enter` | Validates and submits. Renders one of the Success or Error branches in SURF-01.8. | `POST` — HTTP 201 / 200 / 400 / 409 / 503 |
| **Clear** | secondary, 1px `{colors.border-structure-light}` | click | Resets every field **except** the idempotency key, which stays — clearing it would defeat the point of an idempotent client. | — |
| Clock segments | `{components.clock-control}` | click, or `1`–`4` / `Space` | Rate change. **Pacing only** — FR-11(b) may not reorder, add or remove a queued transition, so the control shows no confirmation and no "this changes results" note. There is nothing to confirm, and implying otherwise would be a lie about the system's guarantees. | `PATCH /simulations/{id}/rate` |

`Submit` is never disabled. If a field is incomplete the button submits anyway and the first incomplete field takes focus with its error — a disabled submit tells a student the form is broken when it is merely unfinished.

### SURF-01.8 Loading · Empty · Error · Success

| State | Specification |
|---|---|
| **Loading** | **Field-level, never a form-level overlay.** The estimate readout shows `{typography.mono-label}` skeleton rows at final geometry while the delegated verdicts resolve. The `Submit` control renders a `{typography.mono-data}` `VALIDATING…` label and stays operable. Entered values are never cleared, never re-ordered and never re-rendered. NFR-9 bounds visibility at ≤ 500 ms of real time at every rate. |
| **Empty** | **Not applicable — a form is never empty-state.** Stated so it is not mistaken for an omission. The form's zero state is its filled state with no estimate yet. |
| **Error** | The five refusal branches in SURF-01.4, plus the 409, plus per-field FR-2 rejections. Every one renders its `reason` code in `{typography.mono-label}` and its full citation row. **Missing verdict** reads: *"Cannot verify entitlement. Nothing was queued."* — and its obligation is to be specific about what it is waiting for, not to soften the failure. This is the one refusal where the correct product behaviour is to look broken, and smoothing it is the defect. |
| **Success** | HTTP 201. The form **navigates to SURF-04 for the new `job_id`** — not to the Pending Set. UJ-1's climax is a position and a projected first-start attached to *her* job; a 500-row list would bury the one number she came for. Before navigating, a confirmation band renders the three numbers and the `ADMIT` record: state, Pending Set position, projected first start, Retention Deadline, and the one `ADMIT` Decision Record with its complete citation row. |

**Decision Records the form renders on failure.** A refusal is a `decision-banner` even when the outcome is a refusal to validate the *form* — SM-5 targets 100% of decisions presented to a user, and a decision the user cannot check is not explainable. The banner is the same component as on the console, in the light theme.

**Specimen — the `DENY` for NP-1.3 (over Max Night Span), at 14:30.** Rendered verbatim from the record; see `ux/wireframes/03-submission-form.md`.

```
!  Decision · deny                                              DENY
   Not admitted — MAX_NIGHT_SPAN_EXCEEDED. Estimated duration 52 h exceeds the
   38.75 h ceiling (5 × 7 h 45 min). Reduce scope and resubmit.
   [ self:MAX-NIGHT-SPAN-v1 ]
   decision_id ‹decision_id›  ·  sim_timestamp 2026-10-04T14:30:11-05:00
```
`self:` alone is correct here and nowhere else in this form. Max Night Span is a module-owned rule with no delegated authority to name — scope boundary, Max Night Span, queue cap, Job Spec validation (F-1). A `DENY` that reaches for `self:` out of habit on a *delegated* verdict is wrong, and the ink weight is what makes the difference visible to a reader.

**Specimen — the `ADMIT` on success.** Neutral/positive group: 3px border at 60% opacity, `{colors.surface-base-light}` fill, `✓` group glyph, the word `admit`. Same summary treatment, same citation row. **A quieter `ADMIT` is a de-emphasis, never a citation-stripped summary** (SM-5, FR-25(b), absolute).

### SURF-01.9 Accessibility

- WCAG 2.1 AA per NFR-15. `{colors.text-primary-light}` on `{colors.surface-base-light}` is 15.79:1; `{colors.text-muted-light}` is 5.33:1; the nine `-light` state tokens are 4.57–7.39:1. The binding pair in the whole light set is `{colors.state-checkpointing-light}` at 4.87:1 on base.
- Each field's error is programmatically associated with its input via `aria-describedby`, so the message is announced with the field rather than being found by reading the page.
- **A new Decision Record is announced.** The banner carries a `role="status"` node on first appearance, **escalated to `aria-live="assertive"` because it is an adverse decision on the viewer's own job** — one of the three reserved cases, and the one UJ-1 exists to exercise. A screen-reader user who submits and hears nothing cannot tell success from failure. Once present the banner is a navigable region, not a live region, and never re-announces on repaint.
- Every reason code is real text in `{typography.mono-label}`, never an image and never an `aria-label` that paraphrases it.
- Focus order matches reading order. No banner auto-dismisses and no time-limited content exists on this surface.
- `prefers-reduced-motion` is satisfied vacuously: this surface has no change animation, and the only permitted console animation is a 120 ms background wash.

---

## SURF-04 — Job detail

**Route:** `g j` on the focused row, tile or log line; or `Enter` on any job row. Reached from SURF-01 on success — the landing route for a submission.
**Persona:** both. `STUDENT` sees her own jobs only (FR-31(b)); `LAB_ADMIN` sees all.
**PRD basis:** FR-25, FR-24, FR-26, FR-22, FR-27, NFR-4, NFR-11, NFR-15. Realises UJ-1 step 4, and the frame for UJ-3, UJ-4, UJ-5, UJ-6.
**Deltas added elsewhere:** `scenario-3.md` (the `CHECKPOINTING` / `EVICTED_RESUMABLE` / `EVICTION_FAILED` / `FAILED` state panels, the Quarantine release entry point), `scenario-4.md` (the `PREEMPT` banner variant, the gate-arithmetic panel, the Priority administration entry point).

### SURF-04.1 The two-column split

Not decorative. FR-25(b) requires the citation list to render alongside any decision the surface displays, and a two-column layout means **the citation is never behind a disclosure the operator has to remember to open**.

```
┌─────────────────────────── work region ───────────────────────────┬──────────────────────────┐
│ LEFT — the subject                                           1fr │ RIGHT — Decision Records  1fr │
│                                                                   │                           │
│  JOB-0417   ‹ Queued ›          ← mono-data-lg + status-badge      │  Decision · admit   ✓     │
│  ═══════════════════════════════════════════════════════          │  summary @ typography.body│
│  State payload                        {spacing.4} 16px gap         │  citation row (chips)      │
│  Placement / Pending Set position                                │  decision_id · sim_ts      │
│  Retention Deadline                                             │  ─────────────────────────  │
│  Checkpoint                                                    │  earlier records…          │
└───────────────────────────────────────────────────────────────────┴──────────────────────────┘
```

- Column gap `{spacing.gutter}` (16px). Left column carries identity and state; right column carries evidence. `DESIGN.md` Layout: "the subject on the left, the Decision Record evidence on the right."
- Below the desktop floor the split does **not** collapse. `EXPERIENCE.md` Responsive is explicit that the three-region frame has no collapse behaviour, and a stacked column would put the citation below the fold on the one surface where FR-25(b) is load-bearing.
- Modal depth is capped at one: a Decision Record opens as a side panel (SURF-04b), never as a dialog on top of the job detail it belongs to.

### SURF-04.2 Header

| Element | Spec |
|---|---|
| `job_id` | `{typography.mono-data-lg}` (14px) in `{colors.text-primary}`. One of exactly three permitted uses of `mono-data-lg` (`DESIGN.md` Typography) — a `job_id` in a page title — because the reader may copy it into a search or compare it against a log line. |
| `status-badge` | `{components.status-badge}`: 20px high, `{rounded.full}`, `{spacing.2}` horizontal padding, `{typography.mono-label}`, transparent ground, the state's colour as **text and glyph** colour. Glyph `aria-hidden="true"`; the text label is never truncated and the badge is never icon-only (NFR-15). |
| Terminal ring | The four terminal states — `REJECTED` `COMPLETED` `FAILED` `EXPIRED` — take a 1px `{colors.border-structure}` ring. The five non-terminal take none. **A badge never becomes grey because it is terminal**: `{colors.state-expired}` is grey already and one token must mean one thing. |
| Clock context | The simulated instant at which this view is current, `{typography.mono-data}` in `{colors.text-muted}`, right-aligned. §7.1 requires every persisted timestamp to carry an explicit offset so a 24-hour simulated run stays diffable. |

**The nine badges.** Colour, glyph and label, verbatim from `DESIGN.md`:

| State | Glyph | Label | Ring |
|---|---|---|---|
| `REJECTED` | `✕` | Refused | yes |
| `QUEUED_PENDING_WINDOW` | `◷` | Queued | no |
| `RUNNING` | `▶` | Running | no |
| `CHECKPOINTING` | `▼` | Checkpointing | no |
| `EVICTED_RESUMABLE` | `‖` | Evicted, resumable | no |
| `COMPLETED` | `✔` | Completed | yes |
| `FAILED` | `⚠` | Failed | yes |
| `EVICTION_FAILED` | `⚡` | Eviction failed | no |
| `EXPIRED` | `⊗` | Expired | yes |

The labels are **not** translations of the token names. `EVICTED_RESUMABLE` reads "Evicted, resumable" and `EVICTION_FAILED` reads "Eviction failed"; using the raw token name instead would hand the reader back the ambiguity the state table exists to remove. One state has one name everywhere — a per-surface label variant is a defect, not a localisation.

### SURF-04.3 Left column — state payload

A `{spacing.row-dense}`-rhythm key/value list. Keys `{typography.label}` in `{colors.text-muted}`; values `{typography.mono-data}` in `{colors.text-primary}`. Numeric columns use `{typography.mono-column}` with tabular numerals so digits align vertically without the reader tracking glyph widths.

**The nine states' required additional content**, from `EXPERIENCE.md` State Patterns, is contractual — not a suggestion:

| State | The surface must additionally show |
|---|---|
| `REJECTED` | The reason code and the citation. Per-field `pass` or `rule_id` + human-readable message, each failing field shown **individually** (FR-2). |
| `QUEUED_PENDING_WINDOW` | Pending Set position; projected first start; Retention Deadline; `admitted_nights` / `max_night_span`; the Effective Priority decomposition (granted + aged); how many verified Checkpoints are already held — the state "may hold one or more verified Checkpoints" (§4.1). |
| `RUNNING` | `node_id`; slot ordinal; elapsed runtime; `progress_fraction` against `estimated_total_s`; last verified Checkpoint step. |
| `CHECKPOINTING` | Live countdown **and** whether the write is inside the 300 s Checkpoint Budget (05:45:00–05:50:00) or the 05:50:00–05:53:00 reserve. **FR-19(b) makes the reserve still usable, so the surface must not present it as expired.** |
| `EVICTED_RESUMABLE` | Retained Checkpoint **digest, byte count and step**; the next eligible resume. **Never styled or worded as a failure** — UJ-3 specifies the climax reads `EVICTED_RESUMABLE` with a verified digest, "not 'stopped.'" |
| `COMPLETED` | `next_decision_at` is null; the slot is released. |
| `FAILED` | The reason code — `CHECKPOINT_CORRUPT`, `MAX_NIGHT_SPAN_EXCEEDED`, `MODEL_DEPRECATED`, `OOM_KILLED` / `PROCESS_EXITED`, `CHECKPOINT_DEADLINE_MISSED`, `NODE_FAULT_NO_CHECKPOINT` — and confirmation that the last verified Checkpoint is retained (FR-22, Invariant S-2). An `OOM_KILLED` exit additionally carries FR-29(a)'s cited remediation: lower the batch size, or target a 48 GB-class Node (`server-gpu-01`). |
| `EVICTION_FAILED` | The named cordoned Node; the retained verified Checkpoint step; and an explicit "re-admitted at tonight's 22:00:00 Window Activation onto any Eligible Node" (T-20). **The badge must not read as terminal.** |
| `EXPIRED` | The Retention Deadline that passed; Checkpoints inside the 7-day expiry grace are retained; **the instant they become garbage-collection eligible**. |

**Three renderings that must not be got wrong.** They are the ones where a defensible-looking implementation inverts the module's meaning.

1. **`EXPIRED` is terminal and inert; the Checkpoint beside it is not.** Invariant S-2 names `EXPIRED` as one of only three exits that end a job with admitted work incomplete while **retaining** the last verified Checkpoint for a human to recover — and for `EXPIRED` the window is a **7-day expiry grace** (F-2), after which the artefact is garbage-collection eligible. So the surface shows a **second countdown**, to garbage-collection eligibility, and the digest, byte count and step stay **fully legible**. Dimming the artefact to match the badge would tell a student her work is gone while it sits on disk. The badge is the only near-neutral one in the palette because it is an absence — the Retention Deadline passed and nothing happened — and a saturated red here would be a lie about severity.
2. **`EVICTION_FAILED` is the loudest non-red in the palette and is still non-terminal.** `{colors.state-eviction-failed}` `#FFA657` with `⚡`; the token appears nowhere else in either job-state set, and it holds no hue a terminal state uses. Its name reads as terminal and it is not: the job holds a retained verified Checkpoint and is re-admitted at the next activation onto a **different** node. The `‖` / `⚡` glyph pair and the two labels are the channels that survive deuteranopia, where `{colors.state-rejected-light}` and `{colors.state-eviction-failed-light}` converge to roughly dE 1.6. The label is always followed by the retained Checkpoint step, so the operator reads "failed to stop cleanly on a node" rather than "job lost".
3. **`EVICTED_RESUMABLE` is not an error.** `‖` pause-bar, `{colors.state-evicted-resumable}` violet. If a reader confuses this with `FAILED` pink `⚠`, the design has failed even though both are technically "not running". The module's whole thesis is that a job stopped at dawn is not a failed job.

### SURF-04.4 Right column — the Decision Record list

- **The last 10 records, and never fewer.** FR-25 names 10; that is an **upper bound, not a quota**. A job with three records renders three and the list is **not** padded to ten.
- The bound is stated on screen: **`10 of 27`**, with a see-more affordance onto SURF-05. A bounded window is auditable; an unbounded one is not, and a silent cut is how a citation list quietly disappears.
- Newest first. Each row is a collapsed `decision-banner` at SURF-04.6 anatomy; `Enter` opens SURF-04b.
- Each record's `summary` and its **full** `citations` list render on the row. **All ten variants, every time.** Only visual weight differs between the adverse and neutral/positive groups. A quieter `ADMIT` or `RESUME` is a de-emphasis, never a citation-stripped summary (SM-5, FR-25(b), absolute).

### SURF-04.5 `next_decision_at`

Always present, `{typography.mono-data}`, `{colors.text-muted}` when null, because §6.1 discipline applies to a null as much as a value: a `COMPLETED` job renders **`none — terminal`** as prose, and a field that carries a value carries it. Never a bare en dash, never a blank. The status strip's own countdown is the nearest-value shortcut to it (SURF-02a).

### SURF-04.6 The `decision-banner`

One component, ten variants, two groups. `{rounded.md}`, `{spacing.banner-inset}` padding, a 3px left border in the group's colour, `{colors.surface-raised}` fill for adverse and `{colors.surface-base}` for neutral/positive.

| Group | Variants | Left border | Group glyph | Weight |
|---|---|---|---|---|
| **adverse** | `DENY` `DEFER` `PREEMPT` `EVICT` `EXPIRE` `FAIL` `CORDON` | `{colors.state-rejected}` for `DENY`/`DEFER` **and for `FAIL`** · `{colors.state-eviction-failed}` for `EXPIRE`/`CORDON` · `{colors.state-failed}` for `PREEMPT`/`EVICT` | `!` | 3px border at full opacity |
| **neutral / positive** | `ADMIT` `RESUME` `COMPLETE` | `{colors.node-available}` | `✓` | 3px border at 60% opacity |

**The `FAIL` border follows design log §4 conflict 4**: the `FAIL` *banner* is red-bordered, sharing with `DENY`/`DEFER`, while the `FAILED` *job badge* is pink. Different components carrying different facts. A pink `FAIL` banner beside a pink `FAILED` badge would collapse "refused a request" into "the machine broke", which is the one distinction this palette is built to keep.

**The group is never signalled by hue alone.** The eyebrow opens with the group glyph *and the group word* — `Decision · deny` against `Decision · admit` — and the border weight differs. The 1.09:1 fill difference between raised and base is **decoration, never a signal**. Under deuteranopia the adverse and positive borders land roughly dE 6.8 apart, and a refusal that looks like an admission is the worst failure this component can have.

**Anatomy, top to bottom.** Eleven §6.1 fields in six places, because three slots cannot hold eleven fields and the remainder had to be placed rather than left implied:

1. `supersedes` — a `supersedes ‹decision_id›` link **above** the eyebrow, when non-null. Revision appends; records are immutable (FR-24(d)), so a revised decision appears as a new record linked to its predecessor, never as an edit.
2. Group glyph + group word + `decision` as the eyebrow, `{typography.mono-label}`.
3. `summary` at `{typography.body}`. **The console never authors a summary — it renders the one the daemon emitted**, and the console's own surrounding copy obeys the same ban, because a UI that says "Policy violation" beside a carefully-cited summary destroys the summary's credibility.
4. `citations` — `citation-chip` elements at `{typography.mono-label}` (design log §4 conflict 3), full `authority:identifier@version` **unabbreviated**, wrapping and **never truncating**. `policy:M2/class-schedule@policy-v3` is copyable and checkable; an ellipsised citation defeats the entire purpose of §6. Chips carry a `{colors.border-subtle}` decorative hairline and sit on `{colors.surface-overlay}`; they render 19.4px tall, below the WCAG 2.2 SC 2.5.8 24px target, which the design accepts because a citation is a **copy** target and the full string is also reachable as selectable text in SURF-04b.
5. `decision_id` then `sim_timestamp` — `{typography.mono-data}`, `{colors.text-muted}` — under the summary. `decision_id` first because it is the handle the reader quotes.
6. `inputs` renders as the summary's own trace, **not as a JSON blob**: the evaluated values that produced the decision, as label/value pairs.
7. `actor_id` renders the **resolved display name and the raw `actor_id` side by side** (NFR-11), and where resolution fails the raw value stands alone rather than a blank — an unresolvable actor is a fact.
8. `job_id` / `node_id` are **nullable** in §6.1. A record carrying neither renders as `Decision · deny` and the detail carries the reason it has no subject — **never a dash, never an inferred value**.

**The F-1 split is visible, not merely satisfied.** `self:` citations render at base weight in `{colors.citation-ink}`; delegated authorities — `policy:M2/…`, `quota:M8/…`, `entitlement:M1/…`, `node-state:M3/…`, `reservation:M4/…`, `catalog:M5/…` — render in the same channel at a heavier weight. A reader can see at a glance whether a decision rests on an external authority or on this module's own bookkeeping, which is the distinction §6.2 says must never be blurred: "a denial, preemption, or eviction of a user's work may never be justified solely by a time or bookkeeping reason." **Neither channel uses `{colors.accent}`** — accent is for interactive affordance, and a `policy:M2/…` chip painted as a button would blur exactly this.

### SURF-04.7 Controls and triggers

| Control | Trigger | Result |
|---|---|---|
| `Enter` on a banner | keyboard | Opens **SURF-04b**, not an expansion. On a decision the full record is what a reader who pressed `Enter` wants. |
| `→` on a job row in a list | keyboard | Expands the row in place to its last Decision Record, without leaving the list. `←` collapses it, so an expansion is always reversible. `Shift+→` expands in both list and grid contexts. |
| `g j` / `g n` | keyboard | Operate on the **focused** row or tile; with nothing focused they follow the last-focused subject; with no prior subject they go to the route's index rather than nowhere. |
| `Esc` | keyboard | Closes the topmost panel and returns focus to the control that opened it **at the preserved scroll offset**. `Esc` never closes a panel that has a text field in focus — it leaves the field first. |
| `→` on a Quarantined Checkpoint | keyboard / click | Opens **SURF-08** Quarantine release (`LAB_ADMIN` only), from the `FAILED` badge rather than from the node — `EXPERIENCE.md` Flow 6 step 2, and FR-20(e)'s requirement that the UI not imply the node is suspect. |
| Priority administration | click | Opens **SURF-06b** (`LAB_ADMIN` only, FR-17). |

Row actions are revealed on **hover and on keyboard focus equally**. A row action that exists only under the pointer is unreachable by keyboard and undiscoverable by touch; hover never carries information available only on hover, and the citation list, reason string and Checkpoint digest are always in the DOM.

### SURF-04.8 Loading · Empty · Error · Success

| State | Specification |
|---|---|
| **Loading** | Field-by-field skeleton **in the FR-25 response shape** — state, position-or-placement, records, `next_decision_at` — at final geometry, so nothing shifts when values arrive. Never a spinner over a blank panel. |
| **Empty** | **Not applicable, and the reason is worth stating:** a `job_id` that resolves always has a state, so a valid `job_id` has no empty case. A 404 is an error, not an emptiness. |
| **Error** | **404** → `No such ‹job_id›.` A genuine query failure → a retry affordance and the last-received-update instant, with controls `aria-disabled` but **not dimmed**: `{colors.text-secondary}` at 40% opacity composites to 2.40:1, and a control the operator cannot read is the vanished control this design refuses to create. **Daemon unreachable** → `Daemon unreachable — data may be stale`, last known values **visible and marked stale, never blanked**, because the surface must never imply the fleet changed while data was stale. **A corrupt Checkpoint is not a tenth state.** `CHECKPOINT_CORRUPT` is a reason code on `FAILED`; what renders is the `FAILED` badge with that reason, the Quarantine notice, and the confirmation that a human has been notified. FR-20(e) is explicit that **no Cordon Request is issued for a corrupt artefact**, because a corrupt file is not evidence of a faulty Node — so this surface must not imply the node is suspect. |
| **Success** | Resolves with the retained Checkpoint digest and step visible whenever the state holds one, and the Effective Priority decomposition readable before any navigation elsewhere. |

### SURF-04.9 Accessibility

- WCAG 2.1 AA (NFR-15). Every state carries colour **and** glyph **and** text label.
- **Live regions are scoped to the smallest stable node.** A job *state* change announces as `JOB-0417 Queued` — never a bare state name, never a colour. A new Decision Record gets `role="status"` (polite) on first appearance in the focused surface, **escalated to assertive only when it is an adverse decision on the viewer's own job**; once present the banner is a navigable region and never re-announces on repaint.
- **Focus never moves on a background poll.** If the view recomputes while focused, the change is announced and the focus stays put.
- Every detail panel returns focus to its opener at the preserved scroll offset. An operator auditing five jobs in sequence must never lose their place, and a panel that drops focus to `<body>` on close sends the next `Tab` back to the top of the frame.
- Citations are **real text** — selectable, copyable, in `{typography.mono-label}`. An `aria-label` that summarises a citation defeats the point of the §6 contract.
- **No content is time-limited.** No banner auto-dismisses. The Eviction Ramp countdown stops at 05:53:00 and stays visible; nothing expires the operator's ability to read why their work stopped.
- The only permitted change animation is a 120 ms background wash on the changed row. `prefers-reduced-motion` replaces it with a 1px `{colors.border-structure}` border on **the row as well as any tile** — rows are included because the wash applies to them too, and `border-subtle` at 1.34:1 would have made the reduced-motion encoding *less* legible than the one it replaced.

---

## SURF-04b — Decision Record detail

**Reached from:** any banner on SURF-04, or `Enter` on a banner. **Presentation:** side panel, `{rounded.lg}`, over a 60% `{colors.surface-sunken}` scrim. **Modal depth:** capped at one — a panel, never a dialog on top of a dialog.
**PRD basis:** FR-24, §6 in full, NFR-4, NFR-11.

### SURF-04b.1 What it shows that the banner does not

The banner has three content slots. This panel is where the other eight §6.1 fields become fully legible, and it is the surface the module's explainability claim actually rests on.

| Field | Rendering |
|---|---|
| `decision_id` | `{typography.mono-data-lg}` at the top — the handle the reader quotes, in the one of three places that face is permitted. |
| `decision` | `{typography.mono-label}` eyebrow, with group glyph and group word, exactly as on the banner. |
| `summary` | `{typography.body}`, full text, selectable. |
| `citations` | The full list as **plain selectable text**, one per line, `{typography.mono-label}`, unabbreviated — no ellipsis, no chip-only presentation. This is where a citation becomes copyable in full, and it is why the 19.4px chip height is acceptable. |
| `transition` | The §4.2 transition id when present, `mono-data`. **When null the field renders nothing — never a dash, never an inferred value.** Non-transition records are reconciliation, disk pressure, queue-full refusal and Cordon Requests (F-23), and this panel is where the reason for the absence is stated. |
| `job_id`, `node_id` | `mono-data`; each shows the raw value **and**, for `node_id`, the VRAM class and the exclusion reason when one applies. Null renders as prose, never a dash. |
| `sim_timestamp` | `mono-data` with its **explicit timezone offset**. §7.1 requires every persisted timestamp to be a Daemon Timestamp plus an offset so a 24-hour simulated run is reproducible and diffable. |
| `actor_id` | Resolved display name **and** the raw `actor_id`, side by side (NFR-11). Resolution failure shows the raw value alone. |
| `inputs` | A `data-table` of the evaluated values — Effective Priority, Consecutive Nights Missed, Granted Priority, VRAM class, elapsed runtime, remaining budget — as the **trace of the summary**, not a raw JSON payload. |
| `supersedes` | A link to the predecessor record, or nothing. |
| `reason` | The mandatory reason code in `{typography.mono-label}` (§6.4), when the transition carries one. |

### SURF-04b.2 The F-1 assertion, shown

Because this panel is where a reader checks the contract, the citation block states which class of rule the record rests on, derived from the citations themselves and never from a separate flag:

- at least one **non-`self:`** citation present → *"Cites a delegated authority."*
- only `self:` citations **and** the reason is a module-owned rule — scope boundary, Max Night Span, queue cap, Job Spec validation, or a Retention Deadline expiry → *"Module-owned rule; `self:` alone is permitted (F-1)."*
- only `self:` citations on a `PREEMPT` or `EVICT` → **this combination is a contract violation.** FR-24(b) makes the emitter refuse such a record and the transition not be applied, so a record in this state cannot exist; if one is ever rendered, the panel reports it as an `EMITTER_REJECTED` integrity event rather than as a valid decision. Fail-closed is a **success** state and the panel says so (SURF-05).

### SURF-04b.3 States

| State | Specification |
|---|---|
| **Loading** | Panel skeleton at final height. Never a spinner inside a panel. |
| **Empty** | Not applicable — a record reference that resolves always has the eleven fields. |
| **Error** | Unresolvable `decision_id` → `No such decision_id.` and a return to SURF-04, focus restored. |
| **Success** | All fields resolved, citations selectable. |
| **Integrity** | Where a record is a fail-closed refusal, the panel states: *"`EMITTER_REJECTED` — the transition was not applied. Citation completeness is a precondition of every record (FR-24(b))."* |

### SURF-04b.4 Accessibility

- `role="region"` with an accessible name carrying the `decision_id`; heading level below the job title so the landmark outline stays flat.
- Focus moves into the panel on open and returns to the originating banner on `Esc`, at the preserved scroll offset.
- The citation block is a selectable text region, not a list of images, and the raw `actor_id` is real text rather than an `aria-label` — the resolution must be auditable (NFR-11).
- **No credential ever appears in this panel** (FR-31(f), NFR-11): no token, key or bearer string in any field, and no personal name beyond the persona display fixtures of §2.
