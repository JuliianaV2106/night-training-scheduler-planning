---
title: "Module 9 — Night Training Scheduler"
status: draft
created: 2026-09-27
updated: 2026-09-27
---

# PRD: Module 9 — Night Training Scheduler

*Working title — confirm. Source institution: University AI Compute Management Platform, Plan-2 Module 9 (Tier: Advanced).*

---

## 0. Document Purpose

This PRD is written for two audiences. The **readiness gate owner** needs a document whose every claim is traceable to the Annex and testable, so that Phases 3 and 4 can be executed without re-litigating scope. The **downstream workflow owners** — `bmad-ux` (Phase 2) and `bmad-architecture` (Phase 3) — need stable identifiers: every user journey is numbered `UJ-N`, every job state is a Glossary term used verbatim, every functional requirement is `FR-N`, every non-functional requirement is `NFR-N`, and every state name and node identifier is fixed so the UX state machine and the AD-n invariants can reference them without translation.

Structure: §3 fixes vocabulary, §4 fixes the state machine, §5 fixes what this module owns versus delegates, §6 fixes the shape of every automated decision, §7 fixes clock and simulation semantics, §8 states the requirements, §9 states the cross-cutting quality bars, §10 states the guardrails, and §14 traces the four mandatory Annex scenarios onto requirements. Inferred content is tagged inline as `[ASSUMPTION: ...]` and indexed in §16. Depth that does not earn its place in the main narrative — the real-world mechanism research, measured checkpoint and VRAM figures, the rejected alternatives — lives in `prd-addendum.md` beside this document.

**Inheritance.** This PRD supersedes nothing; there is no prior `prd.md`. It is derived solely from `docs/source/project - university_ai_compute_management_platform_brief.pdf` and the Module 9 entry of the Annex in `docs/source/task - plan 2 - university-ai-compute-fabric-1.pdf`. The `spec.md` and `project-brief.md` named as Phase 1 inputs in the task statement **were not provided and do not exist in this repository**. The two source PDFs named above are the sole inputs to this PRD. No requirement here is inferred from an unavailable document, and no scope in §4, §8, or §12 depends on one.

**Topology and timezone disclosure (F-30, F-31).** The fleet topology — 31 single-GPU workstations and one dual-GPU server — is taken **verbatim** from the task statement's Fleet Topology Profile; it is not a design choice of this PRD and is not open for revision here. The campus timezone is **not stated in the sources**; §10.2 therefore records decision **D-1** (America/Bogota, UTC−05:00, no daylight saving) as a team decision and flags it there, rather than presenting it as a finding.

---

## 1. Vision

A university has 31 single-GPU workstations and one dual-GPU server. Students run LoRA and fine-tuning jobs that occupy a GPU for hours. Daytime interactive teaching needs those same GPUs. The institution has therefore adopted a blunt, non-negotiable rule: **student training jobs may execute only between 22:00 and 06:00 campus local time.** The rule is right and it is also, on its face, hostile to the researcher it is meant to serve.

This module is the thing that makes the rule survivable. A student submits a training job at 14:30 and the system does not reject them, does not silently park them in an invisible holding pen, and does not run their job anyway. It validates the Job Spec, tells them exactly when their job can first run and why, and parks it in a state whose name says what is happening. At 22:00 a controller called the Night Daemon Controller wakes, decides which jobs get tonight, on which nodes, in what order, and starts them. At 05:45 it begins the Eviction Ramp: it asks each running job to stop cleanly, waits for a durable Checkpoint, and frees the GPU so that a human being can walk into a lab at 08:00 and find a machine that works.

The hard part — and the reason this module exists at all — is that an eight-hour window is shorter than most thesis-scale fine-tunes. The system is therefore not a run-to-completion scheduler. It is a **resume-across-nights** scheduler. A job that cannot finish tonight is not a failure; it is a job that checkpoints at 05:53, is re-admitted tomorrow at 22:00, and resumes from where it stopped. The engineering problem is not starting jobs. It is starting them in an order that is fair, stopping them without losing a night of work, and being able to explain every decision it made in a sentence a human can check.

---

## 2. Target User

### 2.1 Jobs To Be Done

- **Kavita**, senior research student: *"I want to submit my LoRA run in the afternoon and stop thinking about it, and I want to know on Monday morning exactly how far it got and when it will finish."* — functional, with a heavy emotional component, because the current alternative is a spreadsheet and a group chat.
- **Kavita**: *"When my job was stopped at dawn, I need to know it was stopped cleanly and that six hours of work is not gone."* — trust, and the reason the Checkpoint rules in §8.5 are as strict as they are.
- **Kavita**: *"When I am denied or deferred, I want the actual rule that did it, not a generic 'policy violation'."* — this is an Annex-wide course constraint (§6) and it is the difference between a system people comply with and a system people route around.
- **Ines Okonkwo**, GPU lab operations engineer: *"I need to know at 07:00 that every GPU is released, and I need to know which node is suspect and why."* — operational certainty, and the reason a failed Checkpoint cordons a node instead of quietly retrying on it.
- **Ines**: *"I need to grant one job an Urgent Grant and know the system will not thrash."* — deliberate, auditable intervention.
- **The Night Daemon Controller** (the non-human operator): *"I must be able to justify every state transition I cause, from a source another system can be asked to confirm."* — a first-class requirement, not a nice-to-have.

*Disclosure (F-33): **Ines Okonkwo** is a **team-added persona**, not named in the Annex. The task statement's Phase 1 instruction 4 invites an "AI Lab Operations Engineer" among the roles to consider, and her role — granting priority (FR-17), clearing cordons (FR-23, UJ-6), operating the board (FR-25) and the simulator (FR-28–FR-30) — is a direct expression of Annex material. Kavita and the Night Daemon Controller are named in the Annex.*

### 2.2 Non-Users (v1)

- **Students seeking interactive inference.** Model serving, notebooks, and chat endpoints are Module 7's concern. A student who wants a GPU at 15:00 is out of scope for this module by policy, not by omission.
- **Course instructors requesting bulk GPU reservations** — Module 4. This module consumes their reservations; it does not create them.
- **Anyone needing multi-node or distributed training.** Module 10. See FR-3.
- **Institutional administration seeking utilisation reporting.** Module 11. This module emits the events Module 11 aggregates; it does not build the dashboard.
- **Students in subjects with no entitlement to train at all.** Module 1 and Module 2 decide that. This module consumes their verdict and never computes it.

### 2.3 Key User Journeys

*Derived from the four mandatory Annex scenarios plus the mandatory edge case, then extended to two journeys the Annex implies but does not narrate (the failed-Checkpoint recovery and the operator's cordon clearance). **These are drafted from the Annex, not captured from Juli — please confirm or correct them, particularly UJ-5 and UJ-6, which the Annex leaves open.***

**UJ-1. Kavita submits a LoRA run at 14:30 and is told exactly when it will run.**
- **Persona + context:** Kavita, a senior research student with a thesis fine-tune to finish, has been holding a laptop-open SSH session all afternoon waiting for a free GPU that never appears.
- **Entry state:** Authenticated against the identity service (Module 1, consumed not owned). On the desktop submission surface or the API.
- **Path:** She submits a LoRA Job Spec — pinned container image digest, 1 GPU, 24 GB class node, a Checkpoint interval, and a self-declared intent of `THESIS`. Spec validation returns instantly; the estimated duration comes back as 31 hours, which exceeds the 7 h 45 min Usable Night Duration but fits inside the 5-night Max Night Span of 38.75 h, so the response states plainly that this job will run across at least four nights. Her granted priority is read from the Policy Engine (Module 2), not from her declaration. The job enters the Pending Set at `QUEUED_PENDING_WINDOW` and the response carries her first estimated start.
- **Climax:** She sees a job state with a name, a position in the Pending Set, and a projected first-start time — before she closes the laptop.
- **Resolution:** She is in `QUEUED_PENDING_WINDOW` with a Checkpoint from any prior night intact and a Retention Deadline set.
- **Edge case:** Her Job Spec requests 2 workers. The system refuses it at submission with a referral to Module 10 rather than admitting a job that could never be placed. Had she declared 52 hours instead of 31, it would refuse with a different reason: over the 38.75-hour Max Night Span, citing the ceiling and proposing a concrete scope reduction.

**UJ-2. At 22:00 the fleet wakes up and the night is decided in public.**
- **Persona + context:** Ines, on the night shift, wants to see the night's plan before it executes, not after.
- **Entry state:** 21:59:50 campus local time. The status board shows the fleet idle, the Pending Set populated, and a countdown to window activation.
- **Path:** At 22:00:00 the Night Daemon Controller performs Window Activation. It filters the fleet to Eligible Nodes, computes each pending job's Effective Priority, applies Starvation Promotion, builds the Admission Order, and places jobs. Every placement writes a Decision Record with citations. Ines watches the board repaint: node `ws-gpu-07` goes to `RUNNING` carrying Kavita's job, and the reason panel names the rule that put it there.
- **Climax:** All Eligible Nodes are either running an attributed job or explicitly shown as idle with a stated reason.
- **Resolution:** The board shows 22 job assignments, each with a citation, and a "next decision point 05:45:00" marker.

**UJ-3. 05:45 — a long job is stopped cleanly and keeps its work.**
- **Persona + context:** Kavita's thesis job has been running for 4 hours of an estimated 31 and is nowhere near done.
- **Entry state:** 05:44:50 campus local time, job in `RUNNING`, last durable Checkpoint 22 minutes old.
- **Path:** At 05:45:00 the Eviction Ramp begins. SIGTERM reaches the job. The job drains, writes a new Checkpoint, `fdatasync`s the file, atomically renames it into place, `fsync`s the parent directory, and records a SHA-256 digest. A Checkpoint verified any time before 05:53:00 — including in the 05:50:00–05:53:00 reserve — clears the Ramp (F-7); at 05:53:00 the daemon SIGKILLs any job still in `CHECKPOINTING` and releases the node. The GPU allocation is returned and the node is immediately eligible for the 06:00 lab walk-through.
- **Climax:** The job state reads `EVICTED_RESUMABLE` with a verified Checkpoint digest and a byte count — not "stopped."
- **Resolution:** Kavita receives a notification with last durable Checkpoint time, verified step count, and her next eligible resume at 22:00 tonight.

**UJ-4. A thesis-grade submission preempts a low-priority exploration run mid-night.**
- **Persona + context:** At 23:10 Kavita's thesis job is queued behind a low-priority exploration run that has held `ws-gpu-12` for an hour and shows a 9-hour estimate. Kavita's job already carries a Granted Priority of `THESIS`, assigned by Module 2 from her academic standing — she asked for nothing, and **no Urgent Grant was needed or requested**.
- **Entry state:** Kavita's job `QUEUED_PENDING_WINDOW`, granted `THESIS`; exploration job `RUNNING`, granted `EXPLORATION`, aged 2 nights. No Eligible Node is free, so ordinary admission cannot proceed.
- **Path:** Kavita's Effective Priority of 50 clears the Preemption Margin over the running job's aged Effective Priority of 22. Her Granted Priority is `THESIS`, so she holds Preemption authority on both conditions in FR-16(b) — and note that the *aging* contributed nothing to her authority; the thesis tier did. The daemon selects a victim — the lowest-Effective-Priority `RUNNING` job that still has a verified Checkpoint or can produce one within the Checkpoint Budget — requests Preemption, and drives the victim through the same Eviction Ramp used at dawn, at 23:10 rather than 05:45. Only after the victim's Checkpoint verifies is `ws-gpu-12` reassigned and Kavita's job enters `RUNNING`.
- **Climax:** Kavita's job is running and she was told *why* the other one stopped.
- **Resolution:** The exploration job transitions back to `QUEUED_PENDING_WINDOW` immediately once its Checkpoint verifies (T-14), with its Checkpoint intact, its **original submission time preserved**, and its Consecutive Nights Missed unchanged — it received an admitted minute this window, so its Effective Priority does not age (FR-14(d), F-8). It may be re-placed the same night if a slot frees. The Preemption is in the audit log with both jobs' digests.
- **Edge case:** The victim has no Checkpoint and cannot write one inside the Checkpoint Budget. It is not preempted. Kavita waits, and the system says so, citing the Checkpoint Budget rule.

**UJ-5. The Checkpoint fails while the node is being drained at dawn.**
- **Persona + context:** Kavita's job, 05:45, is being asked to stop. The node's disk is full or the write errors. This is the Annex's mandatory edge case.
- **Entry state:** `RUNNING`, SIGTERM delivered at 05:45:00, Checkpoint write in progress.
- **Path:** The write fails. The daemon does not retry on the same node, and it does not leave the GPU allocated. It releases the GPU allocation immediately, marks the node as failing a health check, issues a Cordon Request to Module 3, records a Decision Record citing the failed write, and moves the job to `EVICTION_FAILED` with reason `CHECKPOINT_WRITE_FAILED`. The last known good Checkpoint is retained, not deleted.
- **Climax:** `ws-gpu-19` is unavailable for the morning lab; Kavita's notification says her work is safe at her 03:10 Checkpoint and names the node as quarantined.
- **Resolution:** Kavita's job is in `EVICTION_FAILED` — **not** finished, and not waiting on a human. It holds a verified resume point but no node. The GPU is free. The node is off-limits until Ines clears it; the job itself is not, and will be re-admitted tonight (T-20).

**UJ-6. Ines clears the cordoned node and Kavita resumes that night.**
- **Persona + context:** Ines walks the lab at 08:00, finds `ws-gpu-19` with a full disk, clears it, and needs to know whether it is safe to return to service.
- **Entry state:** `ws-gpu-19` reports `SchedulingDisabled` with cause `EVICTION_CHECKPOINT_WRITE_FAILED`; Kavita's job sits in `EVICTION_FAILED` with a retained verified Checkpoint.
- **Path:** Ines inspects the cordon reason and the failed-write evidence, remediates, and releases the cordon. The node returns to the Eligible Node set on its next health evaluation. Kavita's job does **not** wait for this — it was re-admitted at tonight's Window Activation (T-20) onto a different Eligible Node, and is resuming from its last verified step.
- **Climax:** Kavita's job logs `RESUMED_FROM_CHECKPOINT` with the digest it verified, on a Node that is not `ws-gpu-19`.
- **Resolution:** The resume is a normal, cited transition. The cordon is in the audit log with a human clearance event, closing the loop UJ-5 opened.

---

## 3. Glossary

*Every term below is used verbatim for the rest of this document. Introducing a synonym for any of these is a discipline violation.*

- **Training Job** — A single-node, GPU-backed model fine-tuning or LoRA run submitted by a student. The unit this module schedules. Cardinality: one Job occupies exactly one Node for the duration of one contiguous `RUNNING` interval. Multi-worker jobs are not Training Jobs (FR-3).
- **Job Spec** — The validated input document describing a proposed Training Job: container image digest, GPU count and VRAM class, node selector, storage request, Checkpoint interval, restart policy, declared intent, and idempotency key. There is exactly one Job Spec per Training Job.
- **Night Window** — The interval from 22:00:00 to 06:00:00 America/Bogota local time (UTC−05:00, no daylight saving), during which Training Jobs are permitted to execute. Duration is exactly 8 hours on every date of the year for this deployment. There is exactly one Night Window per calendar day. See §10.2 for the portability caveat.
- **Usable Night Duration** — The 7 h 45 min sub-interval of the Night Window from 22:00:00 to 05:45:00 during which usable training work is admitted to accumulate (F-14). The 15 minutes after 05:45:00 belong to the Eviction Ramp, not to training. It is the unit the Max Night Span is expressed in.
- **Eviction Ramp** — The 8-minute interval from 05:45:00 to 05:53:00 during which running Training Jobs are asked to stop, given the Checkpoint Budget to comply, and then killed. The Ramp is anchored to wall-clock local time, not to elapsed job time.
- **Checkpoint Budget** — The 5 minutes within the Eviction Ramp (05:45:00–05:50:00) during which a Training Job is *expected* to produce a durable Checkpoint. The remaining 3 minutes (05:50:00–05:53:00) are **reserve and still usable** (F-7): a Checkpoint verified any time before 05:53:00 satisfies T-8. 05:53:00 is the hard SIGKILL instant; a job with no verified Checkpoint by then fails.
- **Checkpoint** — A durable, integrity-verified snapshot of a Training Job's model and optimizer state, sufficient to resume training at the step it records. A Checkpoint is durable only after its bytes are `fdatasync`'d, atomically renamed, its parent directory is `fsync`'d, and its SHA-256 digest is recorded. See FR-18.
- **Checkpoint Quarantine** — The state of a Checkpoint whose recorded SHA-256 digest does not match a re-read of its bytes. A Quarantined Checkpoint is never loaded and never deleted by automated garbage collection without a human release.
- **Pending Set** — The total ordered collection of Training Jobs in state `QUEUED_PENDING_WINDOW`, awaiting admission to a Night Window. It is a single ordered structure, not per-node or per-priority collections. Cardinality is bounded by Queue Depth Cap.
- **Admission Order** — The deterministic, per-Night-Window ordering of the Pending Set used to decide which jobs run tonight. Derived from Effective Priority, Starvation Promotion, and submission time, in that precedence.
- **Granted Priority** — The priority tier (`EXPLORATION` = 10, `THESIS` = 50, `URGENT` = 90) assigned to a Training Job by a lab administrator or by the Policy Engine. Never by the submitting student. A student's self-declared intent is a recorded *request* and is not a Granted Priority.
- **Urgent Grant** — The administrative act of setting a Training Job's Granted Priority to `URGENT` (90). Always recorded with an actor and a mandatory reason code. It is the *strongest* form of Preemption authority, **not the only one** — see FR-16(b), under which a Granted Priority of `THESIS` or `URGENT` combined with the Preemption Margin authorises Preemption. Aging never authorises Preemption at any level.
- **Preemption Authority** — The two conditions that must both hold before this module may stop a `RUNNING` Training Job: the challenger's Granted Priority is `THESIS` or `URGENT`, **and** the challenger's Effective Priority is at least the victim's plus the Preemption Margin. Authority derives from the *granted* tier only. Effective Priority is a scheduling key, never a grant of authority. Defined normatively in FR-16(b).
- **Effective Priority** — `Granted Priority + min(Consecutive Nights Missed × AGING_RATE, AGING_CAP)`. The single ordering key for Admission Order and the Preemption comparison.
- **Consecutive Nights Missed** — The count of immediately preceding Night Windows in which a Training Job was eligible but received zero admitted minutes. Reset to 0 on any admitted minute.
- **Starvation Promotion** — The rule that a Training Job with `Consecutive Nights Missed ≥ STARVATION_NIGHTS` is moved to the head of the next Admission Order, subject to a per-window promotion cap. Guarantees a floor on access without authorising Preemption.
- **Preemption** — The eviction of a `RUNNING` Training Job by a higher-ranked pending Training Job, at a moment other than the Eviction Ramp. Permitted only when the margin and authority conditions in FR-16 hold.
- **Preemption Margin** — The minimum Effective Priority advantage a challenger must hold over the `RUNNING` victim before Preemption is permitted. Acts as hysteresis to prevent oscillation.
- **Eligible Node** — A Node that is healthy per Module 3, not cordoned, not overlapped by an active reservation from Module 4, and whose VRAM class can satisfy the Job Spec's GPU request. Only Eligible Nodes may receive placements.
- **Cordon Request** — A request from this module to Module 3 to place a Node in a non-schedulable state. This module never cordons a Node itself; it only requests, and consumes the resulting state.
- **Node** — One of the 32 physical machines: 31 workstations identified `ws-gpu-01` … `ws-gpu-31` with one 24 GB GPU each, and one server identified `server-gpu-01` with two 48 GB GPUs — **33 GPU slots in total** (F-42). Node identifiers are fixed and are referenced by FRs, UJs, and the UX layer without translation `[ASSUMPTION: A-4]`.
- **Decision Record** — The structured, immutable explanation emitted for every state transition this module causes. Carries a decision, a one-sentence human-readable summary, and at least one Citation. See §6.
- **Citation** — A reference to the specific delegated authority that justifies a Decision Record, of the form `authority:identifier@version`. Citations are the only permitted justification. Prose alone is not a justification.
- **Retention Deadline** — The wall-clock instant after which an unadmitted Training Job expires and its Checkpoints become eligible for garbage collection. Derived from Job TTL at submission — `JOB_TTL = 14 days` `[ASSUMPTION: A-22]` — and extended by 14 days from each night the job is admitted. 14 days is ≥ 4× the Starvation Promotion threshold (3 nights, FR-15), so a job that is eligible and promoted is admitted long before it can expire; expiry therefore catches only abandoned or permanently unplaceable jobs.
- **Max Night Span** — The ceiling of 5 consecutive Night Windows (38.75 hours of usable, admitted training time — 5 × 7 h 45 min) that a single Training Job may consume (F-14). A Job Spec whose estimate exceeds the span is refused at submission; a job that exhausts the span without reaching `COMPLETED` is refused further admission and transitions to `FAILED`. The span is a per-job budget of *consecutive* admissions, so a job that is preempted and returns does not restart the count. Enforced by FR-2(j), FR-4, and FR-21.
- **Admitted Nights** — The count of Night Windows on which a Training Job received at least one admitted minute. Bounded by Max Night Span. Distinct from Consecutive Nights Missed, which counts nights a job received *nothing*.
- **Daemon Clock** — The module's single time authority, derived from the host's NTP-disciplined monotonic clock, from which all Daemon Timestamps are produced.
- **Simulated Clock** — The accelerated time source used in the standalone prototype in place of wall-clock time. The Daemon Clock is derived from the Simulated Clock in simulation mode and from the host monotonic clock in native mode. All scheduling logic is identical in both modes.
- **Fast-Forward** — The pacing factor by which the Simulated Clock advances relative to real time, from 1× to 1440×. Fast-Forward affects only the rate at which simulated time is consumed; it never changes the ordering or the count of events.
- **Simulation Fault** — A deterministically injected failure, scheduled against the Simulated Clock, used to exercise failure paths without real hardware. Kinds: node fault, Checkpoint write failure, Checkpoint corruption, daemon crash, and **training process exit (PROCESS_EXIT, incl. `OOM_KILLED`)** (F-10).

---

## 4. Job Lifecycle State Machine

*States are Glossary terms and are the shared vocabulary for Phase 2 (`EXPERIENCE.md` state machine) and Phase 3 (AD-n invariants). Transitions fire at exact Simulated Clock instants; Fast-Forward must not quantize them (FR-11, NFR-6). The nine-state shape is a v1 decision `[ASSUMPTION: A-18]`.*

### 4.1 States

| State | Terminal | Node held | Meaning |
|---|---|---|---|
| `REJECTED` | yes | no | Job Spec failed validation. Never entered the Pending Set. Reason code required. |
| `QUEUED_PENDING_WINDOW` | no | no | Validated and admitted to the Pending Set. Awaiting a Night Window. May hold one or more verified Checkpoints. |
| `RUNNING` | no | **yes** | Executing on exactly one Node. |
| `CHECKPOINTING` | no | yes | Eviction signal received; draining and writing a Checkpoint. Substate of the Eviction Ramp or of a Preemption. |
| `EVICTED_RESUMABLE` | no | no | Clean stop with a verified Checkpoint. Eligible for the next Night Window. |
| `COMPLETED` | yes | no | Finished all steps before the deadline. |
| `FAILED` | yes | no | Non-resumable failure. Last verified Checkpoint, if any, is retained per FR-22. |
| `EVICTION_FAILED` | no | no | The Eviction Ramp could not produce a verified Checkpoint (reason `CHECKPOINT_WRITE_FAILED` — a node fault). A Cordon Request is issued against the Node. **Non-terminal and recoverable:** the job holds a retained verified Checkpoint and is re-admitted to the next Night Window (T-20). Checkpoint corruption is **not** a sub-reason of this state — it is detected only at resume time (T-13 and the T-20 guard) and routes to `FAILED` (F-9). |
| `EXPIRED` | yes | no | Retention Deadline passed without admission. Checkpoints eligible for garbage collection. |

### 4.2 Transitions

| # | From | Event | To | Guard | FR |
|---|---|---|---|---|---|
| T-1 | — | Job Spec submitted and passes validation | `QUEUED_PENDING_WINDOW` | All FR-2 checks pass; queue depth below cap; idempotency key unseen | FR-1 |
| T-2 | — | Job Spec fails any validation rule | `REJECTED` | Any FR-2 rule fails | FR-1, FR-2 |
| T-3 | `QUEUED_PENDING_WINDOW` | 22:00:00, node available | `RUNNING` | **Machine-checkable: the job's rank in the Admission Order ≤ the number of free Eligible GPU slots at activation (F-13);** Eligible Node exists; no Cordon Request outstanding | FR-8, FR-12 |
| T-4a | `QUEUED_PENDING_WINDOW` | 22:00:00, no Eligible Node exists | `QUEUED_PENDING_WINDOW` | **Eligible Node set empty — reason code `NO_ELIGIBLE_NODE` (F-13)** | FR-8, FR-12 |
| T-4b | `QUEUED_PENDING_WINDOW` | 22:00:00, eligible capacity exhausted | `QUEUED_PENDING_WINDOW` | **Job rank > free Eligible GPU slots — reason code `CAPACITY_EXHAUSTED` (F-13)** | FR-8 |
| T-5 | `RUNNING` | All steps complete | `COMPLETED` | Completion at or before 05:45:00 | FR-19 |
| T-6 | `RUNNING` | 05:45:00 | `CHECKPOINTING` | Job is `RUNNING` at Eviction Ramp start | FR-19 |
| T-7 | `RUNNING` | Preemption authorised | `CHECKPOINTING` | Challenger margin and authority satisfied (FR-16) | FR-16 |
| T-8 | `CHECKPOINTING` | Checkpoint durable and digest recorded | `EVICTED_RESUMABLE` | **Verified Checkpoint recorded before 05:53:00 (F-7);** digest recorded | FR-18 |
| T-9 | `CHECKPOINTING` | 05:53:00 | `FAILED` (`CHECKPOINT_DEADLINE_MISSED`) | Ramp expired without a verified Checkpoint | FR-19 |
| T-10 | `CHECKPOINTING` | Checkpoint write errors | `EVICTION_FAILED` (`CHECKPOINT_WRITE_FAILED`) | Node released; Cordon Request issued | FR-23 |
| T-12 | `EVICTED_RESUMABLE` | 21:30:00 pre-verification, digest re-verified | `QUEUED_PENDING_WINDOW` | Re-admitted to Pending Set with prior Checkpoint attached (F-16) | FR-21 |
| T-13 | `EVICTED_RESUMABLE` | 21:30:00 pre-verification, digest mismatch | `FAILED` (`CHECKPOINT_CORRUPT`) | Checkpoint Quarantined; human notified (F-16) | FR-20 |
| T-14 | `EVICTED_RESUMABLE` | Victim of Preemption (not the morning ramp), Checkpoint verified | `QUEUED_PENDING_WINDOW` | Eviction cause was Preemption; Checkpoint attached; **Consecutive Nights Missed NOT incremented** (FR-14(d)); original submission time preserved; may be re-placed the same night if a slot frees (F-8) | FR-16 |
| T-15 | `QUEUED_PENDING_WINDOW` | Retention Deadline passed | `EXPIRED` | Checkpoints retained for the 7-day expiry grace, then garbage-collection eligible | FR-22, FR-7 |
| T-16 | `RUNNING` | Node fault reported by Module 3 | `EVICTED_RESUMABLE` | A verified Checkpoint exists; node released | FR-12 |
| T-17 | `RUNNING` | Node fault, no verified Checkpoint | `FAILED` (`NODE_FAULT_NO_CHECKPOINT`) | Work since last Checkpoint is unrecoverable | FR-12 |
| T-18 | any non-terminal | Daemon crash and restart | unchanged | **State restored from the durable decision log with no replay; FR-9 reconciliation runs afterwards as a separate, recorded step (F-12). The no-replay property is enforced by FR-9, not by this guard (F-13)** | FR-9 |
| T-19 | `QUEUED_PENDING_WINDOW` or `EVICTED_RESUMABLE` | Admitted Nights would exceed Max Night Span | `FAILED` (`MAX_NIGHT_SPAN_EXCEEDED`) | Admitted Nights already 5; retained Checkpoint preserved | FR-4, FR-21 |
| T-20 | `EVICTION_FAILED` | Next Night Window opens, retained Checkpoint digest re-verifies | `QUEUED_PENDING_WINDOW` | **A verified Checkpoint is retained AND Admitted Nights < Max Night Span — otherwise T-19 applies (F-11).** Placement is **not** restricted to the cordoned Node: the job may be placed on any Eligible Node | FR-23, FR-20 |
| T-21 | `QUEUED_PENDING_WINDOW` or `EVICTED_RESUMABLE` | Model deprecated at Window Activation re-check | `FAILED` (`MODEL_DEPRECATED`) | Module 5 record shows deprecation; cited `catalog:M5/…` | FR-6 |
| T-22 | `RUNNING` | Training process exits (segfault, OOM, non-zero exit) with a verified Checkpoint | `EVICTED_RESUMABLE` | A verified Checkpoint exists and fewer than 1 automatic PROCESS_EXIT retry used this night (**max 1**, F-10) | FR-18, FR-12 |
| T-23 | `RUNNING` | Training process exits, no verified Checkpoint | `FAILED` | No verified Checkpoint exists for this run segment (reasons `OOM_KILLED` / `PROCESS_EXITED`, F-10) | FR-12 |

**Note on T-20.** `EVICTION_FAILED` quarantines the *Node*, not the *job*. The cordon blocks `ws-gpu-19` and nothing else. A job recovering from a Checkpoint write failure resumes on a different machine from the very next Night Window; it does not wait for a human to clear the cordon. What the human is required for is returning `ws-gpu-19` to service, not restoring Kavita's run.

**Invariant S-1.** No transition may place a Training Job in a state holding a Node other than `RUNNING` and `CHECKPOINTING`. Enforced at 06:00:00: the count of Node allocations held by this module must be zero.

**Invariant S-2.** `EVICTION_FAILED`, `EXPIRED`, and `FAILED` with reason `MAX_NIGHT_SPAN_EXCEEDED` are the only exits that end a Training Job with admitted work incomplete, and **all three retain the last verified Checkpoint** for a human to recover — `EXPIRED` for a **7-day grace period** after expiry, after which it is garbage-collection eligible (F-2); `EVICTION_FAILED` and `MAX_NIGHT_SPAN_EXCEEDED` retain it under FR-22. `EVICTION_FAILED` is not a dead end: T-20 returns it to the Pending Set.

**Invariant S-3.** A Training Job's Admitted Nights never exceeds Max Night Span, and a job is refused admission rather than admitted and immediately evicted. Span exhaustion must never manifest as a wasted night.

---

## 5. Delegated Dependencies and Mock Boundary

*This section answers the task statement's requirement to "clearly specify what this module owns and what it mocks/delegates." Every row is a hard boundary: the right-hand column is never computed here, and a missing left-hand input is a blocking error, not a default.*

| Capability | Owner | This module's obligation | Failure behaviour when the owner is unavailable |
|---|---|---|---|
| User identity, role, subject entitlement | Module 1 | Consume the subject and entitlement verdict at submission (FR-6) | Submission is refused; job is not queued. No offline default. |
| Dynamic policy evaluation (time, class schedule, VRAM tier, emergency freeze) | Module 2 | Consume the ALLOW/DENY/CONSTRAIN verdict and the freeze state | Night Window opens with no jobs admitted. The fleet stays idle. This module never invents an ALLOW. |
| Node health, telemetry, cordon authority, fault classification | Module 3 | Request a cordon (FR-23); consume health and `SchedulingDisabled` state (FR-12) | Treated as not-Eligible. No placement. |
| Resource reservations (class blocks, exam windows) | Module 4 | Exclude reserved intervals when computing the Eligible Node set | Over-reservation is accepted as authoritative; a job may be deferred with a citation naming the reservation. |
| Model catalog, weight formats, license, deprecation | Module 5 | Consume the model record and deprecation state at validation (FR-2) | Submission is refused. |
| Inference serving, notebooks, chat endpoints | Module 7 | None. Out of scope. | — |
| Token metering and quota budgets | Module 8 | Consume the quota verdict at submission (FR-6). This module computes no quota and owns no counter. | Submission is refused. |
| Observability dashboards and utilisation reporting | Module 11 | Emit Decision Records and lifecycle events as the event source | Events are buffered; no dashboard dependency. |
| Natural-language diagnosis and runbooks | Module 12 | Emit Decision Records and Cordon Requests as citable inputs | Unaffected. |
| Multi-node and distributed training | Module 10 | Refuse multi-worker Job Specs with a referral (FR-3) | — |
| Model weights and artifact cache | Module 6 | **No dependency in v1 (F-37).** Checkpoints live in a store **separate** from Module 6's model cache; a disk-full Checkpoint failure cordons the Node regardless of Module 6's cache contents | Unaffected |
| Notification delivery | local outbox mock (no Annex module in v1) | Produce the FR-27 notification payloads and write them to a local outbox so the v1 test harness can assert on delivery. The payload schema is defined in FR-27 (F-43) | Buffered; never blocks the state transition |

**Not modelled at all in v1:** real GPU hardware, real container execution, real telemetry streams, real model weights, real network I/O. Every Training Job in the prototype is a **simulated process** with a modelled duration and a modelled memory profile `[ASSUMPTION: A-3]`. This is stated plainly because a readiness gate must not be told otherwise.

---

## 6. Explainability Contract

*The Annex's course constraint 4 requires that every automated decision produce a human-readable, cited justification. This section fixes the shape; FR-24 makes it enforceable. A Decision Record that violates this section is invalid and the transition it describes must not be applied — the system fails closed.*

### 6.1 Required fields

| Field | Type | Rule |
|---|---|---|
| `decision_id` | identifier | Unique, monotonic, durable. |
| `job_id` | identifier | The Training Job, or `null` for fleet-level decisions. |
| `node_id` | identifier or `null` | Affected Node. |
| `sim_timestamp` | Daemon Timestamp | Simulated Clock reading at commit, not at evaluation. |
| `decision` | enum | `ADMIT`, `DENY`, `DEFER`, `PREEMPT`, `EVICT`, `EXPIRE`, `CORDON`, `RESUME`, `COMPLETE`, `FAIL`. |
| `transition` | identifier or `null` | The §4.2 transition that fired, or `null` for fleet-level and non-transition records (reconciliation, disk pressure, queue-full refusal), per F-23. |
| `actor_id` | identifier | The opaque actor identifier from Module 1's identity fixture. Display names for the §2 personas are resolved by the UI; the actual name is never stored in a log line or Decision Record (NFR-11). |
| `summary` | string | One sentence, ≤ 200 characters, naming the actor, the action, and the reason. Must be readable without the citation list. Must not contain the words "policy", "invalid", "forbidden", or "error" alone as an explanation. |
| `citations` | list | ≥ 1 entry. Zero entries is a contract violation. |
| `inputs` | object | The evaluated values that produced the decision: Effective Priority, Consecutive Nights Missed, Granted Priority, VRAM class, elapsed runtime, remaining budget. |
| `supersedes` | identifier or `null` | Prior `decision_id` when a decision is revised. Decision Records are immutable; revision appends. |

### 6.2 Citation authorities

Citations are drawn only from delegated sources, formatted `authority:identifier@version`:

`policy:M2/rule-id@policy-version` · `quota:M8/verdict-id@version` · `entitlement:M1/subject-id@version` · `node-state:M3/node-id@telemetry-timestamp` · `reservation:M4/window-id@version` · `catalog:M5/model-id@version` · `self:invariant-id` (for decisions this module makes about its own state — the Eviction Ramp deadline, its own scope boundary, its own queue cap, its own Max Night Span ceiling, or its own Job Spec rules)

**Registered `self:` invariant ids (OQ-13).** The document uses or requires exactly these `self:` identifiers — no others. Each id is the module-owned invariant a Decision Record cites when it decides about this module's own state:

- `self:JOBSPEC-VALIDATION-v1` — FR-2, the Job Spec field rules (T-1, T-2).
- `self:SCOPE-BOUNDARY-v1` — FR-3, the Module 9/10 scope boundary (reason `OUT_OF_SCOPE_DISTRIBUTED`).
- `self:MAX-NIGHT-SPAN-v1` — FR-4, the 5-night / 38.75-hour ceiling (FR-2(j), T-19).
- `self:QUEUE-DEPTH-CAP-v1` — FR-7(a), the 500-job Pending Set cap.
- `self:RETENTION-DEADLINE-v1` — FR-7(b), the Retention Deadline assigned at admission (T-15, reason `RETENTION_DEADLINE`).
- `self:PREEMPTION-MARGIN-v1` — FR-16, the Preemption Margin of 20 and the THESIS/URGENT authority gate (T-7, reason `PREEMPTION_REFUSED`).
- `self:EVICTION-RAMP-v1` — FR-19, the 05:45 SIGTERM / 05:53 SIGKILL deadlines (T-5, T-6, T-9, T-10, T-20).
- `self:CHECKPOINT-QUARANTINE-v1` — FR-20, the verification discipline and the Checkpoint Quarantine (T-12, T-13).
- `self:RECONCILIATION-v1` — FR-9, missed-window reconciliation after a daemon restart (T-18).
- `self:CHECKPOINT-STORE-BUDGET-v1` — NFR-13, the Checkpoint store ceiling.
- `self:CLOCK-AUTHORITY-v1` — FR-10, the single Daemon Clock and its 1 s drift latch (readiness gate F-3).
- `self:PRIORITY-GRANT-v1` — FR-17, an administrative priority grant or revocation; the actor and reason code are in `inputs` (readiness gate F-3).
- `self:DELEGATE-UNAVAILABLE-v1` — FR-6, FR-8(e): a required delegated verdict (M1, M2, M3, M4, M5 or M8) is unavailable; reason `DELEGATE_UNAVAILABLE`; the record names the unavailable authority in `inputs`. Permitted alone because no delegated authority exists to cite (architecture edge-case review E-5).

**The split rule (F-1):** a `DENY` may be justified solely by `self:` **only when the reason is a module-owned rule** — the scope boundary (FR-3), Max Night Span (FR-4), the queue cap (FR-7), or Job Spec validation (FR-2); likewise an `EXPIRE` on a Retention Deadline (FR-7(b), T-15) may cite `self:RETENTION-DEADLINE-v1` alone, because retention is a module-owned bookkeeping rule with no delegated authority to name. A `DENY` whose reason is a **delegated verdict** (Modules 1, 2, 5, or 8) may not; it needs at least one non-`self:` citation naming the verdict. **Every `PREEMPT` and `EVICT` requires at least one non-`self:` citation, unconditionally.** `self:` is otherwise legitimate only for time and self-integrity rules. A denial, preemption, or eviction of a user's work may never be justified solely by a time or bookkeeping reason.

### 6.3 Worked example

> **EVICT** · `job_id: JOB-0417` · `node_id: ws-gpu-12` · `sim_timestamp: 2026-10-04T05:45:00-05:00`
> **Summary:** "Night Training Scheduler stopped job JOB-0417 on ws-gpu-12 at the 06:00 morning deadline so the machine is free for 08:00 lab use; last durable Checkpoint is at step 41,200, digest `sha256:3f9a…c201`."
> **Citations:** `self:EVICTION-RAMP-v1`, `node-state:M3/ws-gpu-12@2026-10-04T05:44:58-05:00`
> **Inputs:** `elapsed_runtime_s: 28140`, `checkpoint_budget_s: 300`, `estimated_total_s: 111600`, `progress_fraction: 0.252`

### 6.4 Transition → Decision Record map

*The exhaustive lookup for FR-24(f) injectivity (OQ-12): every §4.2 transition (T-1 … T-20, T-21, T-22, T-23 — T-11 was deleted in the adversarial review) and every non-transition record below carries **exactly one** Decision Record naming its own `decision`, mandatory `reason`, and required `citations`. No transition may be left without a value. Reason codes are the mandatory `reason` value on the record; they are symmetrical with the parenthesised reason in the §4.2 "To" column.*

*Single-source-of-truth rule: the map below is not a parallel spec. The `decision`, `reason`, and citation requirements stated here are the concrete values FR-24's emitter enforces; where FR-text and the map both speak, the map's assignment is the binding one, and a gap found while mapping is closed in the FR it belongs to before a record is emitted.*

| Transition | `decision` | `reason` (mandatory) | Required citation(s) |
|---|---|---|---|
| T-1 | `ADMIT` | — | `self:JOBSPEC-VALIDATION-v1`; every delegated submission verdict consulted (`entitlement:M1/…`, `policy:M2/…`, `catalog:M5/…`, `quota:M8/…`) |
| T-2 | `DENY` | `VALIDATION_FAILED` | The failing rule's authority (F-1 split rule): `self:JOBSPEC-VALIDATION-v1` alone only for a module-owned failure; the delegated verdict otherwise |
| T-3 | `ADMIT` | — | The granted-priority source that ranked the job (`policy:M2/…` or the administrator's grant record); `node-state:M3/…`; `reservation:M4/…` when consulted |
| T-4a | `DEFER` | `NO_ELIGIBLE_NODE` | `node-state:M3/…`, `reservation:M4/…` — the per-Node exclusion reasons (FR-12) |
| T-4b | `DEFER` | `CAPACITY_EXHAUSTED` | `node-state:M3/…` (the Eligible slot count); `policy:M2/…` (the ranks that placed this job outside the free slots) |
| T-5 | `COMPLETE` | — | `self:EVICTION-RAMP-v1` (completion verified at or before 05:45:00) |
| T-6 | `EVICT` | — | `self:EVICTION-RAMP-v1`; `node-state:M3/…` (last health reading) — at least one non-`self:` per FR-24(a) |
| T-7 | `PREEMPT` | — | `self:PREEMPTION-MARGIN-v1`; the challenger's granted-priority source (`policy:M2/…` or administrator grant record) — at least one non-`self:` per FR-24(a) |
| T-8 | `EVICT` / `PREEMPT` | — | Completion record of the initiating T-6/T-7 decision: keeps its `decision` (`EVICT` from the Ramp, `PREEMPT` from a Preemption) and sets `supersedes` = the T-6/T-7 record id; citations mirror the initiating record (`self:EVICTION-RAMP-v1` or `self:PREEMPTION-MARGIN-v1` + `node-state:M3/…`) |
| T-9 | `FAIL` | `CHECKPOINT_DEADLINE_MISSED` | `self:EVICTION-RAMP-v1` (the 05:53:00 deadline) |
| T-10 | `FAIL` | `CHECKPOINT_WRITE_FAILED` | `node-state:M3/…` (the write-failure evidence); `self:EVICTION-RAMP-v1` |
| T-12 | `RESUME` | — | `self:CHECKPOINT-QUARANTINE-v1` (digest re-verified at pre-verification); `node-state:M3/…` (the chosen Node) |
| T-13 | `FAIL` | `CHECKPOINT_CORRUPT` | `self:CHECKPOINT-QUARANTINE-v1` (Quarantine) |
| T-14 | `ADMIT` | — | `node-state:M3/…` (the freed slot that permits same-night re-placement); `self:PREEMPTION-MARGIN-v1` |
| T-15 | `EXPIRE` | `RETENTION_DEADLINE` | `self:RETENTION-DEADLINE-v1` (module-owned rule; permitted alone per §6.2 split rule) |
| T-16 | `EVICT` | `NODE_FAULT` | `node-state:M3/…` (the fault) — at least one non-`self:` per FR-24(a) |
| T-17 | `FAIL` | `NODE_FAULT_NO_CHECKPOINT` | `node-state:M3/…` (the fault) |
| T-18 | `DEFER` | `DAEMON_RESTORE` | `self:RECONCILIATION-v1` — the restore makes **no** new decision and defers everything to the reconciliation step (FR-9) |
| T-19 | `FAIL` | `MAX_NIGHT_SPAN_EXCEEDED` | `self:MAX-NIGHT-SPAN-v1` |
| T-20 | `ADMIT` | — | `self:EVICTION-RAMP-v1` (the ramp failure being recovered); `node-state:M3/…` (any Eligible Node, not the cordoned one) |
| T-21 | `FAIL` | `MODEL_DEPRECATED` | `catalog:M5/<model-id>@<version>` |
| T-22 | `EVICT` | `PROCESS_EXIT` | `node-state:M3/…` (the process-exit telemetry) — at least one non-`self:` per FR-24(a) |
| T-23 | `FAIL` | `PROCESS_EXIT_NO_CHECKPOINT` (`OOM_KILLED` / `PROCESS_EXITED`) | `node-state:M3/…` (the process-exit telemetry) |

**Non-transition records** (`transition: null`, `job_id` or `node_id` as flagged):

| Source | `decision` | `reason` (mandatory) | Required citation(s) |
|---|---|---|---|
| FR-9(c) — reconciliation performs a missed activation | `ADMIT` | `RECONCILIATION_ACTIVATION` | `self:RECONCILIATION-v1`; the FR-8 sequencing inputs |
| FR-9(d) — the missed window has closed | `DEFER` | `MISSED_WINDOW` | `self:RECONCILIATION-v1` |
| FR-8(e) — a blocked activation re-attempt | `DEFER` | the block reason (missing verdict / freeze lifted) | the missing authority, named (e.g. `policy:M2/…`, `catalog:M5/…`) |
| FR-7 — the Pending Set is at the cap | `DENY` | `QUEUE_FULL` | `self:QUEUE-DEPTH-CAP-v1` (module-owned, so `self:` alone is legitimate) |
| NFR-13 — submission refused on store pressure | `DENY` | `STORE_FULL` | `self:CHECKPOINT-STORE-BUDGET-v1` |
| NFR-13 — escalation to a human | `DEFER` | `DISK_PRESSURE_ESCALATION` | `self:CHECKPOINT-STORE-BUDGET-v1` |
| FR-16(c) — a refused Preemption | `DEFER` | `PREEMPTION_REFUSED` | `self:PREEMPTION-MARGIN-v1` (OQ-1) |
| FR-20(f) — a resume not verified by 21:59:00 | `DEFER` | `UNVERIFIED_RESUME` | `self:CHECKPOINT-QUARANTINE-v1` — an unverified resume is never admitted |
| FR-23(c) — a Cordon Request | `CORDON` | `CHECKPOINT_WRITE_FAILED` | `node-state:M3/…`; `self:EVICTION-RAMP-v1` |
| FR-10 — drift latched / cleared (fleet-level, `job_id: null`) | `DEFER` | `CLOCK_DRIFT_LATCHED` / `CLOCK_DRIFT_CLEARED` | `self:CLOCK-AUTHORITY-v1` |
| FR-17 — priority grant or revocation by `LAB_ADMIN` | `DEFER` | `PRIORITY_GRANTED` / `PRIORITY_REVOKED` (actor + reason code in `inputs`) | `self:PRIORITY-GRANT-v1` |
| FR-29(a) — OOM advisory | — | — | Not a separate record: the remediation (lower batch size or a 48 GB node) is carried in the `summary` and `inputs` of the T-23 `FAIL` record with reason `OOM_KILLED`. |

**Notes.**

- **T-8 (OQ-12):** CHECKPOINTING → EVICTED_RESUMABLE is the *completion* of the decision taken at T-6 (Ramp) or T-7 (Preemption), not a second decision. Its record is a revision appended under FR-24(d): same `decision`, `supersedes` = the initiating record, identical required citations. FR-24(f) counts one record per transition; FR-19's "one `EVICT` Decision Record per job" counts one decision chain (initial decision + completion).
- **T-15 vs FR-24(a) — resolved (team decision, 2026-09-28):** `EXPIRE` on a Retention Deadline is a module-owned rule with no delegated authority to name, so it joins the module-owned class of the §6.2 split rule and cites `self:RETENTION-DEADLINE-v1`. FR-24(a) and NFR-4 now require the non-`self:` citation for every `PREEMPT` and `EVICT`, and for a `DENY` based on a delegated verdict.
- **T-18:** the restore record carries `decision` `DEFER` because restoration makes no new decision; every new decision after a restart belongs to the FR-9 reconciliation step and its own records.
- The §6.3 worked example is the T-6 (`EVICT`) record rendered in full.

---

## 7. Simulation and Clock Semantics

*The Annex's standalone prototype is a "Scheduler State-Machine Simulator with fast-forward time controls (simulate 24h in 60s)." That requirement creates a real semantic hazard: at 1440×, a 5-minute Checkpoint Budget elapses in 208 ms of real time, and a naive frame-based loop will skip or double-fire the 22:00 activation, the 05:45 SIGTERM, or the 05:53 SIGKILL. This section fixes the model so the tests mean something.*

### 7.1 Clock authority

- One clock. In native mode it derives from the host's NTP-disciplined monotonic clock; in simulation mode from the Simulated Clock. No component may read wall-clock time directly (NFR-1).
- Drift detection: the Daemon Clock is compared against the host clock at a 1 Hz cadence. Drift beyond 1 s is a latched fault that blocks Window Activation until cleared (FR-10) `[ASSUMPTION: A-5]`.
- All persisted timestamps are Daemon Timestamps plus an explicit timezone offset, so a 24-hour simulated run is reproducible and diffable.

### 7.2 Execution model

- The scheduler is a **discrete-event simulator**: transitions are queued in a priority queue ordered by exact Simulated Clock instant, then by a stable sequence number. Wall-clock Fast-Forward is only a pacing layer that drains this queue faster.
- **No transition may be dropped or fired twice because of Fast-Forward.** The engine advances the Simulated Clock to the next queued instant exactly; it does not sample at frame boundaries (FR-11, NFR-6).
- Ties at an identical instant resolve by the stable sequence number assigned at enqueue, which is itself derived from the Admission Order. Two runs with the same seed and the same submission stream therefore produce identical results (NFR-7).

### 7.3 Modelled durations

Nothing in the simulation is instantaneous. Each duration is derived from a declared model, not a constant:

| Quantity | Model | Reference value |
|---|---|---|
| Checkpoint write time | `checkpoint_bytes / node_drain_rate` + `2 × fsync_latency` | 50–200 MB adapter on NVMe; fsync ≈ 100 µs NVMe, ≈ 1 ms SATA, 5–10 ms spinning |
| Job estimated duration | declared in the Job Spec, else a seeded estimate from the model's size and VRAM class | LoRA-8B QLoRA ≈ 95 min for 10k pairs × 3 epochs on one 24 GB card; peak ≈ 14 GB |
| Node health evaluation | fixed 10 s cadence, 40 s missed-heartbeat threshold | matches Module 3's declared telemetry contract |
| Checkpoint digest verification | `bytes / hash_rate` | 200 MB in ≤ 1.5 s (NFR-8) |

**Periodic Checkpoints and store bound (F-18).** Checkpoint writes also fire on the Job Spec's `checkpoint_interval_minutes` (≤ 30, FR-2(g)). With `CHECKPOINT_RETENTION_COUNT = 2` (FR-22), the steady-state store bound is **Σ over non-terminal jobs (2 × checkpoint_size)**; `CHECKPOINT_STORE_BUDGET` is sized from that formula, not ad hoc, and is driven to pressure by NFR-13.

**Modelling honesty.** Simulated duration models are calibrated against published figures, and the calibration table lives in `prd-addendum.md` `[ASSUMPTION: A-17]`. They are estimates, not measurements of this institution's hardware. A production deployment must re-calibrate against observed fleet telemetry before the Eviction Ramp constants are trusted.

### 7.4 Determinism and fault injection

- A run is identified by `(seed, submission_stream, fault_schedule)`. The same triple yields a byte-identical Decision Record log (NFR-7).
- Simulation Faults are scheduled against the Simulated Clock, never against real time, so a fault intended for 05:46 fires at 05:46 whether the run is at 1× or 1440×.
- The five injected fault kinds are node fault, Checkpoint write failure, Checkpoint corruption, daemon crash, and **training process exit** (`PROCESS_EXIT`, incl. `OOM_KILLED`) — the last exercising T-22 and T-23 (F-10). Fault injection is the only way to exercise T-10, T-13, T-18, T-22, and T-23 in the prototype.

### 7.5 Pre-verification of resuming Checkpoints

Every `EVICTED_RESUMABLE` job's resume depends on its Checkpoint digest being verified **before** the window opens, not during activation (F-16).

- A **pre-verification phase** runs at **21:30:00**: each resuming job's recorded SHA-256 digest is recomputed from its Checkpoint bytes (FR-20) — the same integrity step used at intake.
- The whole phase is budgeted by NFR-8: **every resume in the fleet is verified by 21:59:00**, worst case being all 33 GPU slots resuming within 29 minutes.
- A Checkpoint that fails pre-verification is Quarantined and the job transitions to `FAILED` (`CHECKPOINT_CORRUPT`) exactly as under FR-20(c), 30 minutes earlier than the old 22:00 check, with the same notification.
- A job whose verification is **unfinished at 21:59:00** is **not admitted that night**: Window Activation at 22:00 admits a resume only if it was fully verified beforehand, and the exclusion is recorded as a cited `DEFER` Decision Record — a job is never admitted on an unverified resume.
- Because hashing happens here, **Window Activation never hashes**; NFR-2's admission-order budget explicitly excludes Checkpoint hashing (moved to this phase).

---

## 8. Features

*Each FR states System responsibility, Trigger, Inputs, Validation rules, Outputs, and a testable condition, as required by the task statement. FRs are numbered globally and referenced by the Phase 2 and Phase 3 artifacts.*

### 8.1 Feature A — Submission and Job Spec Validation

**Description:** Kavita submits a Training Job during the day. The system either admits it to the Pending Set or refuses it with a specific, cited reason. It never admits a job it cannot later place, and it never refuses a job without saying which rule refused it. Realizes UJ-1.

#### FR-1: Submit a Training Job

**System responsibility:** Accept a Job Spec, determine whether this module owns it, and place the Training Job in `QUEUED_PENDING_WINDOW` or `REJECTED` — never anywhere else.
**Trigger:** A submission request on the API or the desktop surface.
**Inputs:** Job Spec; submitting principal; idempotency key; client wall-clock reading (advisory only).
**Validation rules:** (a) the idempotency key must be unseen, else FR-5 applies: a repeated key with an identical payload digest returns the existing `job_id` with no state change (HTTP 200), and a repeated key with a different digest is a client error (HTTP 409, no job created). (b) FR-2 must pass in full; (c) the delegated entitlement, quota, and policy verdicts from Modules 1, 8, and 2 must all be present and ALLOW; (d) `worker_count` must equal 1.
**Outputs:** `job_id`, admitted state, position in the Pending Set, projected first-start estimate, Retention Deadline, and a Decision Record with `ADMIT` or `DENY`.
**Testable condition:** A Job Spec submitted at 14:30 with all validations passing and an estimated duration of 31 hours returns HTTP 201 with state `QUEUED_PENDING_WINDOW` and a response body stating the job requires at least 4 Night Windows; the same Job Spec resubmitted with the same idempotency key returns HTTP 200 with the identical `job_id` and the Pending Set length is unchanged.

**Out of Scope:** provisioning API keys (Module 1); license acceptance (Module 5).

#### FR-2: Validate the Job Spec

**System responsibility:** Guarantee that no admitted Job Spec describes work this module cannot place, and that every rejection cites the specific field and rule that failed.
**Trigger:** Every submission; every Window Activation (deprecation re-check, FR-6); and every resume of a `QUEUED_PENDING_WINDOW` job whose Job Spec has changed.
**Inputs:** The Job Spec.
**Validation rules:** (a) container image must be pinned by digest, not tag; (b) `gpus_per_node` must be 1 or 2; (c) requested VRAM must not exceed the largest single-Node VRAM class (48 GB) — this rejects 70B-class jobs on a 24 GB workstation with a citation naming the requested and available classes; (d) resource `requests` must equal resource `limits` for GPU and memory, since quota accounting reads `requests`; (e) `node_selector`, if present, must name a Node matching a declared VRAM class; (f) `restart_policy` must not request a restart that would silently re-enter a Night Window without re-admission; (g) `checkpoint_interval_minutes` must be a positive integer **≤ 30** (F-17) — a longer interval would let progress since the last Checkpoint exceed what the Checkpoint Budget can plausibly flush at the Ramp; (h) the model record from Module 5 must exist and must not be deprecated; (i) the Job Spec must declare an estimated duration, or have one derived from the model record; **(j) the estimated duration must not exceed Max Night Span — 5 consecutive Night Windows, 38.75 hours of usable training (5 × 7 h 45 min). An estimate above 38.75 h is a rejection, not a multi-night admission.** **(k) `gpus_per_node = 2` is valid only when the requested VRAM class is 48 GB, i.e. only `server-gpu-01` can host it (both slots, A-19); a 2-GPU Job Spec targeting the 24 GB class or pinning a `ws-gpu-NN` node is refused with `self:JOBSPEC-VALIDATION-v1` naming this rule, so no admitted job is ever unplaceable (UX edge-case review E-3).**
**Outputs:** A validation result carrying, per field, `pass` or a `rule_id` plus a human-readable message; every rejection's `DENY` Decision Record cites the failing rule under `self:JOBSPEC-VALIDATION-v1`.
**Testable condition:** A Job Spec pinned to `:latest`, on a single-worker Job Spec (`worker_count = 1`, so the FR-3 scope short-circuit never fires), requesting 64 GB VRAM and a `checkpoint_interval_minutes` of 240 produces exactly three rejections — digest (a), VRAM class (c), and Checkpoint interval (g) — each naming the field and the rule identifier, each reported individually rather than as a generic "invalid spec."

#### FR-3: Refuse multi-node and distributed Training Jobs

**System responsibility:** Keep the Module 9 / Module 10 boundary enforceable at the edge, not merely documented.
**Trigger:** Any submission whose `worker_count` or `replicas` exceeds 1.
**Inputs:** The Job Spec.
**Validation rules:** (a) `worker_count = 1` and `replicas = 1`; (b) no `elastic_policy`, no `nprocPerNode: auto`, no rendezvous configuration.
**Note (F-28):** the scope check short-circuits **before** FR-2's field validation runs — a multi-worker or multi-replica Job Spec is refused here with `OUT_OF_SCOPE_DISTRIBUTED` and FR-2 is never evaluated. FR-2's field-level rejection test therefore uses `worker_count = 1`.
**Outputs:** `REJECTED` with a `DENY` Decision Record citing `self:SCOPE-BOUNDARY-v1` and naming Module 10 as the owning module.
**Testable condition:** A valid 4-worker PyTorchJob-style Job Spec is rejected with reason `OUT_OF_SCOPE_DISTRIBUTED` and a message naming Module 10; the Pending Set length is unchanged and no GPU allocation is attempted.

**Out of Scope:** all multi-node placement, topology validation, and gang scheduling.

#### FR-4: Estimate duration, enforce Max Night Span, and required VRAM

**System responsibility:** Produce the two numbers the Admission Order and the Eviction Ramp both depend on, bound the job against Max Night Span, and be honest that the numbers are estimates.
**Trigger:** Admission to the Pending Set; re-estimation on every resume; and at every Admission Order computation, against the job's Admitted Nights.
**Inputs:** The Job Spec; the model record from Module 5; the target Node's VRAM class; the job's Admitted Nights.
**Validation rules:** (a) the estimate must be expressed in seconds and must carry a stated confidence; when declared it is trusted as given `[ASSUMPTION: A-11]`; (b) an estimate exceeding the **Usable Night Duration (7 h 45 min, 22:00–05:45)** must set `requires_multiple_nights = true` on the response (F-15), and must never be treated as a rejection on its own; (c) an estimate exceeding **38.75 hours** is refused at submission with a Decision Record citing `self:MAX-NIGHT-SPAN-v1`, naming the estimate and the 5-night ceiling (5 × 7 h 45 min) `[ASSUMPTION: A-12]`, and proposing a **concrete scope reduction** — lower `epochs`, raise `gradient_accumulation_steps` to trade compute for memory, reduce the dataset size, or target a smaller base model; (d) a Training Job whose Admitted Nights has reached 5 without reaching `COMPLETED` is refused further admission and transitions to `FAILED` with reason `MAX_NIGHT_SPAN_EXCEEDED` and the same citation; (e) a refusal under (c) or (d) must retain the job's last verified Checkpoint (Invariant S-2) and must name the step the job reached, so a human can decide whether to resubmit a reduced scope or to seek an extension.
**Outputs:** `estimated_duration_s`, `estimated_completion_nights`, `required_vram_gb`, `admitted_nights`, `max_night_span`, `confidence`; or a refusal carrying the citation and the proposed scope reduction.
**Testable condition:** A Job Spec declaring 31 hours returns `requires_multiple_nights: true` and `estimated_completion_nights: 4` and is admitted; a Job Spec declaring 3 hours returns `false` and `1` and is admitted; a Job Spec declaring 52 hours is refused with a `DENY` Decision Record citing `self:MAX-NIGHT-SPAN-v1`, naming both 52 h and the 38.75 h ceiling, and proposing at least one concrete scope reduction, and the Pending Set length is unchanged; a job admitted on 5 consecutive nights that has not completed is refused admission on the 6th night and transitions to `FAILED` with reason `MAX_NIGHT_SPAN_EXCEEDED` while its last verified Checkpoint remains byte-identical on disk.

#### FR-5: Idempotent submission

**System responsibility:** Make double-clicks, client retries, and Fast-Forward-induced replays harmless.
**Trigger:** Any submission; any daemon restart replay.
**Inputs:** Idempotency key; payload digest.
**Validation rules:** a repeated key with an identical payload digest returns the original result; a repeated key with a different digest is a client error and returns HTTP 409.
**Outputs:** The original `job_id` and state, or 409.
**Testable condition:** Submitting the same key 100 times concurrently produces exactly one Training Job, 99 HTTP 200 responses and 1 HTTP 201, and a Pending Set length increase of exactly 1; the same key resubmitted with a **different** payload digest returns HTTP 409 and creates no job (F-29).

#### FR-6: Consume delegated verdicts

**System responsibility:** Treat Modules 1, 2, 5, and 8 as authorities and never as advisory input. This module computes no entitlement, no quota, and no policy verdict of its own.
**Trigger:** Every submission and every Window Activation.
**Inputs:** Entitlement verdict (M1), quota verdict (M8), policy verdict and freeze state (M2), model record (M5).
**Validation rules:** (a) all four must be present; (b) any missing verdict is a blocking error, never a default ALLOW; (c) a `freeze` state from Module 2 admits zero jobs and is re-evaluated at **every** activation attempt (FR-8(e)), not cached for the night `[ASSUMPTION: A-16]`; (d) **the Module 5 model record is re-checked at every Window Activation (F-6)** — a job whose model was deprecated since submission transitions to `FAILED` with reason `MODEL_DEPRECATED` and a `catalog:M5/<model-id>@<version>` citation, before any placement, so a queued job never wakes only to fail on first use; (e) if the deprecation verdict is itself missing at activation, the job is deferred with a cited reason rather than assumed healthy.
**Outputs:** A consolidated admission verdict feeding FR-1 and FR-8; the individual verdicts are attached to the resulting Decision Record as citations.
**Testable condition:** With the Module 8 quota source returning 503, 100 consecutive submissions produce 100 refusals and 0 admissions; with the freeze state active, Window Activation admits 0 jobs and every Eligible Node is reported idle with the freeze cited; a job whose model record flipped to deprecated while it waited is `FAILED` with reason `MODEL_DEPRECATED` and a `catalog:M5/…` citation after the next activation.

#### FR-7: Bound the Pending Set

**System responsibility:** Prevent unbounded queue growth, which is an operational failure mode in its own right.
**Trigger:** Every admission attempt; nightly garbage collection at 03:00.
**Inputs:** Current Pending Set length; candidate Job TTL; Checkpoint store size.
**Validation rules:** (a) `QUEUE_DEPTH_CAP = 500` `[ASSUMPTION: A-20]`; if the Pending Set length is at or above it, refuse the submission with a `self:QUEUE-DEPTH-CAP-v1` citation and a next-available-slot estimate; (b) every admitted job receives a Retention Deadline; (c) garbage collection at 03:00 removes Checkpoints only from `EXPIRED` jobs whose **7-day expiry grace has elapsed**, and never removes the 2 most recent verified Checkpoints of a non-terminal job (F-2, F-3).
**Outputs:** Admission or refusal with an estimate; garbage-collection report.
**Testable condition:** With `QUEUE_DEPTH_CAP` set to 10, the 11th submission is refused with a Decision Record citing `self:QUEUE-DEPTH-CAP-v1` and a next-available-slot estimate; garbage collection at 03:00 with an `EXPIRED` job past the 7-day grace and a `QUEUED_PENDING_WINDOW` job removes exactly the first job's Checkpoints, while an `EXPIRED` job still inside the grace retains them.

### 8.2 Feature B — Night Window Activation and Clock

**Description:** At 22:00:00 the Night Daemon Controller decides the night. Realizes UJ-2.

#### FR-8: Perform Window Activation

**System responsibility:** Deterministically decide which Training Jobs run tonight, on which Nodes, and in what order, and record the reasoning.
**Trigger:** Exactly 22:00:00 campus local time; or Window Reconciliation (FR-9).
**Inputs:** Pending Set; Eligible Node set; delegated verdicts; Effective Priority of every pending job; Consecutive Nights Missed.
**Validation rules:** (a) the Admission Order is computed before any placement and is deterministic; (b) a job is admitted only if an Eligible Node with a matching VRAM class exists; (c) **no GPU slot receives more than one Training Job per Night Window** `[ASSUMPTION: A-19]` — allocation is counted per slot (33 slots in total: 31 workstation slots + 2 on `server-gpu-01`), so `server-gpu-01` may host up to two 1-GPU jobs or one 2-GPU job (F-42); (d) activation is idempotent — a second activation in the same window performs no additional placement; (e) **if activation is blocked** — a delegated verdict is missing, or a freeze was lifted since the last attempt — **it re-attempts every 5 simulated minutes until 04:00:00**, and each attempt is recorded as a Decision Record with the block reason cited (F-38).
**Outputs:** The Admission Order; one placement per admitted job; one `ADMIT` Decision Record per placement citing the specific rule that ranked the job; a status of every Eligible Node as running or idle-with-reason.
**Testable condition:** Given a fixed seed, a Pending Set of 22 jobs, and a 32-node (33-slot) fleet with 33 eligible slots, activation produces exactly 22 placements, the same 22 `job_id`s in the same order across 10 consecutive runs, and an Admission Order that places no job at a rank lower than its Effective Priority permits; with the Module 2 verdict missing at 22:00, activation re-attempts at 22:05 with a recorded attempt Decision Record and admits jobs once the verdict returns.

#### FR-9: Reconcile a missed Night Window

**System responsibility:** Recover from the daemon being down when the window opened, which is a realistic and under-specified failure.
**Trigger:** Daemon start, or drift fault clearance, at any Simulated Clock instant.
**Inputs:** Last committed decision sequence number; Pending Set; Daemon Clock.
**Validation rules:** (a) on start, the daemon first restores every job's state from the durable decision log, **without replaying any transition** (F-12); (b) reconciliation then runs as a **separate, recorded step**: the daemon computes whether any Window Activation instant elapsed while it was not running; (c) if one elapsed and the Night Window is still open, activation is performed immediately with a Decision Record citing `self:RECONCILIATION-v1`; (d) if the Night Window has also closed, the missed window is recorded as a Decision Record with `DEFER` and no jobs are admitted; (e) the no-replay property (F-13) is enforced here rather than by the T-18 guard: restore reproduces the exact pre-crash state, and only then does reconciliation decide something new.
**Outputs:** A reconciliation Decision Record; either a completed activation or a recorded deferral.
**Testable condition:** With the daemon crashed at 21:00 and restarted at 22:30, activation runs once, admits jobs, and produces exactly one reconciliation Decision Record; with the daemon crashed at 21:00 and restarted at 07:00, zero jobs are admitted and exactly one `DEFER` Decision Record names the missed window.

#### FR-10: Enforce Daemon Clock authority and drift detection

**System responsibility:** Ensure no scheduling decision is made against an untrustworthy clock.
**Trigger:** Every second; every scheduling decision.
**Inputs:** Simulated or host monotonic clock; offset reading.
**Validation rules:** (a) no module component reads wall-clock time directly; (b) drift beyond 1 s latches a fault that blocks the next Window Activation; (c) the fault clears only when drift is within tolerance for 3 consecutive checks.
**Outputs:** Latched or cleared drift fault; a Decision Record on each transition of the fault.
**Testable condition:** Injecting 5 s of drift blocks the next activation and emits a Decision Record; restoring the clock for 3 consecutive checks clears it and the following activation proceeds.

#### FR-11: Advance simulated time without quantizing events

**System responsibility:** Make Fast-Forward a pure pacing concern so that a 60-second 24-hour run and a 24-hour real run produce the same decisions.
**Trigger:** Any Fast-Forward rate change, including stepping and pausing.
**Inputs:** Current Simulated Clock; queued transition instants; target rate.
**Validation rules:** (a) the engine advances the Simulated Clock to each queued instant exactly, never by sampling; (b) changing the rate mid-window may not reorder, add, or remove any queued transition; (c) a rate of 0 pauses without draining the queue.
**Outputs:** Exact event firing; a reconciliation count.
**Testable condition:** Running 24 simulated hours at 1440×, then at 1×, then at 60× with the same seed produces identical Decision Record logs and an identical total event count; the count equals the analytic expectation for that seed's fault schedule; a 1× versus 1440× comparison over the 05:30:00–06:00:00 simulated slice yields byte-identical logs, proving the Ramp is not quantized (F-22).

### 8.3 Feature C — Node Eligibility and Placement

**Description:** Decide which of the 32 Nodes may take work tonight, and which specific Node a given job gets. Realizes UJ-2.

#### FR-12: Compute the Eligible Node set

**System responsibility:** Never place a job on a Node that is unhealthy, cordoned, reserved, or of the wrong VRAM class.
**Trigger:** Window Activation; and re-evaluation before every placement and before every resume.
**Inputs:** Module 3 node health and `SchedulingDisabled` state; Module 4 active reservations; the Job Spec's VRAM class; the Cordon Request register.
**Validation rules:** (a) a Node with a Module 3 fault, a `SchedulingDisabled` condition, or an outstanding Cordon Request from this module is not Eligible; (b) a Node whose reservation interval overlaps the Night Window is not Eligible for the whole window; (c) a Node whose VRAM class is below the Job Spec's requirement is not Eligible for that job; (d) eligibility is re-evaluated immediately before each placement, so a fault arriving mid-activation is honoured.
**Outputs:** The Eligible Node set with a per-Node exclusion reason.
**Testable condition:** With `ws-gpu-19` cordoned and a Module 4 reservation covering `ws-gpu-20`…`ws-gpu-25` for the full window, Window Activation places zero jobs on `ws-gpu-19` through `ws-gpu-25`, and every other idle Node reports an exclusion reason naming either `M3_CORDONED`, `M4_RESERVED`, or `VRAM_CLASS_INSUFFICIENT`.

#### FR-13: Select the Node

**System responsibility:** Choose deterministically and explainably, so that the same inputs always yield the same placement and Ines can defend it.
**Trigger:** Each placement.
**Inputs:** Eligible Node set; VRAM class; the Job's prior Node from a prior night.
**Validation rules:** (a) placement prefers the job's prior Node when it is Eligible and its VRAM class or slot matches, because resuming on a different Node invalidates local SSD cache locality; (b) otherwise select the Eligible Node with the lowest current **slot**-allocation count, breaking ties by Node identifier ascending; (c) the choice is recorded in the Decision Record with the two or three candidates considered and the rule that decided it.
**Outputs:** A chosen Node and a `Decision Record` naming the candidates and the deciding rule.
**Testable condition:** Two jobs requiring the same VRAM class land on the two lowest-identifier Eligible Nodes of that class; a resuming job lands on its prior Node when that Node is Eligible, and on a different Node with a `PRIOR_NODE_INELIGIBLE` note when it is not.

### 8.4 Feature D — Priority, Aging, and Preemption

**Description:** Decide whose work runs tonight, and — rarely, and only on explicit administrative authority — whose running work stops. Realizes UJ-4.

#### FR-14: Compute Effective Priority

**System responsibility:** Produce one deterministic ordering key, and make starvation structurally impossible over time.
**Trigger:** Every Admission Order computation; every Preemption comparison.
**Inputs:** Granted Priority from Module 2 or a lab administrator; Consecutive Nights Missed; `AGING_RATE`; `AGING_CAP`.
**Validation rules:** (a) `AGING_RATE = 6` and `AGING_CAP = 30` `[ASSUMPTION: A-6 — see §15 Open Question 1]`; (b) Granted Priority is read-only to this module and may only be `EXPLORATION`, `THESIS`, or `URGENT`; (c) a student's self-declared intent never contributes to Effective Priority; (d) Consecutive Nights Missed is incremented at the end of each Night Window in which the job received zero admitted minutes, and reset to zero on any admitted minute.
**Outputs:** `effective_priority`, a decomposition showing the granted and aged components, and the Decision Record fields needed to explain the rank.
**Testable condition:** An `EXPLORATION` job with 0 missed nights has Effective Priority 10; the same job with 5 missed nights has 40; a `THESIS` job with 0 missed nights has 50 and cannot be outranked by an aged `EXPLORATION` job at any aging level; a job with 1 admitted minute has Consecutive Nights Missed reset to 0.

#### FR-15: Apply Starvation Promotion

**System responsibility:** Guarantee that no job waits forever, **without** authorising Preemption — starvation is fixed by admission order, not by killing a thesis run.
**Trigger:** Admission Order computation.
**Inputs:** Consecutive Nights Missed for every pending job; `STARVATION_NIGHTS`; `STARVATION_PROMOTION_LIMIT`.
**Validation rules:** (a) `STARVATION_NIGHTS = 3` `[ASSUMPTION: A-7]`; (b) a job with `Consecutive Nights Missed ≥ 3` is promoted to the head of the Admission Order, ahead of all non-promoted jobs; (c) at most `STARVATION_PROMOTION_LIMIT = 4` jobs are promoted per Night Window, and where more qualify, the highest Consecutive Nights Missed wins with submission time as tie-break; (d) promotion confers no authority to preempt.
**Outputs:** The Admission Order with promotions annotated.
**Testable condition:** With 6 jobs at `Consecutive Nights Missed ≥ 3` and a cap of 4, exactly 4 are promoted, being the 4 with the highest missed-night counts, and the Admission Order places all 4 ahead of the unpromoted `THESIS` job that has 0 missed nights.

#### FR-16: Authorise and execute Preemption

**System responsibility:** Make stopping someone's running work a deliberate, gated, and fully explained act — and make thrashing impossible.
**Trigger:** A pending job outranks a `RUNNING` job and no Eligible Node is free.
**Inputs:** Challenger and victim Effective Priority; Challenger Granted Priority; Preemption Margin; victim's Checkpoint state.
**Validation rules:** (a) `Preemption Margin = 20` `[ASSUMPTION: A-8]`; (b) the challenger's Effective Priority must be at least the victim's plus 20, **and** the challenger's Granted Priority must be `THESIS` or `URGENT` — aging alone can never authorise Preemption; (c) the victim must have a verified Checkpoint, or be able to produce one within the Checkpoint Budget, or the Preemption is **refused and recorded as a `DEFER` Decision Record with reason `PREEMPTION_REFUSED` and a citation to `self:PREEMPTION-MARGIN-v1` (OQ-1)**; (d) Preemption drives the victim through the same `CHECKPOINTING` path as the Eviction Ramp — the challenger does not start until the victim's Checkpoint verifies and the Node is released; (e) the victim transitions `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW` **immediately** once its Checkpoint verifies (T-14), with its Checkpoint attached and its **original submission time preserved** — its Consecutive Nights Missed is **not** incremented, because it received an admitted minute this window (FR-14(d)); it may be re-placed the same night if an Eligible Node frees (F-5, F-8); (f) the same victim may not be preempted twice within one Night Window.
**Outputs:** Preemption Decision Record, `CHECKPOINTING` → `EVICTED_RESUMABLE` for the victim, `ADMIT` for the challenger; the victim's preserved state.
**Testable condition:** **Annex Scenario 4** — a `THESIS` challenger at Effective Priority 50 preempts an `EXPLORATION` victim at aged Effective Priority 22 (50 ≥ 22 + 20), with no Urgent Grant anywhere in the path, and the victim is checkpointed before the challenger starts. Conversely, an aged `EXPLORATION` challenger at Effective Priority 40 **cannot** preempt a `THESIS` victim at 50 (margin 10 < 20) and is refused with a `DEFER` Decision Record, reason `PREEMPTION_REFUSED`, citing `self:PREEMPTION-MARGIN-v1` — proving aging alone confers no authority. An `URGENT` challenger at 90 preempts a `THESIS` victim at 50. In every preemption case the victim is not preempted again in the same window.

#### FR-17: Administer Priority grants

**System responsibility:** Ensure priority is a governed resource and cannot be self-allocated.
**Trigger:** A priority grant, a self-declared intent at submission, or a revocation.
**Inputs:** Actor identity from Module 1; actor role; target `job_id`; reason code.
**Validation rules:** (a) only a role the lab administrator recognises may set Granted Priority — and a Urgent Grant is scoped **per job**, not per submitter per window `[ASSUMPTION: A-13]`; (b) setting `URGENT` requires a non-empty reason code and is written to a Decision Record (`PRIORITY_GRANTED`, `self:PRIORITY-GRANT-v1`, PRD §6.4) with the actor; (c) a self-declared intent is stored as a request visible to the administrator and never applied; (d) revoking a grant takes effect at the next Admission Order computation and never aborts a `RUNNING` job.
**Outputs:** The grant, revocation, or recorded request; the Decision Record.
**Testable condition:** A student submitting with `declared_intent: THESIS` receives `granted_priority: EXPLORATION` until an administrator grants otherwise, and the Decision Record shows the request as `PENDING_REVIEW`; a grant of `URGENT` without a reason code is rejected; revoking `URGENT` does not stop the already-`RUNNING` job.

### 8.5 Feature E — Checkpointing, Eviction, and Resume

**Description:** The heart of the module. Stop work without losing it, and prove it stopped cleanly. Realizes UJ-3, UJ-5, UJ-6.

#### FR-18: Capture a durable Checkpoint

**System responsibility:** Guarantee that a Checkpoint is genuinely recoverable, or that the system knows it is not. A Checkpoint that is merely written is not a Checkpoint.
**Trigger:** Eviction signal, Preemption, node fault, or the Job Spec's `checkpoint_interval_minutes`.
**Inputs:** Job state at signal; the training process; the Node's storage class.
**Validation rules:** (a) the sequence is: write to a temporary file → `fdatasync` the file → atomic `rename` into the final path → `fsync` the parent directory → compute and record the SHA-256 digest; (b) the Checkpoint is not considered durable until all five steps complete; (c) the digest, byte count, step number, and Simulated Timestamp are recorded together or not at all; (d) a partial or undurable Checkpoint is deleted, never left to be discovered later.
**Outputs:** A durable Checkpoint with a recorded digest, or a typed failure.
**Testable condition:** A Checkpoint interrupted after `rename` but before the parent-directory `fsync` is treated as not durable and is deleted; the next night's resume does not find it and the job re-enters `QUEUED_PENDING_WINDOW` with no attached Checkpoint. A complete Checkpoint survives a simulated power loss of the Node with digest intact.

#### FR-19: Execute the Eviction Ramp

**System responsibility:** Guarantee that at 06:00:00 no Training Job holds a GPU, and that the 2 h 07 min between the end of the Eviction Ramp (05:53:00) and the 08:00 lab session stay clean.
**Trigger:** 05:45:00 campus local time.
**Inputs:** Set of `RUNNING` jobs; the Daemon Clock; each job's Checkpoint state.
**Validation rules:** (a) SIGTERM is dispatched to every `RUNNING` job at 05:45:00 ± 2 s; (b) the Checkpoint Budget is the 300 s *expected* window from 05:45:00 to 05:50:00, but the 05:50:00–05:53:00 reserve is **still usable** (F-7): a Checkpoint verified any time before 05:53:00 satisfies T-8 `[ASSUMPTION: A-9]`; (c) SIGKILL is dispatched to every surviving job at 05:53:00 ± 2 s regardless of its state; (d) each Node's allocation is released independently and immediately on that job's exit, not at 05:53:00; (e) a job that reaches `COMPLETED` before 05:45:00 is not signalled; (f) a job that has not produced a verified Checkpoint by 05:53:00 transitions to `FAILED` (reason `CHECKPOINT_DEADLINE_MISSED`) with its last verified Checkpoint retained.
**Outputs:** Every job in a terminal or resumable state; every Node released; one `EVICT` Decision Record per job citing the Eviction Ramp rule and the Node's last health reading.
**Testable condition:** Advancing the Simulated Clock to 06:00:00 with 14 jobs `RUNNING` results in exactly 0 Node allocations held, 14 `EVICT` Decision Records, and 0 jobs in `RUNNING` or `CHECKPOINTING`; a job that completed at 05:44:00 receives no signal.

#### FR-20: Verify Checkpoint integrity on resume

**System responsibility:** Never load a Checkpoint that might be corrupt, and never destroy one that might be recoverable.
**Trigger:** The 21:30:00 pre-verification phase (F-16); re-admission of an `EVICTED_RESUMABLE` job at 22:00:00.
**Inputs:** The recorded SHA-256 digest; the Checkpoint bytes.
**Validation rules:** (a) the digest is recomputed from the bytes and compared **at the 21:30:00 pre-verification phase** before the job is admitted as a resume; (b) a match admits the resume and emits a `RESUME` Decision Record citing the digest; (c) a mismatch places the Checkpoint in Checkpoint Quarantine, transitions the job to `FAILED` with reason `CHECKPOINT_CORRUPT`, emits a `FAIL` Decision Record citing `self:CHECKPOINT-QUARANTINE-v1`, and notifies a human; (d) a quarantined Checkpoint is excluded from garbage collection until released by a human; (e) no Cordon Request is issued for a corrupt artifact, because a corrupt file is not evidence of a faulty Node; (f) **a job whose Checkpoint was not fully verified by 21:59:00 is not admitted that night**, recorded as a cited `DEFER` Decision Record — a job is never admitted on an unverified resume (F-16).
**Outputs:** A verified resume, or a quarantined Checkpoint and a `FAILED` job.
**Testable condition:** A Simulation Fault corrupting one byte of a recorded Checkpoint causes the resume to be refused, the Checkpoint to enter Checkpoint Quarantine, zero bytes to be loaded into any training process, and a human notification naming the digest mismatch; a fault-free Checkpoint resumes and logs `RESUMED_FROM_CHECKPOINT`.

#### FR-21: Resume a Training Job from its Checkpoint

**System responsibility:** Make a job that spans nights one job, not four.
**Trigger:** Admission of an `EVICTED_RESUMABLE` job to a Night Window.
**Inputs:** Verified Checkpoint; the Job Spec; the chosen Node.
**Validation rules:** (a) resume proceeds only from the most recent verified Checkpoint; (b) the resume point is logged as a step number, not a wall-clock time; (c) a job whose Job Spec changed incompatibly since the Checkpoint is refused with an explanation; (d) the job's total elapsed training time is the sum of its admitted intervals, excluding Ramp and downtime; (e) a resume that would take the job's Admitted Nights past Max Night Span is refused under FR-4(d) rather than admitted, so a job is never woken from a verified Checkpoint only to be evicted at dawn with nothing gained; (f) a job in `EVICTION_FAILED` resumes on **any** Eligible Node — the cordon on the failed Node constrains that Node, not the job (T-20).
**Outputs:** A `RUNNING` job resuming at a known step, with a `RESUME` Decision Record.
**Testable condition:** A job evicted three times and admitted four times logs a single continuous step count and a total admitted duration equal to the sum of its four intervals, with the three Ramp periods excluded; the same job at 4 Admitted Nights resumes into a 5th night but is refused admission into a 6th, and the refusal Decision Record names `MAX_NIGHT_SPAN_EXCEEDED` rather than silently evicting it.

#### FR-22: Govern the Checkpoint lifecycle

**System Responsibility:** Bound disk growth without ever destroying recoverable work.
**Trigger:** 03:00 nightly; Retention Deadline expiry; disk budget pressure.
**Inputs:** Checkpoint store contents; job states; Retention Deadlines; `CHECKPOINT_STORE_BUDGET`.
**Validation rules:** (a) `CHECKPOINT_RETENTION_COUNT = 2` `[ASSUMPTION: A-21]` — garbage collection at 03:00 removes Checkpoints belonging only to `EXPIRED` jobs whose **7-day expiry grace has elapsed** (F-2), and **superseded Checkpoints beyond the latest 2 verified** (`CHECKPOINT_RETENTION_COUNT`); (b) **the 2 most recent verified Checkpoints of a non-terminal job are never removed automatically** (F-3); (c) no Quarantined Checkpoint is ever removed automatically; (d) when the store exceeds `CHECKPOINT_STORE_BUDGET` `[ASSUMPTION: A-10]`, the oldest eligible `EXPIRED`-job Checkpoints are removed first and the pressure is reported; (e) if only non-terminal or quarantined Checkpoints remain and the budget is still exceeded, collection halts and escalates to a human rather than deleting them.
**Outputs:** A garbage-collection report; a disk-pressure Decision Record.
**Testable condition:** With the store at 21 GB containing one `EXPIRED` job's Checkpoint (past its 7-day grace) and three `QUEUED_PENDING_WINDOW` jobs' Checkpoints, plus a superseded third-oldest Checkpoint of one pending job, collection removes only the `EXPIRED` artifacts and the superseded third-oldest, brings the store under budget, and leaves the 2 most recent verified Checkpoints of every non-terminal job byte-identical; with no eligible artifacts available, collection halts and escalates.

#### FR-23: Handle Checkpoint failure during the Eviction Ramp

**System responsibility:** Satisfy the Annex's mandatory edge case: a failed Checkpoint at dawn must cost a node, not a night's work and not a morning lab session. This is the module's hardest correctness requirement.
**Trigger:** Any Checkpoint error during the Eviction Ramp or a Preemption.
**Inputs:** The typed Checkpoint failure; the Node identity; the last verified Checkpoint.
**Validation rules:** (a) on Checkpoint write failure the Node allocation is released **immediately** and unconditionally — before any retry, diagnosis, or notification; (b) the daemon must not retry the Checkpoint on the same Node; (c) a Cordon Request naming the Node and the failure is issued to Module 3, and the Node is treated as not Eligible for the remainder of the night and until a human clears it — treated optimistically as not Eligible pending Module 3's acknowledgement `[ASSUMPTION: A-15]`; (d) the job transitions to `EVICTION_FAILED` with reason `CHECKPOINT_WRITE_FAILED`; (e) the last verified Checkpoint is retained, never deleted; (f) the submitting principal and the lab administrator are both notified, with the Node named and the resume point stated; (g) the failure is reported to the Job's status board with the same citation discipline as any other decision; (h) **known limitation 1 (F-45):** if Module 3 *rejects* the Cordon Request, this module still keeps the Node locally not-Eligible for the remainder of the night — the rejection is recorded in a Decision Record, and the Node returns to the Eligible set only after a human clears it; (i) **known limitation 2 (F-45):** a Checkpoint write failure caused by kubelet DiskPressure rather than a faulty Node is a possible **false positive**; the cordon reason names the failure so the lab administrator can distinguish the two during clearance (see addendum §B.3).
**Outputs:** A released GPU, a Cordon Request, a `FAIL` Decision Record, a retained Checkpoint, and two notifications.
**Testable condition:** Injecting a Checkpoint write failure at 05:46:00 on `ws-gpu-19` results in: `ws-gpu-19` GPU allocation released by 05:46:01; a Cordon Request emitted for `ws-gpu-19`; `ws-gpu-19` absent from the Eligible Node set for the rest of the window; the job in `EVICTION_FAILED` with reason `CHECKPOINT_WRITE_FAILED`; the 03:10 Checkpoint still present and byte-identical; exactly two notifications, one to the submitter and one to the lab administrator; and zero jobs placed on `ws-gpu-19` for the remainder of the night.

### 8.6 Feature F — Explainability, Observability, and Audit

**Description:** Make the module's behaviour inspectable by a human who was not present. Realizes UJ-2, UJ-4, UJ-5.

#### FR-24: Emit a cited Decision Record for every transition

**System responsibility:** Make §6 a machine-enforced invariant rather than a documentation aspiration.
**Trigger:** Every state transition in §4.2, without exception.
**Inputs:** The transition; the delegated verdicts consulted; the evaluated inputs.
**Validation rules:** (a) a `DENY` based on a delegated verdict, and every `PREEMPT` and `EVICT`, require at least one non-`self:` citation; a `DENY` based on a module-owned rule (scope boundary, Max Night Span, queue cap, or Job Spec validation) and an `EXPIRE` on a Retention Deadline may cite `self:` alone (F-1, §6.4); (b) any record with zero citations is rejected by the emitter and **the transition it describes is not applied** — fail closed, and the rejection is logged as an `EMITTER_REJECTED` integrity event; (c) `summary` must satisfy §6.1; (d) records are immutable and append-only; (e) emission is durable before the transition is committed, not after; (f) **every transition has exactly one Decision Record (injective), and every non-transition record carries `transition: null`** (F-23).
**Outputs:** A durable Decision Record for every transition; an integrity count of records against transitions.
**Testable condition:** Across a 30-night simulated run, every transition has exactly one Decision Record, every record names a transition or carries `transition: null`, and zero records have an empty `citations` array; a deliberately citation-less denial is refused by the emitter, the job is left in its prior state, and an `EMITTER_REJECTED` integrity event is logged.

#### FR-25: Expose job state and the night's plan

**System responsibility:** Let Ines see what will happen and Kavita see what happened.
**Trigger:** Any status query; a polling interval; a state change.
**Inputs:** The Pending Set; the Admission Order; live job states; Node states.
**Validation rules:** (a) every state a job can occupy is one of the nine in §4.1 and no other; (b) the status surface renders the citation list for any decision it displays; (c) polling at 1 Hz over 500 jobs returns within the NFR-9 budget; (d) the board shows idle Nodes with a reason, never a blank; an Eligible, free slot that no pending job needs carries the reason code `FREE` (surplus capacity), distinct from the exclusion codes `M3_CORDONED`, `M4_RESERVED`, `VRAM_CLASS_INSUFFICIENT`, `NO_ELIGIBLE_NODE`, `CAPACITY_EXHAUSTED`.
**Outputs:** A status response and a board view.
**Testable condition:** A query for `JOB-0417` returns state, position or placement, the last 10 Decision Records with citations, and a `next_decision_at` instant; the board displays all 32 Nodes (33 GPU slots) and every idle slot carries a reason string.

#### FR-26: Record the lifecycle event log

**System Responsibility:** Make the night reconstructable after the fact, including the failures.
**Trigger:** Every transition; every Simulation Fault; every cordon and clearance.
**Inputs:** The full transition stream.
**Validation rules:** (a) the log is append-only and covers the whole run; (b) failures and cordons are recorded with the same rigour as successes; (c) a human cordon clearance is recorded as a distinct event type with an actor; (d) the log survives daemon restart (FR-9).
**Outputs:** A queryable, ordered event log.
**Testable condition:** Replaying the log for one simulated night reconstructs the identical state vector as the live run, and the mandatory edge case appears as exactly one `CORDON` event, one `FAIL` event, and one `CORDON_CLEARED` event after Ines acts.

#### FR-27: Notify the submitter and the administrator

**System Responsibility:** Ensure a user is never surprised by the fate of their work.
**Trigger:** Eviction, Preemption, Expiry, Checkpoint failure, cordon, resume.
**Inputs:** The Decision Record; the submitting principal; the administrator contact.
**Validation rules:** (a) every notification names the job, the outcome, the last verified Checkpoint step, and the next eligible action; (b) delivery is delegated; this module produces the payload, not the transport; (c) a failed delivery is retried and recorded, and never blocks the state transition that triggered it.
**Outputs:** A notification payload per triggering event, with delivery status.
**Testable condition:** An Eviction produces exactly one notification to the submitter and none to the administrator; a Checkpoint failure produces exactly one to each; a failed delivery does not delay the node release by more than 0 ms and is recorded as `DELIVERY_FAILED`.

### 8.7 Feature G — Simulation Control

**Description:** The Annex requires a standalone simulator with fast-forward time controls. Realizes UJ-2 and supports FR-11.

#### FR-28: Control simulated time

**System Responsibility:** Make a 24-hour night inspectable in 60 seconds without changing any decision.
**Trigger:** Operator control on the board, or a `PATCH /simulations/{id}/rate` request. There is no separate CLI in v1; every control is reachable from the board or the API.
**Inputs:** Target rate, pause, step, jump-to-instant.
**Validation rules:** (a) supported rates are 1×, 60×, 360×, and 1440×, plus pause; (b) a rate change alters pacing only; (c) jumping to an instant drains all transitions at or before it before rendering.
**Outputs:** Rate changes; a rendered timeline.
**Testable condition:** 24 simulated hours at 1440× complete in **≤ 75 s**, including the scheduling work for 200 jobs, and produce a Decision Record log byte-identical to the same seed run at 1× (F-20).

#### FR-29: Inject Simulation Faults deterministically

**System Responsibility:** Make the failure paths demonstrable and repeatable without hardware.
**Trigger:** A fault schedule attached to a run, or an operator trigger.
**Inputs:** Fault kind; target Node or job; Simulated Clock instant; seed.
**Validation rules:** (a) the five kinds are node fault, Checkpoint write failure, Checkpoint corruption, daemon crash, and **training process exit (`PROCESS_EXIT`, incl. `OOM_KILLED`)** — the last exercising T-22 and T-23 (F-10); an `OOM_KILLED` exit additionally emits a cited Decision Record suggesting a lower batch size or a 48 GB-class Node (`server-gpu-01`); (b) a fault fires at its scheduled Simulated Clock instant regardless of the current rate; (c) the same seed and schedule produce the same faults at the same instants; (d) the active fault schedule is recorded in the run manifest.
**Outputs:** A deterministic fault trace; a run manifest.
**Testable condition:** Scheduling a Checkpoint write failure at 05:46:00 on `ws-gpu-19` produces FR-23's full consequence set at 1×, 60×, and 1440× identically.

#### FR-30: Run a scripted headless simulation through the API

**System responsibility:** Make the module testable in CI, which is how the Annex's "independently testable" requirement is met, without introducing a second invocation surface.
**Trigger:** `POST /simulations` carrying a complete run specification. There is no separate CLI in v1.
**Inputs:** `seed`; `submission_stream`; `fault_schedule`; simulated `duration`; `operator_action_schedule` (optional — an ordered list of timed operator actions, e.g. `CLEAR_CORDON ws-gpu-19 at 2026-09-28T08:05:00-05:00` applied by a `LAB_ADMIN` fixture, F-25).
**Validation rules:** (a) `seed`, `submission_stream`, `fault_schedule`, and simulated `duration` must be present, or the request is rejected with HTTP 400 and no run is created; `operator_action_schedule` is optional and, when present, is executed in Simulated Clock order against the in-process Module 3 stub (NFR-16, F-25); (b) the run executes non-interactively and writes a run manifest, the Decision Record log, and the event log; (c) the run's status is `RUNNING` and then exactly one of `PASSED` or `FAILED` — it never terminates in any other state; (d) the status is `FAILED` if any invariant in §4 (S-1 … S-3) or any of NFR-4, NFR-5, NFR-6, NFR-7, NFR-10, NFR-14, or NFR-16 is violated, and the response names **each** violated invariant (F-36); NFR-1 and NFR-11 are **build-time static checks**, not run-gated; and the latency NFRs (NFR-2, NFR-3, NFR-8, NFR-9) are measured by a separate benchmark harness rather than by a run verdict, because a CI run without real time discipline cannot meaningfully assert wall-clock latency (F-36); (e) the run requires no network reachability beyond the local host and no physical GPU.
**Outputs:** A run identifier and HTTP 202; a terminal run status retrievable via `GET /simulations/{id}`; the manifest, Decision Record log, and event log retrievable via `GET /simulations/{id}/artifacts`.
**Testable condition:** A `POST /simulations` with a fault schedule exercising T-10 returns HTTP 202, and the subsequent `GET /simulations/{id}` reports `PASSED` with every invariant holding; the same run with an injected citation-less denial asserts **fail-closed** (F-24): the emitter refuses the record, the job stays in its prior state, an `EMITTER_REJECTED` integrity event is logged, and the run is `PASSED` — the refusal is the correct behaviour, not a failure. A run whose `operator_action_schedule` clears the `ws-gpu-19` cordon at 08:05 via the `LAB_ADMIN` fixture places jobs on that node the following night (F-25). A `POST /simulations` missing `fault_schedule` returns HTTP 400 and creates no run.

### 8.8 Feature H — Endpoint Authentication and Roles

**Description:** Every API endpoint requires a bearer token validated against the Module 1 identity fixture, and every endpoint enforces the role that may call it. No anonymous request reaches a scheduling decision (F-40).

#### FR-31: Authenticate and authorise every endpoint

**System responsibility:** Make role boundaries enforceable at the API surface, so a student cannot clear a cordon and only the lab administrator can operate the simulator.
**Trigger:** Every API request.
**Inputs:** Bearer token; the endpoint identity; the Module 1 role fixture.
**Validation rules:** (a) every endpoint in FR-1, FR-5, FR-25, FR-28, FR-29, and FR-30 requires a bearer token validated against the Module 1 identity fixture; (b) `STUDENT` may submit jobs (FR-1) and read their own jobs (FR-25); (c) `LAB_ADMIN` may additionally issue priority grants (FR-17), clear cordons (FR-23, FR-30's `operator_action_schedule`), and control the simulation (FR-28, FR-29, FR-30); (d) an unauthenticated request returns HTTP 401 with no partial work performed; (e) an authenticated request with the wrong role returns HTTP 404 with a byte-identical body for every authorisation failure, so the response never discloses whether a job or route exists, and the refusal is recorded as an authorisation LifecycleEvent carrying the actor, route and time — never a silent no-op (amended from 403 by team decision, architecture adversarial review F-4/F-5); (f) no token, key, or credential is ever written to a log line, stack trace, or Decision Record (NFR-11).
**Outputs:** HTTP 200/201 on success, HTTP 401 unauthenticated, or HTTP 404 with a byte-identical body for every authorisation failure (never disclosing whether the job or route exists), recorded as an authorisation LifecycleEvent with the actor — team decision from the architecture adversarial review F-4/F-5.
**Testable condition:** A cordon-clear call (as exercised by FR-30's `operator_action_schedule`) with no token returns 401; with a `STUDENT` token returns 404 and the cordon is unchanged; with a `LAB_ADMIN` token succeeds and the node returns to the Eligible Node set. Submitting a job with a `LAB_ADMIN` token succeeds. No credential string appears in any asserted log line or Decision Record.

---

## 9. Non-Functional Requirements

*Cross-cutting. Every value is a number with a stated tolerance. No elastic words — "efficiently", "appropriately", "securely", "scalable", "robust" are prohibited in this section and their appearance is a defect.*

- **NFR-1 — Single time authority.** No component outside the Daemon Clock module reads wall-clock or process time. Test: static analysis of all source modules finds exactly one time-reading call site class. Violation is a build failure.
- **NFR-2 — Admission Order latency.** Computing the Admission Order and all placements for a 31-Node (33-slot) fleet with 500 pending jobs completes in **≤ 200 ms at p95** over 1000 consecutive runs. Tolerance: p99 ≤ 500 ms. This budget **excludes Checkpoint digest hashing**, which is no longer part of activation — hashing moved to the 21:30 pre-verification phase (§7.5, F-16) and has its own budget in NFR-8.
- **NFR-3 — Decision latency.** Per-job eligibility and priority evaluation completes in **≤ 50 ms at p95**. Tolerance: p99 ≤ 150 ms.
- **NFR-4 — Citation completeness.** **100%** of Decision Records carry ≥ 1 citation, and **100%** of `DENY` records based on a **delegated verdict**, and **100%** of `PREEMPT` and `EVICT` records, carry ≥ 1 non-`self:` citation. A `DENY` based on a module-owned rule (scope boundary, Max Night Span, queue cap, Job Spec validation) and an `EXPIRE` on a Retention Deadline may cite `self:` alone (F-1, §6.4). Tolerance: zero, absolute, no sampling. A single violation fails the build.
- **NFR-5 — Eviction timing accuracy.** SIGTERM dispatch lands within **± 2 simulated seconds** of Simulated Clock 05:45:00 and SIGKILL within **± 2 simulated seconds** of 05:53:00, at every Fast-Forward rate. Tolerance: absolute (F-21).
- **NFR-6 — Event fidelity under Fast-Forward.** Across a 24-hour run at 1440×, the number of fired transitions equals the analytic expectation for the seed's fault schedule, with **0 dropped and 0 duplicated** events. The **oracle (F-26)** is golden scenario fixtures: each of the 4 Annex scenarios and the mandatory edge case ships its expected ordered transition list and expected transition count, and the run must match exactly.
- **NFR-7 — Determinism.** Two runs with identical `(seed, submission_stream, fault_schedule)` produce **byte-identical** Decision Record logs. Tolerance: zero divergence. Test (F-22): a 24-hour run at 1440× versus the same run at 60× (24 minutes of real time); **plus** a 1× versus 1440× run over a 30-minute simulated slice from 05:30:00 to 06:00:00 covering the Eviction Ramp in fine detail. Both comparisons must be byte-identical.
- **NFR-8 — Checkpoint digest verification.** Recomputing and comparing the SHA-256 of a 200 MB Checkpoint completes in **≤ 1.5 s at p95** on the simulated NVMe class. Tolerance: p99 ≤ 4 s. The **pre-verification phase budget (F-16)** is absolute: every resume in the fleet — worst case all 33 GPU slots — is fully verified by 21:59:00 (29 minutes of simulated time) at every Fast-Forward rate; a single late or unverified resume fails the build.
- **NFR-9 — State visibility latency.** A committed state transition is visible on the status surface in **≤ 500 ms of real time at every Fast-Forward rate** (1×, 60×, 360×, 1440×). Tolerance: absolute, measured per rate (F-21).
- **NFR-10 — Crash recovery.** An abrupt daemon kill at any instant loses **0 committed transitions** and produces **0 duplicate transitions** on restart. Tested by killing at **1000 instants per run, derived deterministically from the run's seed** so the same seed repeats the same kills (F-27); tolerance: zero failures.
- **NFR-11 — Secret hygiene.** Zero authentication tokens, API keys, bearer credentials, or personal names beyond the persona display fixtures in §2 appear in any log line, Decision Record, stack trace, or API response body. Display names are resolved by the UI from the Module 1 identity fixture; the actual name is never stored in a log line or Decision Record (§6.1, F-32). Verified by fixture scan on every build; a single hit fails the build.
- **NFR-12 — Test coverage of the mandated paths.** **4 of 4** Annex mandatory scenarios and **1 of 1** mandatory edge case have an executable end-to-end test that asserts on state transitions, Decision Record citations, and Node allocation counts. Every FR has at least one automated test. Tolerance: zero uncovered FRs.
- **NFR-13 — Checkpoint store bound.** When Checkpoint store usage exceeds `CHECKPOINT_STORE_BUDGET`: (1) new submissions are refused with a `self:CHECKPOINT-STORE-BUDGET-v1` Decision Record that cites the reason; (2) an escalation Decision Record is emitted within **1 simulated minute**; (3) **no protected Checkpoint is deleted** — where protected means one of the 2 most recent verified Checkpoints of a non-terminal job (FR-22(b)) or any Quarantined Checkpoint. Test: driving the store 1 GB over budget yields the refusal, the escalation within 1 simulated minute, and zero protected deletions at every minute the budget is exceeded. A single protected deletion or a missed escalation instant fails the build.
- **NFR-14 — Invariant S-1.** At any Simulated Clock instant ≥ 06:00:00 and < 22:00:00, the number of Node allocations held by this module is exactly 0. Tested at every simulated minute across a 30-night run; a single violation fails the build.
- **NFR-15 — Accessibility.** The status board meets WCAG 2.1 AA: 4.5:1 text contrast minimum, full keyboard operability of the Admission Order view, and a non-colour encoding for every state (each of the nine states carries a distinct glyph and text label, so the board is readable without colour discrimination). This constrains Phase 2 and is stated here so the UX work inherits it.
- **NFR-16 — Independent executability.** The module starts and completes a full simulated night with `docker compose up` in a clean container, or in a clean local virtual environment with no other services running. It depends on **seed fixtures and simulated GPU telemetry only**: no physical GPU, no NVIDIA driver or CUDA runtime, no Kubernetes or Slurm cluster, and **no network reachability to any other module** in the Annex. Every delegated authority in §5 is satisfied by a local fixture or an in-process stub that can be driven to any verdict, including failure. Test: with networking to all other services blocked and no GPU present, the module starts, admits jobs, runs a full Night Window, executes the Eviction Ramp, and returns `PASSED` from `POST /simulations` per FR-30. Violation is a build failure. This is course constraint 1 ("Independent Executability") and constraint 2 ("Hardware Agnosticism") expressed as a testable requirement.

---

## 10. Constraints and Guardrails

### 10.1 The hard temporal constraint

Training Jobs execute only inside the Night Window. There is no student-facing exception path, by design: a self-service override is a self-service fairness hole. The only exception is an emergency compute freeze, and that belongs to Module 2 — this module **consumes** the freeze state and admits zero jobs while it is set (FR-6).

The 06:00 boundary is not arbitrary. It protects a human who walks into a lab at 08:00. The interval between the end of the Eviction Ramp (05:53:00) and 08:00 is **2 hours 7 minutes**, and it is deliberate headroom for the drain pattern that Module 4's reservation workflow assumes `[ASSUMPTION: A-1]`.

### 10.2 Timezone and the absence of daylight saving — Decision D-1

**The timezone is a team decision, not a sourced fact.** The Annex and the task statement name no campus location; no finding in this PRD is about the timezone. This PRD records **decision D-1**: the campus runs on **America/Bogota (UTC−05:00), which observes no daylight saving**, chosen because the deployment context is a Colombian university (the course institution) and this timezone removes DST risk entirely. Because there is no daylight saving, the Night Window is exactly 8 hours on every date of the year, and FR-19's wall-clock constants — SIGTERM at 05:45:00, SIGKILL at 05:53:00 — are correct year-round. Wall-clock anchoring, chosen over elapsed-time anchoring, is consequently **correct for this deployment by decision** (F-31): a lab technician can verify the deadline against a wall clock, and no date in the deployment's lifetime mis-evicts.

This is a decision, not a portability guarantee. A campus in a timezone that observes daylight saving would see a 7-hour Night Window on a spring-forward date; the Eviction Ramp would still fire at 05:45:00 and 05:53:00 wall clock, and that night's usable training time would silently drop by one hour. Making the module safe under such a deployment — offsetting the Ramp from window open instead of from wall clock, or asserting the 8-hour invariant at activation and refusing to schedule a 7-hour night — is a **v2 portability concern, deliberately out of scope for v1**. It is documented here so that a future deployment outside Bogotá inherits the hazard knowingly rather than discovering it in production. The residual assumption is narrower: that v1 is never deployed to a DST-observing timezone `[ASSUMPTION: A-2]`.

### 10.3 Safety

- **Never destroy recoverable work.** No automatic deletion of the 2 most recent verified Checkpoints of a non-terminal job, or of any Quarantined Checkpoint (FR-22).
- **Never leave a GPU held.** NFR-14 is absolute.
- **Never evict onto a suspect Node.** After a Checkpoint write failure, the Node is cordoned and the job is not retried on it (FR-23).
- **Never admit a job that cannot be placed.** FR-2 and FR-4.

### 10.4 Fairness and governance

- Priority is administered, never self-allocated (FR-17).
- Aging guarantees a floor on access without authorising Preemption (FR-15, FR-16) — a starvation fix that does not destroy thesis progress.
- Every administrative act carries an actor and, for `URGENT`, a reason code.

### 10.5 Cost and resource bound

- Checkpoint store is bounded and self-correcting (NFR-13).
- The Pending Set is bounded (FR-7).
- Node hours are the scarce institutional resource; SM-C1 and SM-C3 in §13 exist to stop this module being optimised in ways that waste them.

---

## 11. Non-Goals (Explicit)

- **Not a general-purpose batch scheduler.** It schedules GPU Training Jobs inside one Night Window. It does not schedule CPU jobs, notebooks, inference, or interactive work.
- **Not a policy engine.** It consumes Module 2's verdicts. It contains no policy rules of its own, and it will never emit an ALLOW it did not receive.
- **Not an identity, quota, or entitlement authority.** Modules 1 and 8.
- **Not a node health monitor.** It does not detect hardware faults; it consumes Module 3's health state and requests cordons.
- **Not a reservation system.** It excludes Module 4's reservations; it does not create them.
- **Not a distributed training planner.** Module 10. FR-3 refuses those jobs at the edge.
- **Not a dashboard product.** Module 11 consumes this module's events.
- **Not a natural-language diagnosis tool.** Module 12.
- **Not a training framework, a container runtime, or a GPU driver.** It orchestrates simulated training processes.
- **Not multi-tenant.** The university is the sole tenant. There is no cross-institution isolation problem to solve, and pretending otherwise would be padding.

---

## 12. MVP Scope

### 12.1 In Scope

- Submission, Job Spec validation, idempotency, and Pending Set bounding (FR-1 … FR-7).
- Window Activation, Window Reconciliation, Daemon Clock authority, and non-quantizing Fast-Forward (FR-8 … FR-11).
- Eligible Node computation and deterministic Node selection (FR-12, FR-13).
- Effective Priority, Starvation Promotion, gated Preemption, and priority grant administration (FR-14 … FR-17).
- Durable Checkpoint capture, the Eviction Ramp, integrity verification, resume, lifecycle governance, and the mandatory Checkpoint-failure edge case (FR-18 … FR-23).
- The §6 Explainability Contract, the status board surface, the event log, and notifications (FR-24 … FR-27).
- Deterministic simulation control, fault injection, API-triggered headless runs, and endpoint authentication roles (FR-28 … FR-31).
- The nine-state job machine in §4, including Max Night Span bounding (Invariant S-3).
- All 32 simulated Nodes (33 GPU slots) and the five simulated Simulation Fault kinds.
- Independent executability via `docker compose up` or a clean local virtual environment, on seed fixtures and simulated telemetry, with no physical GPU and no network dependency on any other module (NFR-16).

### 12.2 Out of Scope for MVP

- **Automatic aging-constant calibration** against real submission volume. The constants ship as configured values; calibration needs production telemetry the prototype cannot produce. Deferred to v2. `[NOTE FOR PM: if the readiness gate flags the constants as unevidenced, a sensitivity analysis over a synthetic 90-night load is the cheapest defensible substitute — it is a reporting exercise, not a code change.]`
- **Interactive-inference reservation of the fleet.** Whether training should be capped below 31 nodes to leave capacity for Module 7's serving is a genuine institutional tension this module does not own. Deferred, see §15 Open Question 8 `[ASSUMPTION: A-14]`. `[NOTE FOR PM: this is the most likely source of a readiness-gate objection, because the tension is real and the PRD currently answers it with an assumption rather than a decision.]`
- **Multi-hour partial-night admission policy.** Every admitted job currently gets the full window or a clean eviction. A policy for deliberately admitting a job that can only use the last 90 minutes is deferred to v2.
- **DST-aware elapsed-time anchoring for non-Bogotá deployments.** §10.2 decision D-1 sets America/Bogota (no daylight saving), so wall-clock anchoring is correct for this deployment and no date mis-evicts. Portability to a DST-observing timezone — where a spring-forward inside the Night Window yields a 7-hour night — is a v2 concern.
- **Checkpoint compression or offload to shared storage.** Checkpoints stay on the Node's local SSD.
- **Per-submitter fairness quotas.** Fairness is expressed through priority and aging only. A student who submits 40 jobs is not penalised in v1. `[NOTE FOR PM: a single flooding submitter can consume the whole night under Starvation Promotion. This is a known, accepted, and unmitigated hole. Flagging it rather than hiding it.]`
- **Live Kubernetes integration.** All scheduling is simulated; the module emits the same decisions a Kueue or Slurm integration would need, but performs no cluster calls.

---

## 13. Success Metrics

**Primary**

- **SM-1 — Mandated-path fidelity.** 4 of 4 Annex mandatory scenarios and 1 of 1 mandatory edge case execute end-to-end with asserted state transitions, citations, and Node allocation counts. Target: 100%. Validates FR-1, FR-8, FR-16, FR-19, FR-23, NFR-12.
- **SM-2 — Dawn guarantee.** Across a 30-night simulated month, the number of Simulated Clock instants in the forbidden interval where a Node allocation is held is exactly 0. Target: 0. Validates NFR-14, FR-19, Invariant S-1.
- **SM-3 — Night utilisation.** Mean occupancy of Eligible **GPU slots** (33 in total) across the Eviction-Free portion of the Night Window (22:00:00–05:45:00) is ≥ 85% over 30 simulated nights, measured against slots on Nodes that were Eligible for at least 90% of the window (F-42). Target: ≥ 85%. Validates FR-8, FR-12, FR-13.
- **SM-4 — No starvation.** Maximum `Consecutive Nights Missed` observed across all jobs in a 30-night run is ≤ 4. Target: ≤ 4, which holds only if Starvation Promotion fires. Validates FR-14, FR-15.
- **SM-5 — Explainability.** 100% of decisions presented to a user in the Phase 2 experience carry a citation and a one-sentence summary that a reader can check against the delegated authority. Target: absolute. Validates FR-24, NFR-4.

**Secondary**

- **SM-6 — Work preservation.** Across a 30-night run, the number of steps lost per interruption is **≤ the steps produced in one Checkpoint interval** (FR-2(g) interval), measured on **every** eviction, preemption, and fault — **no exclusions** (F-19). Target: 100% of interruptions meet the bound, including T-17 and process exits. Validates FR-18, FR-20, FR-21.
- **SM-7 — Admission latency.** p95 Admission Order computation is ≤ 200 ms with 500 pending jobs. Validates NFR-2.
- **SM-8 — Simulation credibility.** A 24-hour run at 1440× completes in **≤ 75 s**, including scheduling work for 200 jobs, and yields a byte-identical Decision Record log to the 1× run (F-20). Validates FR-28, NFR-6, NFR-7.

**Counter-metrics (do not optimise)**

- **SM-C1 — Do not optimise raw job throughput.** Maximising jobs-run-per-night drives the scheduler toward admitting many small jobs, which starves exactly the thesis-scale work the module exists to protect. Track alongside SM-3, never instead of it. Counterbalances SM-3.
- **SM-C2 — Do not optimise Checkpoint frequency.** More frequent Checkpoints mean more disk, more garbage-collection churn, and a higher probability of hitting the mandatory edge case (FR-23). Track Checkpoint store pressure and edge-case frequency; a rise in throughput bought by doubling Checkpoint frequency is a regression. Counterbalances SM-6.
- **SM-C3 — Do not optimise Preemption count.** Every Preemption costs a victim a full stop, Checkpoint write, and restart, and a restarted job re-does warmup. A high Preemption count is a sign the Preemption Margin in FR-16 is mistuned, not that the system is performing. Track **wasted GPU-minutes per preempted job**; the target is that this metric falls, not that preemptions rise. Counterbalances SM-4.
- **SM-C4 — Do not optimise explanation length.** A longer `summary` is not a better one. NFR caps it at 200 characters. Counterbalances SM-5.

---

## 14. Scenario-to-Requirement Traceability

*Required by the grading rubric ("all 4 scenarios traced to FRs"). Note: the BMad PRD convention is to omit traceability matrices; the course rubric explicitly requires this one, so the rubric wins and the section is retained.*

| Annex scenario | State path | Primary FRs | Supporting FRs |
|---|---|---|---|
| **1. Daytime Submission & Queuing** — Kavita submits at 14:30, specs validated, parked in `QUEUED_PENDING_WINDOW` | — → `QUEUED_PENDING_WINDOW` | FR-1, FR-2, FR-4 | FR-3, FR-5, FR-6, FR-7, FR-24 |
| **2. Night Window Activation (22:00)** — clock strikes 22:00, queue scanned, nodes selected, jobs `RUNNING` | `QUEUED_PENDING_WINDOW` → `RUNNING` | FR-8, FR-12, FR-13 | FR-9, FR-10, FR-11, FR-14, FR-15, FR-24, FR-28, FR-29 |
| **3. Morning Hard Eviction (05:45)** — SIGTERM, Checkpoint saved, node freed | `RUNNING` → `CHECKPOINTING` → `EVICTED_RESUMABLE` | FR-18, FR-19 | FR-21, FR-22, FR-24, FR-26, FR-27, NFR-5 |
| **4. Priority Queue Preemption** — high-priority thesis submission preempts a low-priority exploration job | `RUNNING` → `CHECKPOINTING` → `EVICTED_RESUMABLE`; challenger `QUEUED_PENDING_WINDOW` → `RUNNING` | FR-16, FR-17 | FR-14, FR-15, FR-18, FR-21, FR-24, FR-26, FR-27 |
| **Mandatory edge case. Checkpointing failure during morning eviction** — cordon the Node, notify the user, release GPU allocations | `CHECKPOINTING` → `EVICTION_FAILED` | FR-23 | FR-18, FR-19, FR-20, FR-24, FR-26, FR-27, NFR-13 |
| *(Annex-implied) Resume on a subsequent night* | `EVICTED_RESUMABLE` → `QUEUED_PENDING_WINDOW` → `RUNNING` | FR-20, FR-21 | FR-22, FR-4 |
| *(Annex-implied) Operator clears the cordon, job recovers* | `EVICTION_FAILED` → `QUEUED_PENDING_WINDOW` → `RUNNING` (T-20; placement on **any** Eligible Node) | FR-23, FR-20 | FR-21, FR-26, FR-27, FR-12 |
| *(Derived guard) Max Night Span exhausted* | `QUEUED_PENDING_WINDOW` → `FAILED` (`MAX_NIGHT_SPAN_EXCEEDED`) | FR-4 | FR-2(j), FR-21, Invariant S-3 |

**Uncovered-by-scenario FRs:** FR-25 (status board), FR-30 (headless runs), and FR-31 (endpoint authentication) are cross-cutting surfaces, not scenario behaviours; all three are exercised by NFR-12's per-FR test requirement, FR-30 additionally by NFR-16's standalone-executability path, and FR-31 by every API-level test. Every other FR appears in at least one scenario or derived-guard row above.

---

## 15. Open Questions

*Items still unknown. Questions that were asked and then answered are retained in place with their resolution, so the audit trail shows what was uncertain at the time of drafting — they are not silently deleted.*

1. **Aging constants need calibration.** `AGING_RATE = 6` and `AGING_CAP = 30` are reasoned defaults, not measured. They interact with real submission volume in a way this prototype cannot observe. Cheapest resolution: a sensitivity analysis across a synthetic 90-night load, reported in Phase 4.
2. ~~**What is the campus timezone, and does DST fall inside the Night Window?**~~ **RESOLVED as decision D-1.** The sources name no campus location, so the timezone is a team decision, not a finding (F-31). **Decision D-1** sets **America/Bogota (UTC−05:00)**, which observes no daylight saving, so the Night Window is exactly 8 hours year-round, wall-clock anchoring is correct for this deployment, and FR-19's fixed 05:45:00 / 05:53:00 constants are correct on every date. Portability to a DST-observing timezone is a v2 concern documented in §10.2 and §12.2. No open question remains.
3. **Is the 2 h 07 min between the end of the Eviction Ramp (05:53:00) and an 08:00 lab session sufficient** for Module 4's reservation drain pattern, or should the deadline be moved earlier?
4. **Who owns per-student Checkpoint disk?** Module 8 owns token quota; nobody in the Annex owns Checkpoint bytes. A single student's 40-night run could consume the store.
5. **Is an Urgent Grant scoped per job or per submitter per window?** Per-job permits 30 Urgent Grants in one night; per-window does not. FR-17 currently permits both.
6. **Is a singleton daemon acceptable, or is leader election required?** A single-instance prototype is simpler; a real 32-Node deployment has one daemon, so a crash is a total outage for the night. FR-9 and FR-10 mitigate but do not eliminate this.
7. ~~**What happens to a queued job whose model is deprecated by Module 5 while it waits?**~~ **CLOSED (F-6).** FR-6(d) re-checks the Module 5 model record at every Window Activation: a deprecated model fails the job with reason `MODEL_DEPRECATED` and a `catalog:M5/<model-id>@<version>` citation, so it is never admitted only to fail on first use.
8. **Should training be capped below 31 Nodes to leave capacity for Module 7's inference serving?** This module currently assumes all Eligible Nodes are available to training `[ASSUMPTION: A-14]`. The tension is real and the answer is institutional, not technical.
9. ~~**Do the `spec.md` and `project-brief.md` named as Phase 1 inputs exist?**~~ **CLOSED.** They were not provided and are not in this repository. The two source PDFs are the sole inputs to this PRD. No requirement is inferred from an unavailable document, and no scope in §4, §8, or §12 depends on one. Nothing in this PRD is blocked on them.
10. **Is a job that was `RUNNING` when the window opened but whose node faulted mid-night eligible for automatic re-placement on another Node?** T-16 currently re-queues it but does not re-admit it until the next window. Immediate re-placement would improve SM-3 but could interact badly with Cordon Requests.
11. **Who may authorise an extension past Max Night Span, and on what evidence?** A job legitimately needing more than 38.75 admitted hours is refused at submission by FR-2(j) with a suggested scope reduction, and a job that overruns is refused admission and failed by FR-4(d). Both behaviours are correct for v1, but a real thesis will eventually hit the ceiling, and the escape hatch is currently unspecified — the lab administrator has no defined mechanism to grant a 6th or 7th night. This is a deliberate v1 gap, not an oversight; it needs a decision before the module meets a real thesis deadline.

---

## 16. Assumptions Index

*Every `[ASSUMPTION]` in the document, surfaced for explicit confirmation. Each is a genuine unknown, not a decision I made on your behalf.*

- **A-1 (§10.1)** — The 2 h 07 min between 05:53:00 and 08:00 is intentional headroom for Module 4's drain pattern, not slack. Confirm against Module 4's expectations. See Open Question 3.
- **A-2 (§10.2)** — Residual under decision D-1: v1 is never deployed to a DST-observing timezone. If that changes, §10.2's v2 portability note becomes immediately load-bearing.
- **A-3 (§5)** — The prototype performs **no real training and touches no real GPU**. Every Training Job is a simulated process. This must be stated in the Phase 2 and Phase 3 artifacts too.
- **A-4 (§3, §4)** — Node identifiers are `ws-gpu-01`…`ws-gpu-31` and `server-gpu-01`, following the Annex's own naming. Fixed so FRs, UJs, and Phase 2/3 artifacts reference them without translation.
- **A-5 (§7.1, NFR-1)** — The campus host clock is NTP-disciplined to within 1 s. If it is not, drift detection becomes a load-bearing feature rather than a guard.
- **A-6 (§8.4, FR-14)** — `AGING_RATE = 6` and `AGING_CAP = 30` are uncalibrated defaults. See Open Question 1.
- **A-7 (§8.4, FR-15)** — `STARVATION_NIGHTS = 3` and `STARVATION_PROMOTION_LIMIT = 4` are uncalibrated defaults. The promotion cap in particular is a guess at how much of a night starvation recovery may consume.
- **A-8 (§8.4, FR-16)** — `Preemption Margin = 20` is uncalibrated. It is currently wide enough that aging alone can never authorise Preemption, which is the intended governance property, but the specific value is a guess.
- **A-9 (§8.5, FR-19)** — The 8-minute Eviction Ramp with a 300 s Checkpoint Budget (and the 05:53:00 hard SIGKILL) is sized against a 50–200 MB adapter Checkpoint plus NVMe `fsync` latency, with margin for a ~7 GB optimizer-state Checkpoint. The real fleet's disk class is unknown; a spinning-disk Node would invalidate the sizing.
- **A-10 (§8.5, FR-22)** — `CHECKPOINT_STORE_BUDGET` defaults to 20 GB, sized from the formula Σ over non-terminal jobs (2 × checkpoint size) (F-18). No institution-wide figure exists in the sources.
- **A-11 (§8.1, FR-4)** — Job duration estimates are trusted from the Job Spec when declared. A student may understate duration to win admission; no cross-checking against a derived estimate is performed in v1. This is a gaming vector and is not mitigated.
- **A-12 (§8.1, FR-4)** — `Max Night Span = 5` Night Windows (38.75 h usable, 5 × 7 h 45 min) is a policy ceiling, not a measured optimum. It bounds how much of the fleet's most contended resource one job may consume across nights, and it means a legitimate thesis run needing more than 38.75 admitted hours must be reduced in scope or seek an explicit extension. No institutional figure for this ceiling exists in the sources; 5 was chosen as the smallest span that comfortably contains the 31-hour example in UJ-1 while still capping a single job's claim. The extension path is deliberately not specified in v1 — see Open Question 11.
- **A-13 (§8.4, FR-17)** — An Urgent Grant is scoped per job, not per submitter per window. See Open Question 5.
- **A-14 (§10.2, §12.2)** — Training may use all Eligible Nodes; no capacity is reserved for Module 7's inference serving in v1. See Open Question 8.
- **A-15 (§5, §8.5, FR-23)** — A Cordon Request to Module 3 is asynchronous. This module treats the Node as not Eligible immediately and optimistically, without waiting for Module 3's acknowledgement.
- **A-16 (§5, §8.1, FR-6)** — Module 2's emergency freeze is consumed as a state, never computed here.
- **A-17 (§7.3)** — Simulated duration models are calibrated against published LoRA/QLoRA figures, not against this institution's hardware. A production deployment must re-calibrate.
- **A-18 (§3, §4)** — The 9-state machine is complete for v1. If Phase 2 surfaces a UX state that cannot be expressed, the machine grows and this PRD is amended rather than the UX inventing a state.
- **A-19 (§8.2, FR-8)** — No GPU slot receives more than one Training Job per Night Window (one job per slot; `server-gpu-01` has two slots) (F-42).
- **A-20 (§8.1, FR-7)** — `QUEUE_DEPTH_CAP = 500`. No institutional figure exists in the sources; 500 is a deliberate generous bound on a Pending Set that the 33-slot fleet drains every night.
- **A-21 (§8.5, FR-22)** — `CHECKPOINT_RETENTION_COUNT = 2`, plus the 7-day expiry grace for `EXPIRED` jobs (F-2, F-3). Sized against the store formula in A-10.
- **A-22 (§3, FR-7(b))** — `JOB_TTL = 14 days` from submission, extended by 14 days from each admitted night. Chosen as ≥ 4× the 3-night Starvation Promotion threshold so expiry never pre-empts the anti-starvation guarantee. Team decision closing UX question S1-Q7; uncalibrated.

---

*End of PRD. Depth on real-world mechanisms, measured figures, and rejected alternatives: `prd-addendum.md`. Run artifacts: `_bmad-output/planning-artifacts/prds/prd-module-9-night-training-scheduler-2026-09-27/`.*
