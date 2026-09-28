# 02: Ines Watches the Night Get Decided — Annex Scenario 2: Night Window Activation (22:00)

**Project:** Proyecto final — Module 9, Night Training Scheduler
**Created:** 2026-09-28
**Method:** WDS Phase 3 (UX scenario outline), trigger document = `planning/prd.md`
**Journey:** UJ-2
**State path:** `QUEUED_PENDING_WINDOW` → `RUNNING`
**Design references:** `ux/DESIGN.md` (theme, tokens, component specs) · `ux/EXPERIENCE.md` (IA, state patterns, keyboard model)

> **Trigger-document substitution.** WDS Phase 3 normally derives scenarios from a Trigger Map produced in Phase 2. No Trigger Map exists for this project — Phases 1 and 2 were never run. The substitute is `planning/prd.md`, which supplies the same three things a Trigger Map would: named personas (§2.1), stated jobs-to-be-done, and a success-metric set (§13). See Open Question S2-Q1.

---

## Transaction

**What this scenario covers:** The Night Daemon Controller wakes at 22:00:00, decides the night in public, and the operator watching the board can see every placement, every idle slot and the rule behind both before the work has finished starting. This is the module's fairness moment: an eight-hour window is shorter than most thesis-scale fine-tunes, so *which* jobs get tonight is the decision that determines whether anyone finishes.

---

## Business Goal

**Goal:** No operator has to take the scheduler's word for it. Every placement carries the rule that ranked the job, and every slot that stayed idle carries a reason — so a contested outcome is answerable in one citation rather than a week of archaeology.

**PRD objective reference:** `SM-3` (Night utilisation — mean occupancy of Eligible GPU slots across 22:00:00–05:45:00 ≥ 85% over 30 nights) · `SM-4` (No starvation — maximum `Consecutive Nights Missed` ≤ 4, which holds only if Starvation Promotion fires) · `SM-5` (Explainability)

---

## User & Situation

**Persona:** Ines Okonkwo, GPU lab operations engineer. *(§2.1; role disclosure F-33 — team-added, not named in the Annex.)*

**Situation:** Night shift. The lab is dark and she is alone with 32 machines whose state she is accountable for in the morning. She has been watching the fleet idle all day and knows exactly how much work is queued and against what.

**Trigger:** 21:59:50 campus local time. Ten seconds to activation.

**Hope:** See the night's plan before it executes, and be able to defend any single placement in the morning without rebuilding the Admission Order from scratch.

**Worry:** A board that shows 33 released slots and tells her nothing, because silence and success look identical at 07:00 — and one of them is a lie.

> **Driving forces addressed**
> - ✅ *Want* (§2.1): "I need to know at 07:00 that every GPU is released, and I need to know which node is suspect and why."
> - ❌ *Fear*: A contested placement she cannot explain to a student. The alternative to a checkable decision is a support burden she carries personally.
> - ✅ *Want* (§2.1, the daemon's counterpart): "I must be able to justify every state transition I cause, from a source another system can be asked to confirm." The Night Daemon Controller is a first-class persona here, not a background process.

---

## Device & Starting Point

**Device:** Desktop, dark-first. Ines opens the board at 21:59:50 and it is dark because she works nights (UJ-2). The three-region frame is fixed: a persistent `<header role="banner">` status strip, a `<nav>` left rail, and a `<main>` work region.

**Entry:** She is already on the Board — the console default route. The **Activation panel is on the Board from 21:59:00**, not only behind `g a`. UJ-2 wants the night's plan visible *before* it executes, and the blocked case (FR-8(e)) was already on the board while the normal case was one keystroke away — an odd priority for a failure state.

---

## Best Outcome

**User Success:** Every Eligible Node is either running an attributed job or explicitly shown as idle with a stated reason. There is no blank slot anywhere on the board. The board shows 22 job assignments, each with a citation, and a "next decision point 05:45:00" marker.

**Business Success:** 22 placements from a 22-job Pending Set against a 33-slot fleet, in an Admission Order that is **byte-identical across 10 consecutive runs** of the same seed (FR-8 testable condition) — so the night's fairness is reproducible, not merely observed. Every placement's `ADMIT` Decision Record names the granted-priority source that ranked the job, `node-state:M3/…` for the chosen Node, and `reservation:M4/…` when a reservation was consulted.

---

## Shortest Path

1. **Status strip + Board** — 21:59:50. The status strip carries daemon connection state, the last-received-update `sim_timestamp`, the simulated clock in `{typography.mono-data-lg}` with its explicit UTC−05:00 offset, the rate control, and a countdown to the next decision point. The Board shows 33 slot tiles idle, **each carrying a reason**, and the board header roll-up reads `33 slots · 0 held · 0 reserved · 0 draining · 0 cordoned · 33 idle`.
2. **Activation panel** — 21:59:00. The panel appears on the Board carrying the pre-verification result: every resuming job's SHA-256 digest re-verified inside the §7.5 budget, worst case all 33 slots within 29 minutes from 21:30:00. The simulated clock is jump-to-instant capable at 21:59:00 and 05:44:00 as one-key presets.
3. **Board** — 22:00:00. Window Activation runs: filter to Eligible Nodes, compute each pending job's Effective Priority, apply Starvation Promotion, build the Admission Order, place jobs. The board repaints. `ws-gpu-07` goes to `running` carrying Kavita's job, and the reason panel names the rule that put it there.
4. **Board + Admission Order** — 22 placements, each with a citation. Every remaining slot shows its exclusion reason. The status strip shows "next decision point 05:45:00". ✓

> **What the board displays versus summarises, and why.** FR-25(b) requires the citation list rendered "for any decision it displays". Rendering 22 full cited records inline is neither possible at the 28px row density nor useful, and pretending to is how a citation list quietly disappears. So: the board **displays** the citation list for the decisions it renders as a banner, and the Admission Order **summarises** the remaining placements one line each. The rule that decides which is which is FR-24's — a decision shown to a user must be checkable, and a decision that is summarised rather than displayed is not shown.

---

## Requirement Traceability

### Primary — `planning/prd.md` §14 row 2

| FR | What it constrains in this scenario |
|---|---|
| **FR-8** | Perform Window Activation. Admission Order computed before any placement and deterministic; no GPU slot receives more than one Training Job per Night Window; activation is idempotent; blocked activation re-attempts every 5 simulated minutes until 04:00:00. |
| **FR-12** | Compute the Eligible Node set. Four exclusion rules, re-evaluated immediately before each placement. |
| **FR-13** | Select the Node. Prefers the prior Node when Eligible; otherwise lowest current **slot**-allocation count, ties by Node identifier ascending; records the candidates considered and the deciding rule. |

### Supporting

| FR / NFR | Bearing |
|---|---|
| **FR-9** | Reconcile a missed Night Window. See NP-2.6. |
| **FR-10** | Daemon Clock authority and drift detection. See NP-2.5. |
| **FR-11** | Advance simulated time without quantizing events. Rate change is pacing only. |
| **FR-14** | Compute Effective Priority. `AGING_RATE = 6`, `AGING_CAP = 30`. |
| **FR-15** | Apply Starvation Promotion. `STARVATION_NIGHTS = 3`, `STARVATION_PROMOTION_LIMIT = 4`. |
| **FR-24** | Emit a cited Decision Record for every transition. |
| **FR-28** | Control simulated time. Rates 1×, 60×, 360×, 1440× plus pause. |
| **FR-29** | Inject Simulation Faults deterministically. |
| **NFR-1** | Single time authority — no component outside the Daemon Clock reads wall-clock time. |
| **NFR-2** | Admission Order latency — ≤ 200 ms p95 for 500 pending jobs, excluding Checkpoint hashing. |
| **NFR-8** | Every resume in the fleet fully verified by 21:59:00. |
| **NFR-9** | State visibility ≤ 500 ms real time at **every** Fast-Forward rate. |
| **NFR-14** | Invariant S-1 — zero Node allocations held at any instant ≥ 06:00:00 and < 22:00:00. |
| **NFR-15** | Accessibility. |

### State machine

| Transition | From → To | Decision | Reason | Citations (§6.4) |
|---|---|---|---|---|
| **T-3** | `QUEUED_PENDING_WINDOW` → `RUNNING` | `ADMIT` | — | the granted-priority source that ranked the job (`policy:M2/…` or the administrator's grant record); `node-state:M3/…`; `reservation:M4/…` when consulted |
| **T-4a** | `QUEUED_PENDING_WINDOW` → `QUEUED_PENDING_WINDOW` | `DEFER` | `NO_ELIGIBLE_NODE` | `node-state:M3/…`, `reservation:M4/…` — the per-Node exclusion reasons (FR-12) |
| **T-4b** | `QUEUED_PENDING_WINDOW` → `QUEUED_PENDING_WINDOW` | `DEFER` | `CAPACITY_EXHAUSTED` | `node-state:M3/…` (the Eligible slot count); `policy:M2/…` (the ranks that placed this job outside the free slots) |
| **T-12** | `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW` | `RESUME` | — | `self:CHECKPOINT-QUARANTINE-v1` (digest re-verified at pre-verification); `node-state:M3/…` (the chosen Node) |

**States reached:** `QUEUED_PENDING_WINDOW` (entry) · `EVICTED_RESUMABLE` (pre-verification entry) · `RUNNING` (outcome).
**Slot states reached:** `available` · `reserved` · `cordoned`. (`running` and `draining` are reached in scenarios 3 and 4.)
**Decisions reached:** `ADMIT`, `RESUME`, `DEFER`, `FAIL` (in the non-happy paths).
**Screens:** Status strip · Board · Activation panel · Admission Order · Pending Set · Job detail · Node detail · Decision Record detail · Event log · Simulation run panel.

---

## Scenario Steps

### Step 1 — 21:59:50, the board before anything happens

- **Status strip** (always mounted, never unmounts): daemon connection state · last-received-update `sim_timestamp` · the simulated clock in `{typography.mono-data-lg}` with its explicit timezone offset · the rate control · the countdown to the next decision point.
- **The clock is always visible and always labelled.** The board runs at up to 1440×, and an operator must never be unsure whether they are reading simulated or wall-clock time. Because the offset is displayed, a simulated instant can never be confused with a wall-clock one. No component reads wall-clock time directly (NFR-1).
- **Board layout, and why it does not scroll horizontally:** 33 tiles at 44 px is 1452 px, which already exceeds a 1440 px viewport before a single gap and before the left rail. A board whose right edge is off-screen cannot answer "are all GPUs released" — the first thing Ines checks at 07:00. The board therefore wraps into labelled rows of slots, and the tile keeps a 44 px *height* floor with no width floor.
- **Board header roll-up — always mounted, above the slot grid:** `33 slots · N held · N reserved · N draining · N cordoned · N idle`. Counts are computed **per slot and never per node** — the roll-up is the aggregate of the same per-slot data the tiles show, so a wrong roll-up would be a wrong board.
- **Every idle slot carries a reason. This is unconditional, in and out of the Night Window.** FR-25(d) says the board shows idle Nodes with a reason and never a blank, with no time qualifier, and 06:00–22:00 is exactly when Ines walks the lab at 07:00. Only the **fleet-level sentence** is conditional:

  | Window | Roll-up sentence | Per-slot reason |
  |---|---|---|
  | Outside (06:00:00–22:00:00) | "All 33 GPU slots released. Night Window opens at 22:00:00." | `FREE` |
  | Inside, no Eligible Node | every slot idle | `NO_ELIGIBLE_NODE`, or a Module 2 `freeze` cited |

  A night that admits zero jobs must never look like a rendering failure. The roll-up is a summary over a constant invariant, not an alternative to it: **the sentence is a roll-up, the reasons are the data.**

### Step 2 — 21:59:00, pre-verification completes and the Activation panel arrives

- **§7.5 / F-16 / NFR-8:** the pre-verification phase runs from **21:30:00**. Each resuming job's recorded SHA-256 digest is recomputed from its Checkpoint bytes — the same integrity step used at intake. The phase is budgeted absolutely: **every resume in the fleet is fully verified by 21:59:00**, worst case all 33 GPU slots within 29 minutes.
- **Because hashing happens here, Window Activation never hashes.** NFR-2's admission-order budget explicitly excludes Checkpoint digest hashing, which moved to this phase with its own NFR-8 budget.
- **The Activation panel** appears **on the Board**, carrying the computed plan: the Admission Order about to execute, the Eligible Node set, and the per-Node exclusion reasons for everything excluded. It is present before 22:00:00, not after — UJ-2 wants the plan visible *before* it executes.
- **Jump-to-instant:** 21:59:00 and 05:44:00 are one-key presets alongside free entry, because those are the two instants an operator actually needs. A jump drains every transition at or before the target instant **before rendering** (FR-28(c)) — the board is never shown mid-drain, because a half-applied window is exactly the state an operator would misread.

### Step 3 — 22:00:00, Window Activation, observed live

Five operations, in the order FR-8 fixes, all visible on the board as they happen:

1. **Filter to the Eligible Node set** (FR-12). A Node is not Eligible with a Module 3 fault, a `SchedulingDisabled` condition, or an outstanding Cordon Request from this module; a Node whose reservation interval overlaps the Night Window is not Eligible **for the whole window**; a Node whose VRAM class is below the Job Spec's requirement is not Eligible for that job. Eligibility is **re-evaluated immediately before each placement**, so a fault arriving mid-activation is honoured.
2. **Compute Effective Priority** (FR-14). `Granted Priority + min(Consecutive Nights Missed × AGING_RATE, AGING_CAP)`, with `AGING_RATE = 6` and `AGING_CAP = 30`. Granted Priority is `EXPLORATION` = 10, `THESIS` = 50, `URGENT` = 90, read-only to this module. A student's self-declared intent **never contributes**.
3. **Apply Starvation Promotion** (FR-15). A job with `Consecutive Nights Missed ≥ 3` moves to the head of the Admission Order, at most 4 per window, tie-broken on submission time. **Promotion confers no authority to preempt** — starvation is fixed by admission order, not by killing a thesis run.
4. **Build the Admission Order** (FR-8(a)). Computed *before* any placement, and deterministic.
5. **Place jobs** (FR-13). Prefer the job's prior Node when Eligible and its VRAM class or slot matches, because resuming elsewhere invalidates local SSD cache locality. Otherwise select the Eligible Node with the lowest current **slot**-allocation count, ties by Node identifier ascending. The Decision Record names the two or three candidates considered and the rule that decided it.

**`server-gpu-01` is a paired tile with a shared node header above both slots.** F-42 fixes the fleet at 32 Nodes and **33 GPU slots** — 31 workstations at 24 GB each plus two 48 GB slots on the server. The two slots render independently, because a job on slot 0 and a reservation on slot 1 are genuinely different facts and a single per-node badge would have to lie about one of them. `server-gpu-01` may host up to two 1-GPU jobs or one 2-GPU job (FR-8(c)).

**`ws-gpu-07` goes to `running`, carrying Kavita's job.** The tile shows its ordinal, its state glyph, its state label, and the `job_id` at `{typography.mono-data}` truncated to 8 characters with the full value in the accessible name and the tooltip. The reason panel names the rule that put it there. This is T-3, decision `ADMIT`, citing the granted-priority source that ranked the job, `node-state:M3/…` for the chosen Node, and `reservation:M4/…` where a reservation was consulted.

**`PRIOR_NODE_INELIGIBLE`** appears in the Decision Record when a resuming job cannot return to its prior Node — a `reason-panel` code, never a slot colour.

**`VRAM_CLASS_INSUFFICIENT` is deliberately absent from the slot vocabulary.** It is not a node-global state: a 48 GB slot is `available` to a job requesting 24 GB and insufficient for one requesting 64 GB. It renders as a per-job exclusion reason on the placement panel, never as a slot colour. Painting a healthy 48 GB slot red because one job cannot use it would make the board lie about the other 32.

### Step 4 — the board after activation ✓

- **22 placements**, each with a citation. Every remaining slot shows its exclusion reason. The status strip shows "next decision point 05:45:00".
- **The Admission Order view** renders the deterministic ordering as a read-only list: rank, `job_id`, `effective_priority` with its granted/aged decomposition, `admitted_nights` against `max_night_span`, and the Starvation Promotion annotation where it applied.
- **Fully keyboard-operable** — NFR-15 names this view specifically. `↑`/`↓` move, `Home`/`End`/`PgUp`/`PgDn` traverse the virtualised list, `Enter` opens the focused row.
- **Focus follows the `job_id`, not the row position.** The order is the daemon's rank output, so a recompute genuinely re-ranks. A reader left on DOM position 3 after a re-rank is looking at a different job than the one that was announced. Focus re-resolves to the same `job_id` at its new rank and announces the new rank. The list never animates a re-rank under the cursor, and drag-to-reorder is banned — the order is the daemon's deterministic output, and letting a user rearrange it would misrepresent a computed artefact as a preference.
- **The climax, stated as the PRD states it:** all Eligible Nodes are either running an attributed job or explicitly shown as idle with a stated reason. **There is no blank slot anywhere on the board.**

---

## Non-Happy Paths

Nine. Activation has the deepest failure surface in the module because it is the one moment where a *missing* input — a verdict, a healthy node, a free slot — must not silently become an empty fleet.

### NP-2.1 — The Eligible Node set is empty (T-4a)

- **Trigger:** no Eligible Node exists at 22:00:00 — every Node cordoned, faulted, reserved, or of insufficient VRAM class for the queued work.
- **Outcome:** the job **stays** `QUEUED_PENDING_WINDOW`. Decision `DEFER`. Reason `NO_ELIGIBLE_NODE`. Citations `node-state:M3/…` and `reservation:M4/…` — the per-Node exclusion reasons.
- **Rendering:** every slot shows its exclusion reason, and the fleet-level sentence says so. §5 states the behaviour when Module 3 is unavailable: treated as not-Eligible, no placement. **The module never invents an ALLOW.**
- **Contrast with success:** 22 placements and a zero-placement night produce the same tile geometry. The difference must be in the reason strings, or a zero-admission night is indistinguishable from a rendering failure.

### NP-2.2 — Eligible capacity exhausted (T-4b)

- **Trigger:** Eligible Nodes exist, but the job's rank exceeds the number of free Eligible GPU slots.
- **Outcome:** stays `QUEUED_PENDING_WINDOW`. Decision `DEFER`. Reason `CAPACITY_EXHAUSTED`. Citations `node-state:M3/…` (the Eligible slot count) and `policy:M2/…` (the ranks that placed this job outside the free slots).
- **The distinction that matters (T-3 vs T-4b):** the machine-checkable guard is *the job's rank in the Admission Order ≤ the number of free Eligible GPU slots at activation*. A job deferred for `CAPACITY_EXHAUSTED` was outranked; a job deferred for `NO_ELIGIBLE_NODE` was blocked by the fleet. These are different facts about a different night and the two reason codes keep them apart.
- **Visible consequence:** its Pending Set position and its `Consecutive Nights Missed` increment at the end of the window, which feeds FR-14 and eventually FR-15's Starvation Promotion. The surface shows the ageing, so the next night has an explanation.

### NP-2.3 — Activation blocked by a missing verdict (FR-8(e))

- **Trigger:** a delegated verdict is absent at 22:00:00.
- **Outcome:** activation **re-attempts every 5 simulated minutes until 04:00:00**, and **each attempt is recorded as a Decision Record with the block reason cited** — a `DEFER` whose `reason` is the block reason and whose citation names the missing authority, e.g. `policy:M2/…` or `catalog:M5/…`.
- **The Module 2 freeze is re-evaluated at every attempt, not cached for the night.** A freeze lifted since the last attempt is the other trigger; the next re-attempt admits.
- **Rendering:** the board shows the block, the next attempt instant, and the citation. **It does not show an empty fleet with no explanation** — this is the single most expensive rendering failure in the module, because 22 queued jobs and a blocked daemon look identical otherwise.
- **Contrast with the success path:** the Activation panel was already on the Board from 21:59:00 for the *normal* case and the blocked case both. An odd priority for a failure state if it were otherwise.

### NP-2.4 — Emergency compute freeze active (FR-6(c))

- **Trigger:** Module 2 reports a `freeze` state.
- **Outcome:** Window Activation **admits zero jobs** and every Eligible Node is reported idle **with the freeze cited**. This is Module 2's emergency exception to the hard temporal constraint, and this module consumes the state and computes nothing.
- **Citation discipline:** this is a `DEFER`, and a `DEFER` is in the adverse banner group. The freeze is a delegated verdict, so the record names `policy:M2/…` — it is not a module-owned rule and cannot cite `self:` alone.
- **Rendering:** the board's fleet-level sentence is the conditional one from step 1, and the per-slot reasons cite the freeze. 22 queued jobs and a deliberate institutional freeze must not read the same way.

### NP-2.5 — Daemon Clock drift latched (FR-10)

- **Trigger:** drift beyond 1 s between the Daemon Clock and the host clock, checked at 1 Hz.
- **Outcome:** a **latched fault that blocks the next Window Activation**. It clears only when drift is within tolerance for **3 consecutive checks**. Decision Records are emitted on each transition of the fault.
- **Rendering:** the Activation control is **disabled** and a banner names the fault. **The board does not silently skip the 22:00 window** — a board that shows 33 idle slots at 22:05 with no explanation is indistinguishable from a clean skip.
- **Framed correctly in the copy:** the order is *not stale* — **it does not exist yet**. "Stale" implies there is an old answer to distrust; there is no answer at all.

### NP-2.6 — The daemon was down across the 22:00 activation (FR-9)

- **Trigger:** the daemon crashed at 21:00 and restarted at 22:30.
- **Outcome, two distinct steps that must not be merged:**
  1. **Restore (T-18).** State is restored from the durable decision log with **no replay of any transition**. Job states are `unchanged`. The record carries decision `DEFER`, reason `DAEMON_RESTORE`, citation `self:RECONCILIATION-v1` — restoration makes **no new decision** and defers everything to the reconciliation step.
  2. **Reconciliation (FR-9(b)–(d)), a separate recorded step.** The daemon computes whether any activation instant elapsed while it was not running. The Night Window is still open at 22:30, so activation is performed immediately with a Decision Record citing `self:RECONCILIATION-v1` — non-transition record, decision `ADMIT`, reason `RECONCILIATION_ACTIVATION`, plus the FR-8 sequencing inputs. **Exactly one** reconciliation Decision Record results.
- **The variant:** crashed at 21:00, restarted at 07:00 — the Night Window has also closed, so the missed window is recorded as `DEFER` / `MISSED_WINDOW` / `self:RECONCILIATION-v1` and **zero jobs are admitted**.
- **The rendering rule this creates:** the board says "last night's window was missed" **in the same place it would have said it succeeded**. A board showing 33 released slots after a skipped window is indistinguishable from a clean dawn — and FR-14(d) ageing quietly changes the Admission Order behind that.

### NP-2.7 — A resume was not fully verified by 21:59:00 (FR-20(f))

- **Trigger:** the pre-verification phase is still running on a job's digest at 21:59:00.
- **Outcome:** **the job is not admitted that night.** Recorded as a cited `DEFER` — non-transition record, decision `DEFER`, reason `UNVERIFIED_RESUME`, citation `self:CHECKPOINT-QUARANTINE-v1`. **A job is never admitted on an unverified resume.**
- **Why this is its own branch and not a variant of NP-2.3:** NP-2.3 blocks the whole activation; this admits 22 other jobs and defers one. The board shows 22 placements *and* a named job that did not make it, with its own reason.
- **Consequence to render:** the job waits a whole night for a hashing operation. That is the honest cost of never loading a Checkpoint that might be corrupt, and the surface should show the digest verification as the stated cause rather than leaving the job silently absent.

### NP-2.8 — The model was deprecated while the job waited (FR-6(d), T-21)

- **Trigger:** the Module 5 record shows deprecation at the Window Activation re-check.
- **Outcome:** the job transitions to `FAILED` **before any placement**. Reason `MODEL_DEPRECATED`. Citation `catalog:M5/…` — a delegated catalogue authority, so F-1 is satisfied and `self:` alone would not be.
- **Why the re-check exists:** so a queued job never wakes only to fail on first use. The failure is deliberately placed *before* the placement it would have wasted.
- **Rendering:** the `FAILED` badge with its reason code and citation, adjacent to a statement of the retained last verified Checkpoint per FR-22 and Invariant S-2. The terminal states take a 1px `{colors.border-structure}` ring; terminality is carried by the label and the ring, never by desaturation.

### NP-2.9 — Max Night Span exhausted at activation (T-19, FR-4(d))

- **Trigger:** the job's Admitted Nights has already reached 5 without reaching `COMPLETED`.
- **Outcome:** `FAILED`. Reason `MAX_NIGHT_SPAN_EXCEEDED`. Citation `self:MAX-NIGHT-SPAN-v1` — module-owned, so `self:` alone is legitimate under F-1. The retained Checkpoint is preserved, and the refusal Decision Record **names the step the job reached** so a human can decide whether to resubmit a reduced scope.
- **Invariant S-3 made visible:** a job is **refused admission rather than admitted and immediately evicted**. Span exhaustion must never manifest as a wasted night — so the job is not placed, does not hold a slot, and does not appear in the 22 placements.
- **Related guard:** FR-21(e) refuses a resume that *would* take Admitted Nights past Max Night Span, rather than waking a job from a verified Checkpoint only to evict it at dawn with nothing gained.

---

## Open Questions

**S2-Q1 — The trigger document is a PRD, not a Trigger Map.** Personas, jobs-to-be-done and success metrics come from PRD §2.1 and §13. If Phases 1 and 2 are ever run, re-anchor the Business Goal and Driving Forces to the real objective ids.

**S2-Q2 — The board has no viewport, and the AA claim depends on one.** FR-1's word "desktop" qualifies the *submission* surface only. Nothing in the PRD describes the status board's viewport, breakpoint or minimum size, yet FR-25 requires it to display 32 Nodes and 33 GPU slots and NFR-15 claims WCAG 2.1 AA. The desktop floor asserted for the console is a design decision; the SC 1.4.4 / SC 1.4.10 boundary that goes with it is a design decision. Below the floor the console renders a viewport notice rather than silently clipping, because a clipped operations board is worse than an honest refusal.

**S2-Q3 — A simulation run is `RUNNING` then exactly one of `PASSED` or `FAILED`; the run panel is a separate authority.** FR-30(d) makes a `FAILED` verdict name **each** violated invariant individually — among S-1…S-3, NFR-4, NFR-5, NFR-6, NFR-7, NFR-10, NFR-14, NFR-16 — not as a count. NFR-1 and NFR-11 are build-time static checks and the latency NFRs (NFR-2, NFR-3, NFR-8, NFR-9) are measured by a separate benchmark harness, so the panel says they are **not** run-gated rather than showing them as passed. This is an activation-adjacent surface because `operator_action_schedule` is how a cordon gets cleared in a headless run; it is specified in the Simulation run panel, not in this scenario's path.

**S2-Q4 — `fault_schedule` has no authoring surface.** FR-29 makes the failure paths "demonstrable and repeatable" and FR-30 requires a `fault_schedule` on every `POST /simulations`, but no PRD surface creates one. The run panel renders the active schedule, the fault kind, the target and the Simulated Clock instant, plus a copyable request body — and states that authoring is API-only. An operator demonstrating a failure path to a marker therefore has to leave the console, which undercuts FR-29's stated purpose. (Carried from `EXPERIENCE.md` OQ-11.)

**S2-Q5 — The rate control's initial state is unstated.** FR-28(a) fixes the set; FR-11(c) establishes that a rate of 0 pauses without draining the queue, so pause is a real state rather than an absence of one. What a run *starts* at, and whether a rate survives a page reload mid-window, is unspecified. It is load-bearing here specifically because this scenario is the one an operator uses to watch a night: a board that opens at 1440× and one that opens paused are very different first impressions of the same activation.

**S2-Q6 — No in-app notification inbox in v1.** §5 routes FR-27 payloads to a local outbox so the v1 test harness can assert on delivery. The *content* is specified — job, outcome, last verified Checkpoint step, next eligible action — but where a human reads it in v1 is unstated, and `DELIVERY_FAILED` has no surface either. This scenario produces `ADMIT` records; whether any of them notify is FR-27's trigger list, which names Eviction, Preemption, Expiry, Checkpoint failure, cordon and resume — **not** admission.

---

## Page Specifications

> **Phase 4 — WDS UX design.** This file is the **canonical specification** for eight surfaces, per the registry in `ux/_progress/00-design-log.md` §2: **SURF-02** (Board), **SURF-02a** (daemon status strip), **SURF-02b** (clock control), **SURF-03** (Admission Order), **SURF-03b** (Pending Set), **SURF-05** (Event log), **SURF-09** (Activation panel), **SURF-10** (Simulation run panel). `scenario-1.md` owns SURF-04 Job detail and SURF-04b Decision Record detail; `scenario-3.md` and `scenario-4.md` add deltas to SURF-05 and reference SURF-04.
>
> Sources, in precedence order: `planning/prd.md` → `ux/EXPERIENCE.md` → `ux/DESIGN.md` → this section. Conventions are stated once in `scenario-1.md` § *Specification conventions* and are not repeated here.

### SURF-02.1 The three-region frame

```
<header role="banner">  status strip ·········································· SURF-02a
<nav>                   left rail — region selectors
<main>                  work region
                        ├ Board .............. SURF-02      (default route)
                        ├ Admission Order ... SURF-03
                        ├ Pending Set ....... SURF-03b
                        ├ Event log ......... SURF-05
                        ├ Activation panel .. SURF-09      (on the Board from 21:59:00)
                        └ Job / Node / Decision detail — scenario-1.md, scenario-3.md
```

- **The frame does not collapse.** No sheet, no drawer, no stacked column, at any width. `EXPERIENCE.md` Responsive is explicit.
- **The first focusable element on every route is a `Skip to work region` link.** Without it a keyboard user crosses the status strip and the rail — eight or more controls — on every route. That is SC 2.4.1 Bypass Blocks at Level A, and therefore already inside the AA claim NFR-15 makes.
- Tab order follows the three regions in reading order. The status strip is a landmark carrying connection state, last-update instant and the rate control.
- **Below the desktop floor the console renders a viewport notice rather than silently clipping**, because a clipped operations board is worse than an honest refusal. That notice does not satisfy SC 1.4.4 or SC 1.4.10, so the AA claim holds **at and above the stated floor only** — the floor being a design decision with no requirement behind it (**S2-Q2**).

### SURF-02.2 Board geometry

- **One tile per GPU slot, not per node** — 31 `ws-gpu-NN` tiles at 24 GB plus **two slots on `server-gpu-01` at 48 GB**, 33 in total (F-42, `A-4`).
- **No horizontal scroll, ever.** The arithmetic is the reason and it is worth stating: 33 tiles at 44px is 1452px, which already exceeds a 1440px viewport before a single gap and before the left rail. A board whose right edge is off-screen cannot answer *are all GPUs released* — the first thing Ines checks at 07:00. The board therefore **wraps into labelled rows of slots**, one row group per node, with a `{typography.mono-label}` node header above each group.
- The tile keeps a **44px height floor with no width floor** (`{components.node-slot-tile.size}`). As the tile narrows, the ordinal, glyph and state label stay on it; the `job_id` moves into the accessible name and the slot inspector, truncated to 8 characters visually.
- `server-gpu-01` renders as a **paired tile with a shared node header above both slots**. The two slots are visually independent inside the pair — slot 0 `running` and slot 1 `reserved` is a legal and common display, because the node is one machine and Ines reasons about the machine, while the slots are genuinely different facts.
- Row gap `{spacing.1}` (4px) within a node group, `{spacing.panel-gap}` (12px) between groups, `{spacing.gutter}` (16px) from the region gutter.
- Tiles reflow narrower; they never scroll.

### SURF-02.3 The slot composition rule

Two orthogonal attributes compose on every tile, because the PRD keeps them separate: **occupancy** (Invariant S-1 — which states hold a Node) and **eligibility** (FR-12 — why a Node is not Eligible). The rule, stated because it is the one a developer cannot guess:

> **Occupancy paints the tile. Eligibility adds a mark on it.**

A slot running a job that a Module 4 reservation has since taken is `running · reserved` — the `▶` and the `▨` both present, the tile coloured by occupancy, the eligibility carrying a corner badge and a word in the accessible name. A slot that is `draining` **and** `cordoned` renders both, and `cordoned` does not release the slot, because FR-23(c) keeps the Node not-Eligible while a job may still be draining on it.

| Slot state | Axis | Glyph | Label | Token |
|---|---|---|---|---|
| `available` | occupancy | `○` | available | `{colors.node-available}` |
| `running` | occupancy | `▶` | running | `{colors.node-running}` |
| `draining` | occupancy | `▼` | draining | `{colors.node-draining}` |
| `reserved` | eligibility | `▨` | reserved · M4 | `{colors.node-reserved}` |
| `cordoned` | eligibility | `⊘` | cordoned · ‹cause› | `{colors.node-cordoned}` |

- Four hues are deliberately shared across the two axes: `{colors.node-running}` = `{colors.state-running}`; `{colors.node-draining}` = `{colors.state-checkpointing}`; `{colors.node-reserved}` = `{colors.accent-hover}`. `{colors.node-cordoned}` is a brown held **deliberately apart** from `{colors.state-rejected}` red, so a cordoned *machine* is never mistakable for a refused *job* — the two appear on screen together. The container differs (a 44px tile versus a 20px badge) and the label differs in every case.
- **`VRAM_CLASS_INSUFFICIENT` is deliberately absent from this vocabulary.** It is not a node-global state: a 48 GB slot is `available` to a job requesting 24 GB and insufficient for one requesting 64 GB. It renders as a per-job exclusion reason in a `reason-panel` on the placement panel, **never as a slot colour**. Painting a healthy 48 GB slot red because one job cannot use it would make the board lie about the other 32.
- `draining` exists because scenarios 3 and 4 happen inside it. Between 05:45:00 and 05:53:00 a slot is still held by a job in `CHECKPOINTING`, and Invariant S-1 permits exactly that until 06:00:00. **A board that showed such a slot as `available` would be lying during the most safety-critical eight minutes of the night.**

### SURF-02.4 Board header roll-up

Always mounted, above the slot grid, and the direct answer to *are all GPUs free?*.

```
33 slots · 0 held · 0 reserved · 0 draining · 0 cordoned · 33 idle
```

- Counts are computed **per slot and never per node**. The roll-up is the aggregate of the same per-slot data the tiles show, so a wrong roll-up would be a wrong board.
- **Bucket precedence — design decision D-a (`ux/_progress/00-design-log.md` §5).** Each slot counts exactly once, in the order `held → draining → reserved → cordoned → idle`. A slot that is **idle and cordoned counts as `cordoned`**, so the operator sees the condition on the roll-up; its per-slot reason string still shows its occupancy. The PRD fixes the roll-up's *format* (step 1) but never says which axis wins when a slot carries both attributes. **Flagged for review** — the alternative is that an idle+cordoned slot counts as `idle`, which reads as a healthier board.
- **The roll-up is never the only place a count appears.** Every count it shows is also derivable from the tiles.

### SURF-02.5 Idle slots and the fleet-level sentence

**The per-slot reason is unconditional in both windows. Only the fleet-level sentence is conditional.** FR-25(d) says the board shows idle Nodes with a reason and never a blank, with no time qualifier — and 06:00–22:00 is exactly when Ines walks the lab at 07:00. An earlier draft made the reason appear only inside the Night Window, which handed the operator one reassuring sentence and 33 reasonless tiles at the one moment she needs per-slot evidence.

| Window | Fleet-level roll-up sentence | Per-slot reason |
|---|---|---|
| Outside — 06:00:00–22:00:00 | `All 33 GPU slots released. Night Window opens at 22:00:00.` | `FREE` |
| Inside, no Eligible Node | *(conditional sentence withheld)* | `NO_ELIGIBLE_NODE`, or a Module 2 `freeze` cited |

**The two are a summary over a constant invariant, not alternatives: the sentence is a roll-up, the reasons are the data.** A night that admits zero jobs must never look like a rendering failure.

**Exclusion reason codes, verbatim** (`EXPERIENCE.md` Reason panel): `M3_CORDONED`, `M4_RESERVED`, `VRAM_CLASS_INSUFFICIENT`, `NO_ELIGIBLE_NODE`, `CAPACITY_EXHAUSTED`, `PRIOR_NODE_INELIGIBLE`. Each renders in a `reason-panel` as the code at `{typography.mono-label}` plus one human sentence — the component that makes FR-25(d) expressible.

**`reserved` is a Node-level fact applied to every slot of that Node**, so both slots of `server-gpu-01` go `reserved` together. F-42's per-slot independence governs job *occupancy*, not an eligibility rule the PRD states at Node granularity (FR-12(b): a Node whose reservation interval overlaps the Night Window is not Eligible **for the whole window**).

### SURF-02.6 Board banners

All are `decision-banner` instances at the SURF-04.6 anatomy, mounted above the slot grid. **All render `summary` and the full `citations` list; only visual weight differs.**

| Banner | Condition | `reason` | Citations | Group |
|---|---|---|---|---|
| **Missed Night Window** | the daemon was down across a 22:00:00 activation, or a latched drift fault (FR-10) skipped one | `MISSED_WINDOW` or `DAEMON_RESTORE` | `self:RECONCILIATION-v1` | adverse |
| **Blocked activation** | FR-8(e) — a delegated verdict is missing, or a freeze was lifted since the last attempt | the block reason, named | the missing authority — `policy:M2/…`, `catalog:M5/…` | adverse |
| **Emergency freeze** | FR-6(c) — Module 2 reports a `freeze` | the freeze state | `policy:M2/…` — a delegated verdict, so `self:` alone is **not** permitted | adverse |
| **Latched clock drift** | FR-10 — drift beyond 1 s, 1 Hz check | the drift fault | the drift rule | adverse |
| **Checkpoint store pressure** | NFR-13 / FR-22(d) — store over `CHECKPOINT_STORE_BUDGET` | `DISK_PRESSURE_ESCALATION` | `self:CHECKPOINT-STORE-BUDGET-v1` | adverse |

**The Missed Night Window banner renders in the same place the board would have said activation succeeded.** A board showing 33 released slots after a skipped window is indistinguishable from a clean dawn, and FR-14(d) ageing quietly changes the Admission Order behind that. It states the missed window and the next attempt.

**The blocked-activation banner must not be an empty fleet with no explanation** — this is the single most expensive rendering failure in the module, because 22 queued jobs and a blocked daemon look identical otherwise. It carries the block, the **next attempt instant** (every 5 simulated minutes until 04:00:00, FR-8(e)) and the citation naming the absent authority. **A freeze lifted since the last attempt is re-evaluated at every attempt, not cached for the night** (FR-6(c)), and the next re-attempt admits.

**The frozen-night rendering.** Activation admits **zero** jobs and every Eligible Node is reported idle **with the freeze cited**. 22 queued jobs and a deliberate institutional freeze must not read the same way; the per-slot reasons carry `policy:M2/…` and the fleet sentence is the conditional one from SURF-02.5.

**The drift banner disables the Activation control and names the fault. It does not silently skip the window** — a board showing 33 idle slots at 22:05 with no explanation is indistinguishable from a clean skip. Framed correctly: the order is **not stale — it does not exist yet**. "Stale" implies there is an old answer to distrust; there is no answer at all. It clears only when drift is within tolerance for **3 consecutive checks**, and that condition is stated on the banner so the operator knows what the wait is for.

**Freeze versus unreachable — the distinction Ines must be able to make at a glance:**

| | Module 2 `freeze` | Daemon unreachable |
|---|---|---|
| What it is | a **cited decision** | a **transport fault** |
| Counts | current | last-known, **visible and marked stale, never blanked** |
| Copy | `Emergency compute freeze — 0 jobs admitted. freeze cited.` | `Daemon unreachable — data may be stale. Last update ‹instant›.` |
| Controls | enabled | `aria-disabled="true"`, **not dimmed** |

**Store pressure is a capacity banner on the board, not an error.** The same fact is a refusal to a submitter (SURF-01.4) and a capacity notice to an operator. The PRD names no surface for store pressure, so this placement is a design decision (**S1-Q4**, **S2-Q3**), and the banner states the escalation is in flight rather than implying a human action the console does not offer.

### SURF-02.7 Board — Loading · Empty · Error · Success

| State | Specification |
|---|---|
| **Loading** | 33 **outlined placeholders at final geometry** — never a spinner over a blank field, because layout shift during a Fast-Forward drain is disorienting. The queue panel shows skeleton rows at `{spacing.row-dense}`. |
| **Empty** | Two distinct empties that mean opposite things, per SURF-02.5: *fleet idle outside the Night Window* (the reassuring sentence) and *fleet idle inside it* (every slot carrying `NO_ELIGIBLE_NODE` or a cited `freeze`). |
| **Error** | `Daemon unreachable — data may be stale` with the last-received-update `sim_timestamp`, controls `aria-disabled` but **not dimmed to 40%** — at that opacity `{colors.text-secondary}` composites to 2.40:1, and a control the operator cannot read is the vanished control this design refuses to create. Automatic retry. **No slot, badge or counter updates while in this state**; last known values stay visible and marked stale, because the surface must never imply the fleet changed while data was stale. This is a **UI state, not a job state** — no job or node state is added and the PRD needs no amendment. |
| **Success** | The board settles with **no flash and no celebratory treatment**. The success signal is the countdown marker and the tiles reaching their terminal state. The single permitted change animation is a 120 ms background wash on the changed tile; `prefers-reduced-motion` replaces it with a 1px `{colors.border-structure}` border on **the tile and the row**. |

### SURF-02.8 Board — accessibility

- `role="grid"` with **one row per Node and one cell per GPU slot**, so `server-gpu-01` is announced as two slots of one node and is reachable with `←`/`→` — the only way to reach slot 1 from slot 0. Roving `tabindex`, so the grid is **one tab stop**.
- **Each cell's accessible name is `‹node_id› slot ‹n›, ‹occupancy label›, ‹eligibility label if any›, ‹job_id or reason›`** — four fields, because a name that can hold only one attribute is a name that lies. For a slot held by another submitter's job the last field reads `occupied by another job` with **no identifier at all** (FR-31(b)). A `‹cause›` string on a cordoned slot is included unabbreviated.
- Every state glyph carries `aria-hidden="true"` — in the grid, in the `status-badge` and in the clock control. A `⚡` announced as "high voltage" and a `⏸` announced as "check mark button" are worse than no glyph, and the label is already carrying the meaning.
- `↑`/`↓` move between tiles; `Home`/`End`/`PgUp`/`PgDn` traverse; `Enter` opens **Node detail**; `g n` operates on the focused tile.
- **WCAG 2.1 AA.** Every one of the 5 slot states carries colour **and** glyph **and** text label. `{colors.border-structure}` on the tile edge — 3.96:1 on base, 3.63:1 raised, 3.30:1 overlay (design log §4 conflict 1) — because an operator scanning for one cordoned slot at 05:44 needs an edge that is actually there.

---

## SURF-02a — Daemon status strip

**Mounted on every route. Never unmounts. Never hides its control cluster on disconnect.** Persistent, full-width, `<header role="banner">`, `{typography.mono-label}`.

| Field | Spec |
|---|---|
| **Daemon connection state** | `{components.daemon-status-strip}`. Reachable: `{colors.text-secondary}`. Unreachable: `{colors.ui-adverse}` at label weight — a **dedicated token**, because borrowing a job-state hue would make a *connection* problem look like an `EVICTION_FAILED` *job*. |
| **Last-received-update `sim_timestamp`** | `{typography.mono-data}` with explicit offset. Persists while unreachable; that is the point of it. |
| **Simulated clock** | `{typography.mono-data-lg}` — one of exactly three permitted uses of that face. **With its explicit UTC−05:00 offset**, so a simulated instant can never be confused with a wall-clock one. `aria-live="off"` per tick, readable on demand. |
| **Rate control** | SURF-02b. |
| **Countdown to next decision point** | `05:45:00` after activation. `aria-live="off"` per tick. **It stops at 05:53:00 and stays visible** — no time-limited content anywhere in this console. |
| **A-3 simulation disclaimer** | Un-dismissable, in the strip. The honesty constraint is global: v1 models no real GPU, no container execution, no telemetry and no model weights. |
| **Run panel entry** | `LAB_ADMIN` only — SURF-10. |

**Live regions are scoped to the smallest stable node**, and the reason is quantitative: `aria-live` on the whole strip would announce every child mutation, and politeness controls interruption priority, **not announcement rate** — so a region changing many times per second at 1440× still queues many utterances and drowns the assertive channel. Therefore: the per-tick clock and countdown are `aria-live="off"`; a separate throttled node announces the simulated instant **at most once per 30 s**; `aria-live="assertive"` is **reserved for daemon-unreachable and latched drift only**; the queue-depth counter is `aria-live="off"` per tick with one polite announcement when it crosses `QUEUE_DEPTH_CAP`.

**At 1440× the countdown and clock update on every drained transition batch, not on a timer**, so they never disagree with the data below them. NFR-9 bounds a committed transition's visibility at ≤ 500 ms of real time **at every rate**, so the board updates on a fixed cadence that does not scale with the rate and coalesces at 1440× rather than queueing 1440 renders per second.

---

## SURF-02b — Clock control

**Segmented control, `{components.clock-control}`: 28px height, `{rounded.sm}`, `{typography.mono-data}`.**

**The rendered segment order is `1× 60× 360× 1440× ⏸`.** The digit keys are bound **position-for-position** to it — `1`→1×, `2`→60×, `3`→360×, `4`→1440× — and `Space` or `0` pauses. An earlier draft put `⏸` first in the control and last in the keymap, so a user counting segments left to right and pressing `5` got pause instead of 1440×, and a user hearing "1×, radio button, 2 of 5" and pressing `1` got 60×. **The control was reordered rather than the keymap being made non-obvious.** `⏸` is deliberately not a digit: a control whose fifth segment is `⏸` and whose fifth digit is pause is a control a screen-reader user mis-operates, and a live simulation is the worst thing to mis-operate.

| Property | Spec |
|---|---|
| **Active segment** | `{colors.accent}` fill, `{colors.text-on-accent}` text. Inactive: `{colors.surface-raised}` with `{colors.text-secondary}`. Glyphs `aria-hidden`. |
| **Rate set** | Exactly FR-28(a): 1×, 60×, 360×, 1440×, plus pause. **No other rate and no derived preset is offered.** A rate of 0 pauses without draining the queue (FR-11(c)). |
| **Semantics** | `role="radiogroup"` named `Simulated clock rate` of five `role="radio"` with `aria-checked`. A rate change announces as `Rate 360×`. |
| **No confirmation** | A rate change alters **pacing only**. FR-11(b) and FR-28(b): changing the rate mid-window may not reorder, add or remove any queued transition. The control therefore shows **no confirmation, no warning, and no "this will change results" note** — there is nothing to confirm, and implying otherwise would be a lie about the system's guarantees. |
| **What it does show** | The **reconciliation count**, so an operator can watch event fidelity hold across a rate change. |
| **When unreachable** | The whole cluster is `aria-disabled="true"` and **not dimmed**; unavailability is carried by the label and the ARIA state, never by opacity alone. |

**Jump-to-instant** — `j` while the clock has focus. Offers **`21:59:00` and `05:44:00` as one-key presets** plus free entry, because those are the two instants an operator actually needs: 21:59:00 is the pre-verification budget deadline (§7.5 — every resume in the fleet fully verified by then, worst case all 33 slots within 29 minutes from 21:30:00), and 05:44:00 is the last second before the Eviction Ramp.

**A jump drains every transition at or before the target instant before rendering** (FR-28(c)). The board is never shown mid-drain, because a half-applied window is exactly the state an operator would misread.

**Shortcuts are inert while a text field has focus** — `1`–`4`, `Space`, `0`, `g`, `n`, `j` and `?`. The digest field of SURF-01 is hex and contains `1`–`5` and `0`, so without the guard typing a 64-character digest fires the rate control four times with no undo, on a live run. A shortcut that can fire while someone is typing an identifier is a data-loss bug wearing a keyboard shortcut.

---

## SURF-03 — Admission Order

**Route:** `g a`, or the Activation panel on the Board. **Persona:** `LAB_ADMIN` only — absent from `Kavita`'s navigation entirely, not merely disabled. A hidden affordance beats a `403` on click.

**Read-only, deterministic, and derived before any placement** (FR-8(a)). **`data-table`, `{spacing.row-dense}` rows, 24px header, `{spacing.2}` cell padding, numeric cells right-aligned in `{typography.mono-column}`.**

| Column | Content |
|---|---|
| **Rank** | The daemon's rank. `{typography.mono-column}`, right-aligned. |
| **`job_id`** | `{typography.mono-data}`. The identity focus follows. |
| **Effective Priority** | The value, plus its **granted/aged decomposition** — `Granted Priority + min(Consecutive Nights Missed × AGING_RATE, AGING_CAP)` with `AGING_RATE = 6`, `AGING_CAP = 30`, and Granted Priority `EXPLORATION` = 10 / `THESIS` = 50 / `URGENT` = 90. |
| **`admitted_nights`** | Against `max_night_span` (5). |
| **Starvation Promotion** | Annotation where it applied: `Consecutive Nights Missed ≥ 3` (`STARVATION_NIGHTS = 3`), at most `STARVATION_PROMOTION_LIMIT = 4` per window, tie-broken on submission time. Rendered as an explicit annotation, never silently reordered. |
| **Decision** | One line per placement, each carrying its citation — the **summary** form, because the Admission Order **summarises** placements while the board **displays** them as banners. FR-25(b) governs what is *displayed*; rendering 22 full cited records inline is impossible at 28px, and pretending otherwise is how a citation list quietly disappears. |

**The ARITHMETIC IS SHOWN, NOT SUMMED.** A `THESIS` job at 0 missed nights has Effective Priority 50 and cannot be outranked by an aged `EXPLORATION` job at any aging level. When a row's rank is counterintuitive, the decomposition is what makes it checkable.

**Promotion confers no authority to preempt.** A promoted row carries that annotation explicitly, because the fastest way to misread a promotion is as permission to stop someone's running work. Starvation is fixed by admission order, not by killing a thesis run.

**Keyboard — the discipline NFR-15 names this view for, specifically:**

- Fully operable without a pointer. `↑`/`↓` move; `Home`/`End`/`PgUp`/`PgDn` traverse; `Enter` opens the focused row's Job detail; `→` expands in place to its last Decision Record, `←` collapses.
- **Focus follows the `job_id`, not the row position.** The order is the daemon's rank output, so a recompute genuinely re-ranks; a reader left on DOM position 3 after a re-rank is now looking at a different job than the one that was announced. Focus re-resolves to the same `job_id` at its new rank and **announces the new rank**.
- **The list never animates a re-rank under the cursor**, and **drag-to-reorder is banned** — the order is a computed artefact, and letting a user rearrange it would misrepresent that artefact as a preference. Row separation is a 1px `{colors.border-structure}` bottom rule; zebra striping is not used, because a row rule you cannot see is a row you cannot count.
- The focused row carries a 2px `{colors.focus-ring}` outline at 2px offset. **Focus never moves on a background poll** — a recompute is announced and the focus stays put.
- Virtualised, never paginated, never infinite-scrolled. `aria-rowcount` is the full count and `aria-rowindex` the per-row index.

**Loading:** skeleton rows at final geometry, one per Eligible GPU slot (max 33). **Empty:** `No Pending Set entries. Nothing to order.` **Error:** a latched drift fault renders a **blocking** banner naming it — the order does not exist yet (SURF-02.6). **Success:** the order renders with its computed-at `sim_timestamp` and the promoting rows annotated.

---

## SURF-03b — Pending Set

**Route:** `g q`, or the Board's queue panel. **Persona:** both — and it is **viewer-scoped**, which had to be stated because both readings were available.

| Viewer | Contents | The cap counter reads |
|---|---|---|
| `LAB_ADMIN` | the **whole queue** — the structure FR-7's `QUEUE_DEPTH_CAP = 500` bounds | `Fleet queue 312 / 500` |
| `STUDENT` | **her own submissions only** | `Fleet queue 312 / 500` — **fleet-wide and labelled as such** |

A student who believes her own three jobs are 312 deep has been lied to. The counter populates **before** the rows, so the bound is visible while the list is still filling.

**Columns:** position · `job_id` · state badge · Effective Priority decomposition · `Consecutive Nights Missed` · Retention Deadline · reason. A pending job "may hold one or more verified Checkpoints" (§4.1), so the view carries **how many** it holds — that is the difference between a fresh submission and a job resuming tonight.

**Position is the payload of this view.** UJ-1's climax is a position in the Pending Set, so it is a real column, not an ordinal buried in a sort. Virtualised with `aria-setsize` / `aria-posinset` on a `role="list"`, so a screen-reader user arrowing the list hears it. `Home`/`End` reach the bottom without arrowing 500 times. `Enter` opens Job detail; `→` expands in place.

**Loading:** skeleton rows; the depth counter populates first. **Empty:** `Pending Set is empty.` **Error:** at or above `QUEUE_DEPTH_CAP` this is a **capacity banner on the board, not an error** — the fleet is not in trouble, the queue is simply full. The same underlying fact is a *refusal* to a submitter (SURF-01.4) and a *capacity notice* to an operator. **Success:** the admitted job appears at its computed position with its projected first-start.

---

## SURF-05 — Event log

**Route:** `g l`, or the Board's log panel. **Persona:** `LAB_ADMIN` only.**

**Append-only, covering the whole run, surviving daemon restart** (FR-26(a), FR-26(d)). FR-26's testable condition is that replaying one simulated night's log yields the **identical state vector** as the live run — this surface is the instrument that makes the module's history checkable.

| Property | Spec |
|---|---|
| **Ordering** | By `sim_timestamp`, then by the stable sequence number — the same order the discrete-event engine used, so the log is a faithful replay key and not a UI sort. |
| **Row** | `{spacing.row-dense}` · `sim_timestamp` `{typography.mono-data}` · transition or `transition: null` · `decision` · reason code `{typography.mono-label}` · one-line summary · citation chips. |
| **Truncation is stated, never silent** | `showing ‹k› of N`. The PRD sets **no** event-log page size, so `k` is a **server-supplied value and is not hard-coded**. 500 is `QUEUE_DEPTH_CAP` — a different constant that has nothing to do with log pagination. |
| **Streaming** | New lines append at the bottom, with the viewport **pinned only if already pinned**. |
| **Virtualised** | `aria-rowcount` / `aria-rowindex`. Banned: infinite scroll. |
| **Depth** | `Esc` closes and restores focus to the opener at the preserved offset. |

**`EMITTER_REJECTED` renders as a correct outcome, not a failure.** FR-24(b) makes a citation-less record cause the emitter to **refuse** it and the transition **not to be applied**, and FR-30 asserts fail-closed as `PASSED`. The row states: *"`EMITTER_REJECTED` — the transition was not applied. Citation completeness is a precondition of every record (FR-24(b))."* A log that rendered this as an error would report the system working correctly as broken.

**Failures and cordons are recorded with the same rigour as successes** (FR-26(b)) — that clause exists because the alternative is a log that only remembers the good parts. The `CORDON`, `CORDON_CLEARED` and `FAIL` row shapes are specified in `scenario-3.md`; `DELIVERY_FAILED` and the `EMITTER_REJECTED` row are here.

**Loading:** rows streaming, viewport preserved. **Empty:** `No events for this window.` **Error:** a query failure, with retry — the log survives daemon restart, so an error here means a real query failure, not an expected one. **Success:** the log reconstructs a night on demand.

**`DELIVERY_FAILED` has no dedicated surface** (FR-27(c) requires it be recorded and never block the transition; **S2-Q6** notes the silence), so it renders as an event-log row and nothing more. The board does not infer a transport problem from it.

---

## SURF-09 — Activation panel

**Mounted on the Board from 21:59:00**, not only behind `g a`. UJ-2 wants the night's plan visible *before* it executes, and the blocked case was already on the board while the normal case was one keystroke away — an odd priority for a failure state.

| Block | Content |
|---|---|
| **Pre-verification result** | §7.5 / F-16 / NFR-8: the phase runs from **21:30:00**; each resuming job's SHA-256 digest is recomputed from its bytes. Budget is **absolute**: every resume in the fleet fully verified by **21:59:00**, worst case all 33 GPU slots within 29 minutes. **Because hashing happens here, Window Activation never hashes** — NFR-2's admission-order budget explicitly excludes digest hashing. |
| **The plan** | The Admission Order about to execute, the Eligible Node set, and the **per-Node exclusion reason for everything excluded** (`M3_CORDONED`, `M4_RESERVED`, `VRAM_CLASS_INSUFFICIENT`). |
| **Blocked state** | The block reason, the **next attempt instant** — every 5 simulated minutes until 04:00:00 (FR-8(e)) — and the citation naming the absent authority. Each attempt is its own recorded `DEFER` with the block reason cited. |
| **Drift state** | The latched drift fault, the 3-consecutive-check clearance condition, and a disabled Activation control. |
| **Reconciliation** | Where FR-9 produced a missed activation, the reconciliation record and the fact that **exactly one** exists per missed window. |

**The panel is a `reason-panel` cluster above the grid, not a modal**, because it must be readable *while* watching the board activate. It never covers the slot grid.

---

## SURF-10 — Simulation run panel

**Route:** status strip → Run. **`LAB_ADMIN` only** (FR-31(c)).

| State | Specification |
|---|---|
| **Run status** | `RUNNING` then **exactly one** of `PASSED` or `FAILED` — it never terminates in any other state (FR-30(c)). |
| **`FAILED`** | **Names each violated invariant individually**, not as a count: any of S-1 … S-3, NFR-4, NFR-5, NFR-6, NFR-7, NFR-10, NFR-14, NFR-16, each with its own line. FR-30(d) is explicit and the response names *each*. |
| **Not run-gated** | The panel **states** that NFR-1 and NFR-11 are build-time static checks and that the latency NFRs — NFR-2, NFR-3, NFR-8, NFR-9 — are measured by a separate benchmark harness (F-36). It shows them as **not run-gated rather than as passed**. Showing a latency NFR green inside a run that cannot meaningfully assert wall-clock latency would be a false comfort. |
| **Fault schedule** | Renders the active `fault_schedule`, each fault's **kind, target and Simulated Clock instant**, and the run manifest. The five kinds: node fault, Checkpoint write failure, Checkpoint corruption, daemon crash, training process exit (`PROCESS_EXIT`, incl. `OOM_KILLED`). Faults fire against the Simulated Clock, so one scheduled for 05:46:00 fires at 05:46:00 at 1× or 1440× (FR-29(b)). |
| **Authoring** | **API-only in v1, and the panel says so.** It renders the schedule plus a copyable `POST /simulations` body and offers **no editor** — the PRD names no authoring surface, and inventing one would be a design decision masquerading as a requirement (**S2-Q4**). An operator demonstrating a failure path to a marker therefore has to leave the console, which undercuts FR-29's stated purpose; the panel states that limitation rather than hiding it. |
| **`operator_action_schedule`** | Rendered read-only: an ordered list of timed operator actions, e.g. `CLEAR_CORDON ws-gpu-19 at 2026-09-28T08:05:00-05:00`, applied in Simulated Clock order by a `LAB_ADMIN` fixture (F-25). This is how a cordon is cleared in a headless run, which is why the panel is activation-adjacent (**S2-Q3**). |
| **Artifacts** | Run manifest, Decision Record log and event log, retrievable per FR-30. |
| **Loading · Empty** | Run status reads `RUNNING`. Empty: `No run submitted.` |
