---
title: "Module 9 — Night Training Scheduler: Risk-Based Test Design (TEA Step 3.1)"
status: final
version: "1.0.0"
created: 2026-10-18
authors:
  - "Juliana Filigrana Valencia (Test Lead)"
  - "Juan Manuel Casanova Marín (Reviewer)"
module: "Module 9 — Night Training Scheduler"
framework: "BMad TEA (Test Engineering Architecture)"
---

# Risk-Based Test Design & Strategy (BMad TEA)
## Module 9: Night Training Scheduler

---

## 1. Risk Register (P0–P3 Prioritization)

The risk register evaluates architectural, operational, and concurrency risks. Per workshop rules, the **Mandatory Edge Case** (dawn checkpoint failure and node isolation) is classified as **P0**.

| Risk ID | Hazard / Risk Description | Probability (1–3) | Impact (1–3) | Risk Score (P $\times$ I) | Priority | Mitigating Contract / Architectural Invariant | Target Test Suite |
|---|---|:---:|:---:|:---:|:---:|---|---|
| **RSK-01** | **Mandatory Edge Case: Dawn Checkpoint Failure.** At 05:45:00–05:53:00, checkpoint write times out, throws I/O exception, or corrupts digest, causing GPU slots to remain allocated past 06:00:00 (breaching Invariant S-1 and NFR-14 daytime lab lock). | 3 | 3 | **9** | **P0** | `evictAtDeadline` contract (`Q-fail`), `AD-1`, `AD-4`, `AD-7`, `Invariant S-1`, `INV-02`, `INV-05`. | `test_allocations_held_is_zero_at_0600_after_checkpoint_failure` |
| **RSK-02** | **Queue Cap Overflow under Concurrent Bursts.** Concurrent job submissions race past the `< 500` count check before commit, admitting more than 500 non-terminal jobs into the system. | 3 | 3 | **9** | **P0** | `submitJob` contract (`P5`), `AD-1`, `INV-01`, SQLite `BEGIN IMMEDIATE` + partial index `idx_active_jobs_state`. | `test_submit_job_rejects_when_queue_depth_reaches_500` |
| **RSK-03** | **Two-GPU Job Partial / Invalid Allocation.** 2-GPU job admitted on 24 GB node or stranding 1 slot of `server-gpu-01` past 06:00:00. | 3 | 3 | **9** | **P0** | `submitJob` contract (`P2`), `AD-4`, `FR-2(k)`, `INV-03` (`check_two_gpu_requires_48gb`). | `test_two_gpu_job_rejected_on_24gb_workstation` |
| **RSK-04** | **Torn State / Decision Record Decoupling on Crash.** Host process dies after database state update but before `DecisionRecord` commit, producing untracked or duplicated state transitions. | 2 | 3 | **6** | **P0** | `AD-2`, `AD-3`, `INV-04`, atomic SQLite WAL commit batching state mutation and decision rows together. | `test_crash_after_record_write_leaves_zero_orphaned_state_mutations` |
| **RSK-05** | **Corrupt Checkpoint Resume.** Job admitted to resume from a checkpoint whose SHA-256 digest on disk does not match the stored database digest. | 2 | 3 | **6** | **P1** | `AD-7`, `Invariant S-2`, `INV-06`, pre-verification sweep at 21:30:00. | `test_checkpoint_digest_mismatch_quarantines_file_and_fails_job` |
| **RSK-06** | **Window Activation Latency Budget Breach.** Sorting 500 jobs and computing Admission Order at 22:00:00 exceeds 200 ms p95 (NFR-2). | 2 | 2 | **4** | **P1** | `activateWindow` contract, `AD-2`, pure in-memory fold with zero per-job SQL queries. | `test_window_activation_latency_under_200ms_for_500_jobs` |
| **RSK-07** | **Authentication Oracle & Identifier Enumeration.** Returning HTTP 403 vs 404 allows unauthorized users to enumerate valid student job IDs. | 2 | 2 | **4** | **P2** | `AD-8`, uniform HTTP 404 responses for unauthorized resource queries. | `test_unauthorized_job_access_returns_404_not_403` |
| **RSK-08** | **Pacer Fast-Forward Clock Quantization Drop.** Running simulation at 1440$\times$ skips the 05:45:00 eviction ramp or 22:00:00 activation. | 2 | 2 | **4** | **P2** | `AD-1`, discrete event priority queue ordered by `(sim_instant, seq)`. | `test_pacer_1440x_never_skips_eviction_instant` |

---

## 2. Test Level Allocation

To maximize execution velocity, deterministic repeatability, and test isolation, test cases are strictly partitioned across architectural levels. In alignment with BMad TEA standards, **pure domain unit tests comprise the largest share**.

```
           / \
          / E2E \        (UI Scenario Smoke: 5%)
         /-------\
        /   API   \      (HTTP Route / DTO Validation: 15%)
       /-----------\
      / Integration \    (SQLite Adapter + Checkpoint Store: 20%)
     /---------------\
    /   Pure Domain   \  (Pure Reducer, State Guards, Ranking: 60%)
   /-------------------\
```

| Test Level | Scope & Target Components | Execution Mode & Dependencies | Allocation Share |
|---|---|---|:---:|
| **Pure Domain Unit** | `domain/engine.py`, `domain/state_machine.py`, `domain/ranking.py`, `domain/allocation.py`, `domain/emitter.py` | In-memory, zero I/O, zero network, zero wall-clock (injected `fake_clock` only) | **60%** |
| **Contract / Integration** | `adapters/db/sqlite_repository.py`, `adapters/sim/filesystem_checkpoint_store.py` | In-memory SQLite (`:memory:`) or ephemeral file, real 5-step filesystem rename | **20%** |
| **API Boundary** | `api/routes/jobs.py`, `api/routes/board.py`, `api/routes/simulations.py` | FastAPI `TestClient`, Pydantic DTO validation, HTTP status assertions | **15%** |
| **E2E Scenario Smoke** | Full simulated night run (`22:00:00` to `06:00:00`) | Driving adapter pacer, scripted telemetry fault generator | **5%** |

---

## 3. Quality & Coverage Thresholds

1. **P0 Risk Gate:** 100% of P0 risks (RSK-01 through RSK-04) must be bound to $\ge 1$ executable red-phase ATDD contract test.
2. **Domain Coverage Target:** Line coverage for `domain/` must be $\ge 90\%$; branch coverage $\ge 85\%$.
3. **Physical Invariant Verification:** 100% of invariants (INV-01 through INV-08) must have an automated test that turns RED if the physical guard or DB constraint is removed.
4. **Anti-Tautology Rule:** Zero tests may contain `assert True`, empty function bodies, or assertions evaluated against self-configured mock values. Every test must assert on return DTO schemas, database state predicates, emitted audit events, and verifiable non-effects (`Q-fail`).

---

## 4. Testability Feedback & Architecture Cross-Check

- **Deterministic Time:** Injected via `FakeClockPort` (`adapters/sim/simulated_clock.py`) allowing advanceable simulated time without `time.sleep()`.
- **Fleet Seeding:** Seed fixture initializes exactly 31 workstations (`ws-gpu-01..31`) and 1 dual-GPU server (`server-gpu-01`), matching PRD §1 and `001_night_training_scheduler_schema.sql`.
- **Fault Injection:** `sim_telemetry` fixture supports injecting deterministic disk I/O errors and simulated heartbeat drops at specified instants.
