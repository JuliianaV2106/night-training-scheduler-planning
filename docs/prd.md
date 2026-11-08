# Scoped Module PRD — Impl-1

The full Module 9 PRD is in [`planning/prd.md`](../planning/prd.md), with its addendum in [`planning/prd-addendum.md`](../planning/prd-addendum.md). It is not copied here, so there is only one source of truth.

Requirements in scope for Impl-1:

| Story | PRD requirements | Contract | Architectural invariants |
|---|---|---|---|
| 1.1 Job Submission Ingress & Validation | FR-1, FR-2, FR-5, NFR-3 | `submitJob` P2, P3, P5, Q1–Q4 (`planning/detailed-design/contracts.md` §2.1) | AD-1, AD-2, AD-3, INV-01, INV-03 |
| 1.2 Single-Node Scope Boundary | FR-3(a)(b) | `submitJob` P1, Q-fail | AD-4, INV-03 |
| 1.3 Night Window Activation & Allocation Fold | FR-8, FR-12, FR-13, FR-14, FR-15, NFR-2 | `activateWindow` P1, P2, Q1–Q4, I2–I4 (§2.2) | AD-1, AD-2, AD-4, INV-04 |

Explicitly deferred to Impl-2:

- `submitJob` P4: M1/M5/M8 entitlement, catalog and quota fixtures (ENTITLEMENT_DENIED, MODEL_NOT_FOUND)
- `submitJob` P6: checkpoint store budget (STORE_FULL)
- `evictAtDeadline` and the Mandatory Edge Case (Epic 2)
- Starvation promotion, preemption, the pacer daemon, and crash recovery (Epics 3–4)
