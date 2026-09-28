# Adversarial Review — `planning/prd.md` (Module 9 — Night Training Scheduler)

| Field | Value |
|---|---|
| Artifact reviewed | `planning/prd.md` (780 lines, commit `790263d`) + `addendum.md` |
| Lens | Adversarial (`bmad-review-adversarial-general`) |
| Reviewer | OpenCode, **fresh session** (independent from the authoring agent `bmad-prd`) |
| Triage | Team (human decision), with Claude Code as audit assistant |
| Date | 2026-09-27 |
| Result | 50 findings — **44 Accept · 1 Defer · 5 Reject** (F-30 is partially rejected and partially accepted; counted under Accept) |

**Triage rules.** **Accept** = the defect is real; fixed in `prd.md` (resolution below). **Defer** = real but belongs to a later phase or post-V1; owner and phase stated. **Reject** = the critique is invalid; the reason is stated.

---

## A. Mutually unsatisfiable requirements

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-1 | FR-3, FR-4(c), FR-7(a) mandate `DENY` records citing only `self:`, which NFR-4 and §6.2 declare build-failing. | Critical | **Accept** | Split the rule: `DENY` based on a **module-owned rule** (scope boundary, Max Night Span, queue cap, Job Spec validation) may cite `self:`; a `DENY` based on a delegated verdict, and every `PREEMPT`, `EVICT`, `EXPIRE`, needs ≥ 1 non-`self:` citation. Update §6.2, NFR-4, FR-24(a). |
| F-2 | Invariant S-2 says `EXPIRED` retains the Checkpoint; FR-7(c)/FR-22(a) delete it. | High | **Accept** | `EXPIRED` retains the last verified Checkpoint for a **7-day grace period** after expiry, then it is GC-eligible. S-2, FR-7(c), FR-22(a) aligned. |
| F-3 | FR-22(a) (remove superseded Checkpoints) contradicts FR-22(b) (never remove a non-terminal job's Checkpoint); retention count undefined. | High | **Accept** | Define `CHECKPOINT_RETENTION_COUNT = 2` (latest verified + previous verified). FR-22(b) becomes: "the 2 most recent verified Checkpoints of a non-terminal job are never removed automatically". |
| F-4 | NFR-13 is an absolute the design cannot meet (FR-22(e) allows exceeding the budget). | High | **Accept** | Rewrite NFR-13 as a testable response: when usage > budget, (1) new submissions are refused with a cited reason, (2) an escalation Decision Record is emitted within 1 simulated minute, (3) no protected Checkpoint is deleted. |
| F-5 | FR-16(e)/T-14 increment Consecutive Nights Missed on a preempted victim, but FR-14(d) resets it on any admitted minute. | Medium | **Accept** | FR-14(d) wins: the victim ran, so its counter is 0. Remove "incremented" from FR-16(e) and T-14; the victim keeps its original submission time (queue age). |
| F-6 | Deprecation handling differs between FR-2 trigger, FR-6 trigger, and OQ-7. | Medium | **Accept** | Module 5 model record is re-checked at every Window Activation (FR-6). A deprecated model → job `FAILED` (`MODEL_DEPRECATED`) with a `catalog:M5/...` citation. FR-2 trigger aligned; OQ-7 closed. |

## B. State-machine holes

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-7 | A Checkpoint verified between 05:50 and 05:53 (reserve) satisfies no transition; job stuck in `CHECKPOINTING`. | Critical | **Accept** | T-8 guard becomes "verified Checkpoint recorded **before 05:53:00**". The 300 s Checkpoint Budget is the *expected* window; the 3-min reserve is usable; 05:53:00 is the hard SIGKILL. |
| F-8 | T-14 has the wrong From state; the victim's intra-night return to the queue is not specified. | High | **Accept** | Replace T-14 with: `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW` **immediately** when the eviction cause was Preemption (not the morning ramp). Victim may be re-placed the same night if a node frees. |
| F-9 | `EVICTION_FAILED` / `CHECKPOINT_CORRUPT` is unreachable; T-11 is dead code. | Medium | **Accept** | Remove the `CHECKPOINT_CORRUPT` sub-reason from `EVICTION_FAILED` and delete T-11. Corruption is detected only at resume (T-13, and in the T-20 guard). |
| F-10 | No transition for training-process death (segfault, OOM, non-zero exit); OOM is the course's first named non-happy path. | Critical | **Accept** | Add fault kind `PROCESS_EXIT` (incl. `OOM_KILLED`) and transitions: `RUNNING` → `EVICTED_RESUMABLE` if a verified Checkpoint exists (max 1 automatic retry per night), else `FAILED` (`OOM_KILLED` / `PROCESS_EXITED`). An OOM also emits a cited Decision Record suggesting a lower batch size or a 48 GB node. |
| F-11 | T-20 re-admission from `EVICTION_FAILED` has no Max Night Span guard → S-3 violable. | High | **Accept** | Add guard "Admitted Nights < Max Night Span" to T-20; otherwise T-19 applies. |
| F-12 | T-18 ("unchanged") contradicts FR-9 (restart may perform activation). | Medium | **Accept** | T-18 = state restored from the durable log with no replay; **then** FR-9 reconciliation runs as a separate, recorded step. |
| F-13 | Guards on T-3, T-4, T-18 are not machine-checkable predicates. | Medium | **Accept** | T-3: "job rank ≤ number of free Eligible GPU slots". Split T-4 into T-4a (`NO_ELIGIBLE_NODE`) and T-4b (`CAPACITY_EXHAUSTED`) with different reason codes. T-18 guard moved to FR-9 as a property. |

## C. Arithmetic

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-14 | 5 nights × usable 7.75 h = **38.75 h**, not 40 h; a 39.5 h job is admitted and wastes 5 nights. | Critical | **Accept** | Define **Usable Night Duration = 7 h 45 min** (22:00–05:45). Max Night Span = 5 × 7.75 h = **38.75 h**. Update Glossary, FR-2(j), FR-4(c), UJ-1, T-19. |
| F-15 | "Fits in one night" compares against 8 h instead of 7.75 h. | High | **Accept** | FR-4(b): `requires_multiple_nights = estimate > 7.75 h`. |
| F-16 | NFR-2's 200 ms activation budget ignores FR-20's SHA-256 re-verification (≥ 46 s for 31 resumes; minutes for 7 GB checkpoints). | High | **Accept** | Add a **pre-verification phase at 21:30** that verifies all resuming Checkpoints before 22:00. NFR-2 explicitly excludes hashing; NFR-8 budgets pre-verification (all resumes verified by 21:59:00). A job whose verification did not finish is not admitted that night (cited). |
| F-17 | FR-2(g) allows a 120-min checkpoint interval (up to ~2 h of lost work); addendum justification inverted. | High | **Accept** | Cap `checkpoint_interval_minutes` at **30**. Fix the addendum statement. |
| F-18 | Periodic Checkpoint writes are unmodelled against the 20 GB store. | Medium | **Accept** | §7.3 models periodic writes; with retention count 2 (F-3), max store use = Σ(2 × checkpoint size) over non-terminal jobs; the store budget is sized from that formula (documented). |
| F-19 | SM-6 is not measurable and cannot fail. | Medium | **Accept** | Redefine SM-6 in steps: *lost steps per interruption ≤ steps produced in one checkpoint interval*, measured on every eviction, preemption and fault; no exclusions. |
| F-20 | SM-8/FR-28 "24 h in 60 s ± 10 %" is a tautology of the pacing layer. | Low | **Accept** | Keep the determinism assertion (byte-identical logs); replace the duration target with *wall time ≤ 75 s including scheduling work for 200 jobs over 24 h at 1440×*. |
| F-21 | NFR-9 and NFR-5 do not state which clock their tolerances use. | Medium | **Accept** | NFR-5 tolerance in **simulated** time (± 2 simulated seconds); NFR-9 in **real** time (≤ 500 ms real) at every rate. |

## D. Tests that cannot run or cannot fail

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-22 | Determinism tests require a 24 h real-time run at 1×. | High | **Accept** | Determinism test = 24 h at 1440× vs 24 h at 60× (24 min); plus a 1× vs 1440× comparison over a **30-min slice 05:30–06:00** covering the ramp. |
| F-23 | FR-24 "records = transitions" is falsified by records with no transition (reconciliation, disk pressure, queue-full refusal). | High | **Accept** | Invariant becomes: *every transition has exactly one Decision Record* (injective), and non-transition records carry `transition: null`. |
| F-24 | FR-30's citation-less-denial test contradicts FR-24(b) fail-closed. | Medium | **Accept** | Test asserts the fail-closed behaviour itself: emitter refuses, job stays in prior state, an `EMITTER_REJECTED` integrity event is logged, run verdict `PASSED`. |
| F-25 | FR-26's test needs a human (Ines) inside a headless run. | Medium | **Accept** | The run specification accepts a scripted **operator-action schedule** (e.g. `CLEAR_CORDON ws-gpu-19 at 08:05 by actor LAB_ADMIN fixture`). Module 3 is an in-process stub (NFR-16). |
| F-26 | NFR-6 has no oracle ("analytic expectation" undefined). | High | **Accept** | Oracle = **golden scenario fixtures**: each of the 4 Annex scenarios + the edge case ships with an expected transition list and count. |
| F-27 | NFR-10 random kill instants contradict NFR-7 determinism. | Medium | **Accept** | Kill instants are derived from the run seed (reproducible), 1000 per run. |
| F-28 | FR-2 test mixes rules from FR-1/FR-3; response shape undefined. | Low | **Accept** | Order fixed: FR-3 scope check short-circuits first; FR-2 then reports **all** field violations. FR-2 test uses `worker_count = 1`. |
| F-29 | FR-1(a) and FR-5(b) disagree on reused key + changed payload. | Medium | **Accept** | FR-1(a) delegates to FR-5: same key + same digest → 200 original; same key + different digest → 409. Add that case to FR-5's test. |

## E. Governance and self-description

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-30 | §0 claims everything derives from the PDFs, but "31 workstations" and America/Bogota are in neither. | High | **Partially Reject / Accept** | **Reject** the fleet part: the task statement §1 and "Fleet Topology Profile" state *31 Workstations* and *1 Central Server with two 48 GB GPUs* verbatim; the reviewer checked only the brief. **Accept** the timezone part: see F-31. |
| F-31 | The timezone was chosen for convenience and then presented as a sourced fact. | High | **Accept** | Record it honestly as **team decision D-1**: the sources name no location; the team sets America/Bogota because the deployment context of the course is a Colombian university, which removes DST risk. §10.2 states it as a decision, not a finding; portability kept as v2. |
| F-32 | NFR-11 (no names in logs) conflicts with FR-17/FR-26 (record actor); "three protagonists" wrong (Annex names two). | Medium | **Accept** | Logs and Decision Records store an **opaque `actor_id`** from Module 1; the UI resolves display names from the identity fixture. NFR-11 references §2 personas instead of "three". |
| F-33 | Ines Okonkwo is an undisclosed invented persona. | Low | **Accept** | Disclose in §2.1: team-added persona (task statement, Phase 1 instruction 4 invites an "AI Lab Operations Engineer"); role = lab administrator, the actor who grants priority and clears cordons. |
| F-34 | §16 has 18 bullets, 6 inline tags, and A-number holes. | Medium | **Accept** | Renumber A-1…A-n contiguously; every entry has a matching inline `[ASSUMPTION: A-n]` tag. |
| F-35 | Load-bearing inventions untagged: 05:53 SIGKILL, 300 s budget, QUEUE_DEPTH_CAP, 1 job/node/night, "Pack Affinity", retention count. | Medium | **Accept** | Tag each as an assumption; set `QUEUE_DEPTH_CAP = 500`; remove "Pack Affinity" (undefined); retention count via F-3. |
| F-36 | FR-30(d)'s invariant list is arbitrary. | Low | **Accept** | FR-30 gate = every invariant **checkable within one run** (S-1…S-3, NFR-4, 5, 6, 7, 10, 14, 16); NFR-1/11 are build-time static checks; latency NFRs are measured by a separate benchmark. Rationale written in FR-30. |

## F. Delegation and integration

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-37 | Module 6 absent from §5. | Low | **Accept** | Add a row: no dependency in V1. Checkpoints live in a store separate from Module 6's model cache; a disk-full Checkpoint failure cordons regardless of cache contents. |
| F-38 | A single delegated-service outage at 22:00 idles the fleet all night. | High | **Accept** | Add an **intra-night re-activation retry**: if activation is blocked by a missing delegated verdict or a lifted freeze, re-attempt every 5 simulated minutes until 04:00; each attempt is recorded. |
| F-39 | Job Spec uses Kubernetes fields, but Kubernetes integration is out of scope; no mapping to internal state. | Medium | **Defer → Phase 3** | Intentional: the Job Spec follows the Kubeflow/K8s vocabulary from the course's technology baseline so a V2 integration needs no new contract. The field → internal-model mapping is an **Architecture (Phase 3) data-model deliverable**. |
| F-40 | No access-control requirement on state-mutating endpoints. | High | **Accept** | Add FR-31: every endpoint requires a bearer token validated against the Module 1 fixture; roles `STUDENT` (submit, read own jobs) and `LAB_ADMIN` (grants, cordon clearance, simulation control). Unauthenticated → 401, wrong role → 403 with a cited Decision Record. |
| F-41 | Quota is checked only at submission; tokens consumed during an 8 h run are unmetered. | Medium | **Reject** | Scope creep. Module 8 meters **inference** tokens; a training job consumes no inference tokens. GPU time is already bounded by this module (Night Window + Max Night Span). This module emits GPU-minute events for Module 8/11 to consume; continuous metering is Module 8's responsibility. |
| F-42 | Two-GPU capacity of `server-gpu-01` modelled ambiguously (32 nodes vs 33 GPUs). | High | **Accept** | Allocation is counted **per GPU slot**: 33 slots (31 × 24 GB + 2 × 48 GB). `server-gpu-01` hosts up to two 1-GPU jobs or one 2-GPU job. Board shows 32 nodes / 33 slots; SM-3 measured per slot. |
| F-43 | FR-27 delegates notification to a module not listed in §5. | Low | **Accept** | Add §5 row: notifications written to a **local outbox mock** (not an Annex module); payload schema defined in FR-27. |

## G. Addendum

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-44 | Addendum claims "no number invented" but cites no sources. | Medium | **Accept** | Remove the claim; mark each figure as *published estimate, source unverified* or add the reference. Figures are non-normative calibration inputs (§7.3 already says re-calibrate). |
| F-45 | Addendum risks (false-positive cordon under DiskPressure; cordon rejected) contradict unqualified FR-23. | Medium | **Accept** | Move both into FR-23 as known limitations: a rejected Cordon Request still marks the node locally not-Eligible; a possible false positive is surfaced to the lab admin in the cordon reason. |
| F-46 | Addendum cross-reference points to the wrong assumption (A-9). | Low | **Accept** | Fix reference after renumbering (F-34). |

## H. Audit trail and deliverables

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-47 | `reviews/review-prd-adversarial.md` does not exist. | — | **Reject** | Not a PRD defect: the review was run *on* the committed PRD, and this file is its output. |
| F-48 | `.memlog.md` summary line is stale. | — | **Reject** | `.memlog.md` is the BMad agent's internal working file, not a deliverable. The graded audit trail is `ai-log/decision-log.md`. |
| F-49 | CLI reversal left in memlog without rationale; contradicts task guidance ("CLI dashboard" for headless modules) and "simulate 24h in 60s". | — | **Reject** | The CLI removal is a deliberate team decision with rationale (decision log entry 3). The "CLI dashboard" guidance applies to **Headless/Engine modules** (Gateway, Policy Engine); Module 9's Annex prototype is a UI simulator with a job status board. "Simulate 24h in 60s" is met by the board's fast-forward control and `POST /simulations`. |
| F-50 | Decision log and memlog attribute the 9 fixes to different actors. | — | **Reject** | Both are true and consistent: Claude Code (human-directed audit) **detected** the 9 defects; the authoring agent in OpenCode **applied** them (memlog FIX 1–9). Detection ≠ application. Decision log entry 4 wording clarified to say so. |

---

## Summary of changes required in `prd.md`

All **Accept** resolutions above are applied to `planning/prd.md` (and `addendum.md` for F-44–F-46). Deferred F-39 is carried into Phase 3 as an input to `ARCHITECTURE.md` (Job Spec → internal data model mapping). The resolution of each finding is verified after the fix, before Phase 2 starts.
