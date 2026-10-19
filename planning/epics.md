---
title: "Module 9 — Night Training Scheduler: Sprint Backlog (Epics & Stories)"
status: ready
version: "1.0.0"
created: 2026-10-18
authors:
  - "Juan Manuel Casanova Marín (Architect-Lead)"
  - "Juliana Filigrana Valencia (Reviewer & Test Lead)"
module: "Module 9 — Night Training Scheduler"
readiness_gate: "PASS"
---

# Sprint Backlog: Vertical Epics & Contract-Bound Stories

This backlog specifies 4 vertical slices delivering user-visible value for named protagonists (**Kavita**, Graduate Student Researcher, and **Dr. Chen**, Lab Administrator). Every story is bound to behavioral contracts, database schemas, architectural invariants, and executable ATDD tests with zero forward dependencies.

---

## Epic 1: The Walking Skeleton — End-to-End Single-Node Job Submission, Night Window Activation & Dawn Completion

**Protagonist:** Kavita (Student Researcher) submitting a lightweight training job that gets placed at 22:00:00, executes on a single workstation GPU, and completes before dawn.

### Story 1.1: Job Submission Ingress & Validation Skeleton
- **User Story:** As Kavita, I want to submit a single-node training job specification through the HTTP API with an idempotency token, so that my job is validated and queued for the upcoming night window without risk of duplicate execution.
- **Traceability:** PRD `FR-1`, `FR-2`, `FR-5`; UX Scenario 1 (`NP-1.1`); `NFR-3` ($< 50$ ms p95).
- **Binding Invariants:** `AD-1` (queue integrity), `AD-4` (single-node boundary), `INV-01` (queue cap).
- **Files Touched:** `api/routes/jobs.py`, `ports/in/job_submission.py`, `domain/engine.py`, `adapters/db/sqlite_repository.py`.
- **Schema & DTOs:** `JobSubmissionRequestDTO`, `JobSubmissionResponseDTO`, `JobSpecDTO`, `001_night_training_scheduler_schema.sql` (`jobs` table).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestSubmitJobContract::test_submit_job_happy_path_admits_and_persists_pending_job`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** an authenticated student actor `student-kavita` and a valid single-node `JobSpecDTO` requesting 1 GPU (24 GB)
    - **When** the student posts to `/api/v1/jobs` with idempotency key `idemp-key-happy-001`
    - **Then** the response status is `201 Created` returning `JOB-0001` in state `QUEUED_PENDING_WINDOW` and exactly one row is committed in `jobs`.
  - *Failure Path (Idempotency Conflict):*
    - **Given** an existing job registered under idempotency key `idemp-key-happy-001` with SHA-256 digest `digestA`
    - **When** a client posts a job with the same key `idemp-key-happy-001` but differing digest `digestB`
    - **Then** the response status is `409 Conflict` with error code `IDEMPOTENCY_CONFLICT` and zero rows are inserted.
- **Definition of Done (DoD):** DTO schemas validated, SQLite transaction commits `jobs` and `decision_records` atomically, ATDD test passes.

### Story 1.2: Single-Node Scope Boundary Enforcement
- **User Story:** As Dr. Chen, I want multi-worker distributed training specifications to be immediately rejected at submission, so that distributed workloads do not accidentally occupy single-node workstation slots.
- **Traceability:** PRD `FR-3(a)(b)`; UX Scenario 1 (`NP-1.2`); Course Constraint 1.
- **Binding Invariants:** `AD-4` (fleet scope), `INV-03`.
- **Files Touched:** `ports/in/job_submission.py`, `domain/engine.py`.
- **Schema & DTOs:** `JobSpecDTO` (`worker_count`, `replicas`, `distributed_artifact_present`), `ErrorBodyDTO`.
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestSubmitJobContract::test_submit_job_precondition_violation_distributed_spec_rejected_with_zero_state_mutation`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** a spec with `worker_count = 1` and `replicas = 1`
    - **When** submitted to `/api/v1/jobs`
    - **Then** validation passes to the queue evaluation stage.
  - *Failure Path (Distributed Rejection):*
    - **Given** a job spec with `worker_count = 4` or `nprocPerNode = auto`
    - **When** submitted to `/api/v1/jobs`
    - **Then** the response status is `400 Bad Request` with error code `OUT_OF_SCOPE_DISTRIBUTED` citing `self:SCOPE-BOUNDARY-v1` and zero database mutations occur (`Q-fail`).
- **Definition of Done (DoD):** Precondition check runs prior to database write, error response cites Module 10, zero orphaned state created.

### Story 1.3: Night Window Activation at 22:00:00 & Deterministic Allocation Fold
- **User Story:** As Kavita, I want the scheduler to activate at 22:00:00 and evaluate all queued jobs deterministically, placing my job onto an eligible workstation slot based on fair priority ranking.
- **Traceability:** PRD `FR-8`, `FR-12`, `FR-13`, `FR-14`, `FR-15`; UX Scenario 2; `NFR-2` ($< 200$ ms p95).
- **Binding Invariants:** `AD-1`, `AD-4` (deterministic total order), `INV-04`.
- **Files Touched:** `ports/in/window_activation.py`, `domain/ranking.py`, `domain/allocation.py`, `adapters/db/sqlite_repository.py`.
- **Schema & DTOs:** `WindowActivationRequestDTO`, `WindowActivationResultDTO`, `PlacementDTO`, `001_night_training_scheduler_schema.sql` (`gpu_slots`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestActivateWindowContract::test_activate_window_happy_path_places_jobs_deterministically`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** simulated time advances to `22:00:00-05:00` with 5 queued jobs and 31 healthy workstation slots
    - **When** `activateWindow` is executed
    - **Then** the jobs are sorted by Admission Order, placed into slots `ws-gpu-01..05`, their state becomes `RUNNING`, and one atomic transaction commits all placements.
  - *Failure Path (Activation Outside Window):*
    - **Given** simulated time is `14:00:00-05:00` (daytime)
    - **When** `activateWindow` is triggered
    - **Then** the response is `400 Bad Request` with error code `WINDOW_ACTIVATION_OUTSIDE_WINDOW` and zero placements occur.
- **Definition of Done (DoD):** Placement follows total order (prior node $\rightarrow$ lowest allocations held $\rightarrow$ node ID), commits in single SQLite transaction, ATDD test passes.

### Story 1.4: Dawn Completion & Slot Deallocation
- **User Story:** As Dr. Chen, I want a job that completes all training steps before 05:45:00 to release its GPU slot immediately, so that the workstation is clean and available.
- **Traceability:** PRD `FR-19`, `FR-25`; UX Scenario 3; `NFR-14` (Invariant S-1).
- **Binding Invariants:** `AD-1`, `AD-4`, `INV-02`.
- **Files Touched:** `domain/engine.py`, `domain/state_machine.py`, `adapters/db/sqlite_repository.py`.
- **Schema & DTOs:** `001_night_training_scheduler_schema.sql` (`jobs.state = 'COMPLETED'`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestEvictAtDeadlineContract::test_evict_at_deadline_happy_path_completes_checkpoint_and_releases_slots`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** job `JOB-0001` running on `ws-gpu-05` finishes its final step at `04:15:00`
    - **When** the completion event is processed
    - **Then** job state transitions to `COMPLETED` (`T-5`), `gpu_slots.allocated_job_id` is set to NULL, and a `COMPLETE` DecisionRecord is appended.
- **Definition of Done (DoD):** Slot cleared immediately, `allocations_held` decremented, completion event written to `audit_events`.

---

## Epic 2: Dawn Eviction Ramp, 5-Step Checkpoint Durability & Mandatory Edge Case Isolation

**Protagonist:** Dr. Chen (Lab Admin) ensuring campus lab machines are 100% free of student workloads by 06:00:00, and Kavita receiving resilient fault recovery.

### Story 2.1: Dawn Checkpoint Failure at 05:45:00–05:53:00, Node Cordoning & Unconditional Slot Release (Mandatory Edge Case)
- **User Story:** As Dr. Chen, I want any node whose checkpoint write fails during the dawn eviction ramp to be immediately cordoned and its GPU slot released, guaranteeing zero student GPU allocations by 06:00:00.
- **Traceability:** PRD `FR-19(c)(d)`, `FR-23(a)(b)`, PRD Annex Scenario 3; `NFR-14` (Invariant S-1).
- **Binding Invariants:** `AD-1`, `AD-4`, `AD-7`, `Invariant S-1`, `INV-02`, `INV-05`.
- **Files Touched:** `ports/in/eviction.py`, `domain/engine.py`, `adapters/sim/simulated_delegates.py`, `adapters/db/sqlite_repository.py`.
- **Schema & DTOs:** `EvictionRequestDTO`, `EvictionResultDTO`, `001_night_training_scheduler_schema.sql` (`cordon_requests`, `nodes.status = 'CORDONED'`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestEvictAtDeadlineContract::test_mandatory_edge_case_checkpoint_failure_at_dawn_cordons_node_releases_all_slots_at_0600`
- **Gherkin Scenarios:**
  - *Happy Path (Dawn Ramp with Verified Checkpoint):*
    - **Given** job `JOB-0002` running on `ws-gpu-10` at `05:45:00`
    - **When** `evictAtDeadline` executes and the 5-step checkpoint completes by `05:50:00`
    - **Then** job transitions to `EVICTED_RESUMABLE` (`T-8`), checkpoint is marked `VERIFIED`, and slot is released.
  - *Mandatory Edge Case (Failure at 05:53:00):*
    - **Given** job `JOB-EDGE-001` running on `ws-gpu-17` experiencing a disk write timeout at `05:53:00`
    - **When** `evictAtDeadline` watchdog triggers SIGKILL
    - **Then** job state transitions to `EVICTION_FAILED` (`T-9`), node `ws-gpu-17` status is updated to `CORDONED`, a `CordonRequest` row is committed, `ws-gpu-17` slot is set to NULL, and at `06:00:00` `allocations_held == 0` strictly holds.
- **Definition of Done (DoD):** Node cordoned locally and in M3 outbox, slot freed before 06:00:00, DecisionRecord cites `self:EVICTION-RAMP-v1`, ATDD test passes.

### Story 2.2: User Notification & Next-Night Rescheduling on Checkpoint Eviction Failure
- **User Story:** As Kavita, I want to receive a clear notification when my job's dawn checkpoint fails, informing me that the node was isolated and that my job is automatically queued for re-admission next night.
- **Traceability:** PRD `FR-23(h)`, `FR-27(a)(b)`, `T-20`; UX Scenario 3.
- **Binding Invariants:** `AD-1`, `AD-7`.
- **Files Touched:** `ports/out/notification_outbox.py`, `adapters/sim/in_memory_outbox.py`, `domain/engine.py`.
- **Schema & DTOs:** `001_night_training_scheduler_schema.sql` (`audit_events`), `events.md` (`JobEvictedPayload`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestEvictAtDeadlineContract::test_mandatory_edge_case_user_notified_and_job_rescheduled_after_dawn_checkpoint_failure`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** job `JOB-EDGE-001` enters `EVICTION_FAILED` at dawn
    - **When** eviction completes
    - **Then** an outbox notification is recorded for `student-kavita` explaining the failure and stating re-admission eligibility for the next window (`T-20`).
- **Definition of Done (DoD):** Notification payload in outbox contains last verified step, failure reason, and next eligible action without sensitive data leakage.

### Story 2.3: Corrupt Checkpoint Detection & Quarantine during Pre-Verification Sweep
- **User Story:** As Dr. Chen, I want checkpoints to be verified against their SHA-256 digests at 21:30:00 prior to window activation, so that corrupt files are quarantined and prevented from resuming.
- **Traceability:** PRD `FR-20(a)(b)`, `FR-21(a)`, `Invariant S-2`; `NFR-8`.
- **Binding Invariants:** `AD-7`, `Invariant S-2`, `INV-06`.
- **Files Touched:** `adapters/sim/filesystem_checkpoint_store.py`, `domain/engine.py`.
- **Schema & DTOs:** `001_night_training_scheduler_schema.sql` (`checkpoints.state = 'QUARANTINED'`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestEvictAtDeadlineContract::test_checkpoint_digest_mismatch_quarantines_file_and_fails_job`
- **Gherkin Scenarios:**
  - *Failure Path (Corrupt Digest):*
    - **Given** an evicted job with checkpoint file on disk whose content was altered (digest mismatch)
    - **When** the `21:30:00` pre-verification sweep runs
    - **Then** the checkpoint state is updated to `QUARANTINED`, job state transitions to `FAILED` with reason `CHECKPOINT_CORRUPT`, and zero cordon requests are issued against the hardware.
- **Definition of Done (DoD):** Corrupt file moved to quarantine, job marked `FAILED`, zero hardware cordons issued, `INV-06` enforced.

---

## Epic 3: Fleet Concurrency, 2-GPU Atomic Placement & System Invariant Protections

**Protagonist:** Dr. Chen (Lab Admin) maintaining cluster stability during heavy submission traffic and managing dual-GPU workloads.

### Story 3.1: Dual-GPU Job Atomic Spanning Placement on `server-gpu-01`
- **User Story:** As Kavita, I want to request 2 GPUs for large 48 GB models and have both slots of `server-gpu-01` allocated atomically, ensuring no partial or stranded allocation.
- **Traceability:** PRD `FR-2(k)`, `FR-12`, `FR-13`; UX Scenario 2; `AD-4`.
- **Binding Invariants:** `AD-4`, `INV-03`.
- **Files Touched:** `domain/allocation.py`, `domain/engine.py`, `adapters/db/sqlite_repository.py`.
- **Schema & DTOs:** `001_night_training_scheduler_schema.sql` (`check_two_gpu_requires_48gb`), `PlacementDTO`.
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestActivateWindowContract::test_activate_window_invariant_atomic_server_gpu_allocation`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** a 2-GPU job requesting 48 GB VRAM and `server-gpu-01` having both slots free
    - **When** window activation allocates slots
    - **Then** both `slot-srv-01-0` and `slot-srv-01-1` are assigned to the same job in one atomic database transaction.
  - *Failure Path (2-GPU Requested on 24GB):*
    - **Given** a submission spec requesting 2 GPUs and `required_vram_gb = 24`
    - **When** posted to `/api/v1/jobs`
    - **Then** request is rejected with `422 Unprocessable Entity` and error code `TWO_GPU_REQUIRES_48GB`.
- **Definition of Done (DoD):** Both slots allocated or zero slots allocated; SQL CHECK constraint enforces 48GB hardware rule.

### Story 3.2: Fleet Capacity Limit (33 Slots) & Deterministic Candidate Tie-Breaking
- **User Story:** As Dr. Chen, I want the scheduler to enforce the 33-slot hardware bound and resolve placement conflicts using deterministic tie-breaking (affinity $\rightarrow$ allocations held $\rightarrow$ node ID).
- **Traceability:** PRD `FR-8`, `FR-13`; `NFR-7` (Determinism).
- **Binding Invariants:** `AD-4`, `INV-02`.
- **Files Touched:** `domain/allocation.py`, `domain/ranking.py`.
- **Schema & DTOs:** `001_night_training_scheduler_schema.sql` (`nodes`, `gpu_slots`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestActivateWindowContract::test_activate_window_invariant_total_allocated_slots_never_exceeds_33`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** 40 eligible jobs competing for 33 GPU slots
    - **When** window activation runs
    - **Then** exactly 33 jobs are admitted to `RUNNING` and remaining 7 receive `T-4b CAPACITY_EXHAUSTED`.
- **Definition of Done (DoD):** Never more than 33 slots allocated; total order verified across identical runs with same seed.

### Story 3.3: Concurrency Burst Serialization & Global 500-Job Queue Cap Guard
- **User Story:** As Dr. Chen, I want the system to serialize rapid concurrent submissions and strictly reject submissions when active jobs reach 500, preventing out-of-memory crashes.
- **Traceability:** PRD `FR-1(a)`, `PRD §4.1`; `NFR-3`.
- **Binding Invariants:** `AD-1`, `INV-01`.
- **Files Touched:** `adapters/db/sqlite_repository.py`, `domain/engine.py`.
- **Schema & DTOs:** `001_night_training_scheduler_schema.sql` (`idx_active_jobs_state`), `ErrorBodyDTO`.
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestSubmitJobContract::test_submit_job_invariant_queue_cap_500_enforced_under_burst_submissions`
- **Gherkin Scenarios:**
  - *Failure Path (Queue Cap Exceeded):*
    - **Given** the database already contains 500 non-terminal jobs
    - **When** a 501st submission is received
    - **Then** the request is rejected with `429 Too Many Requests` and error code `QUEUE_CAP_EXCEEDED` without altering database count.
- **Definition of Done (DoD):** `BEGIN IMMEDIATE` transaction serializes count query and insert; partial index optimizes check.

### Story 3.4: Crash Recovery & State Reconciliation without Replay
- **User Story:** As Dr. Chen, I want the scheduler to recover from unexpected process crashes by folding the durable SQLite decision log up to the last committed ID, with zero duplicate transitions.
- **Traceability:** PRD `FR-9(a)–(e)`, `T-18`; `NFR-10`.
- **Binding Invariants:** `AD-2`, `AD-5`, `INV-04`.
- **Files Touched:** `adapters/db/sqlite_repository.py`, `domain/engine.py`.
- **Schema & DTOs:** `001_night_training_scheduler_schema.sql` (`decision_records`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestSubmitJobContract::test_submit_job_invariant_queue_cap_500_enforced_under_burst_submissions`
- **Gherkin Scenarios:**
  - *Happy Path (Crash Recovery):*
    - **Given** process terminated abruptly during a simulation run
    - **When** the daemon restarts
    - **Then** state is rebuilt by folding the decision log prefix with zero replay, and a `DEFER DAEMON_RESTORE` record is committed (`T-18`).
- **Definition of Done (DoD):** State vector byte-identical to pre-crash state, zero duplicate decision IDs created.

---

## Epic 4: Explainability Dashboard, Priority Preemption & Authorization Security

**Protagonist:** Kavita and Dr. Chen inspecting transparent decision citations, authorized preemption, and privacy boundaries.

### Story 4.1: Transparent Decision Records & Explanation DTO Citations on Status Board
- **User Story:** As Kavita, I want every decision made on my job (admission, placement, deferral, eviction) to display citations of specific rules and observed values on the status board.
- **Traceability:** PRD `FR-24`, `FR-25`; `NFR-4`; UX Scenario 1, 2, 3.
- **Binding Invariants:** `AD-3`, `INV-04`.
- **Files Touched:** `api/routes/board.py`, `domain/emitter.py`, `schemas/dto.py`.
- **Schema & DTOs:** `ExplanationDTO`, `001_night_training_scheduler_schema.sql` (`decision_records.citations`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestSubmitJobContract::test_submit_job_explainability_payload_cites_jobspec_validation_rule`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** a job admitted or deferred by the scheduler
    - **When** queried via `/api/v1/jobs/{job_id}` or viewed on `/board`
    - **Then** the response includes `citations` containing at least 1 non-empty rule ID (e.g. `policy:M2/night-window@v1`).
- **Definition of Done (DoD):** Decision records fail closed if citations are empty; UI renders citations and observed values.

### Story 4.2: Thesis Priority Preemption with Deterministic Victim Order
- **User Story:** As Dr. Chen, I want urgent or thesis jobs to preempt lower-priority exploratory jobs only when the priority margin is at least 20, guaranteeing fair deterministic victim selection.
- **Traceability:** PRD `FR-16(a)–(e)`, `T-7`, `T-14`; UX Scenario 4; `AD-6`.
- **Binding Invariants:** `AD-6`, `INV-08`.
- **Files Touched:** `domain/state_machine.py`, `domain/allocation.py`, `domain/engine.py`.
- **Schema & DTOs:** `001_night_training_scheduler_schema.sql` (`jobs.preempted_in_window`, `jobs.granted_priority`).
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestActivateWindowContract::test_activate_window_invariant_atomic_server_gpu_allocation`
- **Gherkin Scenarios:**
  - *Happy Path:*
    - **Given** a challenger with `THESIS` priority delta $\ge 20$ over a victim whose `preempted_in_window == 0`
    - **When** preemption is evaluated before 05:45:00
    - **Then** victim is transitioned to `CHECKPOINTING` (`T-7`), its slot is reassigned to the challenger upon verified checkpoint, and victim returns to tonight's queue (`T-14`).
  - *Failure Path (Margin Under 20):*
    - **Given** a challenger with priority delta $< 20$
    - **When** preemption is evaluated
    - **Then** preemption is refused with `PREEMPTION_REFUSED` citing `PRIORITY_MARGIN_INSUFFICIENT` and the running job remains in place.
- **Definition of Done (DoD):** Preemption margin $\ge 20$ enforced, victim capped at 1 preemption per window, refused preemption emits audit record.

### Story 4.3: Uniform 404 Access Control & Identity Redaction
- **User Story:** As Kavita, I want other students to receive HTTP 404 if they query my job details, so that my job identifiers and research models cannot be enumerated.
- **Traceability:** PRD `FR-31(a)–(f)`; `NFR-11`; `AD-8`.
- **Binding Invariants:** `AD-8`, `INV-07`.
- **Files Touched:** `api/routes/auth.py`, `api/routes/jobs.py`.
- **Schema & DTOs:** `ErrorBodyDTO`, `AD-8` `ROLE_CAPABILITY` table.
- **ATDD Test Path:** `test/atdd/night_training_scheduler_contracts_test.py::TestSubmitJobContract::test_submit_job_precondition_violation_distributed_spec_rejected_with_zero_state_mutation`
- **Gherkin Scenarios:**
  - *Happy Path (Owner Access):*
    - **Given** an authenticated student querying their own job `JOB-0001`
    - **When** GET `/api/v1/jobs/JOB-0001` is invoked
    - **Then** status is `200 OK` with full job details.
  - *Failure Path (Unauthorized Query):*
    - **Given** an authenticated student querying another student's job `JOB-0002`
    - **When** GET `/api/v1/jobs/JOB-0002` is invoked
    - **Then** status is `404 Not Found` (byte-identical to non-existent job query, no 403 returned) and a `LifecycleEvent` is logged.
- **Definition of Done (DoD):** Zero 403 status codes returned, zero bearer tokens logged, byte-identical 404 responses for unauthorized and absent jobs.
