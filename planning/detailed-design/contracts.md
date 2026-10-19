---
title: "Module 9 — Night Training Scheduler: Formal Behavioral Contracts (Phase 1)"
status: final
version: "1.0.0"
created: 2026-10-18
authors:
  - "Juan Manuel Casanova Marín (Architect-Lead)"
  - "Juliana Filigrana Valencia (Reviewer)"
module: "Module 9 — Night Training Scheduler"
governance: "AI Governance Level 3"
---

# Formal Behavioral Contracts: Core Operations

This document specifies the machine-enforceable, design-by-contract specifications for the 3 core operations of the **Night Training Scheduler (Module 9)**.

**Contractual Precision Rule:** This specification contains **zero elastic language**. Every descriptive adjective is replaced by a concrete numeric threshold, a typed data structure, an enumeration literal, an HTTP status code, or an explicit state transition identifier.

---

## 1. Typed Error Catalog

The following catalog defines the canonical typed errors shared across all inbound ports, core domain handlers, and driving adapters. Every error maps to an immutable uppercase machine code, a standard HTTP status code, a deterministic trigger, a template for user/system diagnostics, and an explicit boolean retryable flag.

| Error Code (`CODE`) | HTTP Status | Trigger Condition | Human-Readable Explanation Template | Retryable |
|---|---|---|---|:---:|
| `OUT_OF_SCOPE_DISTRIBUTED` | `400 Bad Request` | `spec.worker_count > 1` OR `spec.replicas > 1` OR `spec.distributed_artifact_present == true` | `"Job submission specifies distributed multi-node execution (worker_count={worker_count}, replicas={replicas}). Module 9 processes single-node jobs only. Route distributed workloads to Module 10."` | No |
| `VALIDATION_FAILED` | `422 Unprocessable Entity` | Parameter syntax or boundary violation (e.g., malformed image digest, VRAM class $\notin \{24, 48\}$, checkpoint interval $\notin [1, 30]$) | `"Job specification field '{field}' failed validation rule '{rule_id}': observed value '{observed}', required threshold '{constraint}'."` | No |
| `TWO_GPU_REQUIRES_48GB` | `422 Unprocessable Entity` | `spec.gpu_slots_requested == 2` AND `spec.required_vram_gb != 48` | `"Two-GPU spanning allocations are supported exclusively on 48 GB hardware (server-gpu-01). Requested VRAM: {vram} GB."` | No |
| `MAX_NIGHT_SPAN_EXCEEDED` | `422 Unprocessable Entity` | `spec.estimated_duration_s > 139500` ($> 38.75$ hours / 5 usable night windows of 7.75 hours) | `"Estimated job duration {duration_s}s exceeds maximum allowable night span of 139500s (5 nights x 27900s). Reduce batch size or total training steps."` | No |
| `IDEMPOTENCY_CONFLICT` | `409 Conflict` | Existing `idempotency_key` found with differing SHA-256 payload digest | `"Idempotency key '{idempotency_key}' was previously registered with payload SHA-256 '{original_digest}', differing from current payload SHA-256 '{incoming_digest}'."` | No |
| `QUEUE_CAP_EXCEEDED` | `429 Too Many Requests` | Total count of non-terminal jobs in system $\ge 500$ at admission attempt | `"Scheduler queue capacity limit of 500 non-terminal jobs reached (current count: {current_count}). Retry submission after window activation or job completion."` | Yes |
| `STORE_FULL` | `507 Insufficient Storage` | `checkpoint_store.available_bytes < spec.storage_request_bytes` | `"Checkpoint storage root capacity reached. Available: {available_bytes} bytes, requested: {requested_bytes} bytes. Submissions suspended until 03:00:00 cleanup."` | Yes |
| `ENTITLEMENT_DENIED` | `404 Not Found` | Actor role lacks capability or course entitlement (status 404 enforced per AD-8 to prevent ID enumeration) | `"Resource not found or unauthorized access attempt for actor '{actor_id}'."` | No |
| `MODEL_NOT_FOUND` | `422 Unprocessable Entity` | Model ID not found in Module 5 catalog fixture or marked deprecated | `"Model identifier '{model_id}' version '{version}' does not exist or is deprecated in catalog."` | No |
| `DELEGATE_UNAVAILABLE` | `503 Service Unavailable` | Required delegated fixture (M1, M2, M3, M4, M5, M8) fails to return response within 100 ms timeout | `"Delegated module '{module_name}' is unavailable. Automatic fail-closed policy applied citing self:DELEGATE-UNAVAILABLE-v1."` | Yes |
| `WINDOW_ACTIVATION_OUTSIDE_WINDOW` | `400 Bad Request` | `activateWindow` invoked when simulated time is not `22:00:00` ($\pm 2$ simulated seconds) | `"Window activation invoked at invalid simulated instant '{sim_instant}'. Window activation occurs strictly at 22:00:00."` | No |
| `EVICTION_CALLED_BEFORE_RAMP` | `400 Bad Request` | `evictAtDeadline` invoked when simulated time $< 05:45:00$ | `"Eviction ramp invoked at simulated instant '{sim_instant}', preceding scheduled ramp threshold 05:45:00."` | No |
| `INVALID_STATE_FOR_EVICTION` | `409 Conflict` | Target job is not in `RUNNING` or `CHECKPOINTING` state at eviction execution | `"Job '{job_id}' is in state '{current_state}', expected RUNNING or CHECKPOINTING for eviction processing."` | No |
| `CHECKPOINT_DEADLINE_MISSED` | `500 Internal Error` | Checkpoint write incomplete at deadline `05:53:00` | `"Job '{job_id}' failed to complete verified checkpoint write by deadline 05:53:00. SIGKILL issued, node '{node_id}' cordoned."` | No |

---

## 2. Behavioral Contract Matrix

### 2.1 Operation: `submitJob`

```python
submitJob(
    spec: JobSpecDTO, 
    idempotency_key: str, 
    actor_id: str, 
    at: datetime
) -> JobSubmissionResponseDTO
```

- **Layer:** Driving Adapter (`api/routes/jobs.py`) $\rightarrow$ Inbound Port (`ports/in/job_submission.py`) $\rightarrow$ Core Domain (`domain/engine.py`).
- **Preconditions (P):**
  - **P1 (Distributed Scope Check):** `spec.worker_count == 1` AND `spec.replicas == 1` AND `spec.distributed_artifact_present == false`.  
    *Violation:* `OUT_OF_SCOPE_DISTRIBUTED`, HTTP 400.
  - **P2 (Specification Type and Range):**  
    - `idempotency_key` is ASCII string with length between 1 and 64 characters inclusive.  
    - `spec.image_digest` matches regular expression `^sha256:[a-f0-9]{64}$`.  
    - `spec.gpu_slots_requested` $\in \{1, 2\}$.  
    - `spec.required_vram_gb` $\in \{24, 48\}$.  
    - If `spec.gpu_slots_requested == 2`, then `spec.required_vram_gb == 48`.  
    - `spec.checkpoint_interval_minutes` $\in [1, 30]$.  
    - `spec.estimated_duration_s` $\in [60, 139500]$.  
    *Violation:* `VALIDATION_FAILED` or `TWO_GPU_REQUIRES_48GB` or `MAX_NIGHT_SPAN_EXCEEDED`, HTTP 422.
  - **P3 (Idempotency Verification):** If `idempotency_key` matches an existing database record, SHA-256 digest of serialized `spec` must match `existing_job.payload_digest`.  
    *Violation:* `IDEMPOTENCY_CONFLICT`, HTTP 409.
  - **P4 (Security, Entitlement & Quota):** `actor_id` exists in M1 fixture with role `STUDENT` or `LAB_ADMIN`. Model ID exists in M5 catalog fixture. M8 quota check returns status `APPROVED`.  
    *Violation:* `ENTITLEMENT_DENIED` (HTTP 404 per AD-8), `MODEL_NOT_FOUND` (HTTP 422), or `QUOTA_EXHAUSTED` (HTTP 422). If M1/M2/M5/M8 fixture fails to answer: `DELEGATE_UNAVAILABLE`, HTTP 503.
  - **P5 (Queue Capacity Boundary):** Current count of non-terminal jobs (`QUEUED_PENDING_WINDOW`, `RUNNING`, `CHECKPOINTING`, `EVICTED_RESUMABLE`, `EVICTION_FAILED`) $< 500$.  
    *Violation:* `QUEUE_CAP_EXCEEDED`, HTTP 429.
  - **P6 (Storage Budget):** Checkpoint store free bytes $\ge spec.storage_request_bytes$.  
    *Violation:* `STORE_FULL`, HTTP 507.
- **Postconditions (Q):**
  - **Q1 (Return Value Schema):** Returns `JobSubmissionResponseDTO` with fields: `job_id` (format `JOB-[0-9]{4}`), `status: "QUEUED_PENDING_WINDOW"`, `idempotency_key: str`, `admitted_at: str` (ISO-8601 with `-05:00`), `queue_position: int` ($\in [1, 500]$), `payload_digest: str`. On idempotent resubmission with identical digest, returns HTTP 200 with original `job_id` and existing state.
  - **Q2 (State Mutation & Database Transition):** Inserts exactly one row into `jobs` table with `state = 'QUEUED_PENDING_WINDOW'`, `consecutive_nights_missed = 0`, `admitted_nights = 0`, `retry_count = 0`. Inserts exactly one row into `decision_records` with `decision = 'ADMIT'`, `transition = 'T-1'`.
  - **Q3 (Audit Event Emission):** Emits lifecycle event `JOB_SUBMITTED` containing `job_id`, `actor_id`, `sim_timestamp`, and `payload_digest`.
  - **Q4 (Explainability Payload):** Appends `DecisionRecord` citing rule IDs: `self:JOBSPEC-VALIDATION-v1`, `policy:M2/night-window@v1`, `catalog:M5/{model_id}@{version}`.
  - **Q-fail:** If any precondition fails, zero rows are inserted into `jobs`, zero rows are inserted into `decision_records`, zero checkpoint files are created, and zero GPU allocations are modified.
- **Invariant (I):**
  - **I1:** Total active non-terminal jobs $\le 500$. Bound to: `AD-1`, `PRD §4.1`.
  - **I2:** Every admitted job holds a unique non-null `idempotency_key`. Bound to: `AD-1`, `FR-5`.
  - **I3:** Every admitted 2-GPU job requires 48 GB VRAM. Bound to: `AD-4`, `FR-2(k)`.
- **Concurrency / Idempotency:** Concurrent submissions are serialized through SQLite transaction isolation (`BEGIN IMMEDIATE`). Simultaneous requests with identical `idempotency_key` produce exactly one `201 Created` and subsequent requests return `200 OK` (if digest matches) or `409 Conflict` (if digest differs).
- **Time:** Injected via `ClockPort.now()`. Timezone strictly `America/Bogota` (UTC-05:00). Submissions accepted 24/7; jobs submitted outside `[22:00:00, 06:00:00)` remain in state `QUEUED_PENDING_WINDOW` until next window activation.
- **Latency Budget (NFR):** Execution time p95 $< 50$ ms at 20 concurrent requests (PRD NFR-3).

---

### 2.2 Operation: `activateWindow`

```python
activateWindow(clock: ClockPort) -> WindowActivationResultDTO
```

- **Layer:** Driving Adapter (`pacer/daemon.py` or `api/routes/simulations.py`) $\rightarrow$ Inbound Port (`ports/in/window_activation.py`) $\rightarrow$ Core Domain (`domain/engine.py`).
- **Preconditions (P):**
  - **P1 (Trigger Instant Verification):** Time component of `clock.now()` is exactly `22:00:00` within tolerance of $\pm 2$ simulated seconds.  
    *Violation:* `WINDOW_ACTIVATION_OUTSIDE_WINDOW`, HTTP 400.
  - **P2 (Hardware Fleet Availability):** Outbound port `FleetRepositoryPort.get_fleet()` returns exactly 32 node records (31 $\times$ 24 GB workstations, 1 $\times$ 2 $\times$ 48 GB server).  
    *Violation:* `DELEGATE_UNAVAILABLE`, HTTP 503.
- **Postconditions (Q):**
  - **Q1 (Return Value Schema):** Returns `WindowActivationResultDTO` containing: `activation_id: str`, `sim_instant: str`, `total_evaluated: int`, `admitted_count: int`, `deferred_count: int`, `placements: list[PlacementDTO]`.
  - **Q2 (State Mutation & Deterministic Placement):**
    - Calculates deterministic Admission Order for all non-terminal candidate jobs sorting by:
      1. `effective_priority` descending,
      2. `consecutive_nights_missed` descending,
      3. `submitted_at` ascending,
      4. `job_id` ascending.
    - Allocates eligible nodes according to strict total ordering:
      1. Previously assigned node (if eligible),
      2. Lowest current `allocations_held`,
      3. `node_id` ascending (lexicographical string comparison).
    - Admitted jobs transition from `QUEUED_PENDING_WINDOW` (or `EVICTED_RESUMABLE`) to `RUNNING` (`T-3` / `T-12`).
    - Unplaced jobs transition to `QUEUED_PENDING_WINDOW` with `T-4a NO_ELIGIBLE_NODE` (if eligible node set is empty) or `T-4b CAPACITY_EXHAUSTED`.
    - Commits all transition records in exactly one atomic database transaction and atomically swaps snapshot pointer.
  - **Q3 (Audit Event Emission):** Emits `WINDOW_ACTIVATED` event with `activation_id`, `sim_instant`, `admitted_count`, and `deferred_count`.
  - **Q4 (Explainability Payload):** Every job evaluation emits a `DecisionRecord` citing `policy:M2/night-window@v1`, `self:ADMISSION-RANKING-v1`, and records candidates considered and placement tiebreak criteria in `inputs`.
  - **Q-fail:** If unhandled database error occurs during activation, database transaction rolls back completely; in-memory state snapshot remains unchanged; zero partial placements persist.
- **Invariant (I):**
  - **I1:** No job transitions to `RUNNING` outside the time interval `[22:00:00, 05:45:00)`. Bound to: `AD-1`, `Invariant S-1`.
  - **I2:** Fleet active allocations count $\le 33$ GPU slots. Bound to: `AD-4`.
  - **I3:** `server-gpu-01` allocates either 2 slots atomically to a 2-GPU job, or 1 slot to a 1-GPU job; a 2-GPU job never holds 1 slot. Bound to: `AD-4`, `FR-2(k)`.
  - **I4:** State transition and `DecisionRecord` commit atomically in one transaction before becoming visible to readers. Bound to: `AD-2`.
- **Concurrency / Idempotency:** Duplicate execution at identical `sim_instant` `22:00:00` returns existing `WindowActivationResultDTO` without re-executing placement or emitting duplicate decision rows.
- **Time:** Operates on half-open interval `[22:00:00, 06:00:00)`. Placements occur strictly at `22:00:00` or before `05:45:00`.
- **Latency Budget (NFR):** Processing 500 queued jobs and allocating 33 slots completes in p95 $< 200$ ms (PRD NFR-2).

---

### 2.3 Operation: `evictAtDeadline` (Mandatory Edge Case)

```python
evictAtDeadline(at: ClockInstant) -> EvictionResultDTO
```

- **Layer:** Driving Adapter (`pacer/daemon.py`) $\rightarrow$ Inbound Port (`ports/in/eviction.py`) $\rightarrow$ Core Domain (`domain/engine.py`).
- **Preconditions (P):**
  - **P1 (Ramp Instant Boundary):** Injected `sim_instant` time component $\ge 05:45:00$ (for eviction ramp) OR $\ge 05:53:00$ (for deadline enforcement).  
    *Violation:* `EVICTION_CALLED_BEFORE_RAMP`, HTTP 400.
  - **P2 (Job State Validity):** Targeted job must currently reside in state `RUNNING` (at 05:45:00) or `CHECKPOINTING` (at 05:53:00).  
    *Violation:* `INVALID_STATE_FOR_EVICTION`, HTTP 409.
- **Postconditions (Q):**
  - **Q1 (Return Value Schema):** Returns `EvictionResultDTO` containing: `job_id: str`, `node_id: str`, `checkpoint_id: str | None`, `checkpoint_status: "VERIFIED" | "FAILED"`, `slots_released: int`, `cordon_requested: bool`, `final_job_state: "EVICTED_RESUMABLE" | "EVICTION_FAILED"`.
  - **Q2 (State Mutation, Edge Case & Physical Release):**
    - **Step 1 (05:45:00 Ramp):** Job transitions `RUNNING -> CHECKPOINTING` (`T-6`). Invokes 5-step checkpoint write on `CheckpointStorePort`.
    - **Step 2A (Happy Path - Verification Succeeds before 05:53:00):** Checkpoint verified with valid SHA-256 digest $\rightarrow$ job transitions `CHECKPOINTING -> EVICTED_RESUMABLE` (`T-8`). All held GPU slots released.
    - **Step 2B (Mandatory Edge Case - Checkpoint Failure / Timeout at 05:53:00):** If checkpoint write fails, throws I/O exception, or does not complete by `05:53:00`:
      1. Job transitions `CHECKPOINTING -> EVICTION_FAILED` (`T-9`).
      2. Held GPU slots are released unconditionally and immediately (`allocations_held` decremented to 0).
      3. Dispatches `CordonRequest(node_id=node_id, cause="EVICTION_CHECKPOINT_WRITE_FAILED")` to Module 3 outbound port and marks node ineligible locally.
      4. Dispatches user notification to local outbox indicating checkpoint write failure and next night re-admission (`T-20`).
      5. Guaranteed physical property: at `06:00:00`, `allocations_held == 0` for all student workloads across all 32 nodes.
  - **Q3 (Audit Event Emission):** Emits `JOB_EVICTED` lifecycle event containing `job_id`, `node_id`, `checkpoint_status`, and `cordon_requested`.
  - **Q4 (Explainability Payload):** Emits `DecisionRecord` with `decision = 'EVICT'`, `transition = 'T-8'` (success) or `T-9` (failure), citing `policy:M2/day-reclaim@v1` and `self:EVICTION-RAMP-v1`.
  - **Q-fail:** A checkpoint failure never prevents GPU slot release. Under zero circumstances may a job retain a GPU slot past `06:00:00`.
- **Invariant (I):**
  - **I1 (No Daytime Occupancy):** `allocations_held == 0` at all times throughout `[06:00:00, 22:00:00]`. Bound to: `AD-1`, `AD-4`, `Invariant S-1`, `NFR-14`.
  - **I2 (Node Cordon Isolation):** Any node experiencing dawn checkpoint failure is immediately cordoned locally and reported to M3 before next night window opens. Bound to: `AD-7`, `FR-23`.
  - **I3 (Resumption Guard):** Resumption permitted exclusively from verified checkpoints with matching SHA-256 digest. Bound to: `AD-7`, `Invariant S-2`.
- **Concurrency / Idempotency:** Idempotent: multiple calls for the same job at the same deadline instant do not create multiple cordon requests or duplicate `T-9` failure records.
- **Time:** Boundary instant $05:45:00 \le \text{sim\_instant} \le 06:00:00$. Tolerance $\pm 2$ simulated seconds (NFR-5).
- **Latency Budget (NFR):** Checkpoint deadline handling, slot release, and cordon dispatch execute in p95 $< 50$ ms (PRD NFR-3).

---

## 3. Invariant Binding Table

Every architectural invariant from `planning/ARCHITECTURE.md` must bind to a concrete physical enforcement point in code, database schemas, or state machine transitions.

| Invariant ID | Rule Summary | Enforces Architectural Decision | Physical Enforcement Point | Test that Turns RED if Removed |
|---|---|---|---|---|
| **INV-01** | Total active non-terminal jobs in the system must never exceed 500. | `AD-1`, `PRD §4.1` | Precondition check in `submitJob` + SQLite trigger / query verification: `SELECT COUNT(*) FROM jobs WHERE state NOT IN ('COMPLETED', 'FAILED', 'REJECTED', 'EXPIRED') < 500`. | `test_submit_job_rejects_when_queue_depth_reaches_500` |
| **INV-02** | Zero student jobs hold GPU allocations outside `[22:00:00, 06:00:00)`. `allocations_held == 0` during daytime. | `AD-1`, `AD-4`, `Invariant S-1`, `NFR-14` | Assertion hook executed at `06:00:00` + unconditional slot release in `evictAtDeadline` regardless of checkpoint outcome. | `test_allocations_held_is_zero_at_0600_after_checkpoint_failure` |
| **INV-03** | Two-GPU jobs allocate both slots of `server-gpu-01` atomically or zero slots; 2-GPU jobs on 24 GB hardware are forbidden. | `AD-4`, `FR-2(k)` | Schema check constraint `CHECK (gpu_slots_requested = 1 OR (gpu_slots_requested = 2 AND required_vram_gb = 48))` + atomic slot allocation lock in SQLite. | `test_two_gpu_job_rejected_on_24gb_workstation` |
| **INV-04** | State changes and `DecisionRecord` rows commit in a single SQLite transaction before snapshot pointer update. | `AD-2`, `FR-24(e)` | Committer transaction wrapper (`with db.transaction(): insert_decision(); update_job(); swap_snapshot()`). | `test_crash_after_record_write_leaves_zero_orphaned_state_mutations` |
| **INV-05** | Node experiencing checkpoint failure at 05:45:00–05:53:00 must be marked cordoned locally and dispatched to Module 3. | `AD-7`, `FR-23` | Exception handler in `evictAtDeadline` invoking `CordonRequest` construction and node eligibility removal. | `test_checkpoint_failure_at_dawn_cordons_node_and_notifies_user` |
| **INV-06** | Job resume is permitted strictly from a verified checkpoint with identical SHA-256 digest; corrupt checkpoints are quarantined. | `AD-7`, `Invariant S-2` | Pre-verification sweep at `21:30:00` re-hashing checkpoint bytes against stored digest before admission. | `test_checkpoint_digest_mismatch_quarantines_file_and_fails_job` |
| **INV-07** | The core scheduler domain performs zero I/O, reads zero system clocks, and draws zero unseeded randomness. | `AD-1`, `AD-2` | Architectural lint test inspecting AST imports of `domain/`: imports of `time`, `datetime.now()`, `sqlite3`, `fastapi`, `random` are forbidden. | `test_domain_purity_ast_scan_has_zero_forbidden_imports` |
| **INV-08** | Preemption requires challenger tier `THESIS` or `URGENT` and priority margin $\ge 20$; victim is capped at 1 preemption per window. | `AD-6`, `FR-16` | Pure domain guard `evaluate_preemption_eligibility()` comparing effective priorities and inspecting `preempted_in_window` boolean flag. | `test_preemption_refused_when_priority_margin_under_20` |
