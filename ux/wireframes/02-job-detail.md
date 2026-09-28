# Wireframe 02 — Job Detail at a clean dawn Eviction

**Surface:** SURF-04 Job detail (+ SURF-04b Decision Record detail) · **Canonical spec:** `ux/C-UX-Scenarios/scenario-1.md`, deltas in `scenario-3.md`
**Theme:** dark · **Persona:** `STUDENT` (Kavita), the job's submitter · **Instant:** `2026-10-04T05:45:31-05:00`

> **Why this frame.** The PRD's §6.3 worked example is the **T-6 `EVICT` record rendered in full**, and the T-8 completion record `supersedes` it. This is therefore the only place the Explainability Contract can be shown against a record the PRD itself authored — the eyebrow, the summary, the citations and the inputs are all reproduced **verbatim** from `planning/prd.md` lines 266–269, and the surface is the thing that has to render them without softening any of it.

---

## 1. The frame — two columns

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Skip to work region]  ● Daemon reachable  05:45:31-05:00  last update 05:45:31-05:00  … │ SURF-02a
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│  ‹ Board   ‹ Admission Order   ‹ Pending Set   ‹ Event log        JOB-0417 ▸  Back to jobs  │
├───────────────────────────────────────────────────────────────────┬─────────────────────────────┤
│                                                                   │ DECISION RECORDS      10     │
│  JOB-0417                                          ‹ RESEARCH ›   │ ─────────────────────────── │
│  ┌─────────────────────────────────────────────────────────────┐  │ ┃ EVICT                05:45 │
│  │  ‖  EVICTED_RESUMABLE                                       │  │ ┃ 05:45:31-05:00 · T-8     │
│  │     Evicted, resumable · not terminal · no terminal ring     │  │ ┃ supersedes ▸ DR-000441   │
│  └─────────────────────────────────────────────────────────────┘  │ ┃   (T-6, 05:45:00)       │
│                                                                   │ ┃ reason  —               │
│  ┌─────────────────────────────────────────────────────────────┐  │ ┃ EVICT     · stopped 06:00│
│  │ Decision · evict                                            │  │ ┃   deadline · step 41,200│
│  │ supersedes ▸ DR-000441                                       │  │ ┃ [self:EVICTION-RAMP-v1] │
│  │ 2026-10-04T05:45:31-05:00                                   │  │ ┃ [node-state:M3/ws-gpu-12│
│  │                                                             │  │ ┃   @…T05:44:58-05:00]    │
│  │ Night Training Scheduler stopped job JOB-0417 on ws-gpu-12  │  │ ┃                        │
│  │ at the 06:00 morning deadline so the machine is free for    │  │ ┃ EVICT                05:45 │
│  │ 08:00 lab use; last durable Checkpoint is at step 41,200,  │  │ ┃ 05:45:00-05:00 · T-6   │
│  │ digest `sha256:3f9a…c201`.                                  │  │ ┃ reason  —               │
│  │                                                             │  │ ┃ EVICT · stopped 06:00   │
│  │ [self:EVICTION-RAMP-v1] [node-state:M3/…@…T05:44:58-05:00]   │  │ ┃   deadline · step 41,200│
│  │                                                             │  │ ┃ [self:EVICTION-RAMP-v1] │
│  │ inputs  elapsed_runtime_s 28140 · checkpoint_budget_s 300   │  │ ┃ [node-state:M3/…@-05:00]│
│  │         estimated_total_s 111600 · progress_fraction 0.252 │  │ ┃                        │
│  └─────────────────────────────────────────────────────────────┘  │ ┃ ADMIT                22:00 │
│                                                                   │ ┃ 22:00:01-05:00 · T-3    │
│  ▸ PLACEMENT                                                      │ ┃ ADMIT · ws-gpu-12 · …    │
│    ws-gpu-12 · slot 1 · 24 GB · released 05:45:31 · now ○ available│ ┃ [policy:M2/…]          │
│                                                                   │ ┃ [node-state:M3/…]       │
│  ▸ CHECKPOINT                                                     │ ┃                        │
│    verified · step 41,200 · 1.84 GB · 2026-10-04T03:10:00-05:00  │ ┃ + 7 earlier records      │
│    sha256:3f9a4c7e…09c2c201                              [Copy]  │ ┃   (show 4)             │
│    durability — all five steps completed 2026-10-04T05:45:29-05:00│ ┃                        │
│    next eligible resume  2026-10-04T22:00:00-05:00                │ ┃ [Event log ▸]           │
│                                                                   │ ┃                        │
│  ▸ NOTIFICATION                                    (1 of 1)      │ ┃ SURF-04b                │
│    ✓ delivered 05:45:31-05:00 · to submitter · to admin  no      │ ┃ side panel, not modal   │
│    "Stopped cleanly. Last durable Checkpoint is step 41,200,      │ ┃                        │
│     digest sha256:3f9a…c201."                                    │ ┃                        │
│                                                                   │ ┃                        │
│  ▸ CHECKPOINT RETENTION                          2 of 2 kept     │ ┃                        │
│    FR-22(b): the 2 most recent verified Checkpoints of a         │ ┃                        │
│    non-terminal job are never removed automatically.             │ ┃                        │
└───────────────────────────────────────────────────────────────────┴─────────────────────────────┘
```

---

## 2. The state badge — the one thing this design must not get wrong

```
  ‖  EVICTED_RESUMABLE
     Evicted, resumable · not terminal · no terminal ring
```

| Choice | Reason |
|---|---|
| `{colors.state-evicted-resumable}` violet | A clean dawn eviction is **the module working correctly**, not a loss. |
| glyph `‖` · label "Evicted, resumable" | Never a terminal colour, never a desaturation, never the word **"stopped"**. UJ-3's climax is `EVICTED_RESUMABLE` with a verified digest — *"not 'stopped.'"* |
| **No 1px `{colors.border-structure}` terminal ring** | The state is not terminal. The ring is reserved for `COMPLETED`, `FAILED`, `REJECTED`, `EXPIRED`, and terminality is carried by **the label and the ring, never by desaturation**. |
| State name **and** plain-language label both shown | The state name is what an operator greps for; the label is what a student reads at 07:00. Neither alone is sufficient. |

**`EVICTED_RESUMABLE` and `FAILED` must never be confusable.** They both mean "not running", and a reader who confuses them has failed the design even though both are technically correct.

---

## 3. The Decision banner — the §6.3 record, verbatim

Reproduced exactly as authored in `planning/prd.md` §6.3. **Nothing is reworded, abbreviated or softened.**

| Field | Value | Verbatim from |
|---|---|---|
| **Eyebrow** | `Decision · evict` | §6.1 `decision: EVICT` |
| **`job_id`** | `JOB-0417` | line 266 |
| **`node_id`** | `ws-gpu-12` | line 266 |
| **`sim_timestamp`** | `2026-10-04T05:45:00-05:00` | line 266 |
| **Summary** | *"Night Training Scheduler stopped job JOB-0417 on ws-gpu-12 at the 06:00 morning deadline so the machine is free for 08:00 lab use; last durable Checkpoint is at step 41,200, digest `sha256:3f9a…c201`."* | line 267 |
| **Citations** | `self:EVICTION-RAMP-v1`, `node-state:M3/ws-gpu-12@2026-10-04T05:44:58-05:00` | line 268 |
| **Inputs** | `elapsed_runtime_s: 28140`, `checkpoint_budget_s: 300`, `estimated_total_s: 111600`, `progress_fraction: 0.252` | line 269 |

**The citation pair is the Explainability Contract, and both halves are load-bearing.** `self:EVICTION-RAMP-v1` names the **rule** that fired. `node-state:M3/ws-gpu-12@…` names the **delegated authority** whose last health reading the daemon relied on. FR-24(a) and F-1 make the non-`self:` citation **unconditional on every `EVICT` and every `PREEMPT`** — a user's work being stopped may never be justified by a module-owned rule alone, and the emitter is fail-closed on it: a record arriving without the delegated citation is **refused and the transition is not applied**.

**The inputs row is not decoration.** `progress_fraction: 0.252` is `28140 / 111600` — the arithmetic is shown, not asserted, so a reader can check the daemon's own maths rather than trust it. `checkpoint_budget_s: 300` sits beside it so the reader can see the job was inside the budget when the Ramp began.

> ✅ **Resolved 2026-09-28:** `[V]` found that PRD §6.3 stamped this citation `…05:44:58Z` (UTC, five hours before the eviction). The PRD was corrected to `…05:44:58-05:00`, two seconds before the 05:45:00 decision, and this wireframe follows it.
>
> *Original finding:* ⚠ **Finding for `[V]` — the §6.3 citation carries the wrong UTC offset.** The record's `sim_timestamp` is `2026-10-04T05:45:00-05:00`, but its `node-state:M3/…` citation is stamped `@2026-10-04T05:44:58Z`. A `Z` suffix is UTC: `05:44:58Z` is `00:44:58-05:00` local — **five hours before** the eviction, not the two seconds before it that the "last health reading" requires. The `Z` is almost certainly a typo for `-05:00`. **It is rendered verbatim here and not corrected**, because a source citation is never silently rewritten; the defect is carried to `ux/validation-report.md` for the PRD's owner.

---

## 4. Supersession — the record chain made visible

The banner sits above its own history:

```
  supersedes ▸ DR-000441
```

T-8 **keeps `decision: EVICT`** from T-6, sets `supersedes` to the T-6 record id, and mirrors T-6's citations. So:

- **One decision, two records.** FR-24(f) counts one record per transition, and FR-19's "one `EVICT` Decision Record per job" counts one **decision chain**. Rendering the pair as two decisions would overstate what FR-24 constrains — and would double-count `EVICT` in any audit.
- **Records are immutable and append-only.** A revised decision is a **new record linked to its predecessor**, never an edit of the old one. The link is a real control, not a label.
- `DR-000441` is reachable from the current record and vice-versa. The reader can see both the decision and its completion without losing either.

---

## 5. Checkpoint block — the evidence

```
  ▸ CHECKPOINT
    verified · step 41,200 · 1.84 GB · 2026-10-04T03:10:00-05:00
    sha256:3f9a4c7e…09c2c201                                         [Copy]
    durability — all five steps completed 2026-10-04T05:45:29-05:00
    next eligible resume  2026-10-04T22:00:00-05:00
```

**Digest, byte count, step number and `sim_timestamp` are recorded together or not at all** (FR-18(c)). The surface therefore shows a single `verified` row that is either complete or absent — never a digest without a byte count, which would be a record the PRD does not permit to exist.

**Durability is stated as the five completed steps, not as a tick:**

```
  write to a temporary file → fdatasync the file → atomic rename into the final path
                            → fsync the parent directory → compute and record the SHA-256 digest
```

The **`fsync` the parent directory** step is called out by name because it is the one everyone omits: measured from `prd-addendum.md` §B.2, an unsafe Checkpoint survived **0 of 430** crash injections. Without it the rename exists only in memory. A reader who has never written a Checkpoint implementation is being told *why this takes eight minutes*.

**The retention line is a promise with an owner.** `2 of 2 kept` states FR-22(b) — the 2 most recent verified Checkpoints of a non-terminal job are **never removed automatically** — and because the job is non-terminal, the promise is live tonight.

**The next eligible resume is an instant, not a duration.** `2026-10-04T22:00:00-05:00` — tonight's Window Activation. This is the single most important fact on the page for a student who was asleep at 05:45, and it is stated as a **date and time with offset**, never as "tomorrow".

---

## 6. Notification — one, to one party

```
  ▸ NOTIFICATION                                             (1 of 1)
    ✓ delivered 05:45:31-05:00 · to submitter · to admin  no
    "Stopped cleanly. Last durable Checkpoint is step 41,200,
     digest sha256:3f9a…c201."
```

**An Eviction produces exactly one notification, to the submitter, and none to the administrator** (FR-27's testable condition). The asymmetry with a Checkpoint failure — which produces **exactly two**, one each — is load-bearing, and the UI states both facts explicitly so a reader of the contract can derive it rather than infer it.

- **Delivery never blocks the transition and never delays the Node release by more than 0 ms** (FR-23(a), FR-27). A `DELIVERY_FAILED` badge here and a still-`draining` tile would be the *forbidden* combination.
- **The copy is plain and technical.** `Checkpointing`, not "Saving your progress…". Not "Stopped 😢". Not "Your job was terminated". The subject is the run and the fact is the step. **Nothing in this system congratulates the user, apologises to them, or celebrates** — the success signal is the state badge and the released slot.

---

## 7. SURF-04b — the side panel, not a modal

- **Right-hand side panel, not a modal.** A modal would cover the state, the Checkpoint and the placement — the three things a student opens the page to read. It never opens over them; `Esc` closes and restores focus to the opener.
- **The last 10 records, newest first**, with a `+ 7 earlier records (show 4)` expander. Ten is the PRD's stated bound for a job query, so the count is a real number rather than a page of everything.
- Each row is `decision` · `sim_timestamp` · transition · reason · summary · citations. **`transition: null`** renders as an explicit `—` on non-transition records, so a reader can tell *which* records changed the state from those that only recorded a decision. Only the T-8 record changed the state; T-6 and T-3 did not.
- **The only record that is visually emphasised is the one that changed the state.** Group difference is by **group glyph and group word**, never by hue: the `1.09:1` fill difference between `{colors.surface-raised}` and `{colors.surface-base}` is decoration, and the banner hues sit roughly **dE 6.8** apart under deuteranopia.

**Keyboard.** `↑`/`↓` traverse the record list, `Home`/`End` jump, `Enter` opens a record full-width, `→` expands in place, `Esc` closes the panel. The panel is reachable by one tab stop from the job header, and **focus never moves on a background poll** — a new record arriving announces politely and the reader keeps their place.

---

## 8. Loading · Empty · Error · Success

| State | Specification |
|---|---|
| **Loading** | Skeleton rows at final geometry in both columns; the badge, Checkpoint and banner placeholders keep their height. Never a spinner over a blank field. |
| **Empty** | A job with no Decision Records yet — `No decisions recorded for this job.` The state and Checkpoint blocks still render. |
| **Error** | `Daemon unreachable — data may be stale` with the last-update instant. Last known values stay visible and marked stale; **nothing is blanked**, because a blanked state badge is indistinguishable from a released one. |
| **Not found** | A dedicated 404, never a redirect to the job list. FR-31(b) governs: a `STUDENT` querying a job that is not hers gets a 404, **not** a permission error — an error would confirm the `job_id` exists. |
| **Success** | The banner is already the success signal. **No flash, no celebratory treatment.** |

---

## 9. Traceability

| Element | Source |
|---|---|
| The whole record block | `planning/prd.md` §6.3, lines 266–269, **verbatim** |
| `EVICT` badge, summary, citations, inputs | §6.3 |
| T-8 keeps `EVICT`, `supersedes` T-6, mirrors citations | §6.4, FR-24(d), OQ-12 |
| One record per transition; one decision chain | FR-24(f), FR-19 |
| Non-`self:` citation mandatory on `EVICT` | FR-24(a), F-1, NFR-4 |
| Five-step durability, `fsync` the parent directory | FR-18(a) |
| Digest + bytes + step + timestamp together or not at all | FR-18(c) |
| 0 of 430 crash injections | `prd-addendum.md` §B.2 |
| 2 most recent verified Checkpoints never auto-removed | FR-22(b) |
| One notification to submitter, none to admin | FR-27 testable condition |
| Delivery never blocks; 0 ms release delay | FR-23(a), FR-27 |
| 10 Decision Records in a job query | FR-13 testable condition |
| `next_decision_at` | FR-13 |
| Badge, ring and terminality rules | `ux/DESIGN.md` state table; `scenario-1.md` |
| Modal-vs-panel, group differentiation | `ux/EXPERIENCE.md`; `scenario-2.md` § SURF-05 |
| 404 not 403 | FR-31(b) |
