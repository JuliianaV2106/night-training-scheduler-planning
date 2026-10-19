---
title: "Module 9 — Night Training Scheduler: Detailed Design Review (Phase 1–2 Gate)"
status: triaged
created: 2026-10-18
reviewers:
  - "bmad-review-adversarial (AI)"
  - "bmad-review-edge-case-hunter (AI)"
triaged_by:
  - "Juan Manuel Casanova Marín (Architect-Lead)"
  - "Juliana Filigrana Valencia (Reviewer)"
module: "Module 9 — Night Training Scheduler"
verdict: PASS
---

# Detailed Design Review & Triage (Phase 1–2 Gate)
## Packages Reviewed: `planning/detailed-design/` (contracts.md, ports-and-adapters.md, schemas/)

---

## 1. Executive Summary

An adversarial and edge-case review was conducted across the Phase 1 and Phase 2 detailed design artifacts (`contracts.md`, `ports-and-adapters.md`, `001_night_training_scheduler_schema.sql`, `dto.py`, `events.md`, and `openapi.yaml`).

**Verdict: PASS with Triaged Resolutions Applied.**
- Total findings identified: 6
- Accepted and verified in artifacts: 6
- Deferred: 0
- Rejected: 0

---

## 2. Review Findings & Formal Pair Triage

| Finding ID | Lens | Severity | Finding Description | AI Proposed Fix | Human Decision (Accept / Defer / Reject) | Technical Rationale & Resolution in Artifacts | Owner |
|---|---|---|---|---|---|---|---|
| **DD-REV-01** | Adversarial | **Critical** | Concurrency race hazard in `submitJob`: two concurrent requests with different idempotency keys could both pass the count query `< 500` before either commits, temporarily exceeding `QUEUE_CAP_EXCEEDED`. | Rely on Python mutex or async lock in memory. | **ACCEPT WITH MODIFICATION** | In-memory locks fail if processes restart or under concurrency spikes. Instead, SQLite transaction isolation `BEGIN IMMEDIATE` is enforced at the DB committer, serializing the count evaluation and insert within a single write transaction. Indexed via partial index `idx_active_jobs_state`. | Juan Manuel Casanova Marín |
| **DD-REV-02** | Edge-Case | **High** | Dawn Checkpoint Timeout at 05:53:00 vs. In-Flight Network/Disk I/O: If the 5-step write hangs on `fsync`, the engine could stall past 06:00:00. | Increase timeout or make 06:00:00 flexible by 5 minutes. | **REJECT AI FIX / ACCEPT MANDATORY ENFORCEMENT** | Relaxing 06:00:00 violates course constraint 1 and Invariant S-1. The engine executes an asynchronous watchdog timer: at exactly 05:53:00, if `CheckpointStorePort` has not completed step 5, SIGKILL is dispatched immediately, slots are detached, the node is cordoned via `CordonRequest`, and `allocations_held` is reset to 0 before 06:00:00. | Juliana Filigrana Valencia |
| **DD-REV-03** | Adversarial | **Medium** | Elastic word risk in contract documentation: phrases like "reasonable time" or "proper format" could sneak into error descriptions. | Text scan and automated regex search. | **ACCEPT** | Conducted AST and regex pass over `contracts.md`. Confirmed zero banned words (*efficiently, robust, scalable, properly, user-friendly, etc.*); every constraint is backed by an explicit numeric threshold or typed enum. | Juliana Filigrana Valencia |
| **DD-REV-04** | Edge-Case | **High** | 2-GPU job placement on half-free `server-gpu-01`: If `server-gpu-01` has slot 0 occupied by a 1-GPU job and slot 1 free, a 2-GPU job could mistakenly attempt partial allocation. | Introduce a new state `PARTIALLY_ALLOCATED`. | **REJECT AI VOCABULARY / ACCEPT PHYSICAL CONSTRAINT** | No new states permitted (strictly 9 states). Physical constraint in SQL and pure domain allocation logic treats `server-gpu-01` as ineligible for 2-GPU jobs unless `allocations_held == 0` on that node. The job receives `T-4b CAPACITY_EXHAUSTED` and free slot 1 remains available for 1-GPU jobs. | Juan Manuel Casanova Marín |
| **DD-REV-05** | Adversarial | **Medium** | Timezone drift risk: ISO-8601 strings in DTOs or DB could accept UTC `Z` strings without validating the `America/Bogota` (UTC-05:00) offset (D-1). | Standardize on UTC Z everywhere. | **REJECT AI FIX / REINFORCE D-1** | Campus operational requirement D-1 strictly requires local campus time `America/Bogota` (UTC-05:00) so that 22:00:00 and 06:00:00 match physical building lock hours. Pydantic validators in `dto.py` enforce explicit `-05:00` offset on all incoming and emitted timestamps. | Juan Manuel Casanova Marín |
| **DD-REV-06** | Edge-Case | **High** | Orphaned Checkpoints on Abrupt Process Crash: An unverified checkpoint file written during step 1 or 2 before rename could consume disk quota. | Ad-hoc cleanup on reboot. | **ACCEPT** | Verified that `adapters/sim/filesystem_checkpoint_store.py` runs a startup quarantine/prune sweep at 21:30:00 and scheduled 03:00:00 GC, purging any temporary uncommitted `.tmp` files older than 60 minutes. | Juliana Filigrana Valencia |

---

## 3. Contract $\leftrightarrow$ Schema Cross-Check Table (Step 2.3)

| Invariant Clause | Schema / Code Pointer | Verification Status |
|---|---|:---:|
| **INV-01 (Queue Cap < 500)** | `001_night_training_scheduler_schema.sql:84` (`idx_active_jobs_state`) + `domain/engine.py:check_queue_cap()` | **VERIFIED** |
| **INV-02 (allocations_held == 0 at 06:00)** | `001_night_training_scheduler_schema.sql:31` (`gpu_slots.allocated_job_id`) + `evictAtDeadline()` unconditional release | **VERIFIED** |
| **INV-03 (2-GPU strictly 48GB)** | `001_night_training_scheduler_schema.sql:79` (`CONSTRAINT check_two_gpu_requires_48gb`) | **VERIFIED** |
| **INV-04 (Atomic State + Record Commit)** | `adapters/db/sqlite_repository.py:atomic_commit_batch()` | **VERIFIED** |
| **INV-05 (Node Cordon on Dawn Failure)** | `001_night_training_scheduler_schema.sql:128` (`cordon_requests`) + `nodes.status = 'CORDONED'` | **VERIFIED** |
| **INV-06 (Resume from Verified Checkpoint)** | `001_night_training_scheduler_schema.sql:110` (`checkpoints.state = 'VERIFIED'`) | **VERIFIED** |
| **INV-07 (Domain Purity)** | `domain/` directory contains zero framework or I/O imports; verified via AST test | **VERIFIED** |
| **INV-08 (Preemption Margin >= 20)** | `domain/state_machine.py:can_preempt()` checks `effective_priority` delta $\ge 20$ | **VERIFIED** |

---

## 4. Gate Sign-Off

The detailed design package satisfies all structural, physical constraint, and contract-driven criteria. All 6 findings are resolved and aligned across schemas, DTOs, and behavioral contracts.

| Role | Name | Signature | Date |
|---|---|---|---|
| Technical / Architecture Owner | **Juan Manuel Casanova Marín** | Juan Manuel Casanova Marín | 2026-10-18 |
| Requirements & Test Owner | **Juliana Filigrana Valencia** | Juliana Filigrana Valencia | 2026-10-18 |
