---
title: "Module 9 — Night Training Scheduler: Task Impl-2 Implementation & Hardening Walkthrough"
status: final
version: "2.0.0"
date: 2026-11-07
authors:
  - "Juliana Filigrana Valencia"
  - "Juan Manuel Casanova Marín"
module: "Module 9 — Night Training Scheduler"
---

# Task Impl-2 Walkthrough Report — Module 9: Night Training Scheduler

This report documents the architectural hardening, multi-flow test execution (Flows A, B, C, D, and E), and empirical verification evidence for **Module 9: Night Training Scheduler** under **Task Impl-2 (Advanced Implementation, Testing Alternatives & System Hardening)**.

---

## 1. Architectural Hardening Summary (Hexagonal Ports & Adapters)

The production codebase implements the exact Hexagonal Architecture specified in `planning/ARCHITECTURE.md` and `planning/detailed-design/ports-and-adapters.md`:

```mermaid
flowchart LR
    subgraph Driving["Driving Adapters (Inbound)"]
        API["FastAPI REST + Kanban UI\n(api/app.py, api/routes/*)"]
        PACER["Simulation Pacer Daemon\n(pacer/daemon.py)"]
    end

    subgraph Inbound["Inbound Use-Case Ports (ports/in/)"]
        SUB["JobSubmissionService"]
        ACT["WindowActivationService"]
        EVI["EvictionService &\nHardEvictionSupervisorService"]
        BRD["PreemptionAndBoardService"]
        SIM["SimulationControlService"]
    end

    subgraph Domain["Pure Core Domain (domain/ — 100% Pure, 0 I/O)"]
        ENT["entities.py"]
        SM["state_machine.py"]
        RNK["ranking.py"]
        ALC["allocation.py"]
        EMT["emitter.py"]
        ENG["engine.py"]
    end

    subgraph Driven["Driven Adapters (adapters/)"]
        SQL["SQLiteRepositoryAdapter\n(BEGIN IMMEDIATE + RLock)"]
        CLK["SimulatedClockAdapter"]
        CKP["FilesystemCheckpointStoreAdapter\n(5-Step SHA-256 Verified)"]
        FLT["SimulatedFleetAdapter\n(31x24GB + 1x2x48GB)"]
    end

    API --> Inbound
    PACER --> Inbound
    Inbound --> Domain
    Inbound --> Driven
```

### Key Hardening Guarantees
1. **Strict Domain Purity (`AD-1` / `INV-07`):** Every module in `domain/` (`entities.py`, `state_machine.py`, `ranking.py`, `allocation.py`, `emitter.py`, `engine.py`) is 100% pure Python with zero framework, database, network, or wall-clock (`time`) imports—enforced automatically by `TestDomainPurityAstGate`.
2. **Atomic SQLite Serialization (`AD-2` / `INV-01`):** `SQLiteRepositoryAdapter` (`adapters/db/sqlite_repository.py`) wraps all state-mutating operations in a re-entrant mutex (`threading.RLock()`) plus SQLite `BEGIN IMMEDIATE` transactions, preventing race conditions or double-allocations under 50-VU concurrent bursts while serving idempotent replays via a lock-free read fast-path with double-checked locking.
3. **Fail-Closed Explainability Emitter (`AD-3` / `INV-05`):** `domain/emitter.py` validates that every `DecisionRecordEntity` carries a non-empty human-readable summary and $\ge 1$ formal rule/policy citation (`self:*`, `policy:M2/*`, `catalog:M5/*`, `health:M6/*`, `quota:M8/*`) before any state transition can commit.
4. **5-Step Checkpoint Durability & Pre-Verification Sweep (`AD-7` / `INV-06`):** `FilesystemCheckpointStoreAdapter` writes temporary `.ckpt.tmp` files, computes SHA-256 digests, atomically renames to `.ckpt`, and verifies byte integrity on sweep—quarantining corrupted files (`state='CORRUPT'`) and failing affected jobs with `CHECKPOINT_CORRUPT`.
5. **Uniform HTTP 404 Access Control (`AD-8` / `NFR-11`):** `PreemptionAndBoardService.get_job_for_actor` returns a byte-identical `404 Not Found` response (`Requested training job resource was not found.`) whether a job ID does not exist or belongs to another student, eliminating existence disclosure (`403 Forbidden` is never returned) while recording an `UNAUTHORIZED_OR_MISSING_JOB_QUERY` audit event.

---

## 2. Multi-Flow Test Pyramid & Coverage Summary (70 / 20 / 10)

| Pyramid Layer | BMad Flows | Test Count | Share (%) | Execution Speed | Target Scope |
|---|---|:---:|:---:|:---:|---|
| **Unit Tests** (`test/unit/test_domain_core.py`) | **Flow B** (Test-Along) & **Flow C** (Test-After) | **61** | **74.4%** | `< 2 ms` per test (in-memory) | Pure domain state machine, 4-key ranking, 33-slot allocation, explainability emitter, crash-recovery log fold, AST purity |
| **Integration & ATDD Tests** (`test/atdd/*`, `test/integration/*`) | **Flow A** (ATDD-First), **Flow B**, **Flow C**, **Flow D** | **20** | **24.4%** | Real ephemeral SQLite DDL | Stories `9.1`–`9.5`, Solu-2 Contracts 1–3, 16-thread preemption contention hammer, uniform 404 RBAC, checkpoint bitrot quarantine |
| **Playwright E2E + k6 NFR Suites** (`test/e2e/*`, `test/nfr/*`) | **Flow E** (Playwright E2E) & **Flow D** (k6 NFR) | **1 E2E Spec + 1 k6 Suite** (`2,611` HTTP reqs) | **1.2%** | `2.1 s` (E2E) / `10.2 s` (k6) | Story 9.6 24-hour time-lapse Kanban board UI (`trace.zip`) & Story 9.5 50-VU HTTP contention burst |
| **Total** | **All 5 Flows (A, B, C, D, E)** | **82 Automated Specs** | **100%** | **100% PASS** | **100.00% Branch Coverage on `domain/`** (`374/374` stmts, `102/102` branches) |

---

## 3. Per-Story Implementation & Testing Breakdown

### 3.1 Foundational Stories (`Story 9.1`, `Story 9.2`, `Story 9.3`) — Flows B & C
- **Story 9.1 (`JobSubmissionService` & `domain/engine.py`):** Validates single-node boundaries (`worker_count == 1`, `replicas == 1`, `distributed_artifact_present == False`), enforces `2-GPU -> 48GB VRAM`, caps active queue depth at `500`, and guarantees SHA-256 payload digest idempotency (`200 OK` on identical replay, `409 IDEMPOTENCY_CONFLICT` on mutated spec).
- **Story 9.2 (`WindowActivationService` & `domain/allocation.py`):** Activates the `22:00:00` night window (within $\pm 2\text{ s}$ tolerance), ranks candidates by `(-effective_priority, -consecutive_nights_missed, submitted_at, job_id)` with $+50$ starvation boost at $\ge 3$ missed nights, atomically places 2-GPU jobs across both slots of `server-gpu-01`, and respects the 33-slot hardware ceiling.
- **Story 9.3 (`EvictionService` & `FilesystemCheckpointStoreAdapter`):** Executes the `05:45:00` graceful checkpoint ramp (`T-7` $\rightarrow$ `T-8`), verifies SHA-256 checkpoint digests (`Story 2.3`), and emits structured `ExplanationDTO` citations.

---

### 3.2 Story 9.4: Pre-Morning Hard Eviction, Checkpointing & Node Cordoning on Failure — Flow A (ATDD-First)

- **Scenario Implemented:** At `05:45:00`, the scheduler dispatches `SIGTERM` + checkpoint instructions to all active training jobs. A rogue student training script (`JOB-ROGUE-0014`) on node `ws-gpu-14` (`10.20.14.88`) gets stuck in an uninterruptible CUDA kernel hang (`simulate_cuda_hang=True`) and fails to flush its checkpoint within the 60-second grace period. At `05:46:00`, `HardEvictionSupervisorService` escalates to `SIGKILL` (`kill -9`), transitions the job to `EVICTED_FORCEFULLY` (`checkpoint_status = 'FAILED_TIMEOUT'`), cordons `ws-gpu-14` as `CORDONED_DIRTY` (`cordon_cause = 'DIRTY_EVICTION_FAILED'`, `alert_dispatched = True`, `residual_gpu_processes = 0`), and hands over **31 of 32 healthy nodes** (with **0 student GPU allocations held**) at `06:00:00` for daytime lab classes.
- **ATDD Red-Phase Execution Log (`test/evidence/atdd-red-story-9.4.log`):** Captured **before** `ports/in/eviction_supervisor.py` existed:

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /mnt/c/Users/juanc/college/9thSemerter/ai-assisted_development_process/night-training-scheduler-planning
configfile: pytest.ini
collected 1 item

test/atdd/test_story_9_4_hard_eviction_atdd.py::TestStory94HardEvictionATDD::test_hanging_training_job_killed_and_node_cordoned_before_morning_classes FAILED [100%]

=================================== FAILURES ===================================
_ TestStory94HardEvictionATDD.test_hanging_training_job_killed_and_node_cordoned_before_morning_classes _
test/atdd/test_story_9_4_hard_eviction_atdd.py:55: in test_hanging_training_job_killed_and_node_cordoned_before_morning_classes
    supervisor_mod = load_inbound_port_module("eviction_supervisor")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ports/__init__.py:15: in load_inbound_port_module
    raise ImportError(f"Inbound port module not found: {file_path}")
E   ImportError: Inbound port module not found: /mnt/c/Users/juanc/college/9thSemerter/ai-assisted_development_process/night-training-scheduler-planning/ports/in/eviction_supervisor.py
=========================== short test summary info ============================
FAILED test/atdd/test_story_9_4_hard_eviction_atdd.py::TestStory94HardEvictionATDD::test_hanging_training_job_killed_and_node_cordoned_before_morning_classes - ImportError: Inbound port module not found
============================== 1 failed in 1.15s ===============================
```

- **Green-Phase Verification:** After implementing `ports/in/eviction_supervisor.py`, `test_hanging_training_job_killed_and_node_cordoned_before_morning_classes` passes in `< 15 ms` with zero `sleep()` calls.

---

### 3.3 Story 9.5: Dynamic Priority Queue Preemption Cascade Under Heavy Contention — Flow D (Quality Gate / NFR)

- **Scenario Implemented:** During a 100% saturated night window (`23:10:00`, all 31 workstation GPUs occupied by `RUNNING` jobs, including 12 Priority 1 `EXPLORATION` jobs), Kavita submits a Priority 10 `THESIS` fine-tuning job (`1x 24GB VRAM`). `select_preemption_victim` in `domain/ranking.py` deterministically selects the lowest-priority running job with the earliest completed checkpoint (`JOB-EXP-0006` on `ws-gpu-06`, checkpointed at `22:45:00`), writes a verified preemption checkpoint, transitions the victim to `QUEUED_PREEMPTED` preserving its original `submitted_at` timestamp, and atomically assigns `ws-gpu-06` to Kavita's job (`RUNNING`) with `0` orphaned GPU processes.
- **Concurrency Contention Hammer (`test_concurrent_preemption_hammer_zero_double_allocation`):** Fires 8 simultaneous Priority 10 `THESIS` challengers across a `ThreadPoolExecutor(max_workers=8)` against a saturated cluster; verifies that all 8 challengers land on 8 distinct victim nodes (`ws-gpu-01`..`ws-gpu-08`) with zero `sqlite3.OperationalError` lock failures and zero double-allocations.
- **`k6` Load & Contention Burst Results (`test/nfr/scheduler-preemption-burst.js` $\rightarrow$ `test/evidence/k6-nfr-story-9.5.log`):**

| Metric | NFR Threshold | Measured Result (`k6 v0.54.0`) | Verdict |
|---|:---:|:---:|:---:|
| **Total HTTP Requests (`http_reqs`)** | Burst up to 50 VUs | **2,611 requests** (`254.77 req/s`) | **PASS** |
| **Functional Assertions (`checks`)** | `100.00%` | **100.00%** (`5,221 / 5,221` passed) | **PASS** |
| **Error Rate (`http_req_failed`)** | `0.00%` | **0.00%** (`0` failed out of `2,611`) | **PASS** |
| **Median Latency ($p_{50}$)** | — | **1.13 ms** | **PASS** |
| **90th Percentile Latency ($p_{90}$)** | — | **2.52 ms** | **PASS** |
| **95th Percentile Latency ($p_{95}$)** | `< 50.00 ms` | **8.52 ms** ($5.8\times$ faster than target) | **PASS** |

---

### 3.4 Story 9.6: Fast-Forward 24-Hour Time-Lapse Scheduler Status Board E2E — Flow E (Playwright E2E + POM + Forensic Trace)

- **Scenario Implemented:** An interactive Kanban Scheduler Status Board (`/admin/scheduler-board` & `/board`) with a simulated cluster clock (`data-testid="cluster-clock"`), time scrubber, speed multiplier controls (`1x`, `10x`, `60x`), and deterministic time-warp buttons (`Fast-Forward to 22:00` and `Advance to 06:00`).
- **Page Object Model (`test/e2e/pages/SchedulerDashboardPage.ts`):** Encapsulates all `data-testid` locators (`clusterClock()`, `queuedJobCards()`, `runningJobCards()`, `completedOrEvictedJobCards()`, `idleNodeCards()`) and actions (`fastForwardTo2200()`, `advanceTo0600()`, `setSpeedMultiplier()`).
- **Playwright Spec (`test/e2e/scheduler-board.spec.ts`):** Uses strictly web-first auto-retrying assertions (`await expect(...).toHaveText()`, `await expect(...).toHaveCount()`) with **zero `waitForTimeout()` calls**:
  1. At `14:00`: Verifies `5` jobs in **Queued** (`0` Running, `0` Completed/Evicted).
  2. Clicks `Fast-Forward to 22:00`: Verifies clock updates to `22:00` and all `5` jobs transition to **Running** (`0` Queued).
  3. Clicks `Advance to 06:00`: Verifies clock updates to `06:00`, all `5` jobs transition to **Completed / Evicted** (`3` `Completed` + `2` `Evicted` with saved checkpoints), and all **32 cluster nodes** display `IDLE`.
- **Playwright Execution Log (`test/evidence/playwright-e2e-story-9.6.log`):**

```text
Running 1 test using 1 worker

  ✓  1 [chromium] › test\e2e\scheduler-board.spec.ts:15:7 › Story 9.6 — Fast-Forward 24-Hour Time-Lapse Scheduler Status Board E2E › simulates 14:00 -> 22:00 -> 06:00 lifecycle with zero hardcoded sleeps (2.1s)

  1 passed (3.9s)
```

- **Forensic Trace Artifact Confirmation:**
  - Saved at: `test-results/scheduler-board-Story-9-6--1b650-ed-night-window-execution-chromium/trace.zip`
  - Inspectable via: `npx playwright show-trace test-results/scheduler-board-Story-9-6--1b650-ed-night-window-execution-chromium/trace.zip`

---

## 4. Complete Pytest & Coverage Terminal Output (`test/evidence/pytest-coverage.log`)

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /mnt/c/Users/juanc/college/9thSemerter/ai-assisted_development_process/night-training-scheduler-planning
configfile: pytest.ini
testpaths: test
collected 81 items

test/atdd/night_training_scheduler_contracts_test.py .................... [ 18%]
test/atdd/test_story_9_4_hard_eviction_atdd.py .                          [ 19%]
test/integration/test_concurrency_and_stories.py ....                     [ 24%]
test/unit/test_domain_core.py ........................................... [ 77%]
..................                                                        [100%]

================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________

Name                      Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------
domain/__init__.py            0      0      0      0   100%
domain/allocation.py         58      0     26      0   100%
domain/emitter.py            10      0      4      0   100%
domain/engine.py            126      0     42      0   100%
domain/entities.py          113      0      0      0   100%
domain/ranking.py            28      0     12      0   100%
domain/state_machine.py      39      0     18      0   100%
---------------------------------------------------------------------
TOTAL                       374      0    102      0   100%
Required test coverage of 90.0% reached. Total coverage: 100.00%
======================== 81 passed, 1 warning in 17.43s ========================
```
