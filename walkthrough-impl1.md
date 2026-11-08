# Implementation Walkthrough — Impl-1 (Module 9: Night Training Scheduler)

**Scope:** Scaffold foundation + Stories 1.1, 1.2, 1.3 (Epic 1, *Walking Skeleton*).
**Result:** `pytest` reports **44 passed, 0 failed, 0 skipped** (5 Epic 2 contract tests deselected, see §5). `ruff check` passes clean.
**Full evidence:** [`docs/test-evidence-impl1.txt`](docs/test-evidence-impl1.txt).

---

## 1. Architecture and directory layout

Hexagonal (Ports & Adapters), following `planning/detailed-design/ports-and-adapters.md`:

```
HTTP (FastAPI)            ──▶ ports/inbound.py ──▶ application/*  ──▶ domain/* (pure)
adapters/inbound/http_api.py                         │
                                                     └──▶ ports/outbound.py ◀── adapters/outbound/
                                                          (ClockPort,             sqlite_repository.py
                                                           SchedulerRepositoryPort) simulated_clock.py
```

| Layer | Files | Rule enforced |
|---|---|---|
| Domain | `src/domain/entities.py`, `errors.py`, `policies.py`, `scheduling.py` | No FastAPI, Pydantic, sqlite3, `time`, `random`, or `.now()`. Checked by `test_domain_layer_imports_no_framework_io_or_clock` (INV-07). |
| Ports | `src/ports/inbound.py`, `outbound.py`, `dto.py` | DTOs are copied verbatim from Solu-2 `schemas/dto.py`. Protocols only. |
| Application | `src/application/job_submission.py`, `window_activation.py` | One repository transaction per use case. A failure rolls everything back (AD-2, INV-04). |
| Inbound adapter | `src/adapters/inbound/http_api.py` | Routes and status codes are exactly those in `docs/contracts/openapi.yaml`. Every error is an `ErrorBody`. |
| Outbound adapters | `src/adapters/outbound/sqlite_repository.py`, `simulated_clock.py` | `sqlite3` is used only here. Migrations are tracked with `PRAGMA user_version`. |
| Composition root | `src/main.py`, `src/config.py` | App factory. Startup refuses a fleet that is not 32 nodes / 33 slots. Settings are validated (offset `-05:00`, log level). |

**Scaffold checklist:** migrations (`migrations/001_…sql`), config management (`.env.example`, `src/config.py`), simulated fleet fixtures (`tests/fixtures/fleet.json`, seeded by the migration and cross-checked by a test), dependency validation (`verify_fleet_seed`), health probe (`GET /api/v1/health`), and a one-command run (`docker compose up --build`).

### Ceremony justification (Two-Sentence Rule)

None of the three stories can be summarised as a compact change. 1.1 creates the `jobs`, `decision_records` and `audit_events` write paths and the public `POST /jobs` contract. 1.2 defines the module boundary with Module 10. 1.3 introduces the AD-4 placement algorithm that every later epic depends on. In each case the blast radius covers shared tables and public contracts, so the **Full Ceremony was mandatory**.

---

## 2. Story 1.1 — Job Submission Ingress & Validation Skeleton

- **Goal:** Kavita submits a single-node job with an idempotency key. It is validated and queued for the next window, with no risk of duplicates.
- **Contract endpoint:** `POST /api/v1/jobs` returns `201` (new job), `200` (idempotent replay), `409 IDEMPOTENCY_CONFLICT`, `422 VALIDATION_FAILED | TWO_GPU_REQUIRES_48GB | MAX_NIGHT_SPAN_EXCEEDED`, or `429 QUEUE_CAP_EXCEEDED`.
- **Database changes:** one transaction inserts one `jobs` row (`QUEUED_PENDING_WINDOW`, counters at 0), one `decision_records` row (`ADMIT`, `T-1`, citing `self:JOBSPEC-VALIDATION-v1`, `policy:M2/night-window@v1`, `catalog:M5/{model}@{version}`), and one `audit_events` row (`JOB_SUBMITTED`). On any precondition failure nothing is written (Q-fail).
- **Key decisions:** `payload_digest` is SHA-256 over canonical sorted-key JSON. `job_id` follows the `JOB-NNNN` pattern. The domain re-checks P2 even after Pydantic has validated the input, so it never trusts the adapter.
- **Tests:** `tests/unit/test_story_1_1_job_submission.py` (11) + ATDD `TestSubmitJobContract` (5).

## 3. Story 1.2 — Single-Node Scope Boundary Enforcement

- **Goal:** distributed specs are rejected immediately, so they never occupy workstation slots.
- **Contract endpoint:** `POST /api/v1/jobs` returns `400 OUT_OF_SCOPE_DISTRIBUTED` when `worker_count > 1`, `replicas > 1`, or `distributed_artifact_present`. The message routes the user to Module 10, and the explanation cites `self:SCOPE-BOUNDARY-v1`.
- **Database changes:** none, by design. The check runs before any read or write, and the tests assert zero rows in `jobs`, `decision_records` and `audit_events`. A rejected spec does not consume its idempotency key.
- **Tests:** `tests/unit/test_story_1_2_scope_boundary.py` (5, including 3 parametrised variants) + ATDD `…distributed_spec_rejected_with_zero_state_mutation`.

## 4. Story 1.3 — Night Window Activation at 22:00:00 & Deterministic Allocation Fold

- **Goal:** at 22:00:00 every queued job is ranked deterministically and placed on an eligible GPU slot.
- **Contract endpoint:** `POST /api/v1/window/activate` returns `200 WindowActivationResult`, `400 WINDOW_ACTIVATION_OUTSIDE_WINDOW` (outside 22:00:00 ± 2 s, malformed or naive instant), or `503 DELEGATE_UNAVAILABLE` (fleet is not 32 nodes / 33 slots).
- **Algorithm (pure, `src/domain/scheduling.py`):**
  - Admission Order: `effective_priority` desc, then `consecutive_nights_missed` desc, then `submitted_at` asc, then `job_id` asc.
  - Node choice (AD-4): prior node first, then lowest `allocations_held`, then `node_id` asc.
  - A 2-GPU job takes both `server-gpu-01` slots or none (INV-03).
  - With no statically eligible node the job is deferred with `T-4a NO_ELIGIBLE_NODE`. With eligible nodes that are all full it is deferred with `T-4b CAPACITY_EXHAUSTED`.
- **Database changes:** in one transaction, sets `gpu_slots.allocated_job_id` / `held_since`, moves jobs to `RUNNING` with `allocated_node_id` and `admitted_nights + 1`, writes one Decision Record per job (`ADMIT T-3/T-12` with rank, `won_on` and `candidates_considered`, or `DEFER T-4a/T-4b`) citing `policy:M2/night-window@v1` and `self:ADMISSION-RANKING-v1`, and writes one `WINDOW_ACTIVATED` audit event. A repeated activation for the same night returns the recorded result without writing anything new.
- **Tests:** `tests/unit/test_story_1_3_window_activation.py` (13) + ATDD `TestActivateWindowContract` (5).

> **Resolved contradiction:** under AD-4 the first 1-GPU job lands on `server-gpu-01`, because `"server-gpu-01" < "ws-gpu-01"`. The Story 1.3 Gherkin in `planning/epics.md` expected `ws-gpu-01..05`. AD-4 is an explicit, reviewed architectural decision, so the Gherkin was amended to match it. Each `T-3` record now also states which AD-4 key won (`won_on`). See `docs/ai-decision-log.md` #6 and #13.

---

## 5. Test execution evidence

```
$ pytest
collected 49 items / 5 deselected / 44 selected
tests/atdd/night_training_scheduler_contracts_test.py ..........   [ 22%]
tests/unit/test_scaffold.py .....                                   [ 34%]
tests/unit/test_story_1_1_job_submission.py ...........             [ 59%]
tests/unit/test_story_1_2_scope_boundary.py .....                   [ 70%]
tests/unit/test_story_1_3_window_activation.py .............        [100%]
====================== 44 passed, 5 deselected in 1.71s =======================

$ ruff check src tests
All checks passed!
```

The 5 deselected tests are the Solu-2 red-phase contracts for **Epic 2** (`evictAtDeadline` and the Mandatory Edge Case). They are marked `impl2` and deselected through `pytest.ini`, not skipped, so `pytest -m impl2` still runs them, and they fail for the right reason (`NotImplementedError`) until Impl-2.

**Manual smoke run** (`uvicorn src.main:build_from_env --factory`): `GET /health` returned 200, `POST /jobs` returned 201 `JOB-0001`, and `POST /window/activate` returned 200 with a placement on `server-gpu-01` and decision `DEC-ACT-20261018-JOB-0001`.

## 6. Known gaps (planned for Impl-2)

- `submitJob` P4 (M1 entitlement, M5 catalog, M8 quota fixtures) and P6 (checkpoint store budget) are not implemented yet.
- There is no pacer daemon: the simulated clock is fixed by `SIM_START_INSTANT`, and activation takes its instant from the request body.
- Dawn eviction and the Mandatory Edge Case (Epic 2), and preemption, starvation and crash recovery (Epics 3–4).
- `JOB-NNNN` ids overflow above 9999 jobs, which needs a decision when retention (T-15) is implemented.
