# Night Training Scheduler — Module 9

Single-node night training scheduler for the *Academic AI Compute Fabric*. Students submit training jobs during the day. At 22:00:00 the scheduler places queued jobs onto the simulated 33-GPU-slot campus fleet (31 × 24 GB workstations + 1 × 2 × 48 GB server). No physical GPU is needed.

## Authors

- Juliana Filigrana Valencia
- Juan Manuel Casanova Marin

## Quick start

**Option A: Docker (one command)**

```bash
docker compose up --build                          # API on http://localhost:8000/docs
docker compose --profile test run --rm tests       # run the test suite in a container
```

**Option B: local Python 3.11+**

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows   (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
pytest                            # 44 tests, all green
ruff check src tests              # lint
uvicorn src.main:build_from_env --factory --port 8000
```

No `.env` file is required. Every setting has a default (see `.env.example`). The SQLite database is created and migrated on startup.

### Try it

```bash
curl localhost:8000/api/v1/health
curl -X POST localhost:8000/api/v1/jobs -H "content-type: application/json" -d '{
  "idempotency_key": "demo-1", "actor_id": "student-kavita",
  "spec": {"image_digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
           "gpu_slots_requested": 1, "required_vram_gb": 24, "checkpoint_interval_minutes": 15,
           "estimated_duration_s": 7200, "model_id": "llama-3-8b-instruct", "model_version": "1.0.0",
           "storage_request_bytes": 524288000, "worker_count": 1, "replicas": 1,
           "distributed_artifact_present": false}}'
curl -X POST localhost:8000/api/v1/window/activate -H "content-type: application/json" \
     -d '{"sim_instant": "2026-10-18T22:00:00-05:00"}'
```

## Architecture (Ports & Adapters)

```
src/
├── domain/                 # Pure logic: entities, preconditions, Admission Order, AD-4 placement fold
├── ports/                  # inbound.py (use cases), outbound.py (ClockPort, SchedulerRepositoryPort), dto.py
├── application/            # Use-case services: submitJob, activateWindow (one transaction each)
├── adapters/
│   ├── inbound/http_api.py       # FastAPI routes + ErrorBody mapping
│   └── outbound/                 # sqlite_repository.py, simulated_clock.py
├── config.py               # Environment settings + validation
└── main.py                 # Composition root (create_app / build_from_env)
migrations/                 # 001_night_training_scheduler_schema.sql (+ 32-node / 33-slot fleet seed)
tests/
├── conftest.py             # fake_clock, db (in-memory, migrated), services, HTTP client
├── fixtures/               # fleet.json seed, FakeClock, SimTelemetry, explainability asserts
├── atdd/                   # Solu-2 contract suite (Epic 2 tests marked impl2)
└── unit/                   # BDD-mapped tests for the scaffold and Stories 1.1, 1.2, 1.3
docs/
├── prd.md, contracts/openapi.yaml
├── sprint-status.yaml, ai-decision-log.md, test-evidence-impl1.txt
walkthrough-impl1.md        # Impl-1 implementation walkthrough report
```

The domain layer imports no framework, database or clock. `tests/unit/test_scaffold.py` enforces this with an AST scan (INV-07).

## Repository map

- `planning/`: Plan-2 and Solu-2 specification spine (PRD, ARCHITECTURE.md with AD-1…AD-8, contracts, schemas, epics)
- `ux/`: DESIGN.md, EXPERIENCE.md, scenarios, wireframes
- `reviews/`: adversarial and edge-case reviews with triage
- `ai-log/`: Plan-2 and Solu-2 AI decision logs (the Impl-1 log is `docs/ai-decision-log.md`)
- `docs/source/`: task statements and the university brief
