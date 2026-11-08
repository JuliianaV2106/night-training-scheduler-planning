# Night Training Scheduler — Module 9
## Academic AI Compute Fabric (Impl-1 & Impl-2)

Single-node night training scheduler for the *Academic AI Compute Fabric*. Students submit training jobs during the day. At 22:00:00 the scheduler places queued jobs onto the simulated 33-GPU-slot campus fleet (31 × 24 GB workstations + 1 × 2 × 48 GB server). Complete Hexagonal Architecture implementation, multi-flow automated test suite (**Flows A, B, C, D, E**), and system hardening.

## Authors

- **Juliana Filigrana Valencia** (Impl-1 Lead)
- **Juan Manuel Casanova Marín** (Impl-2 Lead)

---

## Key Deliverables

### Task Impl-2 (Hardened System, Multi-Flow Testing & Kanban Board)
1. **Hardened Hexagonal Source Code:**
   - [`domain/`](domain/) — 100% pure core domain engine (`entities.py`, `state_machine.py`, `ranking.py`, `allocation.py`, `emitter.py`, `engine.py`) with **100.00% branch coverage** and zero forbidden I/O or wall-clock imports.
   - [`ports/in/`](ports/in/) & [`ports/out/`](ports/out/) — Inbound use-case services (`job_submission.py`, `window_activation.py`, `eviction.py`, `eviction_supervisor.py`, `board_query.py`, `simulation_control.py`) and outbound port protocols.
   - [`adapters/db/`](adapters/db/) & [`adapters/sim/`](adapters/sim/) — `SQLiteRepositoryAdapter` (`BEGIN IMMEDIATE` + `RLock` atomic transactions), `SimulatedClockAdapter`, `FilesystemCheckpointStoreAdapter` (5-step SHA-256 durability), `SimulatedFleetAdapter` (31×24GB + 1×2×48GB).
   - [`api/`](api/) & [`pacer/`](pacer/) — FastAPI REST endpoints, interactive Kanban Status Board (`/admin/scheduler-board`), presentation deck (`/presentation`), and discrete-event simulation pacer daemon.
2. **Multi-Flow Automated Test Suite (70 / 20 / 10 Pyramid):**
   - **Unit Suite (74.4% — 61 tests):** [`test/unit/test_domain_core.py`](test/unit/test_domain_core.py)
   - **Flow A (ATDD-First — Story 9.4):** [`test/atdd/test_story_9_4_hard_eviction_atdd.py`](test/atdd/test_story_9_4_hard_eviction_atdd.py) + Red-phase log [`test/evidence/atdd-red-story-9.4.log`](test/evidence/atdd-red-story-9.4.log) + Solu-2 contracts [`test/atdd/night_training_scheduler_contracts_test.py`](test/atdd/night_training_scheduler_contracts_test.py)
   - **Flow B & Flow C (Integration — Stories 9.1–9.5, 2.3, 4.3):** [`test/integration/test_concurrency_and_stories.py`](test/integration/test_concurrency_and_stories.py)
   - **Flow D (Quality Gate / NFR & `k6` Load Burst — Story 9.5):** [`test/nfr/scheduler-preemption-burst.js`](test/nfr/scheduler-preemption-burst.js) + evidence [`test/evidence/k6-nfr-story-9.5.log`](test/evidence/k6-nfr-story-9.5.log) ($p_{95} = 8.52\text{ ms}$, `0.00%` error rate)
   - **Flow E (Playwright E2E with POM & Forensic Trace — Story 9.6):** [`test/e2e/pages/SchedulerDashboardPage.ts`](test/e2e/pages/SchedulerDashboardPage.ts), [`test/e2e/scheduler-board.spec.ts`](test/e2e/scheduler-board.spec.ts), and forensic `trace.zip` in [`test-results/`](test-results/)
3. **Governance & Traceability Artifacts:**
   - **Sprint Status (`done`):** [`sprint-status.yaml`](sprint-status.yaml) & [`implementation-artifacts/sprint-status.yaml`](implementation-artifacts/sprint-status.yaml)
   - **Traceability Matrix:** [`traceability-matrix.md`](traceability-matrix.md) & [`test/traceability-matrix.md`](test/traceability-matrix.md)
   - **Implementation Walkthrough Report:** [`walkthrough-impl2.md`](walkthrough-impl2.md)
   - **AI Decision Log:** [`ai-decision-log.md`](ai-decision-log.md) & [`ai-log/decision-log.md`](ai-log/decision-log.md)

### Task Impl-1 (Scaffold, Stories 1.1–1.3 & Initial Contracts)
- [`src/`](src/) — Initial ports, adapters, application services, and domain policies.
- [`tests/`](tests/) — Initial unit tests and Solu-2 ATDD contracts.
- [`walkthrough-impl1.md`](walkthrough-impl1.md) — Impl-1 implementation walkthrough report.
- [`docs/`](docs/) — OpenAPI contracts, Impl-1 story inspections, and PRD.

---

## Quick Verification Commands

### 1. Run Impl-2 Multi-Flow Test Suite (100.00% Domain Branch Coverage)
```bash
PYTHONPATH=.:planning/detailed-design/schemas .venv/bin/pytest test/ --cov=domain --cov-branch --cov-report=term-missing -v
```

### 2. Run Playwright E2E Time-Lapse Suite (Story 9.6 + Forensic `trace.zip`)
```bash
npx playwright test
```

### 3. Run `k6` NFR Concurrency & Preemption Burst Suite (Story 9.5)
```bash
k6 run test/nfr/scheduler-preemption-burst.js
```

### 4. Start Interactive Kanban Status Board & Presentation Deck
```bash
PYTHONPATH=.:planning/detailed-design/schemas .venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8000
# Visit http://127.0.0.1:8000/admin/scheduler-board or http://127.0.0.1:8000/presentation
```

### 5. Docker (Impl-1 baseline)
```bash
docker compose up --build
docker compose --profile test run --rm tests
```
