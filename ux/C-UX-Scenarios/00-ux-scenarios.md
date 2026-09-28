# 00 — UX Scenarios: Index and Coverage

**Project:** Proyecto final — Module 9, Night Training Scheduler
**Created:** 2026-09-28
**Phase:** WDS Phase 3 (UX scenario outlines)
**Trigger document:** `planning/prd.md`
**Companion design artifacts:** `ux/DESIGN.md` · `ux/EXPERIENCE.md` · `ux/wireframes/01-status-board.md` · `ux/wireframes/02-job-detail.md` · `ux/wireframes/03-submission-form.md`

> **Trigger-document substitution — applies to all four files.** WDS Phase 3 normally derives scenarios from a Trigger Map produced in Phase 2. No Trigger Map exists for this project; Phases 1 and 2 were never run. `planning/prd.md` is used as the substitute, because it supplies the same three things a Trigger Map would: named personas (§2.1), stated jobs-to-be-done (§2), and a success-metric set (§13). Recorded in each file as S1-Q1, S2-Q1, S3-Q1 and S4-Q1 rather than papered over.

> **Output location — a deviation from the module config.** `_bmad/wds/config.yaml` declares an output root of `{project-root}/_bmad-output`. These artifacts were written to `{project-root}/ux/` instead, at the user's direction, because the sibling design artifacts (`DESIGN.md`, `EXPERIENCE.md`, `WIREFRAMES.md`) already live there and a scenario set that references design files by relative path is more useful beside them.

---

## 1. The Four Scenarios

| # | File | Journey | State path | Non-happy paths |
|---|---|---|---|---|
| 1 | [`scenario-1.md`](./scenario-1.md) — Daytime Submission & Queuing | UJ-1 | — → `QUEUED_PENDING_WINDOW`; NP-1.8 → `EXPIRED` | 8 |
| 2 | [`scenario-2.md`](./scenario-2.md) — Night Window Activation (22:00) | UJ-2 | `QUEUED_PENDING_WINDOW` → `RUNNING` | 9 |
| 3 | [`scenario-3.md`](./scenario-3.md) — Morning Hard Eviction (05:45) | UJ-3, **UJ-5, UJ-6** | `RUNNING` → `CHECKPOINTING` → `EVICTED_RESUMABLE`; edge case → `EVICTION_FAILED` | 10 |
| 4 | [`scenario-4.md`](./scenario-4.md) — Priority Queue Preemption | UJ-4 | `RUNNING` → `CHECKPOINTING` → `EVICTED_RESUMABLE`; challenger `QUEUED_PENDING_WINDOW` → `RUNNING` | 10 |

**Total: 4 scenarios, 37 non-happy paths.** Every scenario exceeds the two-path minimum the brief required; scenario 3 carries the Annex's mandatory edge case as a full section plus NP-3.2, and scenario 4 carries `PREEMPTION_REFUSED` as NP-4.1 and NP-4.2.

The four scenarios are fixed by the course Annex and are not extended by this set. The `EXPIRED` state is covered **inside** scenario 1 as NP-1.8, not by a fifth scenario: the Retention Deadline is assigned at admission by FR-7(b) and surfaced in the HTTP 201 response, so that is where a reader meets it — its resolution is late, but its cause and its promise are not.

Each file follows one structure, adapted from `.agents/skills/wds-3-scenarios/data/scenario-outline-template.md`: Transaction · Business Goal · User & Situation · Device & Starting Point · Best Outcome · Shortest Path · Requirement Traceability · Scenario Steps · Non-Happy Paths · Open Questions.

---

## 2. Coverage — scenario × FR

`P` = primary FR for that scenario (per PRD §14). `s` = supporting.

| FR | 1 | 2 | 3 | 4 | Notes |
|---|:--:|:--:|:--:|:--:|---|
| FR-1 Submission | **P** | s | | | FR-1's *surface* basis ("desktop") is scoped to submission, not the board — S1-Q2 |
| FR-2 Job Spec validation | **P** | s | | | |
| FR-3 Single-node scope boundary | s | s | | | NP-1.1 |
| FR-4 Max Night Span | **P** | s | s | s | T-19 guard: NP-2.9, NP-3.6 |
| FR-5 Idempotency | s | s | s | | NP-1.4 |
| FR-6 Blocked authority (entitlement, policy, catalog, freeze) | s | s | s | | NP-1.5, NP-2.4, NP-2.8 |
| FR-7 Retention Deadline | s | s | | | `QUEUE_DEPTH_CAP`; **NP-1.8** — the Retention Deadline passing (T-15 → `EXPIRED`) and the 7-day expiry grace (FR-7(c)) |
| FR-8 Window Activation | | **P** | | s | |
| FR-9 Reconciliation | | s | s | | NP-2.6, NP-3.8 |
| FR-10 Daemon Clock | | s | s | | NP-2.5 |
| FR-11 Node isolation | s | s | | s | |
| FR-12 Eligible Node set | | **P** | | s | NP-4.5 |
| FR-13 Node selection | s | **P** | s | s | `PRIOR_NODE_INELIGIBLE`: NP-4.6 |
| FR-14 Effective Priority | | s | s | s | NP-4.7 |
| FR-15 Starvation Promotion | s | s | s | s | FR-15(d) confers no preemption authority — NP-4.2 |
| FR-16 Preemption | | s | s | **P** | NP-4.1, NP-4.2, NP-4.3 |
| FR-17 Priority grants | s | | | **P** | NP-4.9 |
| FR-18 Checkpoint capture | | | **P** | s | |
| FR-19 Eviction Ramp | | | **P** | | |
| FR-20 Checkpoint verification | | s | s | s | NP-2.7, NP-3.3, NP-4.10 |
| FR-21 Resume from Checkpoint | | s | s | s | |
| FR-22 Checkpoint lifecycle | s | s | s | | NP-1.8 (7-day grace), NP-3.9 |
| FR-23 Checkpoint write failure | | | **P** | | *Mandatory edge case* — NP-3.2 |
| FR-24 Decision Records | s | s | s | s | All four; fail-closed emitter: NP-4.8 |
| FR-25 Status board | s | s | s | s | *Cross-cutting per PRD §14* |
| FR-26 Event log | | | s | s | |
| FR-27 Notifications | | s | s | s | |
| FR-28 Simulation control | s | s | s | s | Rate control: S1-Q5, S2-Q5, S3-Q5, S4-Q5 |
| FR-29 Fault injection | | s | s | | NP-3.5 (`OOM_KILLED` remediation) |
| FR-30 Headless runs | | s | | s | *Cross-cutting per PRD §14* |
| FR-31 Endpoint auth | | | s | s | FR-31(b) identity non-disclosure: the victim's identity is never rendered |

**All 31 FRs are covered by at least one scenario.** The PRD's §14 note that FR-25, FR-30 and FR-31 are "uncovered-by-scenario" holds for the PRD's own table; in this set each is exercised where it actually bites — FR-25 on every board, FR-31(b) in scenario 4 where a second student is present, FR-30 in scenario 2 where `operator_action_schedule` is how a cordon gets cleared headlessly.

### Coverage — scenario × NFR

| NFR | 1 | 2 | 3 | 4 | Notes |
|---|:--:|:--:|:--:|:--:|---|
| NFR-1 Build-time static checks | | s | | | Static; not a runtime path |
| NFR-2 Admission Order latency | | s | | | p95 ≤ 200 ms at 500 pending (SM-7) |
| NFR-3 Node-selection latency | | s | | | |
| NFR-4 Citation completeness | s | s | s | s | All four; NP-4.8 is its adversarial case |
| NFR-5 Eviction timing accuracy | | s | s | | ± 2 simulated seconds |
| NFR-6 Event fidelity under Fast-Forward | | s | s | | 0 dropped, 0 duplicated at 1440× |
| NFR-7 Simulation determinism | | s | | | Byte-identical log to the 1× run (F-20) |
| NFR-8/9 Remaining latency NFRs | | s | | | Separate benchmark harness |
| NFR-10 Crash recovery | | s | s | | 0 lost, 0 duplicate transitions; NP-3.8 |
| NFR-11 Static/structural | s | s | | | |
| NFR-12 Mandated-path test coverage | — | — | — | — | **Not exercised as a scenario path** — see §7 |
| NFR-13 Checkpoint store bound | s | | s | | NP-1.7, NP-3.9 |
| NFR-14 Invariant S-1 | | s | s | | |
| NFR-15 Accessibility (WCAG 2.1 AA) | s | s | s | s | All four |
| NFR-16 Standalone executability | | s | | | |

---

## 3. Coverage — the nine job states

Per FR-25(a), a job occupies one of exactly these nine and no other. The set is closed: **no scenario introduces a tenth.**

| State | Glyph / label | 1 | 2 | 3 | 4 |
|---|---|:--:|:--:|:--:|:--:|
| `REJECTED` | `✕` Refused | ● | | | |
| `QUEUED_PENDING_WINDOW` | `◷` Queued | ● | ● | ● | ● |
| `RUNNING` | `▶` Running | | ● | ● | ● |
| `CHECKPOINTING` | `▼` Checkpointing | | | ● | ● |
| `EVICTED_RESUMABLE` | `‖` Evicted, resumable | | ○ | ● | ● |
| `COMPLETED` | `✔` Completed | | ○ | ● | |
| `FAILED` | `⚠` Failed | | ○ | ● | ○ |
| `EVICTION_FAILED` | `⚡` Eviction failed | | | ● | |
| `EXPIRED` | `⊗` Expired | ● | | ○ | |

`●` = a state the scenario's happy path or a non-happy path reaches as a subject. `○` = named in passing (cross-reference or contrast), not exercised as a subject.

**All nine states are now the subject of at least one path.** The last gap closed was `EXPIRED`, added as NP-1.8 in scenario 1: T-15 fires there, decision `EXPIRE`, reason `RETENTION_DEADLINE`, citation `self:RETENTION-DEADLINE-v1` alone — legitimately, because retention is a module-owned bookkeeping rule under the F-1 split rule. It renders in the only near-neutral badge in the palette with a 1px `{colors.border-structure}` terminal ring, and it is the state that makes garbage collection possible at all, since FR-22(d) removes the oldest eligible `EXPIRED`-job Checkpoints first. The `EXPIRED` mention in scenario 3 remains a passing reference (NP-3.9's collection order) and is marked `○` deliberately.

---

## 4. Coverage — the ten decisions

Per §6.1 the enum is closed. All ten are reached across the set.

| Decision | 1 | 2 | 3 | 4 | Notable record |
|---|:--:|:--:|:--:|:--:|---|
| `ADMIT` | ● | ● | ● | ● | T-1, T-3, T-14, T-20 |
| `DENY` | ● | | | ○ | T-2, `VALIDATION_FAILED`; `QUEUE_FULL`, `STORE_FULL` |
| `DEFER` | ○ | ● | ● | ● | T-18, `PREEMPTION_REFUSED`, `UNVERIFIED_RESUME`, `MISSED_WINDOW` |
| `PREEMPT` | | | ○ | ● | T-7 — non-`self:` citation mandatory |
| `EVICT` | | | ● | ● | T-6, T-16, T-22 |
| `EXPIRE` | ● | | ○ | | T-15, `RETENTION_DEADLINE` — NP-1.8 |
| `CORDON` | | | ● | | FR-23(c) — non-transition record |
| `RESUME` | | ● | ● | | T-12 |
| `COMPLETE` | | | ● | | T-5 |
| `FAIL` | | ○ | ● | | T-9, T-10, T-13, T-17, T-19, T-21, T-23 |

### Reason codes reached

`VALIDATION_FAILED` · `NO_ELIGIBLE_NODE` (F-13) · `CAPACITY_EXHAUSTED` (F-13) · `QUEUE_FULL` · `STORE_FULL` · `DISK_PRESSURE_ESCALATION` · `RECONCILIATION_ACTIVATION` · `MISSED_WINDOW` · `DAEMON_RESTORE` · `UNVERIFIED_RESUME` · `PREEMPTION_REFUSED` · `CHECKPOINT_WRITE_FAILED` · `CHECKPOINT_DEADLINE_MISSED` · `CHECKPOINT_CORRUPT` · `NODE_FAULT` · `NODE_FAULT_NO_CHECKPOINT` · `PROCESS_EXIT` · `PROCESS_EXIT_NO_CHECKPOINT` (`OOM_KILLED` / `PROCESS_EXITED`) · `MAX_NIGHT_SPAN_EXCEEDED` · `MODEL_DEPRECATED` · `RETENTION_DEADLINE`

---

## 5. Non-happy path index

### Scenario 1 — 8 paths

| # | Path | Requirement |
|---|---|---|
| NP-1.1 | Multi-worker Job Spec → refused at the scope boundary | FR-3 |
| NP-1.2 | Three simultaneous field rejections, reported individually | FR-2 |
| NP-1.3 | Estimated duration over the Max Night Span | FR-4 |
| NP-1.4 | Repeated idempotency key with a different payload | FR-5 |
| NP-1.5 | A delegated verdict is missing | FR-6(b) |
| NP-1.6 | The Pending Set is at the cap | FR-7(a) |
| NP-1.7 | Checkpoint store pressure | NFR-13 |
| NP-1.8 | The Retention Deadline passes without admission → `EXPIRED` | T-15, FR-7(b)/(c), Invariant S-2, F-2 |

### Scenario 2 — 9 paths

| # | Path | Requirement |
|---|---|---|
| NP-2.1 | The Eligible Node set is empty | T-4a |
| NP-2.2 | Eligible capacity exhausted | T-4b |
| NP-2.3 | Activation blocked by a missing verdict | FR-8(e) |
| NP-2.4 | Emergency compute freeze active | FR-6(c) |
| NP-2.5 | Daemon Clock drift latched | FR-10 |
| NP-2.6 | The daemon was down across the 22:00 activation | FR-9 |
| NP-2.7 | A resume was not fully verified by 21:59:00 | FR-20(f) |
| NP-2.8 | The model was deprecated while the job waited | FR-6(d), T-21 |
| NP-2.9 | Max Night Span exhausted at activation | T-19, FR-4(d) |

### Scenario 3 — 10 paths

| # | Path | Requirement |
|---|---|---|
| NP-3.1 | The Ramp expired without a verified Checkpoint | T-9 |
| **NP-3.2** | **The mandatory edge case: the Checkpoint write fails** | **T-10, FR-23** |
| NP-3.3 | The retained Checkpoint fails re-verification | T-13, FR-20(c) |
| NP-3.4 | A node fault with no verified Checkpoint | T-17 |
| NP-3.5 | The training process exits mid-run | T-22 / T-23 |
| NP-3.6 | The T-20 recovery guard fails | T-19 |
| NP-3.7 | The Checkpoint is interrupted mid-sequence | FR-18(d) |
| NP-3.8 | The daemon crashes during the Ramp | T-18, FR-9 |
| NP-3.9 | Checkpoint store pressure at 03:00 | FR-22(d), NFR-13 |
| NP-3.10 | A job that finished just before the Ramp (near-miss) | FR-19(e) |

### Scenario 4 — 10 paths

| # | Path | Requirement |
|---|---|---|
| **NP-4.1** | **The mandatory edge case: the victim cannot checkpoint inside the budget → `PREEMPTION_REFUSED`** | **FR-16(c)** |
| NP-4.2 | Aging alone cannot authorise a stop | FR-16 converse |
| NP-4.3 | The same victim, twice in one night | FR-16(f) |
| NP-4.4 | The challenger would start before the victim's Node is released | FR-16(d) |
| NP-4.5 | A node fault arrives mid-preemption | FR-12(d) |
| NP-4.6 | The victim's resume lands on a different Node | FR-13 |
| NP-4.7 | The victim's own counters are not incremented | FR-14(d), F-8 |
| NP-4.8 | A `PREEMPT` record with no non-`self:` citation is refused | FR-24(b), F-1 |
| NP-4.9 | A grant is revoked mid-night | FR-17(d) |
| NP-4.10 | The victim's resume is not verified by 21:59:00 | FR-20(f) |

---

## 6. Rules that appear in more than one scenario

These are the requirements a designer will touch in more than one file. Each is written once and cross-referenced, so the two files cannot disagree.

| Rule | Where it governs | Files |
|---|---|---|
| **F-1 split rule** — `self:`-alone is legitimate only for module-owned rules; **every `PREEMPT` and `EVICT` needs a non-`self:` citation unconditionally** | `self:`-alone is *correct* on T-15 and FR-16(c)'s refusal; *insufficient* on T-6/T-7 | 1, 3, 4 |
| **Invariant S-2 / the 7-day expiry grace** — `EVICTION_FAILED`, `EXPIRED` and `MAX_NIGHT_SPAN_EXCEEDED` are the only three exits that end a job with admitted work incomplete while retaining the last verified Checkpoint | `EXPIRED` retains for 7 days (F-2); the others retain under FR-22 | 1, 2, 3 |
| **FR-14(d)** — Consecutive Nights Missed increments only on a window with **zero** admitted minutes | Aging at activation; a preempted victim | 2, 4 |
| **FR-15(d)** — Starvation Promotion confers **no** preemption authority | A promoted job's badge | 2, 4 |
| **FR-20(f)** — an unverified resume is never admitted; one record, `DEFER` / `UNVERIFIED_RESUME` / `self:CHECKPOINT-QUARANTINE-v1` | 21:30:00 pre-verification, T-12 and T-14 | 2, 4 |
| **FR-22(b)/(c)** — 2 most recent verified Checkpoints of a non-terminal job and all Quarantined ones are never auto-removed | Store pressure at submission and at 03:00; the `EXPIRED` grace | 1, 3 |
| **NFR-13** — pressure escalates to a human within 1 simulated minute; collection halts rather than deleting a protected Checkpoint | Submission refusal; 03:00 collection | 1, 3 |
| **T-19 guard** — Admitted Nights already 5 → `FAILED` / `MAX_NIGHT_SPAN_EXCEEDED` rather than a wasted night | Activation; T-20 recovery | 2, 3 |
| **FR-24 fail-closed** — a record without its required citation is refused, the transition is not applied, `EMITTER_REJECTED` is logged, the run is `PASSED` | Every decision | 1, 2, 3, 4 |
| **NFR-15** — colour is never the sole channel; hue, glyph and label always travel together | Every badge, banner and slot tile | 1, 2, 3, 4 |
| **FR-25(d)** — an idle slot is never blank, at any hour, with a reason code and one sentence | Board | 1, 2, 3, 4 |

---

## 7. Named gaps and unstated requirements

Recorded rather than invented around. Each is a place where a designer will have to decide something the PRD does not decide.

| # | Gap | Consequence |
|---|---|---|
| 1 | **NFR-12 is not a scenario behaviour.** It is a test-coverage requirement (4 of 4 scenarios, 1 of 1 edge case, every FR with an automated test). | It belongs to Phase 5/6, not to a scenario file. Listed here so its absence is a decision, not an oversight. |
| 2 | **The status board has no viewport basis.** FR-1's "desktop" qualifies the submission surface only; FR-25 requires 32 Nodes and 33 slots on screen; NFR-15 claims AA. | S1-Q2, S2-Q2. The desktop floor and the SC 1.4.4 / 1.4.10 boundary are design decisions with no requirement behind them. |
| 3 | **`fault_schedule` has no authoring surface.** FR-29 requires failure paths be demonstrable and repeatable; FR-30 requires the schedule on every `POST /simulations`; nothing creates one. | S2-Q4. API-only today, which undercuts FR-29's stated purpose. |
| 4 | **No in-app notification inbox in v1.** FR-27 payloads go to a local outbox so the harness can assert delivery; where a human reads them is unstated, and `DELIVERY_FAILED` has no surface. | S2-Q6. |
| 5 | **No named surface for a rejected Cordon Request** (FR-23(h)) and **no remediation affordance for FR-23(i)'s DiskPressure false positive.** | S3-Q3, S3-Q4. |
| 6 | **No deadline is pinned on a preemption drain.** The Checkpoint Budget (A-9) is defined *inside* the Ramp, so at 23:10 a draining slot has a budget and no hard stop. | S3-Q2. |
| 7 | **A preemption aborted by a Node fault is unspecified**, as is a challenger's Pending Set rank after T-14. | S4-Q2, S4-Q4. PRD Open Question 10 covers the victim's case, not the challenger's. |
| 8 | **The refused Preemption's recipient and copy are unnamed.** FR-27's trigger list does not obviously include a *refused* preemption. | S4-Q3. |
| 9 | ~~**The Retention Deadline has no value.**~~ **RESOLVED — PRD A-22 `JOB_TTL = 14 days`.** FR-7(b) requires one and FR-1 returns it, and §7.3 models every other duration the simulation depends on — but this one is given no number anywhere. | S1-Q7. The 7 days in NP-1.8 is the **expiry grace** (F-2, A-21), a different quantity. |
| 10 | **FR-27's notification counts are pinned for two triggers out of six.** Exact recipients are stated for Eviction and Checkpoint failure; Expiry, refused Preemption and resume are unstated. | S1-Q6, S4-Q3. |

**Closed since the first pass:** the `EXPIRED` state is no longer a gap. It is covered as NP-1.8 in scenario 1, which also closed the `EXPIRE` decision row and the `self:RETENTION-DEADLINE-v1` citation — the one registered `self:` id these scenarios had previously left uncited. All nine states and all ten decisions are now the subject of at least one path.

---

## 8. Open question index

| Id | File | Question |
|---|---|---|
| S1-Q1 | 1 | Trigger document is a PRD, not a Trigger Map |
| S1-Q2 | 1 | The submission surface has a viewport basis; the board does not |
| S1-Q3 | 1 | Which Granted Priority does this particular job receive? |
| S1-Q4 | 1 | No named surface for Checkpoint store pressure |
| S1-Q5 | 1 | The rate control's initial state is unstated |
| S1-Q6 | 1 | FR-27's notification counts are pinned for Eviction and Checkpoint failure only |
| S1-Q7 | 1 | ~~The Retention Deadline has no value~~ **RESOLVED** — PRD A-22: `JOB_TTL = 14 days` |
| S2-Q1 | 2 | Trigger document is a PRD, not a Trigger Map |
| S2-Q2 | 2 | The board has no viewport, and the AA claim depends on one |
| S2-Q3 | 2 | A run is `RUNNING` then exactly one of `PASSED` / `FAILED`; the run panel is a separate authority |
| S2-Q4 | 2 | `fault_schedule` has no authoring surface |
| S2-Q5 | 2 | The rate control's initial state is unstated |
| S2-Q6 | 2 | No in-app notification inbox in v1 |
| S3-Q1 | 3 | Trigger document is a PRD, not a Trigger Map |
| S3-Q2 | 3 | No deadline is pinned on a preemption drain |
| S3-Q3 | 3 | No named surface for a Cordon Request that Module 3 rejects |
| S3-Q4 | 3 | FR-23(i)'s false positive has no remediation affordance |
| S3-Q5 | 3 | The rate control's initial state is unstated |
| S4-Q1 | 4 | Trigger document is a PRD, not a Trigger Map |
| S4-Q2 | 4 | A preemption aborted by a Node fault is not specified |
| S4-Q3 | 4 | The refusal's recipient and its copy are unnamed |
| S4-Q4 | 4 | The victim's admission position after T-14 is not given a value |
| S4-Q5 | 4 | The rate control's initial state is unstated |

**23 open questions across 17 distinct issues.** Four are the same question (S1-Q1, S2-Q1, S3-Q1, S4-Q1 — the trigger-document substitution) and four more are the same question (S1-Q5, S2-Q5, S3-Q5, S4-Q5 — the rate control's initial state). S1-Q2 and S2-Q2 are near-duplicates that would merge to 16 if the board's missing viewport basis were stated once. S1-Q6 and S4-Q3 share a cause — FR-27's silent recipient counts — and would merge to 15. Any of these answered before Phase 4 should be applied to all four files at once, not one.

---

## 9. What Phase 4 inherits

- **Four scenario outlines, 37 non-happy paths, all 31 FRs and 15 of 16 NFRs touched** (NFR-12 excluded by design — §7 item 1). All nine job states and all ten decisions are the subject of at least one path.
- **The two design arguments that must survive into the flows**, both already made in `DESIGN.md` and repeated in the scenario files so they are not lost:
  - `EVICTED_RESUMABLE` and `FAILED` both mean "not running" and a reader who confuses them has failed the design — violet `‖` against pink `⚠`, never hue alone (scenarios 3, 4).
  - `EVICTION_FAILED` reads as terminal and is not; it holds the loudest non-red treatment in the palette, `#FFA657` appearing nowhere else in either state set, with the documented deuteranopia limit carried by glyph and label (scenario 3).
- **The third state that must not be mis-rendered, and it is the subtler of the three** (scenario 1, NP-1.8): `EXPIRED` is terminal and inert *while the Checkpoint beside it is live, retained and recoverable for a 7-day grace period.* A surface that dims the artifact to match the badge tells a student her work is gone when it is on disk. The badge is the only near-neutral one in the palette precisely because it is an absence — a saturated red would be a lie about severity — and a Checkpoint countdown to garbage-collection eligibility has to sit right next to it.
- **The accessibility contract** in `EXPERIENCE.md` that the scenarios rely on: slot cells are a real `role="grid"` with a two-field accessible name (`‹node_id› slot ‹n›, ‹occupancy label›, ‹eligibility label if any›`), every glyph is `aria-hidden`, a slot held by another submitter's job reads `occupied by another job` with no identifier, and **a new Decision Record gets a `role="status"` (polite) node on first appearance** — escalating to **assertive only** for the three reserved cases: daemon-unreachable, latched drift, and an **adverse decision on the viewer's own job**. The two highest-stakes records in the product are Kavita's UJ-1 submission refusal and the UJ-4 preemption refusal, and both are adverse decisions on the viewer's own job, so both are assertive; a 22-placement activation is not, so a screen-reader user who acts and hears nothing on *someone else's* job still cannot be drowned out by 22 polite records interrupting at 1440×.
- **The board does not navigate away from under a reader** when a decision fires. Every flow in this set enters as a banner, not a screen change.

---

## 10. Phase 4 — surface and wireframe cross-reference

**Added 2026-09-28 by WDS Phase 4.** The header of this file (lines 7, 11) references `ux/WIREFRAMES.md` "(if present)". No such file exists. The Phase 4 wireframes are **three files under `ux/wireframes/`**, and the page specifications live in a `## Page Specifications` section at the foot of each scenario file. This table is the map between the two.

| Surface | Specified in | Rendered in |
|---|---|---|
| **SURF-01** Submission form | [`scenario-1.md`](./scenario-1.md) | [`../wireframes/03-submission-form.md`](../wireframes/03-submission-form.md) |
| **SURF-02** Board · **02a** status strip · **02b** clock | [`scenario-2.md`](./scenario-2.md) | [`../wireframes/01-status-board.md`](../wireframes/01-status-board.md) |
| **SURF-03** Admission Order · **03b** Pending Set | [`scenario-2.md`](./scenario-2.md) | — |
| **SURF-04** Job detail · **04b** Decision Record detail | [`scenario-1.md`](./scenario-1.md), deltas in [`scenario-3.md`](./scenario-3.md) and [`scenario-4.md`](./scenario-4.md) | [`../wireframes/02-job-detail.md`](../wireframes/02-job-detail.md) |
| **SURF-05** Event log | [`scenario-2.md`](./scenario-2.md), deltas in [`scenario-3.md`](./scenario-3.md) and [`scenario-4.md`](./scenario-4.md) | — |
| **SURF-06** Admin shell · **06a** Cordon clearance · **06b** Priority administration | [`scenario-3.md`](./scenario-3.md), [`scenario-4.md`](./scenario-4.md) | — |
| **SURF-07** Node detail · **SURF-08** Quarantine release | [`scenario-3.md`](./scenario-3.md) | — |
| **SURF-09** Activation panel · **SURF-10** Simulation run panel | [`scenario-2.md`](./scenario-2.md) | — |

**Each surface is specified exactly once**, in the scenario where it is first reached; every other scenario cross-references it and adds only its own delta. The full registry, the token conflicts resolved in `DESIGN.md`, and the six design decisions taken where the PRD is silent are in [`../_progress/00-design-log.md`](../_progress/00-design-log.md). The `[V]` audit — 37 non-happy paths and 32 record types traced, 9 findings, 0 blocking gaps — is in [`../validation-report.md`](../validation-report.md).

**Two of the nine findings are in this file's own header and are not repaired here**, because it is a Phase 3 artifact: the dangling `WIREFRAMES.md` reference above, and the fact that §8's 23 open questions are now 17 distinct issues with none closed by Phase 4. **Phase 4 invented no answers to any of them.**
