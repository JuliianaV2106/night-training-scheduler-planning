---
title: "Module 9 — Night Training Scheduler: Implementation Readiness Gate Report"
status: complete
verdict: CONCERNS
created: 2026-09-28
revised: 2026-09-28
gate: bmad-check-implementation-readiness
fix_commit: 564eca1
scope: "planning package only — PRD, UX and Architecture. Absence of epics, stories and code is out of scope by instruction."
---

# Implementation Readiness Gate — Module 9: Night Training Scheduler

**Gate:** Implementation readiness (PRD · UX · Architecture alignment).
**Package:** `planning/` · `ux/` · `reviews/` · `planning/architecture-gate/`.
**Opened:** 2026-09-28. **Re-verified after fixes:** 2026-09-28, commit `564eca1`.
**Mode:** Fast path — no questions were put to the team; every ambiguity was recorded as a finding instead.
**Re-verification scope:** the 9 findings in §5 only. No full re-review was performed.

---

## 1. Verdict

## **`CONCERNS`**

Eight of nine findings are cleared and verified in the files. One is **partially** cleared: the priority-grant half of **F-3** is fixed, but its second half — the missing `FR-10` and `FR-29(a)` rows — is not, and the architecture still asserts those gaps are open.

The package is **not** ready to hand to `bmad-create-epics-and-stories` until the F-3 residue is closed.

It is **not** a `FAIL`. The architecture spine is internally coherent, the 92 formally triaged findings are applied, both mandatory edge cases are specified *and* rendered, and scenario coverage is complete. The original blockers are now localised to two PRD rows that do not exist, so two required records cannot be emitted at all.

| Dimension | Result |
|---|---|
| PRD completeness | Complete — 31 FR, 16 NFR, 3 invariants, 23 transition rows, 9 non-transition records, A-1…A-22 contiguous; **+1 row and +1 authority added at `564eca1`** (F-3b) |
| UX completeness | Complete — 4 scenarios, 37 non-happy paths, 9 states, 10 decisions, 16 surfaces, 3 wireframes |
| Architecture completeness | Complete — AD-1 … AD-8, 5 Mermaid diagrams, 10 open questions carried, 10 deferrals recorded |
| PRD ↔ UX alignment | **Clean** — F-1, F-2, F-7 fixed and verified |
| PRD ↔ Architecture alignment | **F-3a residue** — grant authority fixed; `FR-10` / `FR-29(a)` rows still missing |
| Review triage | 92 findings triaged and applied; four-lane gate disposition now stated accurately in the architecture (F-4) |
| Document integrity | Duplicated block removed (F-5), primary broken links repointed (F-6), addendum is a single deliverable (F-9 n/a) |

---

## 2. What was verified as sound

Recorded so the next gate does not re-open settled ground.

| Check | Result |
|---|---|
| §6.3 citation offset | `node-state:M3/ws-gpu-12@2026-10-04T05:44:58-05:00` — correct, two seconds before the 05:45:00 decision. The `Z`-suffix defect found by `[V]` is fixed in the PRD and followed in `wireframes/02-job-detail.md`; the original finding is preserved as history. |
| `T-11` deletion | Consistent everywhere. 0 references outside explanatory text. §6.4 carries 23 transition rows (T-1…T-23 less T-11, with T-4 split into T-4a/T-4b), matching `ux/validation-report.md:28`. |
| `FR-31(e)` amendment, 403 → 404 | Correctly applied in `planning/prd.md`, `ARCHITECTURE.md` AD-3 and AD-8, and `reviews/review-arch-adversarial.md` F-4. The **only** stale copy in the corpus is `ux/EXPERIENCE.md:127` — see F-1. |
| `self:DELEGATE-UNAVAILABLE-v1` | Registered in PRD §6.2 and consumed by AD-3, AD-7 and the refused-verdict path. |
| Technology-currency findings | All 5 addressed. `ARCHITECTURE.md:58-60` carries no version pins by deliberate decision; `:72` names the SQLite WAL-reset corruption floor as a startup check; `:73` names the Starlette 1.x `TemplateResponse` break; stdlib `sqlite3` removes both the SQLAlchemy 2.1 error and the abandoned `httpx` dependency. |
| C4-style context view | Present — `ARCHITECTURE.md` §2.1 "Context — the system box and everything outside it". |
| Scenario coverage | 37/37 non-happy paths, 9/9 job states, 10/10 decisions, 32/32 record types, 16/16 surfaces traced to a specification or a wireframe. All 31 FR covered; 15 of 16 NFR exercised (NFR-12 excluded by decision and recorded as such). |
| Mandatory edge cases | UJ-5/UJ-6 Checkpoint write failure at dawn and UJ-4 preemption refusal are each specified *and* drawn, not merely described. |
| Triage totals | PRD 50 (44 Accept · 1 Defer · 5 Reject) · UX 12 (11 Accept · 1 Partially Reject) · Architecture adversarial 15 Accept · Architecture edge cases 13 Accept + 2 Accept with the team's fix. **92 triaged, 92 applied.** |

---

## 3. Review inventory

| Set | File | Verdict | Triaged? |
|---|---|---|---|
| PRD adversarial | `reviews/review-prd-adversarial.md` | 50 findings | ✅ Fully — 44/1/5, all applied |
| UX edge cases | `reviews/review-ux-edge-cases.md` | 12 findings | ✅ Fully — 11 Accept, 1 Partially Reject |
| Architecture adversarial | `reviews/review-arch-adversarial.md` | 15 findings | ✅ Fully — 15 Accept, 2 PRD amendments |
| Architecture edge cases | `reviews/review-arch-edge-cases.md` | 15 findings | ✅ Fully — 13 Accept, 2 with the team's fix |
| **Architecture four-lane gate** | `planning/architecture-gate/review-adversarial-clash.md` | **26 holes** | ❌ **Scoped, not triaged** — see F-4 |
| " | `planning/architecture-gate/review-reconcile.md` | **GAPS — 47 load-bearing drops + 31 minor** | ❌ **Scoped, not triaged** — F-4 |
| " | `planning/architecture-gate/review-rubric-walker.md` | **NOT SOUND** | ❌ **Scoped, not triaged** — F-4 |
| " | `planning/architecture-gate/review-tech-currency.md` | **OUT OF DATE** (5 defects) | ✅ Fully — all 5 verifiably applied |
| UX validation | `ux/validation-report.md` | 0 blocking gaps, 9 findings | ✅ F-1…F-6 fixed at owner; F-7…F-9 recorded as non-blocking decisions |

---

## 4. Traceability summary

**Scenario → FR.** All 31 FRs are reached by at least one of the four scenarios. FR-25, FR-30 and FR-31, which the PRD's own §14 table marks uncovered-by-scenario, are each exercised where they actually bite: FR-25 on every board, FR-30 in scenario 2 via `operator_action_schedule`, FR-31(b) in scenario 4 where a second student is present.

**Scenario → AD.** Every AD-1 … AD-8 is exercised by at least one specified surface or enforced rule:

| AD | Exercised by |
|---|---|
| AD-1 one writer, one clock, one queue | FR-28 rate control on the status strip; `SURF-10` run panel |
| AD-2 Decision Record is the only commit point | `SURF-04b` Decision Record detail, on every surface |
| AD-3 fail-closed emitter | `SURF-05` deltas, `EMITTER_REJECTED` rendering (NP-4.8) |
| AD-4 GPU slot is the allocation unit | `SURF-02` per-slot tiles, `server-gpu-01` spanning tile, FR-2 rule (k) (NP-1.2 / E-3) |
| AD-5 restore is a fold | `SURF-05` deltas, `MISSED_WINDOW` banner (NP-2.6) |
| AD-6 preemption is granted-tier only | `SURF-06b.4`, NP-4.1 / NP-4.2 / NP-4.3 |
| AD-7 five-step Checkpoint protocol | `SURF-04` deltas, quarantine rendering (NP-3.3) |
| AD-8 one `ROLE_CAPABILITY` table, no existence disclosure | **Contradicted in `EXPERIENCE.md:127` — F-1** |

**NFR → gate.** NFR-1 and NFR-11 are build-time static checks and are correctly excluded from the run gate (F-36). NFR-2, NFR-3, NFR-8 and NFR-9 are benchmark-harness measured and correctly reported rather than gated. The run gate is PRD FR-30(d) verbatim.

---

## 5. Findings

### F-1 — BLOCKER · `ux/EXPERIENCE.md:127` contradicts the amended FR-31(e) on status code *and* record kind

**The text.** The *Priority administration* row of the UX behaviour table reads:

> "HTTP 403 with a cited role mismatch (FR-31(e)) renders as a banner, **never a silent no-op**."

**What the binding sources now say.** FR-31(e) was amended by team decision (`ai-log/decision-log.md` entry 15; `reviews/review-arch-adversarial.md` F-4, Critical, accepted as a PRD amendment) to read **`404`**, byte-identical across absent / not-owned / owned-but-forbidden, so the status leaks nothing about existence, owner or role. The audit trail is a **`LifecycleEvent` carrying actor, route and time** — explicitly *never* a Decision Record, because PRD §6.4's closed ten-value `decision` enum has no row for an authorisation refusal. `ARCHITECTURE.md` AD-3:626 and AD-8:736 both state this, and Open Question 7 records that FR-31(e) was removed from the missing-§6.4-row list precisely because the amendment resolved it.

**Three errors in one cell.** Wrong status code (`403` not `404`), wrong record kind (a cited Decision Record, where the requirement is an uncited `LifecycleEvent`), and a rendering instruction that now contradicts the surface's own security goal.

**Why this is a blocker, not a typo.** `EXPERIENCE.md` is a binding input of equal standing to the PRD and is the source the console's error rendering is specified from. A `403` discloses that the route or `job_id` exists — the exact `job_id` enumerator that F-40 forbids and that `EXPERIENCE.md`'s own Information Architecture section argues against at length. This document originally supplied the *correct* 404 rationale; the row was simply never updated when the PRD moved. `planning/architecture-gate/review-adversarial-clash.md` Hole 25 and `review-reconcile.md` LB-11 both flagged this exact collision before the amendment; the amendment landed in the PRD and Architecture, and this one cell was missed.

**Fix.** Rewrite the cell to: *HTTP 404, byte-identical to a missing resource, with a `LifecycleEvent` carrying actor, route and time — never a Decision Record and never a `403`; renders as a banner so the refusal is never a silent no-op.* Then re-check `ux/DESIGN.md` and the three wireframes for the same row.

---

### F-2 — MAJOR · `ux/EXPERIENCE.md:288` invents transition `T-24`

**The text.** "…every transition T-1…T-24 (T-11 deleted) and every non-transition record has a named `decision` value…"

**The fact.** PRD §6.4 defines 23 transition rows: T-1 through T-23 with T-11 deleted, and T-4 split into T-4a and T-4b. There is no T-24. `ux/validation-report.md:28` states the correct range and count; `ARCHITECTURE.md:259` and `:581` both record the T-11 deletion explicitly.

**Why it matters.** The sentence's whole purpose is to establish that `EXPERIENCE.md` no longer keeps its own partial map, so "the two can never drift." Naming a transition that does not exist reintroduces exactly the drift the sentence disclaims, and an implementer tracing T-24 finds nothing.

**Fix.** Change `T-1…T-24` to `T-1…T-23 less T-11 (23 rows)`.

---

### F-3 — MAJOR · Two PRD §6.4 rows do not exist, and no authority string exists for an administrator's priority grant

Both are declared in `ARCHITECTURE.md` and both are real, not theoretical.

**(a) Open Question 7 — `FR-10` drift and `FR-29(a)` OOM advisory have no §6.4 row.** AD-3 is fail-closed and refuses any record the map does not assign, so the clock-drift record and the OOM advisory **cannot be emitted at all**. `ARCHITECTURE.md:763` states plainly: *"Each is a real, intended record that will be refused — a PRD amendment is required before those two paths can emit anything."* NFR-14-style auditability is lost on both paths, and the refusal is silent at the surface: the run passes while the record the PRD requires never appears.

**(b) Open Question 6 — no registered citation authority for an administrator's priority grant.** §6.4's T-3 row contemplates the administrator's grant as a ranking source; §6.2 registers no authority string for it. AD-3 therefore **fails closed on a grant-sourced `T-3`**: the intent is refused, no transition is applied, an `EMITTER_REJECTED` is appended, and — per `:762` — *"This stops priority grants from producing Decision Records."* FR-17's administrative priority path is disabled at runtime.

`ARCHITECTURE.md:633` prices this honestly: *"the three known PRD gaps are visible stoppages until the PRD is amended."* They are declared non-blocking for the stories, which is defensible, but they are **not** non-blocking for the features: FR-17 and FR-10 cannot work end-to-end until §6.2 and §6.4 are amended.

**Fix.** Either amend PRD §6.2 and §6.4 to close both, or record an explicit, dated decision that FR-10's drift record, FR-29(a)'s advisory and grant-sourced `T-3` ship as known fail-closed stoppages with the affected surfaces and acceptance tests named. Do not leave it implied.

---

### F-4 — MAJOR · The architecture four-lane gate was scoped to 8 items and never individually triaged, while the architecture claims otherwise

`planning/architecture-gate/` holds four independent reviews of the **479-line** draft of `planning/ARCHITECTURE.md` (now 768 lines):

| Review | Verdict | Volume |
|---|---|---|
| `review-adversarial-clash.md` | 26 holes | 26 unit-pair decomposition holes |
| `review-reconcile.md` | GAPS | 47 load-bearing drops + 31 minor |
| `review-rubric-walker.md` | NOT SOUND | checklist verdict |
| `review-tech-currency.md` | OUT OF DATE | 5 defects — **all 5 verifiably applied**, §2 above |

`ai-log/decision-log.md` entry 14 records the team's decision: interrupt the fix-and-regate loop, limit the agent to **one pass on 8 critical items**. The 8 are identifiable and were applied (engine purity and the Effect Executor, the FR-16 preemption architecture as AD-6, the FR-13 deterministic Node order, restore-time queue reconstruction, the 9-state enum, AD-8 unified to 404-only, the §2.1 context view, and the `GET /health` citation). **The remaining 26 holes, 47 drops and 31 minor items have no per-finding triage record anywhere in the package.**

**The inconsistency this creates.** `planning/ARCHITECTURE.md:23` — inside the binding document's own revision note — states: *"This document previously carried `status: final` and was returned NOT SOUND by a four-lane reviewer gate. It has been revised against those findings."* The decision log says the opposite: the gate was scoped to 8 items and the rest was deliberately left. A reader of the architecture alone concludes the four-lane gate is closed; the record says it is partially open.

**Fix.** Amend `ARCHITECTURE.md:23` to state what actually happened — which 8 items were fixed, and that the remaining four-lane findings are open by recorded team decision. Then either triage the 26 holes individually or record them as an accepted, dated risk with a named owner for Phase 4 re-review. `review-reconcile.md`'s LB-9 and LB-11 and `review-adversarial-clash.md` Hole 25 are already resolved by later work; the residue should be listed, not left implicit.

---

### F-5 — MODERATE · `planning/ARCHITECTURE.md:17-19` and `:21-23` — duplicated, mutually inconsistent revision notes

The *Reference convention* paragraph appears twice (`:17` and `:21`) and the *Revision note* appears twice (`:19` and `:23`). The two revision notes describe **different** remediation histories and both are dated 2026-09-28:

- `:19` — the 30-finding formal review, all accepted, with the two PRD amendments named. Accurate.
- `:23` — the four-lane gate returned NOT SOUND, "It has been revised against those findings." Overstated per F-4.

The frontmatter at `:3` reads `status: final`, while `:23` describes the document as having "previously carried `status: final`" — so the same status is asserted as both current and historical. This is an append-without-delete editing artifact in a binding document, and it is the paragraph a reviewer reads first to learn what was fixed.

**Fix.** Delete `:21-23`, keep `:17` and `:19` (corrected per F-4).

---

### F-6 — MINOR · Broken reference to the UX validation report (2 sites)

Both `ux/C-UX-Scenarios/00-ux-scenarios.md:300` and `ux/wireframes/02-job-detail.md:101` point at **`ux/_progress/validation-report.md`**, which does not exist. The file is at **`ux/validation-report.md`**. `ux/_progress/` contains only `00-design-log.md`, so the first half of the same sentence at `:300` resolves correctly and the second does not — which is what makes it easy to miss. Every other relative link in `ux/` resolves.

**Fix.** Repoint both to `../validation-report.md` / `ux/validation-report.md`.

---

### F-7 — MINOR · `ux/C-UX-Scenarios/00-ux-scenarios.md:234` contradicts `:251` on the Retention Deadline

§7 item 9 still lists **"The Retention Deadline has no value"** as an open gap, while §8 marks the same question resolved: *"S1-Q7 — ~~The Retention Deadline has no value~~ **RESOLVED** — PRD A-22: `JOB_TTL = 14 days`"*. `planning/prd.md:134` and A-22 (`:885`) confirm `JOB_TTL = 14 days`, extended by 14 days from each admitted night, and `scenario-1.md:249` records the resolution with its rationale. §7 was not updated when §8 was.

**Fix.** Mark §7 item 9 closed, with the same wording and date as §8.

---

### F-8 — MINOR · `planning/prd-addendum.md:57` misstates the §6.2 citation rule

A.6 states: *"PRD §6.2 requires at least one non-`self:` citation for `DENY`, `PREEMPT`, `EVICT`, and `EXPIRE`."* PRD §6.2 (`:263`), FR-24(a) (`:621`) and NFR-4 (`:705`) all permit an **`EXPIRE` on a Retention Deadline to cite `self:RETENTION-DEADLINE-v1` alone** — a deliberate team decision (`ai-log/decision-log.md` entry 9) that closed an unsatisfiable rule by admitting `EXPIRE` into the module-owned class. `prd.md:294`'s T-15 row and `:321`'s resolution note both record it.

The addendum is explicitly non-normative — *"Nothing here is normative; where it conflicts with the PRD, the PRD wins"* — so this is documentation drift, not a requirement conflict. It is recorded because a reviewer reading A.6 will conclude `T-15` is under-cited, which is the exact defect this decision was made to prevent.

**Fix.** Amend A.6 to match §6.2: non-`self:` is unconditional for every `PREEMPT` and every `EVICT`, and for a `DENY` on a delegated verdict; an `EXPIRE` on a Retention Deadline may cite `self:` alone.

---

### F-9 — MINOR · Two divergent copies of the addendum

`planning/prd-addendum.md` (174 lines) and `_bmad-output/planning-artifacts/prds/prd-module-9-night-training-scheduler-2026-09-27/addendum.md` (173 lines) both exist and **differ**. `ai-log/decision-log.md` entry 6 records that the team moved the addendum into the deliverables as `planning/prd-addendum.md` so the PRD's references resolve; the staging copy was left behind. A second source of truth for a document the PRD cites is a drift risk.

**Fix.** Delete the `_bmad-output` copy, or mark it superseded with a pointer to `planning/prd-addendum.md`.

---

## 6. Blocker resolution log

Re-verified against the working tree at commit `564eca1` on 2026-09-28. Each resolution was checked by reading the cited file, not by trusting the commit message.

| # | Finding | Severity | Resolution applied | Verified | Evidence |
|---|---|---|---|:--:|---|
| F-1 | `EXPERIENCE.md:127` — 403 + cited Decision Record vs amended 404 + `LifecycleEvent` | Blocker | Cell rewritten: byte-identical HTTP 404 per amended FR-31(e), recorded as an authorisation `LifecycleEvent`, never a Decision Record; control hidden for `STUDENT` so there is no silent no-op | **Yes** | `ux/EXPERIENCE.md:127`. Sweep of `ux/` found no remaining 403-instruction; `:52` and `:57` already argued for 404-not-403, so the file is now internally consistent |
| F-2 | `EXPERIENCE.md:288` — phantom `T-24` | Major | Corrected to `T-1…T-23 (T-11 deleted, T-4 split into T-4a/T-4b)` | **Yes** | `ux/EXPERIENCE.md:288`; matches the 23 rows in PRD §6.4 and `ux/validation-report.md:28` |
| F-3a | No registered citation authority for an administrator's priority grant → FR-17 could not emit a record | Major | `self:PRIORITY-GRANT-v1` registered in §6.2; new §6.4 non-transition row `DEFER` / `PRIORITY_GRANTED` / `PRIORITY_REVOKED`; FR-17(b) validation rule updated | **Yes** | `planning/prd.md:262`, `:320`, `:555` |
| **F-3b** | **No §6.4 row for `FR-10` clock drift or `FR-29(a)` OOM advisory → AD-3 refuses both records** | **Major** | **Not applied** | **No** | No `CLOCK-DRIFT` or `OOM-ADVISORY` row in PRD §6.4. `planning/ARCHITECTURE.md:620`, `:628`, `:762`, `:763` still assert these are open gaps. The architecture's OQ 6 text at `:762` is now **stale against the PRD**, which does register the grant authority |
| F-4 | Four-lane gate (26 holes / 47 drops / 31 minor) never individually triaged; architecture claimed otherwise | Major | Revision note replaced with a *Revision history* that states the four-lane gate was a working-file check, was scoped to 8 items by team decision, was not triaged finding-by-finding, and is superseded by the two formal reviews | **Yes** | `planning/ARCHITECTURE.md:17`, `:19`, `:21` — single revision block, accurate disposition, decision-log entries 14–15 cited |
| F-5 | `ARCHITECTURE.md:17-19` / `:21-23` duplicated, inconsistent revision notes | Moderate | Duplicate *Reference convention* and duplicate *Revision note* deleted; one of each remains, plus the new *Revision history* | **Yes** | No duplication remains, and the `status: final` historical-claim contradiction is gone |
| F-6 | `ux/_progress/validation-report.md` does not exist | Minor | Repointed in both reported sites to `ux/validation-report.md` | **Partial** | The two reported sites are clean. **2 residual hits remain** at `ux/_progress/00-design-log.md:105` and `:119`. Non-blocking: the design log is a WDS working file, not a deliverable, and neither line is a rendering instruction |
| F-7 | `00-ux-scenarios.md:234` stale vs `:251` on the Retention Deadline | Minor | §7 item 9 struck through and marked **RESOLVED — PRD A-22 `JOB_TTL = 14 days`**, consistent with §8 S1-Q7 | **Yes** | `ux/C-UX-Scenarios/00-ux-scenarios.md:234` vs `:251` |
| F-8 | `prd-addendum.md:57` misstated the §6.2 citation rule | Minor | A.6 rewritten: non-`self:` unconditional for every `PREEMPT` and `EVICT` and for a `DENY` on a delegated verdict; a module-owned `DENY` and a Retention-Deadline `EXPIRE` may cite `self:` alone | **Yes** | `planning/prd-addendum.md:57`; now matches PRD §6.2 (`:263`), FR-24(a) (`:621`), NFR-4 (`:705`) and the T-15 row |
| F-9 | Two divergent addendum copies | Minor | **Not applicable — no fix required.** `_bmad-output/` is an untracked, git-ignored agent working folder, not a deliverable. The single delivered addendum is `planning/prd-addendum.md` | **Yes (n/a)** | `_bmad-output/` → `IGNORED`; the 173-line staging copy carries no review weight |

**8 of 9 findings fully cleared · 1 partial (F-6) · 1 not cleared (F-3b) · 1 not applicable (F-9).**

**Outstanding — F-3b.** `FR-10`'s clock-drift record and `FR-29(a)`'s OOM advisory still have no row in PRD §6.4, so AD-3's fail-closed emitter refuses both and neither path can emit anything. Two follow-ups are needed:

1. Add the two §6.4 rows (a non-transition record each, with a registered `self:` authority), **or** record a dated decision naming them as accepted fail-closed stoppages with the affected surfaces and acceptance tests listed.
2. Update `planning/ARCHITECTURE.md` OQ 6 at `:762` and OQ 7 at `:763`, plus the AD-3 text at `:620` and `:628`, to match the amended PRD. The architecture now asserts a gap the PRD has already closed — the same class of drift as the original F-1.

**Recommended sequence.** Close the F-3b PRD rows, then update the four architecture lines to match. Everything else in this package is ready for `bmad-create-epics-and-stories`.

---

## 7. Not blocking, recorded

| # | Item | Why it is not blocking |
|---|---|---|
| N-1 | 23 open questions across 17 distinct issues (`S1-Q1` … `S4-Q5`, `OQ-4` … `OQ-15`) | Every one is recorded rather than papered over, and Phase 4 "invented no answers to any of them." Four are the same question and four more are the same question, so the real count is 15 after merge. None gates a story. |
| N-2 | No in-app notification inbox in v1 | FR-27 payloads go to a local outbox so the harness can assert delivery. `DELIVERY_FAILED` has no surface — a design decision with a named open question (`S2-Q6`), not a gap. |
| N-3 | `fault_schedule` has no authoring surface | FR-29/FR-30 require the schedule on every `POST /simulations`; the panel is API-only by decision. Recorded as `S2-Q4` and `ARCHITECTURE.md` Open Question 2. |
| N-4 | No viewport basis for the status board | FR-1's "desktop" qualifies the submission surface only. The desktop floor is a design decision with no requirement behind it (`S1-Q2`, `S2-Q2`, AD Open Question 4). NFR-15's AA claim holds at and above the chosen floor. |
| N-5 | The initial Fast-Forward rate and the desktop floor are unspecified by the PRD | `S1-Q5` … `S4-Q5` and AD Open Questions 3 and 4. Design decisions, correctly deferred. |
| N-6 | NFR-12 is not exercised as a scenario path | A test-coverage requirement belonging to Phase 5/6. Listed in `00-ux-scenarios.md` §7 item 1 so its absence is a decision, not an oversight. |
| N-7 | Trigger-document substitution (PRD used in place of a Trigger Map) | Phases 1 and 2 were never run. Recorded as `S1-Q1` … `S4-Q1` in all four files and in the index header. The PRD supplies personas, JTBD and success metrics, so the substitution is sound. |
| N-8 | Output location deviates from `_bmad/wds/config.yaml` | Artifacts written to `ux/` at the user's direction, beside the sibling design files they reference by relative path. Recorded in `00-ux-scenarios.md` line 11. |

---

## 8. Gate decision

**`CONCERNS` — signed and accepted. Proceed to `bmad-create-epics-and-stories` after the F-3b residue is closed.**

- **Not `PASS`.** F-3b is live: `FR-10`'s drift record and `FR-29(a)`'s OOM advisory still have no PRD §6.4 row, so AD-3 refuses both and neither path can emit anything. The architecture additionally asserts at `:620`, `:628`, `:762` and `:763` that gaps exist which the PRD has since closed — the same class of document drift this gate was opened to catch.
- **Not `FAIL`.** The spine holds. All 92 formally triaged findings are applied and verified; the single original blocker (F-1, a contradiction on a security control) is fixed and the `ux/` sweep is clean; both mandatory edge cases are specified and rendered; scenario coverage is complete at 37/37 paths, 9/9 states, 10/10 decisions, 32/32 record types; all 31 FR and 15 of 16 NFR are traced. Eight of nine findings are cleared, one is a non-deliverable reference, and the residue is two PRD rows plus four architecture lines.
- **Epics, stories and code are out of scope** for this gate, per instruction. Their absence is not counted against the package.

**Carried forward to Phase 4** (unchanged, non-blocking): the desktop floor for the status board, the initial Fast-Forward rate, and whether the 15 merged UX open questions are answered before or during implementation.

---

## 9. Sign-off

This gate was opened as an automated cross-artifact check and **signed off by both owners** on the evidence in §6. Each resolution was verified by reading the cited file at commit `564eca1`, not by accepting the fix report.

| Role | Name | Decision | Date | Signature |
|---|---|---|---|---|
| Product / requirements owner | **Juliana Filigrana Valencia** | **`CONCERNS`** | **2026-09-28** | Juliana Filigrana Valencia |
| Technical / architecture owner | **Juan Manuel Casanova Marin** | **`CONCERNS`** | **2026-09-28** | Juan Manuel Casanova |

**By signing, both owners accept:**

1. The verdict recorded in §8 — **`CONCERNS`**, with F-3b open — or their own replacement verdict.
2. That F-3b is closed before `bmad-create-epics-and-stories` is run, and that the four stale `ARCHITECTURE.md` lines (`:620`, `:628`, `:762`, `:763`) are updated to match the amended PRD in the same pass.
3. That findings F-1, F-2, F-3a, F-4, F-5, F-7 and F-8 are **closed and verified**; that F-6 is accepted as a residual in a non-deliverable working file; and that F-9 is **not applicable**, `_bmad-output/` being an untracked agent working folder rather than a deliverable.
4. That the eight non-blocking items in §7 are accepted as design decisions rather than gaps.
5. That no epics, stories or code were in scope for this gate, and their absence is not a finding.

**Carried decision for the next phase.** F-3b must be closed by amending PRD §6.4 with a row for the `FR-10` drift record and the `FR-29(a)` OOM advisory — each a non-transition record with a registered `self:` authority, matching the `FR-31(e)` and `PRIORITY_GRANT` precedents — or by a dated team decision recording both as accepted fail-closed stoppages, with the affected surfaces and acceptance tests named.
