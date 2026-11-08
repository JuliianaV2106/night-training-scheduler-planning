# Impl-1 Story Inspection — Module 9: Night Training Scheduler

**Scope:** the three Impl-1 stories (1.1 Job Submission, 1.2 Scope Boundary, 1.3 Window Activation), inspected against `planning/epics.md`, `planning/detailed-design/contracts.md`, `docs/contracts/openapi.yaml` and `planning/ARCHITECTURE.md`.
**Method:** every claim below was checked against the running code (tests or direct API calls), not taken from the walkthrough.

Classification used:

- **Implementation defect:** the code does not meet the agreed behaviour.
- **Specification gap:** the intended behaviour was never adequately defined, or the artifacts contradict each other.
- **Legitimate design adjustment:** the approach changed without changing the required behaviour.

---

## Story 1.1 — Job Submission Ingress & Validation Skeleton

**1. Which acceptance criterion can you trace to a specific implementation location?**
The failure-path Gherkin: *"Given an existing job under `idemp-key-happy-001` with digest A, when a client posts the same key with digest B, then 409 `IDEMPOTENCY_CONFLICT` and zero rows are inserted."* It traces as follows:

| Part of the criterion | Location |
|---|---|
| Key lookup inside the same transaction as the insert | `src/application/job_submission.py:49-52` |
| Digest comparison and typed error | `JobSubmissionService._replay`, `job_submission.py:85` |
| Canonical digest | `src/domain/policies.py:38` (`payload_digest`) |
| Code → HTTP 409 mapping | `src/adapters/inbound/http_api.py`, `HTTP_STATUS_BY_CODE` |
| Verified by | `tests/unit/test_story_1_1_job_submission.py::TestIdempotency::test_same_key_different_payload_is_409_with_zero_inserts` |

**2. What did you implement that was not explicitly requested?**
- The digest serialisation (sorted keys, compact JSON). The contract only says "SHA-256 digest of serialized spec".
- The rule behind `estimated_first_window`, which the OpenAPI requires but nothing defines.
- A catch-all handler that turns unexpected exceptions into an `ErrorBody` 500.

**3. What assumption did you — or the AI — make?**
- `queue_position` is the FIFO position among queued jobs (`sqlite_repository.py:84`). The contract calls it the position "in admission queue", but the Admission Order of Story 1.3 is by priority, not FIFO.
- `estimated_first_window` is the next 22:00 at or after submission, so a job submitted at 23:00 waits for the next night.
- `submitJob` P4 (M1/M5/M8 fixtures) and P6 (storage budget) can be deferred to Impl-2.

**4. Did implementation reveal a missing or ambiguous requirement?**
Yes. See **F-1**: what an idempotent replay should return once the job has left the queue.

**5. Which generated change did you accept without fully understanding it?**
The migration `001_…schema.sql` was copied verbatim from Solu-2. Inspection now shows that its `created_at` / `updated_at` defaults use `strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')`. SQLite's `'now'` is **UTC**, so the value is UTC wall time labelled `-05:00`: a row created at 10:03 local time stores `15:03:39-05:00`. It also reads the host clock, which AD-1 forbids for scheduling decisions. These columns are audit metadata that no decision reads, so it is logged as an open item for Impl-2 rather than fixed here.

---

## Story 1.2 — Single-Node Scope Boundary Enforcement

**1. Which acceptance criterion can you trace to a specific implementation location?**
*"Given a job spec with `worker_count = 4`, when submitted, then 400 `OUT_OF_SCOPE_DISTRIBUTED` citing `self:SCOPE-BOUNDARY-v1` and zero database mutations."*

| Part of the criterion | Location |
|---|---|
| Rule and citation | `src/domain/policies.py:44` (`check_single_node_scope`) |
| Runs before any read or write (Q-fail) | called in `job_submission.py` before `self._repo.transaction()` |
| Verified by | `tests/unit/test_story_1_2_scope_boundary.py::test_distributed_spec_is_400_with_zero_mutation` (3 variants) |

**2. What did you implement that was not explicitly requested?**
A rejected distributed spec does **not** consume its idempotency key, so the same key can be reused with a corrected spec (`test_scope_check_runs_before_idempotency_lookup`). The explanation payload also carries `observed_values` and `thresholds`.

**3. What assumption did you — or the AI — make?**
- The AI assumed that `worker_count != 1` is equivalent to the catalog trigger `worker_count > 1`. It is not, which is **F-2**.
- It also assumed that schema validation (Pydantic) may run before P1. A distributed spec with a malformed digest therefore returns 422, not 400.

**4. Did implementation reveal a missing or ambiguous requirement?**
- **Checked, consistent:** the Gherkin mentions `nprocPerNode = auto`, which is not a `JobSpec` field. `ARCHITECTURE.md` (field-mapping row 3) maps `nprocPerNode: auto` to `distributed_artifact_present`, which the code enforces. This is not a gap.
- **Minor gap:** the contract lists P1…P6 but never says which error wins when a spec violates several at once. The current behaviour (schema errors first) is consistent but unspecified.

**5. Which generated change did you accept without fully understanding it?**
The precedence above. It comes from FastAPI validating the body before the handler runs, and it was accepted without first checking it against the order of the contract's preconditions.

---

## Story 1.3 — Night Window Activation at 22:00:00 & Deterministic Allocation Fold

**1. Which acceptance criterion can you trace to a specific implementation location?**
*"Given simulated time 14:00:00-05:00, when `activateWindow` is triggered, then 400 `WINDOW_ACTIVATION_OUTSIDE_WINDOW` and zero placements occur."*

| Part of the criterion | Location |
|---|---|
| Guard before the transaction opens | `src/application/window_activation.py:36` |
| ±2 s rule | `src/domain/policies.py:142` (`is_activation_instant`) |
| Verified by | `tests/unit/test_story_1_3_window_activation.py::TestOutsideWindow::test_daytime_activation_is_400_with_zero_placements` (asserts 0 held slots and all jobs still queued) |

The node total order traces to `src/domain/scheduling.py:56`.

**2. What did you implement that was not explicitly requested?**
- The 503 fleet-size check: the story does not ask for it, but contract P2 does.
- `admitted_nights + 1` on placement (`sqlite_repository.py:126`), which comes from the PRD glossary, not from the story.
- Malformed or naive instants are rejected as 400.
- `won_on` / `candidates_considered` in the Decision Record (AD-4 text).

**3. What assumption did you — or the AI — make?**
- Activation idempotency is keyed by calendar date (`ACT-YYYYMMDD`).
- The instant comes from the request DTO, not from `ClockPort`.
- `consecutive_nights_missed` is **not** incremented on a `T-4b` deferral. We checked this against the PRD glossary: the counter is per Night Window ("received zero admitted minutes" over the whole night), and a deferred job can still be placed later that night. Incrementing it at 22:00 would therefore be wrong. The assumption is consistent, not a defect.

**4. Did implementation reveal a missing or ambiguous requirement?**
Yes, during Impl-1: the Story 1.3 Gherkin (`ws-gpu-01..05`) contradicted AD-4. It was resolved by amending the Gherkin (`docs/ai-decision-log.md` #6). No new gap was found in this inspection.

**5. Which generated change did you accept without fully understanding it?**
The `transaction()` context manager (`sqlite_repository.py:55`) relies on Python `sqlite3`'s implicit-transaction mode, and the shared connection (`check_same_thread=False`) relies on async handlers. This was accepted, then analysed in **F-3**.

---

## Findings

| ID | Story | Classification | Finding | Status |
|---|---|---|---|---|
| **F-1** | 1.1 | **Specification gap** | Contract Q1 says an idempotent resubmission returns "the original `job_id` and **existing state**". But the OpenAPI `JobSubmissionResponse.state` enum allows only `QUEUED_PENDING_WINDOW`, and `queue_position` must be 1–500. The two agreed artifacts contradict each other once the job has been placed. **Observed:** submit, activate at 22:00, then resubmit the same payload. The response is `200 {state: "QUEUED_PENDING_WINDOW", queue_position: 1}` while the database says `RUNNING`. | **Open, team decision.** Proposal: widen `state` to the `JobState` enum and make `queue_position` nullable for non-queued jobs, in `openapi.yaml`, `dto.py` and a new test. Not changed unilaterally, because it alters a public contract. |
| **F-2** | 1.2 | **Implementation defect** | The typed error catalog triggers `OUT_OF_SCOPE_DISTRIBUTED` on `worker_count > 1` / `replicas > 1`, and the OpenAPI declares `enum: [1]`. The code tested `!= 1`, so `worker_count = 0` returned **400 "distributed… route to Module 10"** instead of **422 `VALIDATION_FAILED`**. | **✅ Resolved.** `check_single_node_scope` now uses `> 1`, and `check_spec_ranges` rejects counts below 1 as `VALIDATION_FAILED`. New test `test_count_below_one_is_422_validation_not_out_of_scope[worker_count=0, replicas=0]`: **2 failed** on the old code, **passes** on the fix. Full suite: **46 passed, 0 failed**. |
| **F-3** | 1.3 (and 1.1) | **Legitimate design adjustment** | The contract says concurrent submissions are serialised with SQLite `BEGIN IMMEDIATE`, and the `activateWindow(clock)` signature takes the clock. The implementation serialises through one asyncio event loop instead (async handlers, one shared connection, one uvicorn worker), commits or rolls back through `transaction()`, and takes the instant from the request DTO. **The required behaviour is unchanged:** exactly one `201` per key and replays `200`/`409` (Story 1.1 idempotency tests), a repeated activation returns the recorded result without duplicate records (`test_repeated_activation_is_idempotent`), and nothing partial persists on failure. | **Accepted, with a documented condition.** The adjustment holds only for a single process. Running more than one uvicorn worker requires switching to `BEGIN IMMEDIATE` before scaling. |

**Also checked and found consistent (no defect invented):** the `nprocPerNode = auto` rejection (Story 1.2, question 4) and the `consecutive_nights_missed` handling at activation (Story 1.3, question 3).
**Additional open item:** the UTC-labelled-as-`-05:00` schema timestamps (Story 1.1, question 5), logged for Impl-2.
