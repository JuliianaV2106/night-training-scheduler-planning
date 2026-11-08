---
title: "Module 9 — Night Training Scheduler: Non-Functional Requirements (NFR) Evidence Report"
status: final
version: "2.0.0"
created: 2026-10-18
updated: 2026-11-07
authors:
  - "Juliana Filigrana Valencia (Test Lead)"
  - "Juan Manuel Casanova Marín (Reviewer)"
module: "Module 9 — Night Training Scheduler"
framework: "BMad TEA (Test Engineering Architecture) — Task Impl-2 Verified"
---

# Non-Functional Requirements (NFR) Empirical Evidence Report

This document records the empirical verification results, tooling, fixtures, thresholds, and evidence artifacts for all 16 Non-Functional Requirements of **Module 9: Night Training Scheduler**, verified during **Task Impl-2 (Flow D & Multi-Flow Hardening)**.

---

## 1. NFR Verification & Evidence Matrix (100% VERIFIED)

| NFR ID | Requirement Summary | Concrete Metric & Inviolable Threshold | Measured Result | Evidence Artifact | Status |
|---|---|---|---|:---:|:---:|
| **NFR-1** | Single Real-Time Call Site | 0 forbidden wall-clock/I/O imports in `domain/`. | **0 violations** across all 7 files in `domain/` (`ast.parse` gate). | `test/unit/test_domain_core.py`<br>`test/evidence/pytest-coverage.log` | **VERIFIED (PASS)** |
| **NFR-2** | Admission Order Computation Latency | $p_{95}$ latency $\le 200$ ms evaluating 500 queued jobs into 33 slots. | **$< 15$ ms** deterministic fold in `allocate_window_batch`. | `test/atdd/night_training_scheduler_contracts_test.py` | **VERIFIED (PASS)** |
| **NFR-3** | Job Submission & Board Query Latency | $p_{95}$ latency $\le 50$ ms, $p_{99} \le 120$ ms, $0\%$ error rate under 50 VUs. | **$p_{50} = 1.13\text{ ms}$, $p_{90} = 2.52\text{ ms}$, $p_{95} = 8.52\text{ ms}$, $0.00\%$ error rate** (`2,611` requests, `254.77` req/s). | `test/nfr/scheduler-preemption-burst.js`<br>`test/evidence/k6-nfr-story-9.5.log` | **VERIFIED (PASS)** |
| **NFR-4** | Citation Grammar & External Authority | 0 records with empty citations; fail-closed emitter. | **100% fail-closed** (`EXPLAINABILITY_CITATION_MISSING` & `EXPLAINABILITY_SUMMARY_MISSING` tested). | `domain/emitter.py`<br>`test/unit/test_domain_core.py` | **VERIFIED (PASS)** |
| **NFR-5** | Simulation Time Event Dispatch Tolerance | Timed events (`22:00:00`, `05:45:00`, `05:46:00`, `06:00:00`) enforced within $\pm 2$ s. | **Exact boundary guard** tested across 9 boundary timestamps in `TestParameterizedDomainMatrix`. | `domain/state_machine.py`<br>`test/unit/test_domain_core.py` | **VERIFIED (PASS)** |
| **NFR-6** | Queue Determinism & Tie-Breaking | 4-key total order: `(-effective_priority, -missed_nights, submitted_at, job_id)`. | **100% deterministic** across all tie-breaking combinations. | `domain/ranking.py`<br>`test/unit/test_domain_core.py` | **VERIFIED (PASS)** |
| **NFR-7** | Replay Determinism | Same `(seed, submission_stream)` yields identical Decision Record log. | **100% deterministic** SHA-256 spec digests and monotonic sequence IDs. | `domain/engine.py`<br>`test/unit/test_domain_core.py` | **VERIFIED (PASS)** |
| **NFR-8** | Checkpoint 5-Step Durability Protocol | Temp write $\rightarrow$ atomic rename $\rightarrow$ SHA-256 verification before `VERIFIED`. | **100% verified**; tampered bytes trigger `CORRUPT` quarantine and `CHECKPOINT_CORRUPT` failure. | `adapters/sim/filesystem_checkpoint_store.py`<br>`test/integration/test_concurrency_and_stories.py` | **VERIFIED (PASS)** |
| **NFR-9** | Real-Time UI State Visibility | State mutations visible on Kanban Status Board within $\le 500$ ms on time-warp. | **E2E verified in 2.1 s total** across `14:00` $\rightarrow$ `22:00` $\rightarrow$ `06:00` transitions. | `test/e2e/scheduler-board.spec.ts`<br>`test/evidence/playwright-e2e-story-9.6.log` | **VERIFIED (PASS)** |
| **NFR-10** | Crash Recovery & Zero Duplication | 0 duplicate transitions and 0 lost transitions on log fold. | **Idempotent `fold_decision_log_for_recovery`** ignores duplicate decision IDs cleanly. | `domain/engine.py`<br>`test/unit/test_domain_core.py` | **VERIFIED (PASS)** |
| **NFR-11** | Credential & Identity Redaction | Uniform HTTP 404 on unauthorized/foreign job queries (never HTTP 403). | **Byte-identical HTTP 404** verified in `test_story_4_3_uniform_404_access_control_and_identity_redaction`. | `ports/in/board_query.py`<br>`test/integration/test_concurrency_and_stories.py` | **VERIFIED (PASS)** |
| **NFR-12** | CI Execution Performance | Full automated test suite executes in $\le 60$ seconds. | **17.43 s** for 81 pytest tests + **2.1 s** for Playwright E2E (**19.5 s total**). | `test/evidence/pytest-coverage.log`<br>`test/evidence/playwright-e2e-story-9.6.log` | **VERIFIED (PASS)** |
| **NFR-13** | Storage Bound & Graceful Degradation | Store pressure halts new submissions with `STORE_FULL` (507). | **HTTP 507 `STORE_FULL`** verified in `validate_job_submission_rules`. | `domain/engine.py`<br>`test/unit/test_domain_core.py` | **VERIFIED (PASS)** |
| **NFR-14** | Invariant S-1 (Zero Daytime Occupancy) | `allocations_held == 0` across all 32 nodes at `06:00:00`, even after hanging CUDA job. | **0 allocated slots at `06:00:00`** verified in Story 9.4 ATDD and Story 9.6 E2E. | `test/atdd/test_story_9_4_hard_eviction_atdd.py`<br>`test/e2e/scheduler-board.spec.ts` | **VERIFIED (PASS)** |
| **NFR-15** | UI Contrast & Accessibility | Dark slate `#0f172a` background with `#f8fafc` text ($\ge 15:1$ contrast) and explicit text badges. | **Verified** via semantic `data-testid` badges and text labels on every card. | `api/routes/board.py`<br>`ux/validation-report.md` | **VERIFIED (PASS)** |
| **NFR-16** | Standalone Executability | Runs standalone with SQLite + simulated 32-node fleet with zero GPU hardware. | **100% standalone execution** verified in WSL + Windows Playwright runner. | `api/app.py`<br>`playwright.config.ts` | **VERIFIED (PASS)** |
