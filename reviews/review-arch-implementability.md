---
title: "Module 9 — Night Training Scheduler: Architecture Implementability Review (Phase 0)"
status: triaged
created: 2026-10-18
reviewer: "bmad-review-adversarial (AI) · Triaged & Certified by Juan Manuel Casanova Marín & Juliana Filigrana Valencia"
module: "Module 9 — Night Training Scheduler"
verdict: ACCEPTED_WITH_ACTIONS
---

# Architecture Implementability Review (Phase 0)
## Module 9: Night Training Scheduler

**Goal:** Convert Plan-2's `ARCHITECTURE.md` from "approved" to "buildable" by systematically detecting everything that is not yet decided or where an autonomous developer or AI agent would be forced to invent architectural, schema, or error-handling decisions.

---

### 1. Core Operations Selected (Step 0.1)

In alignment with the seed specifications from Unit 4 Annex A and the mandatory requirements from Plan-2 (`planning/prd.md` and `planning/ARCHITECTURE.md`), the 3 core operations chosen for contract derivation and physical enforcement are:

| # | Core Operation Signature | Category & Risk Profile | Mandatory Requirement Covered |
|---|---|---|---|
| **1** | `submitJob(spec: JobSpecDTO, at: ClockInstant) -> JobSubmissionResultDTO` | **Mutation under Concurrency / Race Hazard** | Idempotency key (`idempotency_key` + SHA-256 payload digest), concurrent submission under global 500-job cap (AD-1), short-circuiting multi-worker distributed specs (FR-3), field-level validation (FR-2). |
| **2** | `activateWindow(clock: ClockPort) -> WindowActivationResultDTO` | **Automated Explainable Decision** | Deterministic Admission Order computation at 22:00:00 (FR-8, FR-14, FR-15), total node allocation ordering over 33 GPU slots (AD-4), emitting auditable `DecisionRecord` payloads with mandatory citations and zero elastic terms. |
| **3** | `evictAtDeadline(at: ClockInstant) -> EvictionResultDTO` | **Time-Critical State Machine & Mandatory Edge Case** | Dawn eviction ramp at 05:45:00, 5-step checkpoint protocol (AD-7), handling timeout/failure at 05:53:00 / 06:00:00 by cordoning node via M3, alerting user, immediately releasing slots to guarantee `allocations_held == 0` at 06:00:00 (Invariant S-1, NFR-14). |

---

### 2. Architecture Gap Audit Table (Step 0.2)

The following table records the implementability gaps identified in `planning/ARCHITECTURE.md`, showing the exact ambiguity, the failure mode if an agent invented the decision, the target resolution phase, and the pair assignment.

| # | Gap in `ARCHITECTURE.md` (What is decided by "nothing") | Example: Where an AI / Dev Agent would invent a decision | Resolved in Phase | Owner | Triage Status | Technical Rationale & Action Plan |
|---|---|---|---|---|---|---|
| **GAP-01** | **Absence of a machine-readable Typed Error Catalog with HTTP status codes and retry flags.** PRD §6.4 has transition reasons (`REJECTED`, `FAILED`), but no typed error structures exist for input/precondition violations. | An agent would invent arbitrary JSON bodies (e.g. `{"error": "invalid"}` vs `{"detail": "bad request"}`) and pick random HTTP codes (400 vs 422 vs 409). | **Phase 1** | Juan Manuel Casanova Marín | **ACCEPT** | Define a shared Typed Error Catalog in `planning/detailed-design/contracts.md` mapping every error code (`CODE`), HTTP status, trigger, explanation template, and boolean `retryable` flag. |
| **GAP-02** | **No concrete DDL physical constraints in SQLite for atomic 2-GPU slot allocation (`AD-4`) and state enum enforcement.** `ARCHITECTURE.md` specifies slots conceptually but provides no SQL schema. | An agent would write naive Python `if slot.is_free: allocate()`, creating a race condition and risking stranding one slot of `server-gpu-01`. | **Phase 2** | Juan Manuel Casanova Marín | **ACCEPT** | Author `001_night_training_scheduler_schema.sql` with `CHECK` constraints, foreign keys, unique active allocation partial indexes, and conditional `UPDATE ... WHERE ... RETURNING` statements. |
| **GAP-03** | **Undefined Hexagonal Port Interfaces (Protocols/ABCs) for Inbound Use-Cases and Outbound Adapters.** Layers are named in diagrams, but no code-level boundaries are typed. | An agent would import FastAPI requests, SQLite drivers, or `datetime.now()` directly inside `domain/`, destroying domain purity and testability. | **Phase 2** | Juan Manuel Casanova Marín | **ACCEPT** | Generate `planning/detailed-design/ports-and-adapters.md` defining strict inbound (`ports/in/`) and outbound (`ports/out/`) Python Protocol signatures with zero framework dependencies in domain. |
| **GAP-04** | **Unspecified Test Fixtures Harness for Deterministic Hardware-Agnostic Simulation.** No concrete contract for `fake_clock`, `seed_fleet`, `sim_telemetry`, `db`, and `explain_assert`. | An agent would write flaky tests using `time.sleep()`, tautological mocks (`assert True`), or unseeded random state, invalidating NFR-7 (determinism). | **Phase 3** | Juliana Filigrana Valencia | **ACCEPT** | Author `test/test-design.md` and concrete fixture scaffolds in `test/fixtures/` with an advanceable deterministic clock and scripted fault generator. |
| **GAP-05** | **Missing Machine-Enforceable Behavioral Specification for Mandatory Edge Case (Dawn Checkpoint Failure).** Transition exists in PRD, but postconditions for non-effects and cordon payload are informal. | An agent would allow the GPU allocation to linger past 06:00:00 while retrying the failed checkpoint, violating Invariant S-1 and NFR-14. | **Phase 1 & Phase 3** | Juliana Filigrana Valencia | **ACCEPT** | Formally define the `evictAtDeadline` contract in `contracts.md` with explicit non-effects (`Q-fail`, zero slots held at 06:00:00) and link to a dedicated P0 red ATDD test. |
| **GAP-06** | **Lack of Concrete DTOs and Data Serialization Schemas for API routes and Event Contracts.** Conceptual models in §4.2 lack strict Pydantic definitions and timezone validations. | An agent would use raw dicts or permit timezone drift (e.g. UTC `Z` instead of `America/Bogota` UTC-05:00 offset per D-1). | **Phase 2** | Juan Manuel Casanova Marín | **ACCEPT** | Author `planning/detailed-design/schemas/dto.py` with Pydantic v2 models, primitive types, strict timezone validation, and corresponding `openapi.yaml`. |
| **GAP-07** | **In-Memory Heap Memory Bound Unspecified Under Ingress Bursts.** AD-1 specifies a 500-job cap at admission `T-1`, but does not bound raw pending events before drain. | An agent would use an unbounded `asyncio.Queue` or list that exhausts process RAM under rapid simulation or stress testing. | **Phase 2** | Juan Manuel Casanova Marín | **ACCEPT** | Bound the inbound event queue at the Driving Adapter layer with a fixed capacity and explicit drop/backpressure policy emitting `STORE_FULL` or `RATE_LIMITED`. |
| **GAP-08** | **No Formal Traceability Matrix linking PRD requirements and risks to executable ATDD test IDs and Stories.** | Stories would be created without verified bindings to AD invariants or without failing red tests, allowing regression. | **Phase 3 & Phase 4** | Juliana Filigrana Valencia | **ACCEPT** | Produce `test/traceability-matrix.md` with 100% of P0 risks and AD-n invariants traced forward to test IDs and story IDs. |

---

### 3. Stack Declaration Summary (Step 0.3)

Recorded and verified in `planning/ARCHITECTURE.md` §1.3.1:
1. **Language & Runtime:** Python 3.12+ (CPython, fully type-annotated).
2. **Web Framework:** FastAPI (ASGI via Uvicorn, OpenAPI 3.0 at `/docs`, Jinja2/HTMX for server-rendered console).
3. **Persistence Engine:** SQLite 3 (`sqlite3` standard library, WAL journal mode, `synchronous=FULL`, single long-lived writer).
4. **Test Framework:** pytest (with `pytest-asyncio` and `hypothesis` for property-based invariant testing).
5. **Time Injection:** `ClockPort` / `SimulatedClockPort` (explicit `sim_instant: datetime` with `America/Bogota` UTC-05:00 offset injected into all domain calls; zero direct wall-clock calls in domain).

---

### 4. Certification & Sign-off

This gap audit has been reviewed and approved by the engineering pair. All 8 findings are accepted and assigned to their respective owners for execution in Phases 1 through 4.

| Role | Name | Decision | Date |
|---|---|---|---|
| Technical / Architecture Owner (Architect-Lead) | **Juan Manuel Casanova Marín** | **`ACCEPTED`** | 2026-10-18 |
| Requirements & Test Owner (Reviewer) | **Juliana Filigrana Valencia** | **`ACCEPTED`** | 2026-10-18 |
