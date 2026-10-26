---
title: "Module 9 — Night Training Scheduler: Requirements Traceability Matrix"
status: final
version: "1.0.0"
created: 2026-10-18
authors:
  - "Juliana Filigrana Valencia (Test Lead)"
  - "Juan Manuel Casanova Marín (Reviewer)"
module: "Module 9 — Night Training Scheduler"
gate: "Phase 3 TEA Gate (100% P0 and AD-n traced)"
---

# Requirements Traceability Matrix

This matrix establishes bidirectional traceability from requirements and architecture invariants through behavioral contracts, executable ATDD tests, and sprint backlog stories.

---

## 1. Traceability Table

| PRD FR / NFR | Scenario (UX) | AD-n Invariant | Contract Clause | Test ID (Executable Red Test) | Target Story ID | Gate Status |
|---|---|---|---|---|---|:---:|
| **FR-1, FR-2, FR-5** | Scenario 1 (Job Submission) | `AD-1`, `AD-4` | `submitJob: P1, P2, P3` | `test_submit_job_happy_path_admits_and_persists_pending_job` | `STORY-1.1` | **PASS (RED)** |
| **FR-3** (Single-Node Boundary) | Scenario 1 (Job Submission) | `AD-4` | `submitJob: P1` | `test_submit_job_precondition_violation_distributed_spec_rejected_with_zero_state_mutation` | `STORY-1.2` | **PASS (RED)** |
| **FR-8, FR-14, FR-15** | Scenario 2 (22:00 Activation) | `AD-1`, `AD-4` | `activateWindow: Q1, Q2` | `test_activate_window_happy_path_places_jobs_deterministically` | `STORY-1.3` | **PASS (RED)** |
| **FR-19** (Eviction Ramp) | Scenario 3 (05:45 Ramp) | `AD-1`, `AD-7` | `evictAtDeadline: P1, Q2` | `test_evict_at_deadline_happy_path_completes_checkpoint_and_releases_slots` | `STORY-1.4` | **PASS (RED)** |
| **FR-19, FR-23, Invariant S-1** | Scenario 3 (Dawn Edge Case) | `AD-1`, `AD-4`, `AD-7` | `evictAtDeadline: Q2 (Edge)` | `test_mandatory_edge_case_checkpoint_failure_at_dawn_cordons_node_releases_all_slots_at_0600` | `STORY-2.1` | **PASS (RED)** |
| **FR-23, FR-27** (Cordon & Alert) | Scenario 3 (Dawn Edge Case) | `AD-7` | `evictAtDeadline: Q2, Q3` | `test_mandatory_edge_case_user_notified_and_job_rescheduled_after_dawn_checkpoint_failure` | `STORY-2.2` | **PASS (RED)** |
| **FR-2(k), FR-12** (2-GPU Server) | Scenario 2 (Placement) | `AD-4` | `submitJob: P2`, `activateWindow: I3` | `test_submit_job_invariant_two_gpu_requires_48gb_physically_enforced` | `STORY-3.1` | **PASS (RED)** |
| **FR-8, FR-13** (Fleet Cap 33) | Scenario 2 (Placement) | `AD-4` | `activateWindow: I2` | `test_activate_window_invariant_total_allocated_slots_never_exceeds_33` | `STORY-3.2` | **PASS (RED)** |
| **FR-1(a), PRD §4.1** (500 Queue Cap)| Scenario 1 (Admission) | `AD-1` | `submitJob: P5`, `INV-01` | `test_submit_job_invariant_queue_cap_500_enforced_under_burst_submissions` | `STORY-3.3` | **PASS (RED)** |
| **FR-24, NFR-4** (Explainability) | Scenario 1, 2, 3 (Board) | `AD-3` | `submitJob: Q4`, `activateWindow: Q4` | `test_submit_job_explainability_payload_cites_jobspec_validation_rule` | `STORY-4.1` | **PASS (RED)** |
| **FR-16** (Priority Preemption) | Scenario 4 (Preemption) | `AD-6` | `INV-08` | `test_preemption_refused_when_priority_margin_under_20` | `STORY-4.2` | **PASS (RED)** |
| **FR-20, Invariant S-2** (Checkpoints)| Scenario 3, 4 (Resume) | `AD-7` | `INV-06` | `test_checkpoint_digest_mismatch_quarantines_file_and_fails_job` | `STORY-2.3` | **PASS (RED)** |
| **FR-31, NFR-11** (Auth Isolation) | Scenario 1, 2 (Console) | `AD-8` | `submitJob: P4` | `test_unauthorized_job_access_returns_404_not_403` | `STORY-4.3` | **PASS (RED)** |
| **NFR-1** (Single Time Call Site) | All Scenarios | `AD-1` | `INV-07` | `test_domain_purity_ast_scan_has_zero_forbidden_imports` | `STORY-1.1` | **PASS (RED)** |
| **NFR-2** (200 ms p95 Latency) | Scenario 2 (Activation) | `AD-2` | `activateWindow: NFR` | `test_window_activation_latency_under_200ms_for_500_jobs` | `STORY-1.3` | **PASS (RED)** |
| **NFR-10** (Crash Recovery) | All Scenarios (Daemon) | `AD-2`, `AD-5` | `INV-04` | `test_crash_after_record_write_leaves_zero_orphaned_state_mutations` | `STORY-3.4` | **PASS (RED)** |

---

## 2. Phase 3 Gate Verification Checklist

- [x] **Zero P0 Risks without an Executable Red Test:** All 4 P0 risks (`RSK-01` through `RSK-04`) are covered by automated tests.
- [x] **Zero Architectural Decisions (AD-1..8) without Invariant Tests:** Every AD invariant is bound to a test that turns RED if the physical rule or constraint is omitted.
- [x] **Zero Orphaned Requirements:** Every PRD FR/NFR maps forward to a contract clause and an executable test ID.
- [x] **Zero Tautological Tests:** All tests assert on real schema fields, database states, and non-effects (`Q-fail`).
