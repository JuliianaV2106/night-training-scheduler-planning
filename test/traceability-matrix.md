---
title: "Module 9 — Night Training Scheduler: Requirements Traceability Matrix (Task Impl-2)"
status: final
version: "2.0.0"
created: 2026-10-18
updated: 2026-11-07
authors:
  - "Juliana Filigrana Valencia (Test Lead)"
  - "Juan Manuel Casanova Marín (Reviewer)"
module: "Module 9 — Night Training Scheduler"
gate: "Task Impl-2 Multi-Flow Verification Gate (100% PASS)"
---

# Requirements Traceability Matrix — Module 9: Night Training Scheduler

This matrix establishes bidirectional traceability from PRD functional/non-functional requirements and architecture invariants (`AD-1`..`AD-8`) through to the **Module 9 Stories (`9.1`–`9.6` & `STORY-1.1`–`STORY-4.3`)**, the **Automated Test Files** across all 5 BMad Testing Flows, the **CI Evidence Logs**, and the final **Verdict**.

---

## 1. Task Impl-2 Master Traceability Matrix (`PRD Requirement → User Story → Automated Test Files → CI Evidence → Verdict`)

| PRD Requirement / Invariant | User Story | BMad Testing Flow | Automated Test Files | CI Evidence Artifact | Verdict |
|---|---|---|---|---|:---:|
| **FR-1, FR-2, FR-3, FR-5, INV-01**<br>Single-node job admission, SHA-256 digest idempotency, distributed rejection (`worker_count > 1`), & 500-job queue cap | **Story 9.1**<br>(`STORY-1.1`, `STORY-1.2`, `STORY-3.3`) | **Flow B** (Test-Along) & **Flow C** (Test-After) | `test/unit/test_domain_core.py`<br>`test/atdd/night_training_scheduler_contracts_test.py`<br>`test/integration/test_concurrency_and_stories.py` | `test/evidence/pytest-coverage.log` | **PASS** |
| **FR-8, FR-12, FR-13, FR-14, FR-15**<br>Deterministic night window activation at `22:00:00`, 4-key tie-breaker, 33-slot ceiling, & atomic 2-GPU placement on `server-gpu-01` | **Story 9.2**<br>(`STORY-1.3`, `STORY-3.1`, `STORY-3.2`) | **Flow B** (Test-Along) | `test/unit/test_domain_core.py`<br>`test/atdd/night_training_scheduler_contracts_test.py` | `test/evidence/pytest-coverage.log` | **PASS** |
| **FR-19, FR-20, FR-24, Invariant S-2**<br>Dawn graceful checkpoint ramp (`05:45:00`), SHA-256 pre-verification sweep, quarantine on mismatch, & `ExplanationDTO` citations | **Story 9.3**<br>(`STORY-1.4`, `STORY-2.3`, `STORY-4.1`) | **Flow B** (Test-Along) & **Flow C** (Test-After) | `test/unit/test_domain_core.py`<br>`test/atdd/night_training_scheduler_contracts_test.py`<br>`test/integration/test_concurrency_and_stories.py` | `test/evidence/pytest-coverage.log` | **PASS** |
| **FR-19, FR-23, FR-27, Invariant S-1**<br>Pre-Morning Hard Eviction (`05:45` SIGTERM $\rightarrow$ `05:46` SIGKILL), `EVICTED_FORCEFULLY`, node cordoning (`CORDONED_DIRTY` / `DIRTY_EVICTION_FAILED`), & 31/32 healthy nodes at `06:00` | **Story 9.4**<br>(`STORY-2.1`, `STORY-2.2`) | **Flow A** (ATDD-First: Strict Red $\rightarrow$ Green $\rightarrow$ Refactor) | `test/atdd/test_story_9_4_hard_eviction_atdd.py`<br>`test/atdd/night_training_scheduler_contracts_test.py` | `test/evidence/atdd-red-story-9.4.log` (Red)<br>`test/evidence/pytest-coverage.log` (Green) | **PASS** |
| **FR-16, NFR-2, NFR-3, AD-6, INV-08**<br>Dynamic Priority Queue Preemption Cascade (`THESIS` Priority 10 vs `EXPLORATION` Priority 1), earliest checkpoint tie-breaker, `QUEUED_PREEMPTED`, & 50-VU contention burst | **Story 9.5**<br>(`STORY-4.2`, `STORY-3.3`) | **Flow D** (Quality Gate / NFR & Concurrency Verification) | `test/nfr/scheduler-preemption-burst.js`<br>`test/integration/test_concurrency_and_stories.py`<br>`test/unit/test_domain_core.py` | `test/evidence/k6-nfr-story-9.5.log`<br>`test/evidence/pytest-coverage.log` | **PASS** |
| **FR-24, NFR-5, NFR-9, Invariant S-1**<br>Fast-Forward 24-Hour Time-Lapse Scheduler Status Board E2E (`14:00` Queued $\rightarrow$ `22:00` Running $\rightarrow$ `06:00` Completed/Evicted + 32 `IDLE` nodes) | **Story 9.6**<br>(`STORY-4.1`, `STORY-1.3`, `STORY-1.4`) | **Flow E** (Playwright E2E with POM & Forensic Traces) | `test/e2e/pages/SchedulerDashboardPage.ts`<br>`test/e2e/scheduler-board.spec.ts` | `test/evidence/playwright-e2e-story-9.6.log`<br>`test-results/.../trace.zip` | **PASS** |
| **FR-31, NFR-11, AD-8**<br>Uniform HTTP 404 Access Control & Identity Redaction (never leaking HTTP 403 on foreign student jobs) | **Story 4.3** | **Flow C** (Test-After Security Hardening) | `test/integration/test_concurrency_and_stories.py` | `test/evidence/pytest-coverage.log` | **PASS** |
| **NFR-1, NFR-10, AD-1, AD-2, INV-04, INV-07**<br>AST Domain Purity Gate (zero I/O or wall-clock imports in `domain/`) & Crash Recovery Log Fold without Replay | **Story 3.4**<br>(`STORY-1.1`) | **Flow B** & **Flow C** | `test/unit/test_domain_core.py` | `test/evidence/pytest-coverage.log` | **PASS** |

---

## 2. Granular Contract-Level Traceability Table (Solu-2 Baseline $\rightarrow$ Impl-2 Green Verification)

| PRD FR / NFR | Scenario (UX) | AD-n Invariant | Contract Clause | Executable Test ID | Target Story ID | Impl-2 Verdict |
|---|---|---|---|---|---|:---:|
| **FR-1, FR-2, FR-5** | Scenario 1 (Job Submission) | `AD-1`, `AD-4` | `submitJob: P1, P2, P3` | `test_submit_job_happy_path_admits_and_persists_pending_job` | `STORY-1.1` / `9.1` | **PASS (GREEN)** |
| **FR-3** (Single-Node Boundary) | Scenario 1 (Job Submission) | `AD-4` | `submitJob: P1` | `test_submit_job_precondition_violation_distributed_spec_rejected_with_zero_state_mutation` | `STORY-1.2` / `9.1` | **PASS (GREEN)** |
| **FR-8, FR-14, FR-15** | Scenario 2 (22:00 Activation) | `AD-1`, `AD-4` | `activateWindow: Q1, Q2` | `test_activate_window_happy_path_places_jobs_deterministically` | `STORY-1.3` / `9.2` | **PASS (GREEN)** |
| **FR-19** (Eviction Ramp) | Scenario 3 (05:45 Ramp) | `AD-1`, `AD-7` | `evictAtDeadline: P1, Q2` | `test_evict_at_deadline_happy_path_completes_checkpoint_and_releases_slots` | `STORY-1.4` / `9.3` | **PASS (GREEN)** |
| **FR-19, FR-23, Invariant S-1** | Scenario 3 (Dawn Edge Case) | `AD-1`, `AD-4`, `AD-7` | `evictAtDeadline: Q2 (Edge)` | `test_story_9_4_hard_eviction_sigkill_cordons_dirty_node_and_hands_over_clean_fleet_at_0600` & `test_mandatory_edge_case_checkpoint_failure_at_dawn_cordons_node_releases_all_slots_at_0600` | `STORY-2.1` / `9.4` | **PASS (GREEN)** |
| **FR-23, FR-27** (Cordon & Alert) | Scenario 3 (Dawn Edge Case) | `AD-7` | `evictAtDeadline: Q2, Q3` | `test_mandatory_edge_case_user_notified_and_job_rescheduled_after_dawn_checkpoint_failure` | `STORY-2.2` / `9.4` | **PASS (GREEN)** |
| **FR-2(k), FR-12** (2-GPU Server) | Scenario 2 (Placement) | `AD-4` | `submitJob: P2`, `activateWindow: I3` | `test_submit_job_invariant_two_gpu_requires_48gb_physically_enforced` | `STORY-3.1` / `9.2` | **PASS (GREEN)** |
| **FR-8, FR-13** (Fleet Cap 33) | Scenario 2 (Placement) | `AD-4` | `activateWindow: I2` | `test_activate_window_invariant_total_allocated_slots_never_exceeds_33` | `STORY-3.2` / `9.2` | **PASS (GREEN)** |
| **FR-1(a), PRD §4.1** (500 Queue Cap)| Scenario 1 (Admission) | `AD-1` | `submitJob: P5`, `INV-01` | `test_submit_job_invariant_queue_cap_500_enforced_under_burst_submissions` | `STORY-3.3` / `9.1` | **PASS (GREEN)** |
| **FR-24, NFR-4** (Explainability) | Scenario 1, 2, 3 (Board) | `AD-3` | `submitJob: Q4`, `activateWindow: Q4` | `test_submit_job_explainability_payload_cites_jobspec_validation_rule` | `STORY-4.1` / `9.3` | **PASS (GREEN)** |
| **FR-16** (Priority Preemption) | Scenario 4 (Preemption) | `AD-6` | `INV-08` | `test_story_9_5_priority_preemption_cascade_and_concurrent_contention` | `STORY-4.2` / `9.5` | **PASS (GREEN)** |
| **FR-20, Invariant S-2** (Checkpoints)| Scenario 3, 4 (Resume) | `AD-7` | `INV-06` | `test_checkpoint_digest_mismatch_quarantines_file_and_fails_job` | `STORY-2.3` / `9.3` | **PASS (GREEN)** |
| **FR-31, NFR-11** (Auth Isolation) | Scenario 1, 2 (Console) | `AD-8` | `submitJob: P4` | `test_story_4_3_uniform_404_on_missing_or_unauthorized_job` | `STORY-4.3` | **PASS (GREEN)** |
| **NFR-1** (Single Time Call Site) | All Scenarios | `AD-1` | `INV-07` | `test_domain_purity_ast_scan_has_zero_forbidden_imports` | `STORY-1.1` / `9.1` | **PASS (GREEN)** |
| **NFR-2, NFR-3** (Latency & Burst) | Scenario 1, 2, 4 | `AD-2` | `k6` + `ThreadPoolExecutor` | `test/nfr/scheduler-preemption-burst.js` ($p_{95} = 8.52\text{ ms}$) | `STORY-1.3` / `9.5` | **PASS (GREEN)** |
| **NFR-10** (Crash Recovery) | All Scenarios (Daemon) | `AD-2`, `AD-5` | `INV-04` | `test_evaluate_preemption_cascade_and_recovery_fold` | `STORY-3.4` | **PASS (GREEN)** |

---

## 3. Gate Verification Checklist

- [x] **100% P0 Risks & Architectural Decisions (`AD-1`..`AD-8`) Verified Green:** Every contract and invariant test passes against the real SQLite database and pure domain engine.
- [x] **$\ge 90\%$ Core Domain Branch Coverage Achieved:** Measured **99.13% branch coverage** across `domain/` (`test/evidence/pytest-coverage.log`).
- [x] **70 / 20 / 10 Test Pyramid Enforced:** 61 Unit Tests (74.4%) / 20 Integration & Contract Tests (24.4%) / 1 Playwright E2E + 1 k6 Load Suite (1.2%).
- [x] **Zero Hardcoded Sleeps (`time.sleep` / `waitForTimeout`):** Enforced across all Python and TypeScript files via simulated clock injection and Playwright web-first assertions.
