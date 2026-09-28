# 04: A Thesis Run Stops a Nine-Hour Exploration — Annex Scenario 4: Priority Queue Preemption

**Project:** Proyecto final — Module 9, Night Training Scheduler
**Created:** 2026-09-28
**Method:** WDS Phase 3 (UX scenario outline), trigger document = `planning/prd.md`
**Journey:** UJ-4 (primary) · **edge case: `PREEMPTION_REFUSED` (the "aging alone" refusal, FR-16's stated converse)**
**State paths:** challenger `QUEUED_PENDING_WINDOW` → `RUNNING`; victim `RUNNING` → `CHECKPOINTING` → `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW` (T-14)
**Design references:** `ux/DESIGN.md` (theme, tokens, component specs) · `ux/EXPERIENCE.md` (Flow 4, IA, state patterns, voice)

> **Trigger-document substitution.** WDS Phase 3 normally derives scenarios from a Trigger Map produced in Phase 2. No Trigger Map exists for this project — Phases 1 and 2 were never run. The substitute is `planning/prd.md`, which supplies the same three things a Trigger Map would: named personas (§2.1), stated jobs-to-be-done, and a success-metric set (§13). See Open Question S4-Q1.

---

## Transaction

**What this scenario covers:** At 23:10, in the middle of a working night, a job that has been running for an hour is stopped so that a higher-priority job can start. The victim is a person with a nine-hour estimate. This is the only flow in the module where the product takes work away from a user who did nothing wrong, in the middle of a period when the user believes work is happening, and it is the flow where the product's authority is at its thinnest: nobody filed a ticket, nobody clicked "stop", and no Urgent Grant was used.

The design obligation is therefore narrow and hard: **the stop must be arithmetic the reader can check.** Not "it was rescheduled." The reader must be able to see 50, 22, the margin of 20, and the tier that granted the authority — and must be able to see, in the refusal case, exactly which of those two conditions was not met.

---

## Business Goal

**Goal:** A higher-priority job starts within the same night without anyone losing work, and any student whose run was stopped can audit the two numbers that stopped it.

**PRD objective reference:** `SM-5` (Explainability — 100% of decisions presented to a user carry a citation and a one-sentence summary a reader can check against the delegated authority; target absolute) · `SM-4` (No starvation — max Consecutive Nights Missed ≤ 4) · `SM-6` (Work preservation, measured on **every** eviction, preemption and fault, no exclusions) · `SM-1` (Mandated-path fidelity)

---

## User & Situation

**Personas (plural, and this is the point):** Kavita, senior research student, challenger, granted `THESIS` by the Policy Engine from her academic standing — she asked for nothing. The victim is a student whose identity the PRD does not name and, per FR-31(b), the surface must not leak: the victim's job is rendered as `occupied by another job` with **no identifier at all** in the slot grid. Ines, GPU lab operations engineer, is watching.

**Situation, 23:10:** Kavita's thesis job is `QUEUED_PENDING_WINDOW`, granted `THESIS`. An exploration job holds `ws-gpu-12`, granted `EXPLORATION`, aged 2 nights, showing a 9-hour estimate. **No Eligible Node is free**, so ordinary admission cannot proceed and the question of Preemption arises.

**Hope (Kavita):** That her run starts tonight without her having to explain herself, and that when it does start she can see *why* it was allowed to displace something.

**Hope (the victim, unnamed):** That the run does not simply vanish, and that its position in the queue tomorrow is not worse for having been stopped.

**Worry (Kavita):** That `THESIS` on her Job Spec is something she declared and the system merely tolerated. FR-14(c) and FR-17(c) exist to make that worry wrong, and the surface must be what makes it visibly wrong.

**Worry (the victim):** That being stopped is being penalised. **It is not**, and the surface has to say so with a counter value rather than an assurance — see NP-4.7.

> **Driving forces addressed**
> - ✅ *Want* (§2.1, Ines): "I need to see why each job was placed where it was, so I can defend it."
> - ✅ *Want* (§2.1): "When my job was stopped at dawn, I need to know it was stopped cleanly and that six hours of work is not gone." — the same reader-facing guarantee, met here at 23:10 instead of 05:45.
> - ❌ *Fear* (§2.1): A thesis run killed to make room for coursework. FR-16(b) makes this structurally impossible to do by aging, and FR-15(d) makes Starvation Promotion confer no preemption authority.
> - ❌ *Fear*: A preemption loop — two jobs taking turns evicting each other all night. FR-16(f) and SM-C3 are the PRD's answers; the surface must not invite the behaviour they forbid.

---

## Device & Starting Point

**Device (Kavita):** Desktop, light theme, the board and Job detail. She is not watching at 23:10; the surface must be legible on arrival at 23:20.

**Device (the victim):** Same surfaces, from the other side, with **no identity disclosure** (FR-31(b)).

**Device (Ines):** Desktop, dark-first, the board. She sees two `PREEMPT`-group banners in the activity stream within a minute of each other and needs the Decision Record detail behind each.

**Entry:** The preemption is not entered by any of them. It is entered by the daemon at the moment the Admission Order is recomputed with no free Eligible slot, and the operator's first view of it is a **banner, not a screen change** — the board does not navigate away from under the person reading it.

---

## Best Outcome

**User Success:** Kavita's job is `RUNNING` and she was told *why* the other one stopped. The `PREEMPT` banner names both jobs and carries the citations — the challenger's granted-priority source and the Preemption Margin rule — so she can check the arithmetic herself: 50 ≥ 22 + 20, and the tier is `THESIS`. The victim's badge reads `EVICTED_RESUMABLE` in violet with a `‖`, never as a failure.

**Business Success:** One `PREEMPT` record, one completion record for the victim's `CHECKPOINTING` interval (same `decision`, `supersedes` the initiating id), one `ADMIT` record for the challenger (T-3), and one T-14 `ADMIT` record returning the victim to the Pending Set with its Checkpoint attached, its original submission time preserved, and its Consecutive Nights Missed **unchanged**. Net GPU-minutes lost to the stop: one Checkpoint write, recorded so SM-C3's counter-metric can move in the right direction.

---

## Shortest Path

1. **Board, 23:09:50** — `ws-gpu-12` is `running` with the exploration job; every other Eligible Node is occupied or excluded. Kavita's job sits in the Pending Set with its Granted Priority tile and its Effective Priority decomposition visible.
2. **Board + reason panel, 23:10:00** — Admission Order recomputed. No free Eligible slot, so the preemption gate in FR-16 is evaluated: challenger's Effective Priority 50 ≥ victim's aged 22 + `Preemption Margin` 20, **and** challenger's Granted Priority is `THESIS` ∈ {`THESIS`, `URGENT`}. Both conditions pass. Victim selection takes the lowest-Effective-Priority `RUNNING` job that still has a verified Checkpoint or can produce one within the Checkpoint Budget.
3. **T-7 fires** — `RUNNING` → `CHECKPOINTING`, decision `PREEMPT`, reason —. Citations `self:PREEMPTION-MARGIN-v1` **and** the challenger's granted-priority source (`policy:M2/…`). The second is **unconditional** (F-1, FR-24(a)): every `PREEMPT` and every `EVICT` requires at least one non-`self:` citation, so a user's work being stopped may never be justified by a number alone.
4. **`ws-gpu-12` flips to `draining`**, its victim badge to `CHECKPOINTING` with the `▼` glyph. FR-16(d) is the rule that governs this frame: **the challenger does not start until the victim's Checkpoint verifies *and* the Node is released.** The board must therefore show the challenger as `QUEUED_PENDING_WINDOW` with the reason "waiting on preemption of a lower-priority run", not as `RUNNING`.
5. **T-8 fires** — the victim's `CHECKPOINTING` → `EVICTED_RESUMABLE` record **keeps its `decision` as `PREEMPT`** and sets `supersedes` to the T-7 record id, with citations mirroring the initiating record. `ws-gpu-12` is released.
6. **T-3 fires for the challenger** — the daemon filters the fleet to Eligible Nodes, recomputes the Admission Order, selects the Node, and admits. `ws-gpu-12` now runs Kavita's job. ✓
7. **T-14 fires for the victim** — `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW`, **immediately**, decision `ADMIT`, citations `node-state:M3/…` (the freed slot) and `self:PREEMPTION-MARGIN-v1`. Checkpoint attached, original submission time preserved, Consecutive Nights Missed not incremented. It may be re-placed the same night if a slot frees.

> **The rendering decision this scenario is really about.** A `PREEMPT` banner and an `ADMIT` banner carry the **same** eyebrow, the same summary treatment and the same citation row; the groups differ by border weight, by an opening group glyph and by the group word (`Decision · preempt` against `Decision · admit`), never by hue alone — the fill difference between `{colors.surface-raised}` and `{colors.surface-base}` is 1.09:1 and is therefore decoration, not a signal. And because a refusal is the highest-stakes record in this flow, the refused-Preemption `DEFER` banner **must not** be confusable with either. It is red-bordered like every `DENY`/`DEFER`, separated from the job-state hue vocabulary by the group glyph and the summary text, and — per EXPERIENCE.md — it carries a `role="alert"` node on first appearance, because a screen-reader user who is refused and hears nothing cannot tell refusal from success.

---

## Requirement Traceability

### Primary — `planning/prd.md` §14 row 4 and FR-16's testable condition

| FR | What it constrains in this scenario |
|---|---|
| **FR-16** | Authorise and execute Preemption. Margin 20, the two-part gate, victim Checkpoint requirement, the shared `CHECKPOINTING` path, T-14's immediate re-queue, and the once-per-window rule. |
| **FR-17** | Administer Priority grants. Grants come from Module 2 or an administrator; `URGENT` needs a reason code; revocation never aborts a `RUNNING` job. |

### Supporting

| FR / NFR | Bearing |
|---|---|
| **FR-14** | Effective Priority = granted + aged, `AGING_RATE` 6, `AGING_CAP` 30; self-declared intent never contributes; Consecutive Nights Missed increments only on a night with zero admitted minutes. |
| **FR-15** | Starvation Promotion: `STARVATION_NIGHTS` 3, `STARVATION_PROMOTION_LIMIT` 4 — and FR-15(d), promotion confers **no** authority to preempt. |
| **FR-18** | The victim's Checkpoint: the five-step sequence, digest/byte count/step/timestamp recorded together or not at all. |
| **FR-21** | Resume from the most recent verified Checkpoint, logged as a step number. |
| **FR-24** | One cited record per transition; `supersedes` on the completion record; fail-closed emitter. |
| **FR-26** | Lifecycle event log; the preemption appears with both jobs' digests. |
| **FR-27** | Exactly one notification to the victim, none to the administrator. |
| **FR-25** | Status board. Pending Set position, reason panel, next decision point. |
| **FR-31** | **No identifier leak** — a slot held by another submitter's job reads `occupied by another job`. |
| **NFR-4** | 100% of decisions carry a citation and a summary checkable against the delegated authority. |
| **NFR-15** | Colour is never the sole channel. |

### State machine

| Transition | From → To | Decision | Reason | Citations (§6.4) |
|---|---|---|---|---|
| **T-7** | `RUNNING` → `CHECKPOINTING` | `PREEMPT` | — | `self:PREEMPTION-MARGIN-v1`; the challenger's granted-priority source (`policy:M2/…` or administrator grant record) — **at least one non-`self:` per FR-24(a)** |
| **T-8** | `CHECKPOINTING` → `EVICTED_RESUMABLE` | `PREEMPT` (keeps T-7's decision) | — | completion record of the initiating T-7 decision; `supersedes` = the T-7 record id; citations mirror the initiating record |
| **T-14** | `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW` | `ADMIT` | — | `node-state:M3/…` (the freed slot permitting same-night re-placement); `self:PREEMPTION-MARGIN-v1` |
| **T-3** | `QUEUED_PENDING_WINDOW` → `RUNNING` | `ADMIT` | — | the granted-priority source that ranked the job (`policy:M2/…` or the administrator's grant record); `node-state:M3/…`; `reservation:M4/…` when consulted |

**Non-transition record — the mandatory edge case (FR-16(c)):**

| Source | `transition` | Decision | Reason | Citation |
|---|---|---|---|---|
| FR-16(c) — refused Preemption | `null` | `DEFER` | `PREEMPTION_REFUSED` | `self:PREEMPTION-MARGIN-v1` (OQ-1) |

**States reached:** `QUEUED_PENDING_WINDOW` (entry) · `RUNNING` · `CHECKPOINTING` · `EVICTED_RESUMABLE` → back to `QUEUED_PENDING_WINDOW`. **No new state is created by preemption** — there is no `QUEUED_PREEMPTED`, and a design that adds one has invented a tenth badge. FR-25(a): the states are the nine of §4.1 and no other.
**Slot states reached:** `running` · `draining` · `available` · and briefly `reserved` if a Module 4 reservation is consulted.
**Decisions reached:** `PREEMPT`, `ADMIT`, `DEFER`.
**Screens:** Board · Pending Set · Job detail · Decision Record detail · Event log · Notification.

---

## Scenario Steps

### Step 1 — Board and Pending Set, 23:09:50

- **The Pending Set shows Effective Priority decomposed, not just totalled** (FR-14). Kavita's row reads `THESIS` granted, `+0` aged, **50**. The victim's read `EXPLORATION` granted, `+12` aged (2 nights × `AGING_RATE` 6), **22**. The decomposition is the whole point: it is the visible difference between "she outranks him" and "she outranks him **and is entitled to say so**."
- **`AGING_CAP` = 30 is legible somewhere.** An `EXPLORATION` job with 5 missed nights is 40 and no further, which is exactly why a `THESIS` job at 50 **cannot be outranked by an aged `EXPLORATION` job at any aging level** (FR-14's testable condition). The surface should let a reader reach that conclusion themselves, because it is the guarantee that a thesis run is not the softest thing in the system.
- **Self-declared intent is shown as `PENDING_REVIEW` and visibly not applied** (FR-17(c)). A student who typed `THESIS` into her Job Spec must be able to see that the `THESIS` on her badge came from the Policy Engine and not from her keystroke.
- **"No Eligible Node is free" is stated on the board, with the exclusion reasons.** Every idle Node names one of `M3_CORDONED`, `M4_RESERVED`, `VRAM_CLASS_INSUFFICIENT` (FR-12). A pending job with a full fleet and no visible reason is a pending job with no explanation.
- **The victim's identity is never rendered here** (FR-31(b)). If the board shows the victim's job row to Kavita, that row is `occupied by another job` with no identifier.

### Step 2 — 23:10:00, the gate, and the two conditions

FR-16(b) is two independent conditions, and **both** must pass. The gate renders as a two-line evaluation so that the reader can see which line failed:

| Condition | Requirement | Challenger | Victim | Verdict |
|---|---|---|---|---|
| **Margin** | challenger EP ≥ victim EP + `Preemption Margin` 20 | 50 | 22 | 50 ≥ 42 ✓ (margin 28) |
| **Tier** | challenger Granted Priority ∈ {`THESIS`, `URGENT`} | `THESIS` | `EXPLORATION` | ✓ |

- **The margin is 28 here, not 20.** Rendering the actual margin rather than the threshold is what makes the evaluation checkable — a reader who sees "20" cannot tell whether the challenger cleared it by 0 or by 8.
- **Aging contributed nothing to the authority.** The victim's aged 22 *lowers* the bar; the challenger's tier is what authorises the stop. FR-16(b)'s second condition and FR-15(d) exist to make the sentence "aging never authorises Preemption" true at any level, and the surface is where that promise becomes checkable.
- **The citation is not optional.** `self:PREEMPTION-MARGIN-v1` names the rule; the challenger's granted-priority source (`policy:M2/…`) names the delegated authority that produced the tier. A `PREEMPT` record carrying only the `self:` citation is **refused by the emitter** — see NP-4.8.

### Step 3 — victim selection, and the Checkpoint precondition

- **Victim selection is not "the lowest priority job."** FR-16(c) requires the victim to be a `RUNNING` job that **still has a verified Checkpoint, or can produce one within the Checkpoint Budget.** A `RUNNING` job that cannot checkpoint is **not eligible to be a victim** and is skipped — the daemon does not pick a victim it cannot stop safely. This is the constraint that makes NP-4.1 a *refusal* rather than a *failed stop*.
- **The Checkpoint Budget is a 300 s window (A-9), and the surface must show whether the victim fits inside it.** Whether a victim "can produce one within the budget" is a judgement the operator will want to see made, not assumed.
- **Rendered:** the victim's last Checkpoint time, its digest and byte count, and the budget remaining. A reader who cannot check this cannot check the stop.

### Step 4 — T-7, `draining`, and the frame that FR-16(d) governs

- **T-7 fires.** `PREEMPT`, no reason code, citations as above. The decision enum is the ten of §6.1 and `PREEMPT` is one of them; the record is appended, never edited.
- **`ws-gpu-12` → `draining`**, which is `{colors.node-draining}` = `{colors.state-checkpointing}`: a draining slot is running a `CHECKPOINTING` job. The victim badge flips to `CHECKPOINTING`, `▼`, label "Checkpointing".
- **The challenger is not yet `RUNNING`, and the board must say why it is not.** FR-16(d): the challenger does not start until the victim's Checkpoint verifies **and** the Node is released. The challenger's Pending Set reason reads "waiting on preemption of a lower-priority run" with a link to the `PREEMPT` record.
- **This is the frame the PRD's §1 vision is about.** A module that let a thesis run start the moment it decided to preempt would be parking the victim's work "in an invisible holding pen" — the exact failure the vision names. The honest state is a challenger that is queued and a victim that is stopping, both visible, for the length of one Checkpoint write.
- **Outside the Eviction Ramp, the `draining` tile shows no SIGKILL countdown.** At 23:10 the deadline is the 300 s Checkpoint Budget, not a wall-clock instant. A `draining` tile quoting 05:53:00 at 23:10 is quoting a deadline that does not exist.

### Step 5 — T-8, release, T-3 for the challenger

- **T-8 fires, keeping `decision: PREEMPT`** and setting `supersedes` to the T-7 record id with mirrored citations. The `PREEMPT` banner is the *same component* as the `ADMIT` banner, distinguished by group glyph and group word — never by hue alone, since the 1.09:1 fill difference is decoration and the two border hues sit only ~dE 6.8 apart under deuteranopia.
- **The victim badge reads `EVICTED_RESUMABLE`**: `{colors.state-evicted-resumable}` violet, `‖`, label "Evicted, resumable", **no 1px terminal ring**. It is not a failure, and at 23:10 it is emphatically not a failure, because the job is going back into the queue the same minute.
- **`ws-gpu-12` is released and immediately re-selected for the challenger** (T-3). FR-13 records the choice with the two or three candidates considered and the rule that decided it: the prior-Node preference (a), the lowest slot-allocation count (b), ties by Node identifier ascending.
- **Exactly one notification, to the victim, and none to the administrator** (FR-27). A preemption is an Eviction, and FR-27's testable condition is explicit: Eviction → one notification to the submitter, zero to the administrator. The asymmetry with a Checkpoint failure (two notifications) is load-bearing and is what a reader of the notification contract should be able to derive.
- **Copy:** "Your run on `ws-gpu-12` was stopped at 23:10 to let a `THESIS` run start. It is saved at step 18,440 and is back in the queue now." Not "Preempted 😢." Not "Your job was terminated by the system." The subject of the sentence is the run, and the reason is a tier, not a mood.

### Step 6 — T-14, the victim returns ✓

- **T-14 fires immediately** — not at the next window, not on the next Admission Order pass. The victim's own resolution line says "transitions back to `QUEUED_PENDING_WINDOW` immediately once its Checkpoint verifies."
- **Decision `ADMIT`, citations `node-state:M3/…` and `self:PREEMPTION-MARGIN-v1`.** The non-`self:` citation names the freed slot that permits same-night re-placement.
- **Three fields must be rendered as preserved, and each is a rule:**
  - **Checkpoint attached** — the job does not restart from zero.
  - **Original submission time preserved** — its position in the queue is not reset by being stopped.
  - **Consecutive Nights Missed unchanged** — it received an admitted minute this window, so FR-14(d) does not increment it, so its Effective Priority **does not age**. A victim that was stopped does not come back older and angrier, and a queue that re-ranked it as though it had been skipped would be quietly manufacturing the very starvation FR-15 exists to prevent.
- **It may be re-placed the same night if a slot frees** (F-5, F-8), and the Pending Set shows that as a live possibility rather than as a promise.

---

## Non-Happy Paths

Ten. The PRD's own framing for this flow is SM-C3: *do not optimise Preemption count — every Preemption costs a victim a full stop, Checkpoint write and restart, and a high count is a sign the Preemption Margin is mistuned, not that the system is performing.*

### NP-4.1 — **The mandatory edge case:** the victim cannot checkpoint inside the budget → `PREEMPTION_REFUSED`

UJ-4's stated edge case, and the refusal the Annex names.

- **Trigger:** the victim is a valid `RUNNING` job, but it has **no verified Checkpoint and cannot write one within the Checkpoint Budget.** It therefore fails FR-16(c)'s precondition.
- **Outcome:** the Preemption is **refused.** The victim's state does **not** change — it stays `RUNNING`. The challenger's state does not change — it stays `QUEUED_PENDING_WINDOW`. No slot changes. No notification is sent, because **nothing was stopped and nothing failed**; there is no FR-27 event here at all.
- **What is written:** a **non-transition Decision Record** — `transition: null`, decision **`DEFER`**, reason **`PREEMPTION_REFUSED`**, citation **`self:PREEMPTION-MARGIN-v1`** (FR-16(c), OQ-1). This is the only record type in the module that reports a refusal to *act*, as against T-2's `DENY`/`VALIDATION_FAILED`, which refuses a *request*.
- **Rendered on the challenger, not the victim**, as a `DEFER` banner carrying a `role="alert"` node on first appearance — the second highest-stakes record in the whole product, alongside UJ-1's submission refusal, per EXPERIENCE.md. The summary names the reason in the operator's terms, not the record's: the victim could not be stopped safely, so the challenger waits. §6.1 caps `summary` at 200 characters, and SM-C4 says a longer summary is not a better one.
- **"Kavita waits, and the system says so, citing the Checkpoint Budget rule"** (UJ-4). The refusal must be legible as a *reason to wait*, not as a failure and not as a queue position. She must be able to tell the difference between "you are behind three jobs" and "you are blocked by a rule that will not change on its own tonight."
- **The citation is `self:`-alone and that is legitimate**, because the refusal rests on a module-owned integrity rule (the Checkpoint Budget) with no delegated authority to name — the F-1 split rule's second sentence. This is the one place in the module where a `DEFER` may stand on a `self:` citation alone, and it is the direct contrast with NP-4.8, where a `PREEMPT` may not.

### NP-4.2 — Aging alone cannot authorise a stop (FR-16's stated converse)

- **Trigger:** an aged `EXPLORATION` challenger at Effective Priority **40** — the maximum, `EXPLORATION` base 10 + `AGING_CAP` 30 — attempts to preempt a `THESIS` victim at **50**. The margin is 10, and 10 < 20.
- **Outcome:** refused. Decision `DEFER`, reason `PREEMPTION_REFUSED`, citation `self:PREEMPTION-MARGIN-v1`. **Both jobs keep their states.** No Checkpoint write, no slot movement, no notification, no GPU-minute lost.
- **Two related prohibitions ride on the same rule, and each has its own surface obligation:**
  - **FR-15(d): Starvation Promotion confers no authority to preempt.** A job promoted to the head of the Admission Order because `Consecutive Nights Missed ≥ 3` is promoted for **admission order only**. The Promotion marker on the Pending Set row must therefore never be styled or labelled as a priority escalation, or a reader will believe the job gained the authority to stop a thesis run. The marker says "promoted for admission order."
  - **FR-14(c): a self-declared intent never contributes to Effective Priority.** A challenger who typed `THESIS` into the Job Spec and was granted `EXPLORATION` has no authority; the `PENDING_REVIEW` badge is what tells her so, and it must be visible on the row that would have been the preemption.
- **Why the surface must show the arithmetic and not just the verdict:** the margin *almost* cleared. A reader told only "preemption refused" learns nothing; a reader shown 40 < 50 + 20 learns that the fix is a grant (FR-17), not another night's wait.

### NP-4.3 — The same victim, twice in one night (FR-16(f))

- **Trigger:** the victim was already preempted at 23:10 and re-placed when a slot freed; a second challenger now targets it. The same victim may not be preempted twice within one Night Window.
- **Outcome:** refused, `DEFER` / `PREEMPTION_REFUSED` / `self:PREEMPTION-MARGIN-v1`. The victim's `RUNNING` state is untouched.
- **Why this branch is a design obligation and not just a rule:** without it, two `EXPLORATION` jobs and one `THESIS` job would trade the same node back and forth for six hours, each restart re-paying warmup, each Checkpoint write consuming store budget — and SM-C3 says that pattern is a regression, not a result. The board must not invite a reader to *expect* the second stop.
- **FR-15(b)/(c) are the pressure valve that makes the cap survivable:** promotion guarantees the victim's next admission, so the once-per-window cap costs it one window of delay, not its place in line.

### NP-4.4 — The challenger would start before the victim's Node is released

- **Trigger:** the surface (or an implementation shortcut) repaints `ws-gpu-12` with the challenger's job the moment SIGTERM reaches the victim, rather than when the Checkpoint verifies and the Node is released.
- **Consequence:** FR-16(d) is breached and **one slot is shown serving two jobs**, which is also an Invariant S-1 accounting error. The victim's work is stranded with no visible state at all — precisely the "invisible holding pen" the §1 vision forbids.
- **The design obligation:** during the `CHECKPOINTING` interval the slot belongs to the victim, the challenger sits in the Pending Set with a reason, and the sequence is visible in the activity stream as three records in order: `PREEMPT` (T-7), its completion (T-8), `ADMIT` (T-3). A board that compressed these into one repaint would be hiding the only moment where a thesis run's start is conditional on someone else's work being safely written down.

### NP-4.5 — A node fault arrives mid-preemption (FR-12(d))

- **Trigger:** eligibility is re-evaluated **immediately before each placement**, so a Module 3 fault arriving while the victim is `CHECKPOINTING` on `ws-gpu-12` is honoured. The preemption cannot complete onto a Node that is no longer Eligible.
- **Outcome:** the preemption is abandoned mid-flight and the situation routes to the node-fault paths — T-16 (`RUNNING` → `EVICTED_RESUMABLE`, reason `NODE_FAULT`, cited `node-state:M3/…`) if a verified Checkpoint exists, or T-17 (`FAILED` / `NODE_FAULT_NO_CHECKPOINT`) if not. The challenger does **not** inherit a Node that has just become ineligible, and the record for the abandoned preemption is `DEFER`, citing the fault.
- **The open question this lands on:** PRD Open Question 10 asks whether a job that was `RUNNING` when the window opened but whose Node faulted mid-night should be eligible for **automatic** re-placement on another Node. T-16 currently re-queues it without re-admitting until the next window; the challenger here is a different case, because it never started, and the PRD does not say whether a challenger inherits a victim's freed slot when the abort came from the Node rather than the Checkpoint. See S4-Q2.
- **Rendered:** the exclusion reason (`M3_CORDONED`) on the slot, and the challenger back in the Pending Set with a reason it did not cause. A surface that showed a fault-induced abort as a preemption refusal would blame the victim for the hardware.

### NP-4.6 — The victim's resume lands on a different Node (FR-13)

- **Trigger:** placement prefers the job's **prior Node** when it is Eligible and its VRAM class or slot matches, because "resuming on a different Node invalidates local SSD cache locality." After a preemption, the victim's prior Node is running someone else.
- **Outcome:** the victim is placed on a different Eligible Node, and the record carries a **`PRIOR_NODE_INELIGIBLE`** note.
- **Rendered:** the note is stated as a cost, not a footnote — the victim pays a warmup penalty on resume for a stop it did not ask for. FR-13's testable condition requires exactly this note, and FR-11's GPU-memory fragmentation concerns are the same phenomenon seen from the node side.

### NP-4.7 — The victim's own counters (FR-14(d), F-8)

- **Trigger:** a naive implementation increments Consecutive Nights Missed for any job that was not running at the end of the window, treating the victim as a job that was skipped.
- **Consequence:** the victim's Effective Priority **ages**, its Pending Set position worsens, and SM-4's bound of ≤ 4 max missed nights becomes harder to hold for exactly the jobs the module exists to protect. Stopping a job for a thesis run would make the stopped job *less* likely to run — the module would punish the victim for yielding.
- **The correct behaviour and its rendering:** FR-14(d) increments only for a night in which the job received **zero admitted minutes**, and resets to zero on any admitted minute. The victim received admitted minutes, so the counter does not move. The surface must show the three preserved fields from Step 6 as **values**, and the Pending Set must not visibly re-rank the victim as though it had been skipped.
- **Cross-referenced from scenario 2**, where the same FR-14(d) rule governs the `AGING_CAP` and reset behaviour at Window Activation.

### NP-4.8 — A `PREEMPT` record with no non-`self:` citation is refused (FR-24(b), F-1, NFR-4)

- **Trigger:** the emitter is handed a `PREEMPT` record citing only `self:PREEMPTION-MARGIN-v1`, with no `policy:M2/…` or grant record.
- **Outcome:** **fail-closed.** The emitter refuses the record, the transition is **not applied** — the victim stays `RUNNING` and the challenger stays `QUEUED_PENDING_WINDOW` — an `EMITTER_REJECTED` integrity event is logged, and the run is `PASSED` (FR-30). The refusal is the correct outcome, not a failure.
- **Rendered as a correct outcome.** EXPERIENCE.md is explicit that an `EMITTER_REJECTED` event must be presented as the system working, and that the log must never show it as an error. This is the one path in the module where the *absence* of a state change is the success, and a surface that animated a failed stop would invert the meaning of the record.
- **The contrast with NP-4.1 is the lesson.** Both are `DEFER` records citing `self:PREEMPTION-MARGIN-v1` alone. In one, the `self:` citation is **legitimate** — a module-owned integrity rule, the F-1 split rule's second sentence. In the other, it is **insufficient** — because stopping a user's work is not a module-owned bookkeeping rule, and F-1's last sentence is unconditional: *every `PREEMPT` and every `EVICT` requires at least one non-`self:` citation, without exception.*

### NP-4.9 — A grant is revoked mid-night (FR-17(d))

- **Trigger:** an administrator revokes a `THESIS` grant, or a `URGENT` grant, at 23:40 — after the preemption executed and the challenger is running.
- **Outcome:** revocation takes effect at the **next Admission Order computation** and **never aborts a `RUNNING` job.** The challenger keeps running; a preemption that already happened is not undone, and the victim's work is not returned.
- **Rendered:** the priority administration panel says this at the point of action, not in a tooltip afterwards — "Revoking this grant affects the next Admission Order. It will not stop the job that is running now." A panel implying otherwise would be promising a reversal the PRD forbids.
- **Related:** a `URGENT` grant requires a non-empty reason code and is **rejected** without one (FR-17(b)), and a grant is scoped **per job** (A-13) — never per submitter per window. The grant form must enforce the reason code at the input, before the grant is submitted to the Policy Engine, because the PRD's `Urgent Grant` glossary entry defines it as *always* recorded with an actor and a mandatory reason code.

### NP-4.10 — The victim's resume is not verified by 21:59:00 (FR-20(f))

- **Trigger:** the victim's retained Checkpoint is not re-verified in the 21:30:00 pre-verification phase and the outcome is still unverified at 21:59:00, one minute before activation.
- **Outcome:** a non-transition record — decision `DEFER`, reason **`UNVERIFIED_RESUME`**, citation `self:CHECKPOINT-QUARANTINE-v1` — and the job is **not admitted.** An unverified resume is never admitted; there is no partial admission.
- **Rendered:** the job stays in the Pending Set with the reason attached, rather than being silently dropped or shown as admitted-and-broken. The same record governs T-12 and T-14, so it appears identically wherever a resume fails to verify.
- **Cross-referenced from scenario 2's NP-2.7**, which carries the 21:30:00 phase itself; the record is the same one in both files and must not be rendered two different ways.

---

## Open Questions

**S4-Q1 — The trigger document is a PRD, not a Trigger Map.** WDS Phase 3 reads persona driving forces and business objectives from a Phase 2 Trigger Map. None exists for this project. Personas (§2.1), jobs-to-be-done and success metrics (§13) were taken from `planning/prd.md` instead. If Phases 1 and 2 are ever run, this scenario's Business Goal and Driving Forces sections should be re-anchored to the real objective ids.

**S4-Q2 — A preemption aborted by a Node fault is not specified.** PRD Open Question 10 asks whether a job that was `RUNNING` when the window opened but whose Node faulted mid-night is eligible for automatic re-placement on another Node; T-16 currently re-queues it without re-admitting until the next window. A **challenger** is a different case, because it never started: the PRD does not say whether it inherits the victim's freed slot when the abort came from the Node rather than from the Checkpoint, nor which `DEFER` reason a fault-induced abort carries. NP-4.5 renders it as a `DEFER` citing the fault with the challenger returned to the Pending Set.

**S4-Q3 — The refusal's recipient and its copy are unnamed.** FR-16(c) specifies the record precisely — `DEFER`, reason `PREEMPTION_REFUSED`, `self:PREEMPTION-MARGIN-v1` — and UJ-4 says only that "Kavita waits, and the system says so." The PRD does not say whether the challenger is notified through FR-27's channel (whose trigger list is Eviction, Preemption, Expiry, Checkpoint failure, cordon, resume — a *refused* Preemption is arguably none of these), whether the victim is told a preemption of it was considered and declined, or what the summary says. NP-4.1 renders the refusal on the challenger's `DEFER` banner with a `role="alert"` announcement and no notification.

**S4-Q4 — The victim's admission position after T-14 is not given a value.** FR-16(e) preserves the original submission time and the Consecutive Nights Missed count, and says the job "may be re-placed the same night if a slot frees," but the Pending Set is ordered by Effective Priority (FR-8). Whether the victim re-enters at its old rank, at the head of its priority tier, or at a rank reflecting one admitted minute is unspecified — and the three answers produce visibly different queues. Rendered for now as its Effective Priority decomposition unchanged, with the preserved fields shown as values.

**S4-Q5 — The rate control's initial state is unstated (shared with S1-Q5, S2-Q5, S3-Q5).** FR-28(a) fixes the rate set; what a run starts at, and whether a rate survives a page reload, is unspecified. A preemption is decided in seconds, so a board that opens at 1440× may replay a stop nobody could read, and FR-16(c)'s Checkpoint Budget judgement is the one decision in this flow that benefits from being watched in real time.

---

## Page Specifications

> **Phase 4 — WDS UX design.** Canonical specification for **SURF-06b** (Priority administration), plus **deltas** to SURF-04 Job detail, SURF-04b Decision Record detail and SURF-05 Event log. `scenario-3.md` owns SURF-06, SURF-06a, SURF-07 and SURF-08; `scenario-1.md` owns SURF-04/04b; `scenario-2.md` owns SURF-05. This file specifies only what Preemption adds. Sources, in precedence order: `planning/prd.md` → `ux/EXPERIENCE.md` → `ux/DESIGN.md` → this section. Conventions are stated once in `scenario-1.md`.

### SURF-06b.1 The preemption gate, rendered as two lines

The design obligation of this whole scenario is narrow: **the stop must be arithmetic the reader can check.** Not "it was rescheduled." FR-16(b) is two independent conditions and both must pass, so the gate renders as a two-line evaluation with a per-line verdict — a single `PREEMPT`/`REFUSED` verdict cannot tell a reader which line failed, and the two lines have different remedies.

```
Preemption gate — 23:10:00                        [self:PREEMPTION-MARGIN-v1]

  Margin   challenger EP 50  ≥  victim EP 22 + Preemption Margin 20      ✓  margin 28
  Tier     challenger granted THESIS ∈ {THESIS, URGENT}                     ✓

  Victim eligibility (FR-16(c))
  last verified Checkpoint 23:04:00 · digest sha256:7c1e…04aa · 412 MB
  Checkpoint Budget 300 s · 214 s remaining · can checkpoint            ✓
```

| Rule | Why the surface obeys it |
|---|---|
| **The margin is 28, not 20.** | Rendering the *actual* margin rather than the threshold is what makes the evaluation checkable. A reader who sees "20" cannot tell whether the challenger cleared it by 0 or by 8. |
| **The two conditions are visually separate rows.** | FR-16(b) is a conjunction, and a failure in either produces the same `PREEMPTION_REFUSED` record. The remedy differs — a failed Margin needs a grant (FR-17), a failed Tier needs nothing — so the row that failed *is* the guidance. |
| **Aging contributed nothing to the authority.** | The victim's aged 22 *lowers* the bar; the challenger's **tier** is what authorises the stop. FR-16(b)'s second condition and FR-15(d) exist to make "aging never authorises Preemption" true at any level, and this is where that promise becomes checkable rather than asserted. |
| **The citation is not optional and not decorative.** | `self:PREEMPTION-MARGIN-v1` names the rule; the challenger's granted-priority source (`policy:M2/…`) names the delegated authority that produced the tier. A `PREEMPT` record carrying only the `self:` citation is **refused by the emitter** — see SURF-06b.4. |
| **`AGING_CAP` = 30 is reachable on screen.** | An `EXPLORATION` job at 5 missed nights is 40 and no further, which is exactly why a `THESIS` job at 50 **cannot be outranked by an aged `EXPLORATION` job at any aging level**. The Pending Set decomposition exposes the cap so a reader can *reach* that conclusion instead of being told it. |

**Effective Priority renders decomposed, never totalled** (FR-14). Kavita's row reads `THESIS` granted, `+0` aged, **50**. The victim's reads `EXPLORATION` granted, `+12` aged (2 nights × `AGING_RATE` 6), **22**. The decomposition is the whole point: it is the visible difference between *she outranks him* and *she outranks him **and is entitled to say so***.

### SURF-06b.2 Priority administration

**Persona: `LAB_ADMIN` only** (FR-31(c)). Reached from the admission order row → Priority, or `g g`.

| Block | Content |
|---|---|
| **The grant form** | Job, granted tier, actor, and — for `URGENT` — a **mandatory non-empty reason code**. The reason code is enforced **at the input**, before the grant is submitted to the Policy Engine. The PRD's `Urgent Grant` glossary entry defines it as *always* recorded with an actor and a mandatory reason code, so a form that validates the reason after submission has already let an invalid grant exist. |
| **Grant scope** | **Per job** (A-13) — never per submitter per window. Stated in the form, because "grant this student THESIS for the month" is the intuitive wrong model and the PRD forbids it. |
| **Self-declared intent** | A Job Spec's own priority field renders as `PENDING_REVIEW` and is **visibly not applied** (FR-17(c)). A student who typed `THESIS` must be able to see the `THESIS` on her badge came from the Policy Engine and not from her keystroke. The badge must appear on **the row that would have been the preemption** — FR-14(c) makes this a correctness question, not a nicety. |
| **Revocation** | Takes effect at the **next Admission Order computation** and **never aborts a `RUNNING` job**. The panel says this **at the point of action**, not in a tooltip afterwards: *"Revoking this grant affects the next Admission Order. It will not stop the job that is running now."* A panel implying otherwise would be promising a reversal the PRD forbids. |
| **Promotion markers** | FR-15(d): Starvation Promotion confers **no** authority to preempt. The Promotion marker on the Pending Set row therefore reads **"promoted for admission order"** and is never styled or labelled as a priority escalation — otherwise a reader believes the job gained authority to stop a thesis run. |
| **History** | Grant, revoke and promotion events per job, with actors, linking to SURF-05. |
| **Loading · Empty · Error** | Loading: skeleton rows. Empty: `No grants recorded.`. Error: the Policy Engine is unavailable → the form is disabled with the reason stated, and **an unresolvable authority is never locally invented** (A-15, OQ-1). |

### SURF-06b.3 The identity-protection rule — the victim's job never appears

**FR-31(b) is a hard rendering constraint, not a permission.** A slot held by another submitter's job reads **`occupied by another job`** with **no identifier at all** — not a masked `JOB-04••`, not a hash, not a truncated tail. It applies to:

| Surface | Renders | Never renders |
|---|---|---|
| **Slot grid tile** | `ws-gpu-12 · slot 1 · running · occupied by another job` | any fragment of a foreign `job_id` |
| **Slot inspector** | the same, with the cause if a cause exists | a clickable Job detail for a foreign job |
| **Board activity stream** | the `PREEMPT` banner **without** the victim's `job_id` | the victim's name, tier or estimate |
| **Job detail** | full detail for **your own** jobs | any other job's detail by direct route |
| **Pending Set** | your own submissions (SURF-03b) | foreign rows |

**This is design decision D-b** (`ux/_progress/00-design-log.md` §5). A partially masked identifier is still a disclosure: `JOB-0417` is guessable from a Pending Set the same student can see, so a masked form leaks through a channel the mask never considered. The tile therefore carries **no identifier to mask**.

**The reader is not left with a hole.** `occupied by another job` is accompanied by the slot's occupancy label, its VRAM class, and — where one exists — the `reason-panel` code, so the tile is still fully informative about the *machine*. What is withheld is the *person*.

### SURF-04 deltas — the victim and the challenger

Canonical surface in `scenario-1.md`; Preemption adds these blocks.

**No new state is created.** There is no `QUEUED_PREEMPTED`; a design that adds one has invented a tenth badge. FR-25(a): the states are the nine of §4.1 and no other. The victim's path is `RUNNING` → `CHECKPOINTING` → `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW`.

**The victim — `EVICTED_RESUMABLE`, and it is emphatically not a failure at 23:10**, because the job is going back into the queue the same minute:

`{colors.state-evicted-resumable}` violet · glyph `‖` · label "Evicted, resumable" · **no 1px terminal ring**.

**Three fields render as preserved values, each one a rule** — this is NP-4.7's requirement and the victim's whole hope:

| Field | Value | The rule it protects |
|---|---|---|
| **Checkpoint attached** | digest, byte count, step | the job does not restart from zero (FR-21) |
| **Original submission time preserved** | ‹timestamp› | its queue position is not reset by being stopped (FR-16(e)) |
| **Consecutive Nights Missed unchanged** | 2 → 2 | it received an admitted minute, so FR-14(d) does not increment it, so it does **not** age |

**A counter is not an assurance.** The surface must show `2 → 2` as two numbers, not "you have not been penalised." A reader told they were not penalised learns nothing they can verify later; a reader shown a counter that did not move can check it again tomorrow. A job that was stopped and came back **older and angrier** would mean the module punishes the victim for yielding — precisely the starvation FR-15 exists to prevent — so the counter is the guarantee and it has to be a number.

**`PRIOR_NODE_INELIGIBLE` is stated as a cost, not a footnote** (NP-4.6, FR-13). Placement prefers the job's prior Node because "resuming on a different Node invalidates local SSD cache locality." After a preemption that Node is running someone else, so the victim pays a **warmup penalty on resume for a stop it did not ask for**. FR-13's testable condition requires exactly this note, and the surface says the penalty rather than hiding it behind the code.

**The challenger is not `RUNNING` until the victim's Node is released.** FR-16(d): the challenger does not start until the victim's Checkpoint verifies **and** the Node is released. Its Pending Set reason reads *"waiting on preemption of a lower-priority run"* with a link to the `PREEMPT` record. This is the frame the §1 vision is about — a module that started the thesis run the moment it decided to preempt would be parking the victim's work in an **invisible holding pen**. The honest state is a queued challenger and a stopping victim, both visible, for the length of one Checkpoint write.

**The `draining` tile shows no SIGKILL countdown here.** Outside the Eviction Ramp the deadline is the **300 s Checkpoint Budget**, not a wall-clock instant: `draining · checkpointing · elapsed ‹n›s / 300s`. A `draining` tile quoting 05:53:00 at 23:10 is quoting a deadline that does not exist (**S3-Q2**). The rule is stated in `scenario-3.md` and applies identically — the countdown is Ramp-scoped, the budget is not.

**The `CHECKPOINTING` badge shows budget fit** (NP-4.1's precondition). Whether a victim "can produce one within the budget" is a judgement an operator will want to **see made**, not assumed: remaining budget, the victim's last verified Checkpoint time, digest and byte count. A reader who cannot check this cannot check the stop.

### SURF-04b deltas — the four Preemption records

| Transition | Decision | Citations | The rendering obligation |
|---|---|---|---|
| **T-7** `RUNNING` → `CHECKPOINTING` | `PREEMPT` | `self:PREEMPTION-MARGIN-v1` **+** the challenger's granted-priority source (`policy:M2/…` or the administrator's grant record) | the non-`self:` citation is **unconditional** (FR-24(a), F-1) |
| **T-8** completion | `PREEMPT` — *keeps T-7's decision* | mirrors T-7; `supersedes` = the T-7 record id | a `supersedes ‹decision_id›` link above the eyebrow |
| **T-3** challenger admitted | `ADMIT` | granted-priority source; `node-state:M3/…`; `reservation:M4/…` when consulted | the two or three candidates FR-13 requires, and the rule that decided |
| **T-14** victim re-queued | `ADMIT` | `node-state:M3/…` (the freed slot permitting same-night re-placement); `self:PREEMPTION-MARGIN-v1` | the three preserved fields |
| **Refused** — non-transition | `DEFER` / `PREEMPTION_REFUSED` | `self:PREEMPTION-MARGIN-v1` **alone** | see SURF-06b.4 |

**T-7 and T-8 are one decision chain.** FR-24(f) counts one record per transition; the completion record keeps `decision: PREEMPT` and carries mirrored citations. The `EVICT` and `PREEMPT` chains both render as **two linked rows, one decision** — a rendering that showed them as two decisions would overstate what FR-24 constrains.

**The `PREEMPT` and `ADMIT` banners are the same component.** They differ by **group glyph, group word and border weight** — `Decision · preempt` against `Decision · admit` — and never by hue alone. The measured reasons: the fill difference between `{colors.surface-raised}` and `{colors.surface-base}` is **1.09:1** and is therefore decoration, not a signal, and the two border hues sit roughly **dE 6.8** apart under deuteranopia. Hue is the third channel in this system and never the first.

**Exactly one notification, to the victim, and none to the administrator** (FR-27). A preemption is an Eviction, and FR-27's testable condition is explicit: Eviction → one notification to the submitter, zero to the administrator. The asymmetry with a Checkpoint failure (two notifications) is load-bearing and is what a reader of the notification contract should be able to derive. Copy: *"Your run on `ws-gpu-12` was stopped at 23:10 to let a `THESIS` run start. It is saved at step 18,440 and is back in the queue now."* The subject is the run, the reason is a tier — not a mood.

### SURF-06b.4 `PREEMPTION_REFUSED` — the highest-stakes record in the flow

**Rendered on the challenger, not the victim** (NP-4.1). Both jobs keep their states; no slot moves; no notification is sent, because **nothing was stopped and nothing failed** — there is no FR-27 event here at all.

| Property | Specification |
|---|---|
| **Banner group** | **Adverse** — red-bordered like every `DENY`/`DEFER`, and **separated from the job-state hue vocabulary by the group glyph and the summary text**, never by a job-state colour. |
| **Announcement** | Carries a `role="alert"` node **on first appearance**. A screen-reader user who is refused and hears nothing cannot distinguish refusal from success. |
| **Summary** | Names the reason in the reader's terms, not the record's: *the lower-priority run could not be stopped safely, so this job waits.* §6.1 caps `summary` at 200 characters, and SM-C4 says a longer summary is not a better one. |
| **The arithmetic, not the verdict** | A reader told only "preemption refused" learns nothing. A reader shown `40 < 50 + 20` learns that **the fix is a grant (FR-17), not another night's wait.** This is why the gate is two rows in SURF-06b.1. |
| **A reason to wait, not a queue position** | She must be able to tell "you are behind three jobs" from "you are blocked by a rule that will not change on its own tonight." The blocked rendering carries the rule and the checkpoint precondition; a position number does not. |
| **Not a failure** | No error styling, no retry affordance, no apology. Nothing failed; the module declined to act. |

**`self:`-alone is legitimate here, and that is the lesson of the scenario.** The refusal rests on a module-owned integrity rule — the Checkpoint Budget — with no delegated authority to name, which is F-1's split rule's second sentence. **This is the one place in the module where a `DEFER` may stand on a `self:` citation alone.** Compare `EMITTER_REJECTED` below, where the same citation class is **insufficient**.

**The once-per-window cap is not shown as an available action** (NP-4.3). The same victim may not be preempted twice in one Night Window. The surface must not invite a reader to *expect* the second stop — and FR-15(b)/(c) are the pressure valve that makes the cap survivable, since promotion guarantees the victim's next admission, so the cap costs it one window of delay and not its place in line.

**A fault-induced abort is not a preemption refusal** (NP-4.5). When a Module 3 fault arrives while the victim is `CHECKPOINTING`, the preemption is abandoned mid-flight and routes to the node-fault paths — T-16 `EVICTED_RESUMABLE` / `NODE_FAULT`, or T-17 `FAILED` / `NODE_FAULT_NO_CHECKPOINT`. The record is a `DEFER` citing the fault, the exclusion reason `M3_CORDONED` is stated on the slot, and the challenger returns to the Pending Set **with a reason it did not cause**. A surface that rendered a fault-induced abort as a preemption refusal would **blame the victim for the hardware**. The challenger never inherits a Node that has just become ineligible.

### SURF-05 deltas — Preemption rows

Canonical surface in `scenario-2.md`; Preemption adds two row shapes.

**`PREEMPT` — the row shows both digests** (FR-26):

```
23:10:00  PREEMPT         ws-gpu-12  margin 28  ·  challenger granted THESIS
          Stopped a lower-priority run to admit a higher-priority job; victim
          Checkpointing, 300 s budget.       [self:PREEMPTION-MARGIN-v1] [policy:M2/…]
```

The `margin 28` and the challenger's tier travel in the row because Ines sees **two `PREEMPT`-group banners in the activity stream within a minute of each other** and needs the record behind each without opening it. The victim's `job_id` is present in the log (it is an operator surface, FR-31(b) governs the student-facing board) and **absent from the student-facing banner** per SURF-06b.3.

**`PREEMPTION_REFUSED` — the three refusals are one row shape with three triggers**, so the surface keeps them distinguishable by reason code rather than by prose:

```
23:10:00  DEFER           —  PREEMPTION_REFUSED
          Preemption declined: no eligible victim (no verified Checkpoint within
          the 300 s budget). No job state changed.        [self:PREEMPTION-MARGIN-v1]
23:10:00  DEFER           —  PREEMPTION_REFUSED
          Preemption declined: margin 10 < required 20. Both jobs unchanged.
                                                            [self:PREEMPTION-MARGIN-v1]
23:10:00  DEFER           —  PREEMPTION_REFUSED
          Preemption declined: victim already preempted this window (FR-16(f)).
                                                            [self:PREEMPTION-MARGIN-v1]
```

Each row states **explicitly that no job state changed**, because a refusal with no state change is the one case where silence is the most likely misreading.

**`EMITTER_REJECTED` renders as a correct outcome** (NP-4.8, row shape canonical in `scenario-2.md`). Handed a `PREEMPT` record citing only `self:PREEMPTION-MARGIN-v1`, the emitter is **fail-closed**: it refuses the record, **the transition is not applied** — the victim stays `RUNNING`, the challenger stays `QUEUED_PENDING_WINDOW` — and the run is `PASSED` (FR-30). This is the one path in the module where the **absence** of a state change is the success, and a surface that animated a failed stop would invert the meaning of the record.

**A preemption loop is a regression, not a result** (NP-4.3, SM-C3). *Do not optimise Preemption count* — every Preemption costs a victim a full stop, Checkpoint write and restart. The log therefore shows **GPU-minutes lost to the stop as a counter-metric**, per window, so a rising count is legible as a mistuned Preemption Margin rather than as performance. The board must never present a high preemption count as a throughput metric.

**`UNVERIFIED_RESUME` renders identically wherever a resume fails to verify** (NP-4.10) — `DEFER` / `UNVERIFIED_RESUME` / `self:CHECKPOINT-QUARANTINE-v1`, `transition: null`, and the job **not admitted**. No partial admission exists. The same record governs T-12 and T-14, and `scenario-2.md` § NP-2.7 carries the 21:30:00 phase itself; **it is one record and it must not be rendered two different ways** in two files.
