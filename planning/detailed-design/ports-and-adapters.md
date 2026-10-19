---
title: "Module 9 — Night Training Scheduler: Ports & Adapters Architecture Mapping"
status: final
version: "1.0.0"
created: 2026-10-18
authors:
  - "Juan Manuel Casanova Marín (Architect-Lead)"
  - "Juliana Filigrana Valencia (Reviewer)"
module: "Module 9 — Night Training Scheduler"
paradigm: "Hexagonal Architecture (Ports and Adapters) + Deterministic Event Sourced Reducer"
---

# Ports & Adapters (Hexagonal) Architecture Mapping

This document establishes the hexagonal layer placement for every file and component in **Module 9: Night Training Scheduler**.

---

## 1. Hexagonal Layer Map

Every component and source path of the module appears exactly once in the table below. Strict architectural dependency rules are enforced:
- **Driving Adapters** depend strictly on Inbound Ports.
- **Inbound Ports** declare use-case contracts using primitive DTOs only.
- **Core Domain** has zero outward dependencies (pure logic).
- **Outbound Ports** declare driven dependencies using pure domain types.
- **Driven Adapters** implement Outbound Ports.

| Component (File Path) | Hexagonal Layer | Allowed Dependencies | Governed By (AD-n / Contract) |
|---|---|---|---|
| `api/routes/jobs.py` | Driving Adapter (HTTP API) | `ports/in/job_submission.py`, DTOs | `AD-8`, `FR-1`, `FR-2`, `FR-31` |
| `api/routes/board.py` | Driving Adapter (HTTP/Console) | `ports/in/board_query.py`, DTOs | `AD-8`, `FR-25`, `EXPERIENCE.md` |
| `api/routes/simulations.py` | Driving Adapter (HTTP API) | `ports/in/simulation_control.py`, DTOs | `AD-1`, `FR-28`, `FR-30` |
| `api/routes/auth.py` | Driving Adapter (HTTP Session) | `ports/in/auth_session.py`, DTOs | `AD-8`, `FR-31(a)` |
| `api/routes/health.py` | Driving Adapter (HTTP Probe) | `ports/out/clock.py`, DTOs | `AD-1`, `NFR-16` |
| `pacer/daemon.py` | Driving Adapter (Simulation Engine Loop) | `ports/in/window_activation.py`, `ports/in/eviction.py`, `ports/out/clock.py` | `AD-1`, `FR-11`, `FR-28` |
| `ports/in/job_submission.py` | Inbound Port (Use-Case Interface) | `schemas/dto.py` | Contract: `submitJob`, `FR-1..FR-7` |
| `ports/in/window_activation.py` | Inbound Port (Use-Case Interface) | `schemas/dto.py` | Contract: `activateWindow`, `FR-8`, `AD-4` |
| `ports/in/eviction.py` | Inbound Port (Use-Case Interface) | `schemas/dto.py` | Contract: `evictAtDeadline`, `FR-19`, `AD-7` |
| `ports/in/board_query.py` | Inbound Port (Use-Case Interface) | `schemas/dto.py` | `FR-25`, `EXPERIENCE.md` |
| `ports/in/simulation_control.py` | Inbound Port (Use-Case Interface) | `schemas/dto.py` | `FR-28`, `FR-30` |
| `domain/entities.py` | Core Domain & Invariants (Pure) | None (standard library types: dataclass, Enum) | `AD-4`, `PRD §4.1`, Data Model |
| `domain/engine.py` | Core Domain & Invariants (Pure Reducer) | `domain/entities.py`, `domain/state_machine.py` | `AD-1`, `AD-2`, `FR-9`, `FR-14` |
| `domain/state_machine.py` | Core Domain & Invariants (Pure Guards) | `domain/entities.py` | `AD-1`, `AD-6`, `PRD §6.4` |
| `domain/ranking.py` | Core Domain & Invariants (Pure Ordering) | `domain/entities.py` | `AD-1`, `AD-4`, `FR-8`, `FR-15` |
| `domain/allocation.py` | Core Domain & Invariants (Pure Placement) | `domain/entities.py` | `AD-4`, `FR-12`, `FR-13` |
| `domain/emitter.py` | Core Domain & Invariants (Fail-Closed Emitter) | `domain/entities.py` | `AD-3`, `FR-24`, `PRD §6.4` Map |
| `ports/out/clock.py` | Outbound Port (Clock Interface) | `domain/entities.py` (Timestamp types) | `AD-1`, `NFR-1` |
| `ports/out/id_generator.py` | Outbound Port (ID Factory) | `domain/entities.py` | `AD-1`, `FR-1` |
| `ports/out/fleet_repository.py` | Outbound Port (Node & Slot Store) | `domain/entities.py` | `AD-4`, `FR-12` |
| `ports/out/decision_log.py` | Outbound Port (Append-Only Log) | `domain/entities.py` | `AD-2`, `AD-3`, `FR-24` |
| `ports/out/checkpoint_store.py` | Outbound Port (Checkpoint File Store) | `domain/entities.py` | `AD-7`, `FR-18`, `FR-20` |
| `ports/out/notification_outbox.py`| Outbound Port (User Notifications) | `domain/entities.py` | `FR-27` |
| `ports/out/delegated_modules.py` | Outbound Port (M1, M2, M3, M4, M5, M8) | `domain/entities.py` | `PRD §5`, `FR-6`, `FR-23` |
| `adapters/db/sqlite_repository.py`| Driven Adapter (Persistence Engine) | `ports/out/fleet_repository.py`, `ports/out/decision_log.py` | `AD-2`, `AD-5`, `NFR-10` |
| `adapters/sim/simulated_clock.py` | Driven Adapter (Timekeeper) | `ports/out/clock.py` | `AD-1`, `NFR-1`, `FR-28` |
| `adapters/sim/simulated_fleet.py` | Driven Adapter (33-slot In-Memory Fleet)| `ports/out/fleet_repository.py` | `AD-4`, `NFR-16` |
| `adapters/sim/filesystem_checkpoint_store.py` | Driven Adapter (5-Step Checkpoint Store)| `ports/out/checkpoint_store.py` | `AD-7`, `FR-18`, `FR-22` |
| `adapters/sim/delegated_fixtures.py`| Driven Adapter (In-Process M1-M8 Fixtures)| `ports/out/delegated_modules.py` | `PRD §5`, `FR-6` |
| `adapters/sim/in_memory_outbox.py` | Driven Adapter (Local Outbox) | `ports/out/notification_outbox.py` | `FR-27` |

---

## 2. Hard Architectural Rules (Compliance Checklist)

1. **Domain Purity (Zero Outside Imports):**
   - No file in `domain/` may import FastAPI, Starlette, SQLite, SQLAlchemy, Pydantic, HTTP clients (e.g. `httpx`, `requests`), or filesystem APIs.
   - Calling `datetime.now()`, `time.time()`, or unseeded `random.random()` within `domain/` is strictly prohibited and constitutes a compilation/test failure.
2. **Deterministic Time and Randomness Injection:**
   - Time is injected exclusively through `ports/out/clock.py` (`ClockPort.now()`), returning a timezone-aware `datetime` with `America/Bogota` (UTC-05:00) offset.
   - Any random tie-breaker must consume a pseudo-random generator initialized with an explicit integer seed (`RunManifest.seed`).
3. **Simulation Agnosticism:**
   - Hardware GPUs, DCGM daemons, Prometheus endpoints, and Kubernetes clusters are entirely simulated. Outbound calls to GPUs or external services are routed exclusively through simulated driven adapters.
4. **DTO Primitive Purity:**
   - DTOs and port method signatures contain only primitive Python types (`int`, `float`, `str`, `bool`, `list`, `dict`) or Pydantic models. Framework request/response objects (e.g., `fastapi.Request`, `fastapi.Response`) never penetrate past the Driving Adapter.

---

## 3. Mermaid Component Diagram (Layer Tagged)

```mermaid
flowchart TB
    subgraph DrivingAdapters["Driving Adapters (Ingress / Triggers)"]
        HTTP_API["api/routes/jobs.py<br/>api/routes/board.py<br/>api/routes/auth.py<br/><b>[Driving: HTTP]</b>"]
        PACER["pacer/daemon.py<br/><b>[Driving: Simulation Loop]</b>"]
    end

    subgraph InboundPorts["Inbound Ports (Use-Case Contracts)"]
        PORT_IN_SUBMIT["ports/in/job_submission.py<br/><b>[Inbound Port]</b>"]
        PORT_IN_WINDOW["ports/in/window_activation.py<br/><b>[Inbound Port]</b>"]
        PORT_IN_EVICT["ports/in/eviction.py<br/><b>[Inbound Port]</b>"]
    end

    subgraph CoreDomain["Core Domain (Pure Logic & Invariants)"]
        direction TB
        ENGINE["domain/engine.py<br/><b>[Pure Reducer: apply]</b>"]
        STATE_MACHINE["domain/state_machine.py<br/><b>[State Guards & Enum]</b>"]
        RANKING["domain/ranking.py<br/><b>[Deterministic Order]</b>"]
        ALLOCATION["domain/allocation.py<br/><b>[AD-4 Slot Placement]</b>"]
        EMITTER["domain/emitter.py<br/><b>[Fail-Closed Emitter]</b>"]
        ENTITIES["domain/entities.py<br/><b>[Pure Models]</b>"]
    end

    subgraph OutboundPorts["Outbound Ports (Driven Contracts)"]
        PORT_OUT_CLOCK["ports/out/clock.py<br/><b>[Outbound: ClockPort]</b>"]
        PORT_OUT_DB["ports/out/decision_log.py<br/>ports/out/fleet_repository.py<br/><b>[Outbound: DB Ports]</b>"]
        PORT_OUT_CKPT["ports/out/checkpoint_store.py<br/><b>[Outbound: CheckpointPort]</b>"]
        PORT_OUT_DELEGATES["ports/out/delegated_modules.py<br/><b>[Outbound: M1-M8 Fixtures]</b>"]
        PORT_OUT_NOTIF["ports/out/notification_outbox.py<br/><b>[Outbound: OutboxPort]</b>"]
    end

    subgraph DrivenAdapters["Driven Adapters (Egress / Implementation)"]
        SIM_CLOCK["adapters/sim/simulated_clock.py<br/><b>[Driven: Fake Clock]</b>"]
        SQLITE_DB["adapters/db/sqlite_repository.py<br/><b>[Driven: SQLite WAL]</b>"]
        FS_CKPT["adapters/sim/filesystem_checkpoint_store.py<br/><b>[Driven: 5-Step Store]</b>"]
        DELEGATES["adapters/sim/delegated_fixtures.py<br/><b>[Driven: In-Process M1-M8]</b>"]
        OUTBOX["adapters/sim/in_memory_outbox.py<br/><b>[Driven: Outbox]</b>"]
    end

    %% Dependency Arrows
    HTTP_API --> PORT_IN_SUBMIT
    HTTP_API --> PORT_IN_WINDOW
    PACER --> PORT_IN_WINDOW
    PACER --> PORT_IN_EVICT

    PORT_IN_SUBMIT --> ENGINE
    PORT_IN_WINDOW --> ENGINE
    PORT_IN_EVICT --> ENGINE

    ENGINE --> STATE_MACHINE
    ENGINE --> RANKING
    ENGINE --> ALLOCATION
    ENGINE --> EMITTER
    ENGINE --> ENTITIES

    ENGINE -.-> PORT_OUT_CLOCK
    ENGINE -.-> PORT_OUT_DB
    ENGINE -.-> PORT_OUT_CKPT
    ENGINE -.-> PORT_OUT_DELEGATES
    ENGINE -.-> PORT_OUT_NOTIF

    PORT_OUT_CLOCK <|.. SIM_CLOCK
    PORT_OUT_DB <|.. SQLITE_DB
    PORT_OUT_CKPT <|.. FS_CKPT
    PORT_OUT_DELEGATES <|.. DELEGATES
    PORT_OUT_NOTIF <|.. OUTBOX
```
