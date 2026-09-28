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
