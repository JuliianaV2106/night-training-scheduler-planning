---
title: "Module 9 — Night Training Scheduler: Non-Functional Requirements (NFR) Evidence Plan"
status: final
version: "1.0.0"
created: 2026-10-18
authors:
  - "Juliana Filigrana Valencia (Test Lead)"
  - "Juan Manuel Casanova Marín (Reviewer)"
module: "Module 9 — Night Training Scheduler"
framework: "BMad TEA (Test Engineering Architecture)"
---

# Non-Functional Requirements (NFR) Evidence Plan

This document establishes the empirical verification strategy, tooling, fixtures, thresholds, and evidence artifacts for all 16 Non-Functional Requirements of **Module 9: Night Training Scheduler**.

---

## 1. NFR Verification & Evidence Matrix

| NFR ID | Requirement Summary | Concrete Metric & Inviolable Threshold | Measurement Method & Fixtures | Evidence Artifact | Status |
|---|---|---|---|---|:---:|
| **NFR-1** | Single Real-Time Call Site | Exactly 1 class/file calling monotonic/system clock (`adapters/sim/simulated_clock.py`). Zero in domain. | AST static scan via `pytest` inspecting all `domain/` and `pacer/` files. | `test/atdd/night_training_scheduler_contracts_test.py` | **PLANNED** |
| **NFR-2** | Admission Order Computation Latency | p95 latency $\le 200$ ms evaluating 500 queued jobs and placing into 33 slots. | Benchmark harness with `fake_clock` and 500 pre-seeded jobs in SQLite. | `test/benchmarks/benchmark_admission_order.py` | **PLANNED** |
| **NFR-3** | Job Submission Latency | p95 latency $\le 50$ ms at 20 concurrent requests. | Locust / `pytest-benchmark` against `POST /jobs` endpoint with in-memory DB. | `test/benchmarks/benchmark_submission.py` | **PLANNED** |
| **NFR-4** | Citation Grammar & External Authority | 0 records with empty citations; 0 `PREEMPT`/`EVICT`/delegated `DENY` records justified solely by `self:`. | Pure domain validator in `domain/emitter.py` asserting against PRD §6.4 map. | `planning/detailed-design/contracts.md` | **PLANNED** |
| **NFR-5** | Simulation Time Event Dispatch Tolerance | All timed events (22:00:00, 05:45:00, 05:53:00, 06:00:00) fire within $\pm 2$ simulated seconds. | Event queue min-heap assertions using `fake_clock` time progression. | `test/atdd/night_training_scheduler_contracts_test.py` | **PLANNED** |
| **NFR-6** | Queue Determinism & Tie-Breaking | Events at identical instant broken deterministically by monotonic batch `seq`. | Property-based tests via `hypothesis` submitting concurrent identical timestamps. | `test/unit/test_priority_queue.py` | **PLANNED** |
| **NFR-7** | Replay Determinism | Same `(seed, submission_stream)` yields byte-identical SQLite Decision Record log. | Golden fixture replay test comparing SHA-256 hash of exported decision log. | `test/integration/test_determinism_golden.py` | **PLANNED** |
| **NFR-8** | Checkpoint 5-Step Durability Protocol | Checkpoint marked `VERIFIED` only after temp write $\rightarrow$ `fdatasync` $\rightarrow$ atomic rename $\rightarrow$ `fsync(dir)` $\rightarrow$ SHA-256. | Filesystem mock interceptor verifying syscall sequence before DB commit. | `test/integration/test_checkpoint_durability.py` | **PLANNED** |
| **NFR-9** | Real-Time UI State Visibility | State mutations visible to API/console snapshot within $\le 500$ ms real time at all rates (1$\times$ to 1440$\times$). | Pacer drain loop timing assertion with atomic snapshot pointer swap. | `test/benchmarks/benchmark_pacer_visibility.py` | **PLANNED** |
| **NFR-10** | Crash Recovery & Zero Duplication | 0 duplicate transitions and 0 lost transitions after abrupt simulated process crash. | Fault injection harness executing 1000 randomized kills (`sim_telemetry`) and log fold. | `test/integration/test_crash_recovery_1000_kills.py` | **PLANNED** |
| **NFR-11** | Credential & Identity Redaction | 0 tokens, raw passwords, or other student job IDs emitted in stdout logs, error responses, or Decision Records. | Regex log scanner searching for bearer tokens, authorization headers, and cross-actor IDs. | `test/security/test_credential_redaction.py` | **PLANNED** |
| **NFR-12** | CI Execution Performance | Full automated test suite (unit + contract + integration) executes in $\le 60$ seconds. | GitHub Actions CI runner step execution time timer. | `test/ci/quality-gate.yml` | **PLANNED** |
| **NFR-13** | Storage Bound & Graceful Degradation | Store pressure halts new submissions with `STORE_FULL` while never deleting protected verified checkpoints. | Storage fault injector setting virtual capacity limit and checking 03:00 GC. | `test/integration/test_storage_pressure_escalation.py` | **PLANNED** |
| **NFR-14** | Invariant S-1 (Zero Daytime Occupancy) | `allocations_held == 0` across all 32 nodes for student jobs at every minute in `[06:00:00, 22:00:00]`. | Continuous minute-by-minute assertion in simulated 24h cycle, including dawn edge cases. | `test/atdd/night_training_scheduler_contracts_test.py` | **PLANNED** |
| **NFR-15** | UI Contrast & Accessibility | Non-text UI contrast $\ge 3:1$; normal text contrast $\ge 4.5:1$; no information conveyed by hue alone. | Headless Chrome Lighthouse / axe-core audit on server-rendered Jinja templates. | `ux/validation-report.md` | **EVIDENCED** |
| **NFR-16** | Standalone Executability | Module executes standalone via `docker compose up` with zero GPU hardware and zero external network access. | Docker container build and isolated network container run test. | `Dockerfile`, `docker-compose.yml` | **PLANNED** |

---

## 2. Exemplary Evidence Specifications (Workshop Minimums)

### 2.1 Performance NFR (NFR-2)
- **Metric:** p95 latency $< 200$ ms.
- **Workload:** 500 queued jobs evaluated against 33 GPU slots.
- **Fixture:** In-memory SQLite populated via `001_night_training_scheduler_schema.sql` with 500 pending jobs.
- **Measurement Tool:** `pytest-benchmark` taking 50 iterations; CPU profile asserting zero per-job disk I/O.

### 2.2 Reliability / Failure NFR (NFR-10 & Mandatory Edge Case)
- **Metric:** Recovery time $< 1000$ ms; 0 lost and 0 duplicate transitions across 1000 simulated kills.
- **Workload:** Abrupt process crash during 05:45:00 eviction ramp and 22:00:00 activation.
- **Measurement Tool:** `sim_telemetry` injecting SIGKILL; restart folds log prefix up to `last_committed_decision_id` and verifies state vector equality against un-killed control run.

### 2.3 Security / Isolation NFR (NFR-11 & AD-8)
- **Metric:** 0 instances of bearer token or unowned resource disclosure; 100% of unauthorized queries return byte-identical HTTP 404 responses.
- **Measurement Tool:** Pytest parameterized security matrix sending unauthorized student tokens to foreign job endpoints; body and status code diff asserts identical output to non-existent job queries.
