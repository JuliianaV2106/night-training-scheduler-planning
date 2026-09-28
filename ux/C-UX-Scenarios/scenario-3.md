# 03: Dawn Stops the Work Without Losing It — Annex Scenario 3: Morning Hard Eviction (05:45)

**Project:** Proyecto final — Module 9, Night Training Scheduler
**Created:** 2026-09-28
**Method:** WDS Phase 3 (UX scenario outline), trigger document = `planning/prd.md`
**Journeys:** UJ-3 (primary) · **UJ-5 and UJ-6 (the mandatory edge case, carried as a failure branch)**
**State paths:** `RUNNING` → `CHECKPOINTING` → `EVICTED_RESUMABLE` · edge case: `CHECKPOINTING` → `EVICTION_FAILED` → `QUEUED_PENDING_WINDOW`
**Design references:** `ux/DESIGN.md` (theme, tokens, component specs) · `ux/EXPERIENCE.md` (IA, state patterns, voice)

> **Trigger-document substitution.** WDS Phase 3 normally derives scenarios from a Trigger Map produced in Phase 2. No Trigger Map exists for this project — Phases 1 and 2 were never run. The substitute is `planning/prd.md`, which supplies the same three things a Trigger Map would: named personas (§2.1), stated jobs-to-be-done, and a success-metric set (§13). See Open Question S3-Q1.

---

## Transaction

**What this scenario covers:** At 05:45:00 every running job is asked to stop, and by 06:00:00 no GPU in the building is still held. The work that cannot finish tonight is written down durably, verified by digest, and handed back to the student as a step number she can resume from. **The mandatory edge case is carried here as a failure branch:** when the Checkpoint write fails, the cost lands on a *node* — cordoned, named, off-limits for the morning lab — and not on a night's work or a morning's teaching.

---

## Business Goal

**Goal:** A human can walk into the lab at 08:00 and find a machine that works, and a student can open a message in the morning and learn that her six hours of work is intact. Neither guarantee may be bought by the other.

**PRD objective reference:** `SM-2` (Dawn guarantee — across a 30-night simulated month, the number of instants in the forbidden interval where a Node allocation is held is exactly 0) · `SM-6` (Work preservation — steps lost per interruption ≤ the steps produced in one Checkpoint interval, measured on **every** eviction, preemption and fault, **no exclusions** including T-17 and process exits) · `SM-1` (Mandated-path fidelity — the mandatory edge case executes end-to-end)

---

## User & Situation

**Persona, primary:** Kavita, senior research student. *(§2.1)*
**Persona, edge case:** Ines Okonkwo, GPU lab operations engineer. *(§2.1; F-33 — team-added persona.)*

**Situation (UJ-3), 05:44:50:** Kavita's thesis job has been running for 4 hours of an estimated 31. It is nowhere near done. The last durable Checkpoint is 22 minutes old. She is asleep; she will not see anything until morning.

**Situation (UJ-5), 05:45:** SIGTERM has been delivered. The Checkpoint write is in progress. The node's disk is full, or the write errors. She is still asleep, and this is the moment the module's hardest correctness requirement is tested.

**Situation (UJ-6), 08:00:** Ines walks the lab and finds `ws-gpu-19` reporting `SchedulingDisabled` with cause `EVICTION_CHECKPOINT_WRITE_FAILED`, and one of Kavita's jobs in `EVICTION_FAILED` with a retained verified Checkpoint. She needs to know whether it is safe to return to service.

**Hope (Kavita):** That "stopped" is not "lost", and that the message says *which step* her work is at.

**Hope (Ines):** That the machine in front of her is safe to hand to a student at 09:00, and that the reason it was taken out of service is legible without a phone call.

**Worry (Kavita):** Discovering on Monday that the queue was frozen and nobody said. Her current alternative is a spreadsheet and a group chat (FR-27's motivation).

**Worry (Ines):** **A cordoned node that was never actually faulty.** FR-23(i) records that a Checkpoint write failure caused by kubelet DiskPressure rather than a faulty Node is a possible false positive, and a blind cordon would be one. Her clearance decision is worse if she cannot tell the two apart.

> **Driving forces addressed**
> - ✅ *Want* (§2.1): "When my job was stopped at dawn, I need to know it was stopped cleanly and that six hours of work is not gone."
> - ✅ *Want* (§2.1): "I need to know at 07:00 that every GPU is released, and I need to know which node is suspect and why."
> - ❌ *Fear*: A morning lab session that starts with a machine in an unknown state.
> - ❌ *Fear* (§2.1): Silently parked work. The §1 vision is explicit that the module must not park a job "in an invisible holding pen".

---

## Device & Starting Point

**Device, UJ-3:** Kavita is asleep. **The scenario does not begin with her at a screen** — it begins with a transition she will learn about from a notification payload. This is the structural difference between this scenario and scenarios 1, 2 and 4: the critical surface at 05:45 is one Ines watches, and the critical surface at 08:00 is one she acts on.

**Device, UJ-3 for Ines:** Desktop, dark-first. She is on the Board watching the Ramp.

**Device, UJ-5:** Same board, same shift. The failure lands on her screen whether or not she is looking at the right panel.

**Device, UJ-6:** Desktop, 08:00, morning light. Node detail, reached from any slot tile.

**Entry:** Ines reaches the Cordon clearance panel from **Node detail → Cordon**. It is Ines-only, per FR-31(c): `LAB_ADMIN` may clear cordons, `STUDENT` may not.

---

## Best Outcome

**User Success, UJ-3:** The job state reads `EVICTED_RESUMABLE` with a verified Checkpoint digest, byte count and step — **not "stopped."** The slot returns to `available`. The notification names the last durable Checkpoint time, the verified step count, and the next eligible resume at 22:00 tonight.

**User Success, UJ-5 / UJ-6:** The `EVICTION_FAILED` job holds a verified resume point and no node. The GPU is free. `ws-gpu-19` is off-limits until Ines clears it, and the surface says in plain words that **the job does not wait for that** — it is re-admitted tonight onto a *different* Eligible Node. Ines's clearance panel states this too, so she does not close the incident believing she unblocked a student's run.

**Business Success:** At 06:00:00 the count of Node allocations held by this module is **exactly zero** (Invariant S-1, NFR-14, absolute, tested at every simulated minute across a 30-night run). The mandatory edge case produces, in one simulated run: a released GPU allocation, a Cordon Request, a `FAIL` Decision Record, a retained Checkpoint, two notifications, and a `CORDON` event that appears exactly once in the log alongside exactly one `FAIL` and — after Ines acts — exactly one `CORDON_CLEARED` (FR-23 testable condition, FR-26 testable condition).

---

## Shortest Path

1. **Board** — 05:44:50. Kavita's thesis job is `RUNNING`, 4 hours into an estimated 31, last durable Checkpoint 22 minutes old. Its slot tile shows `running`. Ines is on the board; the status strip carries the simulated clock, the rate control, and a countdown to the next decision point.
2. **Board + Job detail** — 05:45:00. The Eviction Ramp begins. SIGTERM reaches the job. The slot flips to `draining` — **still held**, because Invariant S-1 permits a hold in `CHECKPOINTING` until 06:00:00 — and a countdown to the 05:53:00 SIGKILL appears. The job badge flips to `CHECKPOINTING`.
3. **Job detail** — The job drains, writes a new Checkpoint, `fdatasync`s the file, atomically renames it into place, `fsync`s the parent directory, and records a SHA-256 digest. A Checkpoint verified any time before 05:53:00 — **including in the 05:50:00–05:53:00 reserve, which is still usable** (F-7) — clears the Ramp.
4. **Board + Job detail** — The job state reads `EVICTED_RESUMABLE` with a verified Checkpoint digest and a byte count. The `EVICT` Decision Record's completion entry supersedes the initiating one, carrying the same citations. The slot returns to `available`. The notification names the last durable Checkpoint time, the verified step count, and the next eligible resume at 22:00 tonight. ✓

> **The single most important rendering decision in this scenario.** `EVICTED_RESUMABLE` and `FAILED` both mean "not running", and a reader who confuses them has failed the design even though both are technically correct. A clean dawn eviction is **the module working correctly**, so the badge is `{colors.state-evicted-resumable}` violet with a `‖` pause-bar glyph and the label "Evicted, resumable" — never a terminal colour, never a desaturation, never the word "stopped". UJ-3 specifies the climax as `EVICTED_RESUMABLE` with a verified digest, "not 'stopped.'"

---

## Requirement Traceability

### Primary — `planning/prd.md` §14 row 3 and the mandatory edge case row

| FR | What it constrains in this scenario |
|---|---|
| **FR-18** | Capture a durable Checkpoint. The five-step sequence, digest/byte count/step/timestamp recorded together or not at all, partial Checkpoints deleted. |
| **FR-19** | Execute the Eviction Ramp. SIGTERM at 05:45:00 ± 2 s, SIGKILL at 05:53:00 ± 2 s, per-Node release independent of the 05:53:00 instant, no signal to a job that completed before 05:45:00. |
| **FR-23** | *Mandatory edge case.* Immediate unconditional release, no retry on the same Node, Cordon Request, `EVICTION_FAILED`, retained Checkpoint, two notifications, plus known limitations (h) and (i). |

### Supporting

| FR / NFR | Bearing |
|---|---|
| **FR-20** | Verify Checkpoint integrity on resume; Checkpoint Quarantine; **no Cordon Request for a corrupt artefact** (FR-20(e)). See NP-3.3. |
| **FR-21** | Resume from the most recent verified Checkpoint; resume point logged as a step number, not a wall-clock time. |
| **FR-22** | Govern the Checkpoint lifecycle. `CHECKPOINT_RETENTION_COUNT = 2`; the 2 most recent verified Checkpoints of a non-terminal job are never removed automatically. |
| **FR-24** | Emit a cited Decision Record for every transition; fail-closed emitter. |
| **FR-26** | Record the lifecycle event log. `CORDON_CLEARED` is a distinct event type with an actor. |
| **FR-27** | Notify the submitter **and** the administrator on Checkpoint failure. Delivery never blocks the transition. |
| **NFR-5** | Eviction timing accuracy — SIGTERM ± 2 simulated seconds of 05:45:00, SIGKILL ± 2 of 05:53:00, at every Fast-Forward rate. |
| **NFR-6** | Event fidelity under Fast-Forward — 0 dropped, 0 duplicated events across a 24-hour run at 1440×. |
| **NFR-13** | Checkpoint store bound — no protected Checkpoint deleted, escalation within 1 simulated minute. |
| **NFR-14** | Invariant S-1 — 0 allocations held at any instant ≥ 06:00:00. |

### State machine

| Transition | From → To | Decision | Reason | Citations (§6.4) |
|---|---|---|---|---|
| **T-6** | `RUNNING` → `CHECKPOINTING` | `EVICT` | — | `self:EVICTION-RAMP-v1`; `node-state:M3/…` (last health reading) — at least one non-`self:` per FR-24(a) |
| **T-8** | `CHECKPOINTING` → `EVICTED_RESUMABLE` | `EVICT` (keeps T-6's decision) | — | completion record of the initiating decision; `supersedes` = the T-6 record id; citations mirror T-6 |
| **T-9** | `CHECKPOINTING` → `FAILED` | `FAIL` | `CHECKPOINT_DEADLINE_MISSED` | `self:EVICTION-RAMP-v1` (the 05:53:00 deadline) |
| **T-10** | `CHECKPOINTING` → `EVICTION_FAILED` | `FAIL` | `CHECKPOINT_WRITE_FAILED` | `node-state:M3/…` (the write-failure evidence); `self:EVICTION-RAMP-v1` |
| **T-12** | `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW` | `RESUME` | — | `self:CHECKPOINT-QUARANTINE-v1`; `node-state:M3/…` |
| **T-13** | `EVICTED_RESUMABLE` → `FAILED` | `FAIL` | `CHECKPOINT_CORRUPT` | `self:CHECKPOINT-QUARANTINE-v1` (Quarantine) |
| **T-20** | `EVICTION_FAILED` → `QUEUED_PENDING_WINDOW` | `ADMIT` | — | `self:EVICTION-RAMP-v1` (the ramp failure being recovered); `node-state:M3/…` (**any** Eligible Node, not the cordoned one) |

**States reached:** `RUNNING` (entry) · `CHECKPOINTING` · `EVICTED_RESUMABLE` · `EVICTION_FAILED` · `FAILED` (non-happy paths) · `QUEUED_PENDING_WINDOW` (UJ-6 recovery).
**Slot states reached:** `running` · `draining` · `cordoned` · `available`.
**Decisions reached:** `EVICT`, `FAIL`, `CORDON`, `RESUME`, `ADMIT`.
**Screens:** Status strip · Board · Job detail · Decision Record detail · Node detail · **Cordon clearance** · **Quarantine release** · Event log.

---

## Scenario Steps

### Step 1 — Board, 05:44:50

- **Kavita's job is `RUNNING`.** The slot tile shows `running`, its `job_id` at `{typography.mono-data}`, and its Granted Priority tier. The tile keeps a 44 px *height* floor with no width floor; the ordinal, the glyph and the state label are mandatory, and the `job_id` moves into the accessible name and the slot inspector as the tile narrows.
- **The accessible name is two fields, not one:** `‹node_id› slot ‹n›, ‹occupancy label›, ‹eligibility label if any›`. A name that can hold only one of them is a name that lies.
- **The status strip** carries the simulated clock in `{typography.mono-data-lg}` with its explicit UTC−05:00 offset. An operator must never be unsure whether they are reading simulated or wall-clock time. Jump-to-instant offers 05:44:00 as a one-key preset precisely because it is the last second before the Ramp.

### Step 2 — 05:45:00, SIGTERM, and the slot becomes `draining`

- **T-6 fires.** Decision `EVICT`. Citations `self:EVICTION-RAMP-v1` **and** `node-state:M3/…` (the Node's last health reading). The non-`self:` citation is unconditional: **every `EVICT` and every `PREEMPT` requires at least one non-`self:` citation, without exception** (FR-24(a), NFR-4, F-1). A user's work being stopped may never be justified solely by a time or bookkeeping reason.
- **The slot flips to `draining` and stays held.** Invariant S-1 permits a hold in `CHECKPOINTING` until 06:00:00, and `draining` exists in the slot vocabulary *because* this window is where the module's hardest cases happen. A board that showed such a slot as `available` would be lying during the most safety-critical eight minutes of the night.
- **The countdown on a `draining` tile is Ramp-scoped.** Inside the Eviction Ramp, where the deadline is real, the tile reads `draining - SIGKILL in mm:ss` counting to 05:53:00. **Outside the Ramp the deadline is the 300 s Checkpoint Budget, not a wall-clock instant** — so at a 23:10 preemption the tile reads `draining - checkpointing` with elapsed seconds and no SIGKILL reference. A `draining` tile that always showed a 05:53:00 countdown would be quoting a deadline that does not exist at 23:10.
- **The `draining` hue is shared with `CHECKPOINTING`, deliberately.** `{colors.node-draining}` = `{colors.state-checkpointing}`: a draining slot is running a `CHECKPOINTING` job. The operator learns one vocabulary rather than two.
- **The `CHECKPOINTING` badge** additionally shows whether the write is inside the 300 s Checkpoint Budget (05:45:00–05:50:00) or the 05:50:00–05:53:00 reserve. **The reserve is still usable** (FR-19(b), F-7) — a Checkpoint verified any time before 05:53:00 satisfies T-8 — so the surface must not present the reserve as expired.
- **Per-Node release is independent and immediate** (FR-19(d)). Each Node's allocation is released on that job's exit, **not** at 05:53:00. A board that held every slot until the hard deadline would report jobs as still held minutes after their allocations were returned — and UJ-2's own activation puts 22 job assignments on the board, so the divergence is large enough to see at a glance.

### Step 3 — the five-step durability sequence, shown as evidence

FR-18(a) is the mechanism that makes a Checkpoint a Checkpoint, and the addendum is blunt about which step everyone omits:

> write to a temporary file → `fdatasync` the file → atomic `rename` into the final path → **`fsync` the parent directory** → compute and record the SHA-256 digest

Without the directory `fsync`, the rename is only in memory. Measured crash safety from `prd-addendum.md` §B.2: an unsafe checkpoint survived **0 of 430** crash injections.

- **Not durable until all five steps complete** (FR-18(b)). The digest, byte count, step number and `sim_timestamp` are recorded **together or not at all** (FR-18(c)).
- **FR-18(d):** a partial or undurable Checkpoint is **deleted**, never left to be discovered later.
- **Rendered:** the digest at `{typography.mono-data}` with its byte count and step. The 480 seconds of the Ramp are the least legible part of the product, and a step-numbered progress line is what converts them into something a reader can follow.

### Step 4 — `EVICTED_RESUMABLE`, and the slot returns ✓

- **T-8 fires.** The record **keeps its `decision` as `EVICT`** and sets `supersedes` to the T-6 record id, with citations mirroring the initiating record. It is the *completion* of the decision taken at T-6, not a second decision — FR-24(f) counts one record per transition, and FR-19's "one `EVICT` Decision Record per job" counts one decision chain.
- **Supersession is visible**, rendered as a `supersedes ‹decision_id›` link above the eyebrow. Records are immutable and append-only, so a revised decision appears as a new record linked to its predecessor — never as an edit.
- **The badge:** `{colors.state-evicted-resumable}` violet, glyph `‖`, label "Evicted, resumable", **no 1px terminal ring** (non-terminal). Alongside it: the retained Checkpoint **digest, byte count and step**, and the next eligible resume. Never styled or worded as a failure.
- **The slot returns to `available` and carries a reason.** FR-25(d) is unconditional: an idle slot is **never blank**, at any hour, carrying a reason code plus one human sentence. Outside the Night Window that reason is `FREE`.
- **The notification (FR-27)** names the job, the outcome, the last verified Checkpoint step, and the next eligible action. An Eviction produces **exactly one notification to the submitter and none to the administrator** — the difference from a Checkpoint failure is load-bearing and is asserted in FR-27's testable condition.
- **Copy:** "Stopped cleanly. Last durable Checkpoint is step 41,200, digest `sha256:3f9a…c201`." Not "Stopped 😢". Not "Your job was terminated". The tone is plain and technical: `Checkpointing`, not "Saving your progress…". Nothing in this system congratulates the user, apologises to them, or celebrates.

---

## The Mandatory Edge Case — `CHECKPOINTING` → `EVICTION_FAILED`

The Annex's mandatory edge case, UJ-5 plus UJ-6. Carried here as a failure branch of scenario 3, as the course requires.

### What fires

- **05:46:00, `ws-gpu-19`, Checkpoint write in progress after SIGTERM at 05:45:00. The write fails.**
- **T-10 fires.** Decision `FAIL`. Reason `CHECKPOINT_WRITE_FAILED`. Citations `node-state:M3/…` (the write-failure evidence) **and** `self:EVICTION-RAMP-v1`.
- **A `CORDON` Decision Record is issued** — non-transition record, decision `CORDON`, reason `CHECKPOINT_WRITE_FAILED`, citations `node-state:M3/…` and `self:EVICTION-RAMP-v1`. FR-23(c): a Cordon Request naming the Node and the failure is issued to Module 3, and the Node is treated as not Eligible for the remainder of the night and until a human clears it — **optimistically, pending Module 3's acknowledgement** (A-15).

### The ordering that makes this correct, and visible

FR-23's ordering is not incidental, and the surface must not obscure it:

1. **The Node allocation is released immediately and unconditionally** — **before any retry, diagnosis or notification** (FR-23(a)). A failed delivery must not delay the node release by more than **0 ms** (FR-27).
2. **The daemon must not retry the Checkpoint on the same Node** (FR-23(b)). §10.3: never evict onto a suspect Node.
3. **The last verified Checkpoint is retained, never deleted** (FR-23(e)). Invariant S-2: `EVICTION_FAILED` retains it under FR-22.
4. **Both parties are notified** — the submitting principal and the lab administrator, with the Node named and the resume point stated (FR-23(f)). FR-27's testable condition asserts **exactly two** notifications, one each.
5. **The failure is reported to the Job's status board with the same citation discipline as any other decision** (FR-23(g)).

### The climax, stated as the PRD states it

- `ws-gpu-19` is unavailable for the morning lab. Kavita's notification says her work is safe at her 03:10 Checkpoint and names the node as quarantined.
- Her badge is `EVICTION_FAILED` — `{colors.state-eviction-failed}` orange, glyph `⚡`, label "Eviction failed", **no terminal ring**, because T-20 returns it to the Pending Set and **this badge must not read as terminal**.
- **The job is not finished, and it is not waiting on a human.** It holds a verified resume point but no node. The GPU is free. The node is off-limits until Ines clears it; **the job itself is not**, and will be re-admitted tonight.
- **Why this badge is the loudest non-red treatment in the palette:** its name reads as terminal and it is not. `{colors.state-eviction-failed}` `#FFA657` appears nowhere else in either job-state set — checkable, and stated as checkable. The documented limit: under deuteranopia `{colors.state-rejected-light}` and `{colors.state-eviction-failed-light}` converge to roughly dE 1.6, so hue alone would not separate a refusal from a failed eviction in the light theme. **The glyph (`⚡` against `✕`) and the label carry it** — the same redundancy NFR-15 already requires, and the reason colour is the third channel in this system and never the first.

### UJ-6 — Ines clears the node at 08:00, and the job does not wait for her

- **Node detail → Cordon clearance**, Ines only (FR-31(c)). The panel shows the cordon cause, the failed-write evidence, and the retained Checkpoint, and states plainly that clearing the node does **not** gate the job: T-20 re-admits it onto any Eligible Node.
- **The slot reads `cordoned` and carries the cause string in place of the state label:** `cordoned · EVICTION_CHECKPOINT_WRITE_FAILED`. That cause is the whole reason FR-23(i) is satisfiable — it is what lets Ines distinguish a genuinely faulty node from a kubelet DiskPressure false positive during clearance. A cordon whose reason is a bare "unhealthy" is not actionable.
- **On release:** a `CORDON_CLEARED` event is recorded with **her as the actor** (FR-26(c)) — a distinct event type, not a status flip. The node returns to the Eligible set on its next health evaluation.
- **T-20.** At tonight's Window Activation the retained Checkpoint digest re-verifies, so the job re-enters `QUEUED_PENDING_WINDOW` → `RUNNING` on **a Node that is not `ws-gpu-19`**. Decision `ADMIT`, citations `self:EVICTION-RAMP-v1` and `node-state:M3/…` for the chosen node. The job logs `RESUMED_FROM_CHECKPOINT` with the digest it verified, and the `RESUME` banner cites the verified digest.
- **The clearance panel says this explicitly**, so Ines does not close the incident believing she unblocked a student's run. This is the sentence that makes T-20 legible to the one human whose action the scenario is waiting on.
- **Checkpoint Quarantine is a separate human obligation, with its own panel** on Job detail, reached from the `FAILED` badge rather than from the node — see NP-3.3.

---

## Non-Happy Paths

Ten, including the mandatory edge case. The PRD's own framing: *a failed Checkpoint at dawn must cost a node, not a night's work and not a morning lab session.*

### NP-3.1 — The Ramp expired without a verified Checkpoint (T-9)

- **Trigger:** 05:53:00 arrives and the job is still in `CHECKPOINTING` with no verified Checkpoint.
- **Outcome:** `FAILED`. Decision `FAIL`. Reason `CHECKPOINT_DEADLINE_MISSED`. Citation `self:EVICTION-RAMP-v1` — module-owned time rule, so `self:` alone is legitimate here (F-1 names the permitted module-owned class as scope boundary, Max Night Span, queue cap, Job Spec validation, and `EXPIRE` on a Retention Deadline; this is a `FAIL` on a time rule, which §6.2 permits as "`self:` is otherwise legitimate only for time and self-integrity rules").
- **Retained:** the last verified Checkpoint is retained (FR-19(f), FR-22).
- **At 05:53:00 SIGKILL is dispatched to every surviving job regardless of its state** (FR-19(c)). A `draining` countdown that stops at 05:53:00 **stays visible** — no banner auto-dismisses, and nothing expires the operator's ability to read why their work stopped.
- **The near-miss that is not an error:** FR-19(e) — a job that reached `COMPLETED` before 05:45:00 is **not** signalled. T-5 fires with decision `COMPLETE`, citation `self:EVICTION-RAMP-v1`, and the slot is released. A board that sent SIGTERM to a finished job would be signalling a state that no longer exists.

### NP-3.2 — **The mandatory edge case:** the Checkpoint write fails (T-10, FR-23)

Fully specified in the edge-case section above. Summary of the assertion set FR-23's testable condition requires, all of which the surface must make observable:

| Assertion | Value |
|---|---|
| `ws-gpu-19` GPU allocation released by | 05:46:01 |
| Cordon Request emitted for `ws-gpu-19` | yes |
| `ws-gpu-19` in the Eligible Node set for the rest of the window | absent |
| Job state | `EVICTION_FAILED`, reason `CHECKPOINT_WRITE_FAILED` |
| The 03:10 Checkpoint | still present and byte-identical |
| Notifications | exactly 2 — one submitter, one lab administrator |
| Jobs placed on `ws-gpu-19` for the remainder of the night | 0 |

**This is the one path in the module where a *slower* UI would be a correctness failure.** FR-23(a) requires release before diagnosis; the board must not hold a stale `draining` tile past 05:46:01.

### NP-3.3 — The retained Checkpoint fails re-verification (T-13, FR-20(c))

- **Trigger:** the 21:30:00 pre-verification phase recomputes the recorded SHA-256 digest and it does not match a re-read of the bytes.
- **Outcome:** the Checkpoint is placed in **Checkpoint Quarantine**; the job transitions to `FAILED` with reason `CHECKPOINT_CORRUPT`; a `FAIL` Decision Record cites `self:CHECKPOINT-QUARANTINE-v1`; a human is notified.
- **`CHECKPOINT_CORRUPT` is a reason code on `FAILED`, not a tenth state.** The badge set has nine; a design that calls it "a first-class state" has a developer adding a badge nobody defined. FR-25(a): every state a job can occupy is one of the nine in §4.1 and no other.
- **FR-20(e): no Cordon Request is issued, because a corrupt file is not evidence of a faulty Node.** This is a hard rendering constraint — the surface must **not imply the node is suspect**, must not grey out a slot tile, and must not route the reader toward a cordon action. The two failures look similar on a status board and mean opposite things about the hardware.
- **Quarantine release is a human obligation with a surface:** the Quarantine release panel on Job detail, reached from the `FAILED` badge. It shows the digest mismatch as evidence, requires a reason code, records the releasing actor, and repeats FR-20(e). A quarantined Checkpoint is excluded from garbage collection until released (FR-20(d)) and is never removed automatically (FR-22(c)) — it is a live liability with a named owner, so the surface must say who owns it.
- **Invariant S-2 note:** `FAILED` here is not one of the three exits that end a job with admitted work incomplete *and* retain the last verified Checkpoint under the 7-day grace — this job's last verified Checkpoint is the one that failed verification, which is why it is in Quarantine rather than retained.

### NP-3.4 — A node fault with no verified Checkpoint (T-17)

- **Trigger:** Module 3 reports a node fault while the job is `RUNNING`, and no verified Checkpoint exists for this run segment.
- **Outcome:** `FAILED`. Reason `NODE_FAULT_NO_CHECKPOINT`. Citation `node-state:M3/…` — the fault, and a delegated telemetry authority.
- **Contrast with T-16:** the same node fault with a verified Checkpoint available routes to `EVICTED_RESUMABLE` (T-16, decision `EVICT`, reason `NODE_FAULT`, `node-state:M3/…`) and re-queues. Whether such a job should be re-placed *immediately* on another node rather than waiting for the next window is PRD Open Question 10, and the surface currently shows the next-window behaviour.
- **Rendered:** the work since the last Checkpoint is unrecoverable, and the surface says so with the reason code. This is one of the interruptions `SM-6` covers with **no exclusions**.

### NP-3.5 — The training process exits mid-run (T-22 / T-23)

Two branches on the same trigger, and the PRD keeps them apart because the difference is whether work survives:

| Transition | Condition | To | Decision | Reason | Citation |
|---|---|---|---|---|---|
| **T-22** | a verified Checkpoint exists **and** fewer than 1 automatic `PROCESS_EXIT` retry used this night (**max 1**, F-10) | `EVICTED_RESUMABLE` | `EVICT` | `PROCESS_EXIT` | `node-state:M3/…` (the process-exit telemetry) |
| **T-23** | no verified Checkpoint exists for this run segment | `FAILED` | `FAIL` | `PROCESS_EXIT_NO_CHECKPOINT` (`OOM_KILLED` / `PROCESS_EXITED`) | `node-state:M3/…` |

- **The `OOM_KILLED` remediation is mandatory** (FR-29(a)): an `OOM_KILLED` exit additionally emits a cited Decision Record suggesting a lower batch size or a 48 GB-class Node — which is `server-gpu-01`. FR-4's spec-reduction advice for `MAX_NIGHT_SPAN_EXCEEDED` has an obvious twin here, and leaving the OOM case without it would be an omission rather than a judgement.
- **Rendered on the `FAILED` badge:** reason code `OOM_KILLED` or `PROCESS_EXITED`, confirmation that the last verified Checkpoint is retained per FR-22 and Invariant S-2, and the cited remediation.
- **The "one retry per night" cap is a governance rule, not a bug.** The surface must not present a job that exhausted its retry as retryable.

### NP-3.6 — The T-20 recovery guard fails (T-19)

- **Trigger:** a job in `EVICTION_FAILED` reaches the next Window Activation, but its Admitted Nights has already reached the Max Night Span of 5.
- **Outcome:** T-20's guard requires **a verified Checkpoint is retained AND Admitted Nights < Max Night Span** — otherwise **T-19 applies**: `FAILED`, reason `MAX_NIGHT_SPAN_EXCEEDED`, citation `self:MAX-NIGHT-SPAN-v1`, retained Checkpoint preserved.
- **Why this is a distinct branch and not a variant of NP-3.2:** a job in `EVICTION_FAILED` is non-terminal and recoverable, and the surface must not promise a recovery that FR-4(d) will refuse. Invariant S-3: a job is refused admission rather than admitted and immediately evicted, so span exhaustion must never manifest as a wasted night.
- **Rendered:** the refusal Decision Record names `MAX_NIGHT_SPAN_EXCEEDED` **rather than silently evicting it** (FR-21(f)), and the retained Checkpoint and the step it reached are both stated so a human can decide whether to resubmit a reduced scope.

### NP-3.7 — The Checkpoint is interrupted mid-sequence (FR-18(d))

- **Trigger:** a Checkpoint is interrupted after `rename` but before the parent-directory `fsync` — the step the addendum names as the one everyone omits, and the one that makes a Checkpoint a Checkpoint.
- **Outcome:** the Checkpoint is treated as **not durable and is deleted**. The next night's resume does not find it, and the job re-enters `QUEUED_PENDING_WINDOW` **with no attached Checkpoint**.
- **The rendering rule this creates:** a `draining` tile that has visibly written its file is still `draining`. There is no intermediate "checkpoint written" state to show, because FR-18(b) says the Checkpoint is not considered durable until all five steps complete. A surface that showed a partial write as success would be claiming a durability the system does not have.

### NP-3.8 — The daemon crashes during the Ramp (T-18, FR-9)

- **Trigger:** an abrupt daemon kill between 05:45:00 and 05:53:00.
- **Outcome:** every job's state is restored from the durable decision log **with no replay of any transition**. Job states are `unchanged`. Decision `DEFER`, reason `DAEMON_RESTORE`, citation `self:RECONCILIATION-v1`. FR-9(b) then runs reconciliation as a **separate recorded step**; because the Night Window is still open, activation is performed immediately with a `RECONCILIATION_ACTIVATION` record.
- **NFR-10's tolerance is zero:** an abrupt kill at any instant loses **0 committed transitions** and produces **0 duplicate transitions**, tested by killing at 1000 seed-derived instants per run. That is why emission is durable **before** the transition is committed, not after (FR-24(e)).
- **Rendered:** the board is restored, not replayed. A board that re-ran the Ramp would show Checkpoint writes the disk has already accepted.

### NP-3.9 — Checkpoint store pressure at 03:00 (FR-22(d), NFR-13)

- **Trigger:** the store exceeds `CHECKPOINT_STORE_BUDGET` `[ASSUMPTION: A-10]`, which the PRD sizes from Σ over non-terminal jobs (2 × checkpoint_size) rather than fixing a number.
- **Outcome:** the oldest eligible `EXPIRED`-job Checkpoints are removed first and **the pressure is reported**. If only non-terminal or quarantined Checkpoints remain and the budget is still exceeded, **collection halts and escalates to a human rather than deleting them.**
- **The invariant that must survive contact with the UI:** **the 2 most recent verified Checkpoints of a non-terminal job are never removed automatically** (FR-22(b)), and no Quarantined Checkpoint is ever removed automatically (FR-22(c)). Under NFR-13, a single protected deletion fails the build.
- **Why it belongs in this scenario:** a job's survival at dawn depends on a Checkpoint existing, and the store pressure that can delete one runs at 03:00, in the middle of the night whose work is at stake. Cross-referenced from scenario 1's NP-1.7, where the same budget produces a submission refusal.

### NP-3.10 — A job that finished just before the Ramp (FR-19(e))

Carried as a near-miss in NP-3.1 rather than as a failure. Restated because it is a *design* obligation, not a PRD obligation: a job that reached `COMPLETED` at 05:44:00 is not signalled, its slot is released, and its badge is `COMPLETED` — terminal, with the 1px `{colors.border-structure}` ring. A board that showed it as `CHECKPOINTING` would be reporting a SIGTERM that was never sent, and **no celebratory treatment** belongs on the transition: the success signal is the countdown marker and the slot tile reaching its terminal state.

---

## Open Questions

**S3-Q1 — The trigger document is a PRD, not a Trigger Map.** WDS Phase 3 reads persona driving forces and business objectives from a Phase 2 Trigger Map. None exists for this project. Personas (§2.1), jobs-to-be-done and success metrics (§13) were taken from `planning/prd.md` instead. If Phases 1 and 2 are ever run, this scenario's Business Goal and Driving Forces sections should be re-anchored to the real objective ids.

**S3-Q2 — No deadline is pinned on a *preemption* drain.** Invariant S-1 and FR-19(d) govern the dawn Ramp, where the slot may be held until 06:00:00. FR-16(d) says a challenger does not start until the victim's Checkpoint verifies and the Node is released, but pins no deadline on that drain — and the Checkpoint Budget (A-9) is defined as the 300 s window *inside the Ramp* (05:45:00–05:50:00), so at a 23:10 preemption the tile has a budget and no hard deadline. NP-3.7's rule and scenario 4's NP-4.4 both depend on the answer. Rendered for now as `draining` with elapsed budget seconds and no SIGKILL reference.

**S3-Q3 — No named surface for a Cordon Request that Module 3 *rejects*.** FR-23(h) says that on rejection this module still keeps the Node locally not-Eligible for the remainder of the night, and records the rejection in a Decision Record. The PRD names no console surface for a rejected outbound request, so the local exclusion would exist as a state with no counterpart event on screen. NP-3.2a renders it as a cause change on the slot tile plus an event-log entry.

**S3-Q4 — FR-23(i)'s false positive has no remediation affordance.** The limitation is explicit that a Checkpoint write failure caused by kubelet DiskPressure is a possible false positive rather than a faulty Node, and that the cordon reason names the failure so Ines can distinguish the two. The PRD specifies the *reason string* but no action Ines can take to record "this was DiskPressure, not hardware" — she must make that judgement from evidence with nowhere to put it. NP-3.2b renders the evidence and leaves the distinction with her.

**S3-Q5 — The rate control's initial state is unstated (shared with S1-Q5, S2-Q5).** FR-28(a) fixes the rate set (1×, 60×, 360×, 1440× plus pause). What a run *starts* at, and whether a rate survives a page reload mid-Ramp, is unspecified — and it bites hardest here, because an operator watching an 8-minute Ramp at 1440× may never see the 05:50:00–05:53:00 reserve at all.

---

## Page Specifications

> **Phase 4 — WDS UX design.** Canonical specifications for **SURF-06** (administrator shell), **SURF-06a** (Cordon clearance), **SURF-07** (Node detail), **SURF-08** (Quarantine release), plus **deltas** to SURF-04 Job detail, SURF-04b Decision Record detail and SURF-05 Event log. `scenario-1.md` owns SURF-04/04b and `scenario-2.md` owns SURF-05; this file specifies only what the dawn Ramp adds to them. Sources, in precedence order: `planning/prd.md` → `ux/EXPERIENCE.md` → `ux/DESIGN.md` → this section. Conventions are stated once in `scenario-1.md`.

### SURF-06.1 The administrator shell

**Persona: `LAB_ADMIN` only** (FR-31(c)). Reached from the Board's left rail as **`Handover`**, `g w` — a name chosen for the 08:00 job Ines actually walks in to do, not for the entities involved.

The PRD names no morning-handoff surface. What it *does* name is a set of facts that land on a human between 05:46 and 09:00 with **no other owner**: FR-23(i) names a human clearing a cordon, FR-20(d) names a human releasing a quarantined Checkpoint, FR-27(f) notifies the lab administrator on Checkpoint failure, and FR-24 records a Cordon Request that may be **rejected** by Module 3. Four PRD obligations, three actor-specific surfaces, and no index connecting them — so the shell is a design decision, not a requirement, and is **flagged for review (S3-Q7)**.

| Block | Content |
|---|---|
| **Suspect Nodes** | One row per cordoned Node: `node_id`, the **cordon cause string**, the incident `sim_timestamp`, and the clearance status. Default sort — most recent first, because Ines's first question at 08:00 is *what happened last night*. |
| **Outstanding obligations** | Quarantined Checkpoints awaiting release, each with its owner and the fact that FR-22(c) protects it from automatic removal. A quarantined Checkpoint is a **live liability with a named owner**; an unowned one is how it becomes a permanent store leak. |
| **Unacknowledged Cordon Requests** | A Cordon Request that **Module 3 rejected** (FR-23(h)) — recorded, with the local exclusion still in force. See SURF-06.3. |
| **Recent notifications** | The `LAB_ADMIN` side of FR-27, the outbox from `scenario-2.md` § SURF-05. |
| **Fleet release count** | The Invariant S-1 answer for the 06:00 boundary, stated as a number. |

**Nothing here auto-clears and nothing expires.** The same rule as every other surface in this module: no banner dismisses itself, no badge times out, and the 08:00 surface still carries the 05:46 incident at 17:00. An operator who closes a tab and comes back must not have to reconstruct what the night did from memory.

### SURF-06.2 Node detail — SURF-07

**Entry:** any slot tile → `Enter`, `g n`, or the Board's tile inspector.

| Block | Content |
|---|---|
| **Identity** | `node_id`, VRAM class and count — `ws-gpu-19`, 1 × 24 GB; `server-gpu-01`, 2 × 48 GB. |
| **Health** | The last Module 3 reading, the reading's `sim_timestamp`, and the transition-time failure points (FR-23(d)(1)(2) calls out kubelet eviction and disk errors specifically). |
| **Current cordons** | Every active cordon with its **cause string**, the incident instant, and the state of the outbound Cordon Request. |
| **Cordon / Clear cordon** | The single mutation this surface owns. `LAB_ADMIN` only. |
| **Assigned jobs** | Occupants of the Node's slots. |
| **History** | Events for this Node, linking to SURF-05. |

**Clearing a cordon is the panel's only write.** One verb, one actor, one irreversible-ish consequence — so Node detail is a **read surface plus exactly one action**, and every other affordance is a link. The panel it opens is SURF-06a.

**The slot inspector, once the tile is too narrow to read.** Because a `draining` countdown and a cordon cause string cannot both live in a 44px tile at the desktop floor, the tile keeps a **hover/focus tooltip carrying the cause string unabbreviated**, and `Enter` promotes the tile to a full-width inspector row beneath the grid. The cause string is never truncated in the accessible name.

### SURF-06.3 Cordon clearance — SURF-06a

**Ines's decision surface, and the reason this scenario's second persona exists.** `LAB_ADMIN` only; the action is **absent from `Kavita`'s DOM entirely** (FR-31(c)).

The panel shows three things, in this order, because the order is the argument:

1. **The cause** — `EVICTION_CHECKPOINT_WRITE_FAILED`, the incident `sim_timestamp`, and the affected `job_id`.
2. **The evidence** — the write-failure evidence from `node-state:M3/…`: the failed write, the node's kubelet state, its disk state, and any concurrent transitions. FR-23(i)'s false positive is a **kubelet DiskPressure** condition rather than a faulty Node, and the PRD's stated remedy is the *reason string* — so the reason string and the evidence must both be on screen, unabbreviated, or the whole limitation is decorative.
3. **The consequence statement** — see below.

> **The sentence that makes this panel honest:**
> *Clearing this cordon returns `ws-gpu-19` to the Eligible Node set at its next health evaluation. It does **not** release the job. `EVICTION_FAILED` re-admits tonight onto a different Eligible Node (T-20).*

Without that sentence Ines closes the incident believing she unblocked a student's run. It is the highest-value sentence in the module and the PRD's state machine does not require it.

| Property | Specification |
|---|---|
| **Actor** | The clearing principal is recorded on the event (FR-26(c)). The panel shows who is acting **before** the click. |
| **Confirmation** | Requires an explicit confirm naming the Node and the cause. Clearing a cordon is a safety-relevant act, so unlike the clock control (SURF-02b) this **does** confirm. |
| **Eligibility return** | *At the next health evaluation* — never immediately on click, and the panel says so. A cordon dropped by fiat rather than by a health reading is a state no invariant in the PRD is written against. |
| **Event** | `CORDON_CLEARED` — a **distinct event type with an actor** (FR-26(c)), not a status flip. It appears in SURF-05 **exactly once**, alongside exactly one `CORDON` and exactly one `FAIL` (FR-23's testable condition). |
| **Effect on the job** | **None.** T-20 re-admits onto **any** Eligible Node, explicitly *not* the cordoned one. The panel repeats this. |
| **No remediation affordance** | FR-23(i) has none (**S3-Q4**). The panel renders the evidence and leaves the DiskPressure-versus-hardware judgement with Ines. Inventing a "mark as DiskPressure" control would be a design decision presenting itself as a PRD feature, and no PRD requirement backs it. |
| **Loading · Empty · Error** | Loading: the evidence block in skeletons at final geometry. Empty: no active cordons — `No active cordons.` Error: the health reading is unavailable, in which case clearance is **disabled and the reason stated**; clearing against an unread health reading is the one action in this module that can make a machine worse. |

**A rejected outbound Cordon Request (FR-23(h))** renders as a **cause change on the slot tile plus an event-log entry** (**S3-Q3**): the local exclusion persists for the rest of the night and is labelled *locally not-Eligible, Module 3 rejected the request* rather than `M3_CORDONED`. The distinction is a correctness fact — the exclusion is this module's own conservatism, not a health verdict — and collapsing it into the normal cordon cause would have Ines clear a node that Module 3 never believed was sick.

### SURF-06.4 Quarantine release — SURF-08

**Entry: the `FAILED` badge on Job detail → Checkpoint Quarantine.** Design decision **D-d**: the release lives under the **job**, not the Node, because a corrupt Checkpoint is a property of a *file* and is **not evidence of a faulty Node** (FR-20(e)).

| Property | Specification |
|---|---|
| **Evidence** | The recorded digest, the recomputed digest, the byte count, the step, and the `sim_timestamp` of verification. The mismatch is shown as two values, never as a boolean. |
| **Required reason code** | A reason code is mandatory on release; a free-text-only field would make the release unauditable. |
| **Actor** | Recorded. The panel states who owns the obligation. |
| **FR-20(e), stated on the panel** | *Releasing a quarantined Checkpoint does not return any Node to service, and a corrupt Checkpoint is never evidence of a faulty Node. No Cordon Request was issued.* |
| **Hard rendering constraint** | The surface must **not** grey out a slot tile, **not** imply the node is suspect, and **not** offer a link toward a cordon action. A corrupt file and a sick machine look similar on a status board and mean opposite things. |
| **Protection** | A quarantined Checkpoint is excluded from garbage collection until released (FR-20(d)) and never removed automatically (FR-22(c)). The panel says it is protected, because "protected" and "will never be cleaned up" are the same sentence to whoever finds it in six months. |
| **Not a tenth state** | `CHECKPOINT_CORRUPT` is a **reason code on `FAILED`**, not a state. FR-25(a): the badge set has nine and no other. |
| **Invariant S-2 caveat** | This `FAILED` is **not** one of the three exits that end a job with admitted work incomplete *and* a retained verified Checkpoint under the 7-day grace — the last verified Checkpoint is the one that failed verification, which is precisely why it is in Quarantine rather than retained. |
| **Loading · Empty · Error** | Loading: skeleton evidence rows. Empty: `No Checkpoints in Quarantine.` Error: digest evidence unavailable → release disabled, reason stated. |

### SURF-04 deltas — the Ramp, on Job detail

Canonical surface in `scenario-1.md`; the dawn Ramp adds these blocks.

**The five-step durability sequence renders as evidence, not as a spinner.** FR-18(a), in order, with the current step marked:

```
write to a temporary file  →  fdatasync the file  →  atomic rename into the final path
                           →  fsync the parent directory  →  compute and record the SHA-256 digest
```

The **`fsync` the parent directory** step is called out by name and given equal weight, because `prd-addendum.md` §B.2 measures an unsafe Checkpoint surviving **0 of 430** crash injections without it, and it is the step a developer omits. A reader who has never seen a Checkpoint implementation is being told *why this takes eight minutes*, and the answer is a directory `fsync`.

- **All five or nothing** (FR-18(b)). The digest, byte count, step number and `sim_timestamp` are recorded **together or not at all** (FR-18(c)) — the surface therefore shows a single "verified" row that is either complete or absent, never a digest without a byte count.
- **A partial or undurable Checkpoint is deleted, never surfaced** (FR-18(d)). NP-3.7: a `draining` tile that has visibly written its file is still `draining`, because there is no intermediate "checkpoint written" state. A surface showing a partial write as success would claim a durability the system does not have.
- **The 300 s Checkpoint Budget and the 05:50:00–05:53:00 reserve render as two distinct phases** on the `CHECKPOINTING` badge. **The reserve is still usable** (FR-19(b), F-7) — a Checkpoint verified any time before 05:53:00 satisfies T-8 — so nothing in the UI may present the reserve as expired or degraded. It is the safety margin, and the surface says so.
- **The completion record supersedes, visibly.** T-8 keeps `decision: EVICT` and sets `supersedes` to the T-6 record id, mirroring T-6's citations. Rendered as a `supersedes ‹decision_id›` link above the eyebrow in SURF-04b. Records are immutable and append-only, so a revised decision is a new record linked to its predecessor — **never an edit**.

**Ramp-scoped vs budget-scoped countdown — the rule that makes `draining` honest.**

| Context | Tile text |
|---|---|
| **Inside the Eviction Ramp** (deadline real) | `draining · SIGKILL in mm:ss`, counting to 05:53:00 |
| **Outside the Ramp** (e.g. a 23:10 preemption) | `draining · checkpointing · elapsed ‹n›s / 300s`, **no SIGKILL reference** |

FR-19(d) and Invariant S-1 govern the dawn Ramp, where a slot may be held until 06:00:00. FR-16(d) pins **no** deadline on a preemption drain (**S3-Q2**), and the Checkpoint Budget (A-9) is defined as the 300 s window *inside* the Ramp. A `draining` tile that always quoted a 05:53:00 countdown would be quoting a deadline that does not exist at 23:10 — so **the countdown is Ramp-scoped and the budget is not**.

**`EVICTED_RESUMABLE` and `FAILED` must never be confusable.** The single most important rendering decision in this scenario. A clean dawn eviction is **the module working correctly**:

| | `EVICTED_RESUMABLE` | `EVICTION_FAILED` |
|---|---|---|
| Token | `{colors.state-evicted-resumable}` violet | `{colors.state-eviction-failed}` `#FFA657` |
| Glyph | `‖` | `⚡` |
| Label | Evicted, resumable | Eviction failed |
| Terminal ring | **no** | **no** — T-20 returns it to the Pending Set |
| Resume point | verified digest, byte count, step | **retained** last verified Checkpoint |
| Node | released | released |

`{colors.state-eviction-failed}` appears **nowhere else** in either job-state set — checkable, and stated as checkable. The documented limit: under deuteranopia `{colors.state-rejected-light}` and `{colors.state-eviction-failed-light}` converge to roughly **dE 1.6**, so hue alone would not separate a *refused* job from a *failed eviction* in the light theme. **The glyph (`⚡` against `✕`) and the label carry it** — colour is the third channel in this system and never the first.

**The word "stopped" is banned** on every surface here. UJ-3's climax is `EVICTED_RESUMABLE` with a verified digest, "not 'stopped.'" Notification copy is plain and technical: *"Stopped cleanly. Last durable Checkpoint is step 41,200, digest `sha256:3f9a…c201`."* Not "Saving your progress…". Nothing in this system congratulates the user, apologises to them, or celebrates.

**`PROCESS_EXIT` branches render differently because the work differs** (T-22 / T-23, F-10):

| Branch | Renders |
|---|---|
| **T-22** — verified Checkpoint exists, fewer than 1 automatic retry used tonight | `EVICTED_RESUMABLE`, `PROCESS_EXIT`, `node-state:M3/…`. The retry badge shows it was the **first** retry. |
| **T-23** — no verified Checkpoint for this run segment | `FAILED`, `PROCESS_EXIT_NO_CHECKPOINT` (`OOM_KILLED` / `PROCESS_EXITED`), the retained-Checkpoint statement, and — for `OOM_KILLED` — the **mandatory cited remediation** suggesting a lower batch size or a 48 GB-class Node, i.e. `server-gpu-01` (FR-29(a)). |

**The one-retry-per-night cap is a governance rule, not a fault.** A job that has exhausted it is **not** presented as retryable. "You can try again" on a job the policy will refuse is a promise the daemon will break tonight.

**Per-Node release is independent and immediate** (FR-19(d)): each Node's allocation is released on that job's exit, **not** at 05:53:00. At 05:44:50 a `running` tile reads `draining`; at 05:46:01 `ws-gpu-19` reads `cordoned` while every other job's slot is already `available` — the board must not hold every slot until the hard deadline and report jobs as held minutes after their allocations were returned.

### SURF-05 deltas — the Ramp's event rows

Canonical surface in `scenario-2.md`; the Ramp adds three row shapes, each **exactly once** per incident (FR-23's testable condition).

**`CORDON`**

```
05:46:00  CORDON          ws-gpu-19  EVICTION_CHECKPOINT_WRITE_FAILED
          Checkpoint Request issued to Module 3; Node not Eligible for the remainder
          of the night and until a human clears it.            [node-state:M3/…] [self:EVICTION-RAMP-v1]
```

Optimistically pending Module 3's acknowledgement (A-15), which the row states — the exclusion is this module's decision until Module 3 agrees, and the copy must not imply a health verdict Module 3 never returned.

**`CORDON_CLEARED`** — a **distinct event type with an actor** (FR-26(c)), not a status flip:

```
08:05:00  CORDON_CLEARED  ws-gpu-19  actor: ines.okonkwo
          Cordon cleared; Node returns to the Eligible set at its next health
          evaluation. The associated job was not blocked by this cordon.        [self:CORDON-CLEARANCE-v1]
```

**`FAIL`** — reason-scoped, and the reason is the whole content:

```
05:46:00  FAIL            JOB-0417   CHECKPOINT_WRITE_FAILED
          Checkpoint write failed; last verified Checkpoint retained, byte-identical.
          Node allocation released 05:46:01.                    [node-state:M3/…] [self:EVICTION-RAMP-v1]
```

**Failures and cordons are recorded with the same rigour as successes** (FR-26(b)) — that clause exists because the alternative is a log that only remembers the good parts. The `DELIVERY_FAILED` and `EMITTER_REJECTED` row shapes are in `scenario-2.md`.

**`EVICT` and the completion pair.** T-6 and T-8 are **one** Decision chain: FR-24(f) counts one record per transition and FR-19's "one `EVICT` Decision Record per job" counts one decision. The log renders them as **two rows linked by `supersedes`**, so the replay key is intact and the chain is legible. Rendering them as two decisions would overstate the count FR-19 constrains.

### SURF-04b deltas — Ramp decisions and the notification record

**`EVICT` (T-6 / T-8).** Citations `self:EVICTION-RAMP-v1` **and** `node-state:M3/…`. **The non-`self:` citation is unconditional** — every `EVICT` and every `PREEMPT` requires at least one non-`self:` citation, without exception (FR-24(a), NFR-4, F-1). A user's work being stopped may never be justified solely by a time or bookkeeping reason, and the record's citation list is where that is checked.

**`FAIL` reasons in this scenario, with their permitted citation classes** (F-1 governs, and the classes differ):

| Reason | `self:` alone permitted? | Citations |
|---|---|---|
| `CHECKPOINT_DEADLINE_MISSED` (T-9) | **yes** — a time rule (§6.2) | `self:EVICTION-RAMP-v1` |
| `CHECKPOINT_WRITE_FAILED` (T-10) | no | `node-state:M3/…`, `self:EVICTION-RAMP-v1` |
| `CHECKPOINT_CORRUPT` (T-13) | **yes** | `self:CHECKPOINT-QUARANTINE-v1` |
| `NODE_FAULT_NO_CHECKPOINT` (T-17) | **no** — a delegated telemetry authority | `node-state:M3/…` |
| `MAX_NIGHT_SPAN_EXCEEDED` (T-19 guard) | **yes** — named module-owned class | `self:MAX-NIGHT-SPAN-v1` |

**`DEFER` / `DAEMON_RESTORE` (T-18).** Restoration makes **no new decision** and defers everything to the separate reconciliation step; job states are `unchanged` and **no transition is replayed**. The record is visibly a *restore*, not a *recovery* — a board that re-ran the Ramp would show Checkpoint writes the disk has already accepted (NP-3.8). NFR-10's tolerance is zero: **0 committed transitions lost, 0 duplicated**, which is why emission is durable *before* the transition commits (FR-24(e)).

**The T-20 recovery guard is visible before it is relied on.** A job in `EVICTION_FAILED` needs **a verified Checkpoint retained AND Admitted Nights < Max Night Span**; otherwise **T-19** applies and the job is refused. The `EVICTION_FAILED` badge therefore states both preconditions rather than promising a recovery FR-4(d) may refuse — Invariant S-3, so span exhaustion never manifests as a wasted night. When T-19 does fire, the refusal record names `MAX_NIGHT_SPAN_EXCEEDED` **rather than silently evicting** (FR-21(f)), and states the retained Checkpoint and the step it reached, so a human can decide whether to resubmit a reduced scope.

**Notifications (FR-27).** An Eviction produces **exactly one** notification, to the submitter, and **none to the administrator** — the difference from a Checkpoint failure is load-bearing and is asserted in FR-27's testable condition. A Checkpoint failure produces **exactly two**: the submitting principal and the lab administrator, with the Node named and the resume point stated (FR-23(f)). The notification record is visible in the Notification tab of SURF-04b for the submitter, and in SURF-06 for the administrator.

**Delivery never blocks the transition, and never delays the release by more than 0 ms** (FR-23(a), FR-27). A `DELIVERY_FAILED` row in the log and a stale `draining` tile is the *forbidden* combination: the board must not hold a tile past 05:46:01 because a notification is slow. **This is the one path in the module where a slower UI would be a correctness failure.**

**Store pressure at 03:00** (FR-22(d), NFR-13) renders as a board capacity banner and as a Job detail notice on affected jobs, both stating that **the 2 most recent verified Checkpoints of a non-terminal job and every Quarantined Checkpoint are never removed automatically** — a single protected deletion fails the build. Cross-referenced from scenario 1's NP-1.7, where the same budget produces a submission *refusal*; the same fact is a refusal to a submitter and a capacity notice to an operator, and neither surface may imply the other.

**No banner auto-dismisses, and no countdown disappears.** A `draining` countdown that hits 05:53:00 **stays visible** with the reason the work stopped. Nothing expires the operator's ability to read why their job was stopped at 09:00.
