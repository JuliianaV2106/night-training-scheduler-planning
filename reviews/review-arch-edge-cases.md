# Edge-Case Review — `planning/ARCHITECTURE.md` (Module 9 — Night Training Scheduler)

| Field | Value |
|---|---|
| Artifact reviewed | `planning/ARCHITECTURE.md` (711 lines, commit `3288df1`) |
| Source of truth | `planning/prd.md` |
| Lens | Edge-case hunter (`bmad-review-edge-case-hunter`), reports only unhandled paths |
| Reviewer | OpenCode, **fresh session** (independent from the authoring agent and from the adversarial reviewer) |
| Triage | Team (human decision), with Claude Code as audit assistant |
| Date | 2026-09-28 |
| Result | 15 findings: **13 Accept · 2 Accept with a different fix** (E-12, E-15; the reviewer's suggested fix was rejected) · 0 Defer |

**Overlap with the adversarial review.** E-8, E-9 and E-10 describe the same defects as adversarial F-8, F-3/F-9 and F-12, found independently from a different angle. They are accepted and resolved by the same fix, and cross-referenced below.

---

| # | Edge case (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| E-1 | T-20 (re-admit from `EVICTION_FAILED`) requires a re-verified digest, but the 21:30 pre-verification sweep only covers `EVICTED_RESUMABLE`. The mandatory edge case's recovery could resume unverified bytes, or never resume. | Critical | **Accept** | The 21:30 sweep covers `EVICTED_RESUMABLE` **and** `EVICTION_FAILED` jobs. T-20 is gated on a digest verified in that phase; otherwise `DEFER` with reason `UNVERIFIED_RESUME`. |
| E-2 | At 05:52:59.9 a checkpoint completes its five steps but commits at 05:53:00.1, so it is deleted as undurable and the job FAILS (T-9) despite having durable bytes. At 05:53:00.000 T-8 and SIGKILL race. | Critical | **Accept** | The T-8 guard compares the **simulated instant at which the fifth step completed** (recorded in the intent), not the commit time. At an identical instant, **T-8 ranks ahead of SIGKILL**. |
| E-3 | AD-2 allows splitting a drain into batches. Splitting the 05:45 Ramp would stamp some SIGTERMs after 05:45:02 (NFR-5), or after 05:53. | Critical | **Accept** | The `EVICTION_RAMP` drain is **never split**: every T-6 is stamped at 05:45:00.000. Any job whose T-6 is not committed by 05:53:00 goes through the FR-19(c) SIGKILL path. |
| E-4 | Nothing forbids admission after 05:45:00, so a job placed at 05:50 (challenger or same-night re-placement) is `RUNNING` at 05:53 with no T-6, and holds a slot past 06:00 (S-1, NFR-14). | Critical | **Accept** | T-3 and T-14 re-placement add the guard `sim_instant < 05:45:00`. A preemption attempted at or after 05:45:00 is refused with `PREEMPTION_REFUSED`. No job can start after the Ramp begins. |
| E-5 | When a delegated module (M2/M3/M4/M5/M8) is unavailable, the required record has no authority to cite, so AD-3 rejects it and the night silently produces no record. | Critical | **Accept (PRD amendment)** | Register `self:DELEGATE-UNAVAILABLE-v1` in PRD §6.2 with reason `DELEGATE_UNAVAILABLE`, used for FR-8(e) blocked attempts, T-4a with M3/M4 absent, T-2 with an absent M8 verdict and FR-6(e). The record also names the unavailable authority (e.g. `M2`) in `inputs`. Add the missing M5 branch to §5.1. |
| E-6 | §5.3 reconciliation only checks a missed 22:00. A crash across 05:53 or 06:00 leaves `CHECKPOINTING` jobs holding slots past 06:00 and the ageing counters unwritten. | Critical | **Accept** | Reconciliation enumerates **every elapsed event** of the AD-1 inventory: an elapsed `CHECKPOINT_DEADLINE` fires T-9 (release slots before the record); an elapsed `NIGHT_CLOSE` applies the ageing accounting as a recorded reconciliation entry. |
| E-7 | At exactly 05:45:00.000, T-5 (complete) and T-6 (SIGTERM) both hold, so a job that finished at 05:45 could be evicted or lose its `COMPLETED`. | High | **Accept** | At an identical instant **T-5 ranks ahead of T-6**. Completion at 05:45:00.000 counts as completion; the bound is written the same way in T-5 and FR-19(e). |
| E-8 | Store exhaustion "halts checkpoint writes" with no record, so a job runs on a stale checkpoint and a healthy Node gets cordoned at 05:45 for a full store. | High | **Accept** (same fix as adversarial F-8) | Store pressure **never** blocks a Ramp or Preemption checkpoint write (F-8). If a write still fails with cause `STORE_FULL`, T-10 applies **without a Cordon Request**, because a full store is not evidence of a faulty Node (PRD FR-23(i)). |
| E-9 | The "closed inventory" omits 21:30, 21:59, T-15, the checkpoint interval and the 03:00 reaper; `PREEMPTION_WINDOW_CLOSE` has no instant. | High | **Accept** (same fix as adversarial F-3, F-9) | Inventory completed (F-3). `PREEMPTION_WINDOW_CLOSE` is removed in favour of a per-victim flag cleared at WINDOW_ACTIVATION (F-9). |
| E-10 | The reaper "never runs inside a Night Window" but is scheduled at 03:00, which is inside it. | High | **Accept** (same fix as adversarial F-12) | Rule restated: the reaper runs at 03:00 and **never between 05:45:00 and 06:00:00**. The garbage-collection report is a non-transition record (`transition: null`) per PRD §6.4. |
| E-11 | The admission loop re-reads M3/M4 per placement but never re-reads the M2 freeze, so a freeze latching mid-loop still places every remaining job. | High | **Accept** | M2 is re-consumed with M3/M4 before each placement. The loop stops at the first latched freeze, and the remaining ranks get `DEFER` citing `policy:M2/…`. |
| E-12 | A 2-GPU job when only one of `server-gpu-01`'s slots is free matches neither T-4a nor T-4b, and no reason code describes it. | High | **Accept with a different fix** | **Rejected** the suggested fix of a new eligibility mark and reason code, because it adds vocabulary for one case. Eligibility is an **allocation-level** predicate: a 2-GPU job needs both slots free, so this case is **T-4b `CAPACITY_EXHAUSTED`** for that job. The single free slot is still correctly `FREE` on the board, because it is free for any 1-GPU job. |
| E-13 | A preemption started during the Ramp has no Checkpoint Budget, and if the victim ends in T-9/T-10 mid-preemption the challenger has no transition. | High | **Accept** | Preemption at or after 05:45:00 is refused (E-4). If a victim routes to T-9 or T-10 during a preemption, the challenger's pending placement is **cancelled** and it stays in `QUEUED_PENDING_WINDOW` with a `DEFER` record. |
| E-14 | Modelled durations (checkpoint write, SHA-256) are charged in real time while pacing is real time, so at 1440× 33 resumes cannot fit 21:30–21:59 and outcomes depend on the rate (breaks NFR-8, FR-11). | High | **Accept** | Every modelled duration is charged in **simulated time** as a scheduled event. The real hash is I/O the Pacer amortises and is never measured against the 21:59 deadline, so outcomes are rate-independent. |
| E-15 | The 500-job cap is enforced only at submission; re-entries (T-12, T-14, T-20) can push the Pending Set above 500. | Medium | **Accept with a different fix** | **Rejected** the suggested fix (asserting the cap on every re-entry), because refusing a re-entry would strand a job that already holds admitted work. The cap counts **all non-terminal jobs** (queued, running, checkpointing, evicted-resumable, eviction-failed) and is checked only at T-1, so re-entries can never exceed it. `/admission-order` returns the true length. |

---

## Outcome

All resolutions are applied to `planning/ARCHITECTURE.md` together with the adversarial review's in one pass. E-5 also amends PRD §6.2 (new registered id `self:DELEGATE-UNAVAILABLE-v1`). The AD-1…AD-8 identifiers are unchanged.
