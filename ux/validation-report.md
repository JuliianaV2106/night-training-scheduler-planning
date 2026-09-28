# Validation Report — `[V]`

> **Triage by the team (2026-09-28).** All six routed findings were fixed at their owner: **F-1** PRD §6.3 citation `…05:44:58Z` → `…05:44:58-05:00`; **F-2** PRD FR-6 testable "Module 2 quota source" → "Module 8"; **F-3** PRD FR-25(d) now defines `FREE` as the reason code for an Eligible, free, unneeded slot; **F-4** `00-ux-scenarios.md` header points at the three real wireframe files; **F-5** `EXPERIENCE.md` OQ-9 marked resolved; **F-6** `DESIGN.md` contradictions resolved exactly as this report recommends (tile border `border-structure`, citations `citation-ink` + `mono-label`, `FAIL` banner border `state-rejected`). F-7…F-9 remain documented design decisions and open questions (non-blocking). A typo in wireframe 01 ("Checkpoint Request" → "Cordon Request") was also fixed.

**Run:** WDS Phase 4, step `[V]` · **Project:** Proyecto final — Module 9, Night Training Scheduler
**Date:** 2026-09-28
**Audited:** four scenario files with their `## Page Specifications` sections · three wireframes · `00-design-log.md`

---

## 1. The question this step answers

> **Is every error state, every rejection banner and every edge condition the four scenarios name visible in a specification or a wireframe?**

One question, because a validation step that asks four questions gets four partial answers and a green tick. The method is therefore mechanical before it is judgemental: every `NP-n.m` in the four files, and every row of the PRD's §6.4 map, was located in at least one specification section or wireframe. **Nothing is closed by assertion** — a claim of coverage with no line reference is a gap.

**Result: 0 blocking gaps. 9 findings, all carried to the owner of the affected spine rather than designed around.**

---

## 2. Coverage counts

| Class | Count | Traced | Untraced |
|---|---|---|---|
| Non-happy paths (`NP-n.m`) | **37** — 8 + 9 + 10 + 10 | 37 | 0 |
| Transitions (§6.4, T-1…T-23 less deleted T-11) | **23** | 23 | 0 |
| Non-transition records (`transition: null`) | **9** | 9 | 0 |
| **Record types total** | **32** | **32** | **0** |
| Job states (§4.1) | 9 | 9 | 0 |
| Slot states | 5 | 5 | 0 |
| Decisions (§6.1) | 10 | 10 | 0 |
| Exclusion reason codes (`EXPERIENCE.md`) | 6 | 6 | 0 |
| Surfaces specified | 16 | 16 | 0 |

**Every one of the 9 non-transition records is specified, which is where most designs quietly drop half their audit trail** — a `DENY`/`QUEUE_FULL`, a `DEFER`/`STORE_FULL`, a `CORDON`, a `DEFER`/`PREEMPTION_REFUSED` and a `DEFER`/`MISSED_WINDOW` are all things the system *did* and the four scenarios were written to require.

---

## 3. The mandatory edge cases

The Annex requires these to execute end-to-end. Each is traced to a specification **and** to a visible rendering.

| Edge case | Where specified | Where rendered | Traced |
|---|---|---|---|
| **UJ-5/UJ-6 — Checkpoint write fails at dawn** (`T-10`, FR-23) | `scenario-3.md` § SURF-04 deltas, § SURF-06.3, § SURF-05 deltas | `wireframes/01-status-board.md` §1, §3, §4, §5 — `ws-gpu-19` cordoned, `EVICTION_FAILED`, 0 held | ✅ |
| **UJ-4 — Preemption refused** (`PREEMPTION_REFUSED`, FR-16(c)) | `scenario-4.md` § SURF-06b.4 | `scenario-4.md` § SURF-05 deltas — three refusal row shapes | ✅ |
| **UJ-1 — 52 h submission refused** (FR-2(j), FR-4(c)) | `scenario-1.md` SURF-01 | `wireframes/03-submission-form.md` §1 | ✅ |
| **UJ-3 — clean dawn eviction** (FR-18, FR-19, T-8) | `scenario-3.md` § SURF-04 deltas | `wireframes/02-job-detail.md` — §6.3 record verbatim | ✅ |
| **UJ-2 — activation with 22 placements** (FR-8, FR-13) | `scenario-2.md` § SURF-02 | `wireframes/01-status-board.md` §3 — 22-placement reconciliation | ✅ |

**All five execute as renderings, not as descriptions.** A design that specifies them but never draws them has not shown that a reader can *see* them.

---

## 4. Findings

Severity: **BLOCKING** = a specification cannot be implemented as written · **MAJOR** = a reader would be misled or a spine is internally inconsistent · **MINOR** = a stale cross-reference or an unstated assumption.

### F-1 · MAJOR · The §6.3 worked example carries the wrong UTC offset

`planning/prd.md` line 266 gives `sim_timestamp: 2026-10-04T05:45:00-05:00`. Line 268 gives the citation as `node-state:M3/ws-gpu-12@2026-10-04T05:44:58Z`.

A `Z` suffix is UTC. `2026-10-04T05:44:58Z` is `2026-09-04 19:44:58-05:00` local — **five hours before** the eviction, not the two seconds before it that a "last health reading" must be. The `Z` is almost certainly a typo for `-05:00`.

**Why it matters beyond tidiness:** FR-24(a) requires a non-`self:` citation on every `EVICT`, and the whole point of that citation is to name the health reading the daemon trusted. An instant that predates the decision by five hours would not satisfy it. **The record as written may be self-inconsistent under its own requirement.**

**Handled as:** rendered **verbatim** in `wireframes/02-job-detail.md` §3 with the defect flagged inline. A source citation is never silently rewritten. **Owner: PRD.** Fix is one character.

### F-2 · MAJOR · FR-6's testable condition names the wrong module for quota

Line 440: *"With the **Module 2 quota source** returning 503, 100 consecutive submissions produce 100 refusals and 0 admissions."*

Quota is **Module 8**, on the PRD's own evidence, four separate places:

| Line | Statement |
|---|---|
| 212 | "Token metering and quota budgets \| **Module 8** … This module computes no quota and owns no counter." |
| 247 | The citation grammar defines `quota:M8/verdict-id@version` — there is no `quota:M2/…`. |
| 279 | T-1's required citations list `quota:M8/…`. |
| 437 | Window Activation's inputs: "Entitlement verdict (M1), **quota verdict (M8)**, policy verdict and freeze state (M2)…" |
| 759 | Modules 1 and 8 are the "not an identity, quota, or entitlement authority". |

**Why it matters:** this is the acceptance criterion for the fail-closed submission path. Read literally, it makes a **policy** outage the trigger for 100 submission refusals — so an unrelated Module 2 condition would be tested as a submission outage, and a genuine Module 8 quota outage would go untested. **Handled as:** the specs and wireframe cite `quota:M8/…` per lines 247/279, and the discrepancy is recorded here. **Owner: PRD.**

### F-3 · MAJOR · The exclusion reason vocabulary has no code for surplus capacity

`EXPERIENCE.md`'s Reason panel defines six codes: `M3_CORDONED`, `M4_RESERVED`, `VRAM_CLASS_INSUFFICIENT`, `NO_ELIGIBLE_NODE`, `CAPACITY_EXHAUSTED`, `PRIOR_NODE_INELIGIBLE`.

**All six describe why a Node was excluded.** None describes a slot that was **Eligible, free, and simply not needed** — the `ws-gpu-21…31` case at 22:00:00, and every slot on the board at 05:46:01 once the Ramp has released them.

FR-25(d) nevertheless requires that *every* idle slot carry a reason, unconditionally. The design meets the requirement by rendering `FREE` (outside the window) and a release timestamp, **but `FREE` is not a PRD reason code and no surplus-capacity code exists.**

Surfaced by `wireframes/01-status-board.md` §5. **Handled as:** the honest label is rendered and the gap is flagged rather than papered over with an invented code. **Owner: `EXPERIENCE.md` / PRD** — a seventh code, or an explicit statement that `FREE` is the code for "free and unneeded", would close it.

### F-4 · MINOR · `00-ux-scenarios.md` points at a wireframe file that does not exist

Lines 7 and 11 both reference `ux/WIREFRAMES.md` ("if present"). No such file exists. The Phase 4 wireframes are three files under `ux/wireframes/`.

**Handled as:** a cross-reference table was appended to `00-ux-scenarios.md` §10 pointing at the real paths. The stale references were **not** edited, because that file is a Phase 3 artifact and rewriting its header is outside this run's deliverables. **Owner: whoever maintains the scenario index.**

### F-5 · MINOR · `EXPERIENCE.md` OQ-9 records that no wireframe was produced

That was true when OQ-9 was written and is now superseded: three wireframes exist. **Handled as:** recorded here; `EXPERIENCE.md` is a Phase 2 spine and was not edited.

### F-6 · MAJOR · Four internal contradictions in `DESIGN.md` (§4 of the design log)

| # | Contradiction | Resolution applied |
|---|---|---|
| 1 | `node-slot-tile` border: token block says `border-structure`, Components prose says `border-subtle` | **`border-structure`** — two sources incl. the Contrast section against one, and `border-subtle` measures 1.22:1 |
| 2 | Citation ink: Do's/Don'ts says `accent` for non-`self:` and `text-muted` for `self:`; the `decision-banner` and `citation-chip` sections say `citation-ink` for both and forbid accent | **`citation-ink` both** — `text-muted` measures 4.37:1 on the chip's own ground, under the 4.5 floor |
| 3 | `decision-banner` citation token: block says `mono-data`, prose and chip say `mono-label` | **`mono-label`** — three sources against one |
| 4 | `FAIL` banner left border: table says `state-failed`, the paragraph below says `state-rejected` | **`state-rejected` for the banner**; the `FAILED` **job badge** stays `state-failed` |

Each is resolved in favour of the passage carrying its own stated reason, and each is recorded rather than silently chosen. **Owner: `DESIGN.md`.** In every case the resolution is also independently supported by `EXPERIENCE.md`, so no specification depends on a contested choice.

### F-7 · MINOR · The board has no stated viewport basis (carries S2-Q2)

FR-1 qualifies "desktop" for the *submission* surface only. Nothing describes the board's viewport, breakpoint or minimum size, yet FR-25 requires it to display 32 Nodes and NFR-15 claims WCAG 2.1 AA.

**Handled as:** a desktop floor is asserted as an explicit **design decision** and the SC 1.4.4 / SC 1.4.10 boundary is stated with it — the AA claim holds *at and above the floor only*, and below it the console renders a viewport notice rather than clipping an operations board. **Owner: PRD / design review.**

### F-8 · MINOR · `fault_schedule` and the notification inbox have no authoring or reading surface

S2-Q4 and S2-Q6, carried. FR-29 requires failure paths to be "demonstrable and repeatable" and FR-30 requires a `fault_schedule` on every `POST /simulations`, but no PRD surface creates one; FR-27 routes payloads to a local outbox with no named reader.

**Handled as:** SURF-10 renders the schedule and a copyable request body and **states that authoring is API-only**; `DELIVERY_FAILED` renders as an event-log row and nothing more. Both limitations are surfaced in-product rather than hidden. **Owner: PRD** — a marker demonstrating a failure path must currently leave the console.

### F-9 · MINOR · Six decisions taken where the PRD is silent

`00-design-log.md` §5 records **D-a** … **D-f** (D-b, D-c, D-d pre-existing; D-e roll-up verb tense, D-f a `self:`-only `FAIL` citation). Each is flagged as a decision rather than a finding, because each is a point a reviewer may reasonably disagree with:

| # | Decision | The disagreement it invites |
|---|---|---|
| **D-a** | Roll-up bucket precedence `held → draining → reserved → cordoned → idle`; idle+cordoned counts as `cordoned` | Counting it as `idle` reads as a healthier board |
| **D-b** | The victim's `job_id` is hidden from `STUDENT` with **no partial mask** | A partially masked id is still a disclosure through the Pending Set |
| **D-c** | A `draining` slot is never shown as idle | None defensible — Invariant S-1 requires the hold |
| **D-d** | Quarantine release is reached from the `FAILED` **job** badge, not the Node | FR-20(e) requires the node not be implicated |
| **D-e** | The roll-up says "released", never "idle", outside the Night Window | "Idle" would contradict a reason code that says `FREE` |
| **D-f** | A `self:`-only citation is legitimate on the `FAIL` record for `CHECKPOINT_DEADLINE_MISSED` | §6.2's "time and self-integrity rules" covers a `self:EVICTION-RAMP-v1` deadline; T-9's own row names no non-`self:` citation, so the two agree |

---

## 5. What the audit checked that the counts do not show

Counts prove a string appears somewhere. Three checks were made by hand because they are the ones that actually fail in practice.

**5.1 · Is every *failure* rendered as legible as its success?** Every adverse path renders a reason code, a summary and a citation. Specifically checked: the ramp deadline miss (T-9), the write failure (T-10), Quarantine (T-13), `PREEMPTION_REFUSED`, `QUEUE_FULL`, `STORE_FULL`, and the two reconciliations. **All 9 non-transition records render a reason; none renders a bare colour or a bare banner.**

**5.2 · Is any record rendered as a failure that is actually the system working?**

| Record | Must render as | Reason |
|---|---|---|
| `EMITTER_REJECTED` | **success** | FR-24(b) fail-closed means the transition was correctly *not* applied; FR-30 asserts `PASSED` |
| `PREEMPTION_REFUSED` | **a decision, not a fault** | Nothing stopped and nothing failed; the two jobs keep their states |
| `UNVERIFIED_RESUME` | **a deferral, not a failure** | No partial admission exists |
| `RECONCILIATION_ACTIVATION` | **a normal admission** | A missed window being *caught* is the requirement working |

**All four are specified as outcomes rather than errors.** A log that rendered `EMITTER_REJECTED` in the error channel would report the module working correctly as broken.

**5.3 · Does any surface contradict the board about the same fact?** The board, Job detail, the Event log and the run panel all state release, cordon and refusal. The four were compared on: the release instant (05:46:01 on all of them), the cause string, the citation set, and the "no job state changed" wording for refusals. **No contradiction found.** The one place they could have diverged — a `draining` tile held past 05:46:01 because a notification was slow — is explicitly forbidden, because FR-23(a) and FR-27 set a **0 ms** release delay and it is the one path where a slow UI would be a correctness failure.

---

## 6. The 17 inherited open questions

Carried forward unresolved and **not designed around**, because each is a fact the PRD does not state. Full register in `00-ux-scenarios.md` §8.

| Merged issue | Entries | Why it matters here |
|---|---|---|
| Trigger-document substitution | S1-Q1 … S4-Q1 | Phases 1–2 were never run; the PRD substitutes |
| Rate control's initial state | S1-Q5 … S4-Q5 | A board opening at 1440× may replay a stop nobody could read |
| Board viewport basis | S1-Q2, S2-Q2 | see F-7 |
| FR-27's silent recipient counts | S1-Q6, S4-Q3 | see F-8 |
| Preemption drain deadline | S3-Q2 | `draining` is budget-scoped outside the Ramp as a result |
| Cordon Request rejection by M3 | S3-Q3 | Renders as a cause change plus a log row |
| FR-23(i) false-positive remediation | S3-Q4 | Evidence is rendered; the judgement stays with Ines |
| Preemption aborted by a node fault | S4-Q2 | Renders as a fault abort, never as a refusal — it would blame the victim |
| Victim's admission rank after T-14 | S4-Q4 | Preserved fields shown as values |
| Run panel / `fault_schedule` authority | S2-Q3 | see F-8 |
| **Plus S1-Q3, S1-Q4, S1-Q7, S2-Q1** | 4 | Submission-side and index items |

**None is a specification gap.** Each is a place where the spec says *"the PRD does not state this; rendered as X and flagged"*, which is the only honest handling available without inventing a requirement.

---

## 7. Verdict

| Check | Result |
|---|---|
| Every non-happy path reaches a rendering | ✅ 37 / 37 |
| Every record type reaches a rendering | ✅ 32 / 32 |
| All five mandatory edge cases execute as visible states | ✅ 5 / 5 |
| Every state, decision and slot state specified | ✅ 9 / 10 / 5 |
| Every failure rendered as legibly as its success | ✅ hand-checked |
| No surface contradicts another about the same fact | ✅ hand-checked |
| No specification invents a state, code, citation or requirement | ✅ |
| Spine defects found and routed to their owner | 9 findings |
| **Blocking gaps** | **0** |

**`[V]` passes.** The nine findings are defects in `planning/prd.md`, `ux/DESIGN.md`, `ux/EXPERIENCE.md` and the scenario index — **not** in the Phase 4 output. None is repairable from inside this run, and all nine are recorded rather than silently worked around, which is the only thing a validation step can honestly do with a defect it does not own.
