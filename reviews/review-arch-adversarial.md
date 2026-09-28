# Adversarial Review — `planning/ARCHITECTURE.md` (Module 9 — Night Training Scheduler)

| Field | Value |
|---|---|
| Artifact reviewed | `planning/ARCHITECTURE.md` (711 lines, commit `3288df1`) |
| Source of truth | `planning/prd.md` |
| Lens | Adversarial (`bmad-review-adversarial-general`) |
| Reviewer | OpenCode, **fresh session** (independent from the authoring agent `bmad-architecture`) |
| Triage | Team (human decision), with Claude Code as audit assistant |
| Date | 2026-09-28 |
| Result | 15 findings + 1 closing note: **15 Accept · 0 Defer · 0 Reject** (F-4 accepted as a PRD amendment) |

**Why everything is accepted.** Each finding points to a concrete contradiction between an AD-n rule and a PRD requirement, or to a rule that cannot be tested as written. None is a matter of taste. The reviewer also noted that F-3, F-4, F-5 and the T-11 references had already been raised by the authoring agent's own internal gate and survived the revision, which confirms the value of an independent review.

---

| # | Finding (summary) | Sev. | Triage | Resolution |
|---|---|---|---|---|
| F-1 | AD-6 gates preemption on the *victim's* tier and never states FR-16(b)'s challenger gate (granted ∈ {THESIS, URGENT} **and** effective ≥ victim + 20). FR-16's testable cases (URGENT@90 preempts THESIS@50; aged EXPLORATION@40 refused vs 50) are unreachable. | Critical | **Accept** | AD-6 Rule states the challenger's two-part gate verbatim from FR-16(b). The Preemption Margin is a **priority delta of 20**, not a slot count. The refusal reason names which gate failed (authority or margin). |
| F-2 | `seq` is both the Admission rank and a per-batch counter, so it is neither unique nor monotonic, yet AD-2 orders the log by it and AD-5 folds `seq ≤ last_committed`. This breaks NFR-10 (0 lost / 0 duplicated). | Critical | **Accept** | The log is keyed and folded on `decision_id` (monotonic, PRD §6.1). `seq` is only the intra-batch tiebreak. The fold watermark is `last_committed_decision_id`. |
| F-3 | AD-1's "closed" scheduled-event inventory omits six PRD-required instants: 21:30 pre-verification, the 21:59 verification deadline, the periodic checkpoint interval, T-15 Retention Deadline, the FR-29 fault events, and the FR-10 1 Hz drift check. AD-5 would drop them on restore. | Critical | **Accept** | AD-1 inventory extended with all six. AD-5 rebuilds the queue from exactly that inventory. |
| F-4 | AD-8 answers every authorisation failure with 404, but PRD FR-31(e) says 403 for a wrong role. The architecture contradicts the PRD. | Critical | **Accept (PRD amendment)** | Team decision: keep **404** (it never discloses that a job or route exists, which is AD-8's security goal and matches the UX 404-not-403 rule, UX review E-5). **PRD FR-31(e) is amended to 404**; only 401 distinguishes "no identity" from "no permission". |
| F-5 | AD-8 requires a role-mismatch Decision Record, but PRD §6.4 has no row for it and AD-3 would accept an unmapped record. | High | **Accept** | An authorisation refusal is a **LifecycleEvent** (actor, route, time), not a Decision Record, because it is not a scheduling decision. AD-3's rejection list adds "no PRD §6.4 row exists for this record" and is declared closed. |
| F-6 | AD-7 ties Checkpoint `VERIFIED` to a non-existent `RESUMED_FROM` transition in the same transaction, which would make every T-8 fail its 05:53 guard. | High | **Accept** | Two separate records: the T-8 record at dawn (Checkpoint durable and digest recorded) and the T-12 record at 21:30 (digest re-verified). The non-existent transition name is removed. |
| F-7 | The PROCESS_EXIT retry budget resets on every re-placement, so a crashing job can loop all night; exhaustion routes to the deleted T-11, leaving the slot held past 06:00. | High | **Accept** | Budget = **1 automatic retry per night** (PRD T-22), reset only at NIGHT_CLOSE; exhaustion routes to **T-23 only**. All T-11 references deleted. |
| F-8 | AD-7 halts all checkpoint writes on "sustained pressure" (undefined), which would make the 05:45 ramp fail every job. Reason codes are written with an `NFR-13` prefix that AD-3 would reject. | High | **Accept** | Transcribe NFR-13 (1)(2) verbatim: refuse **new submissions** and emit the escalation record within 1 simulated minute. Store pressure **never** blocks a Ramp or Preemption checkpoint write. Reason codes are the registered `STORE_FULL` / `DISK_PRESSURE_ESCALATION`. |
| F-9 | AD-6 sends a preempted victim to *tomorrow's* order (contradicting T-14 / FR-16(e): re-queue immediately, same-night re-placement allowed), and caps preemption globally per window instead of per victim (FR-16(f)). | High | **Accept** | Restore T-14's immediate re-entry with the original submission time. The cap is **per victim per window** (a flag cleared at WINDOW_ACTIVATION). PREEMPTION_WINDOW_CLOSE is removed. |
| F-10 | AD-4's node order is node_id-only, which deletes FR-13(a)'s prior-Node preference and FR-13(b)'s lowest-allocation rule. `Job.last_node_id` is never read. | High | **Accept** | Order: (1) prior Node if Eligible, (2) lowest current allocation count, (3) fixed-width `node_id` ascending. The Decision Record lists the candidates considered (FR-13(c)). |
| F-11 | §1.5's run-gate list omits S-3 and the NFRs named by FR-30(d), and adds undefined items (F-ids as checks, "AD rules where testable"). | High | **Accept** | The run gate is exactly PRD FR-30(d): S-1…S-3 + NFR-4, 5, 6, 7, 10, 14, 16, each enumerated by name. |
| F-12 | "The reaper runs at 03:00 and never inside a Night Window" is self-contradictory (03:00 is inside 22:00–06:00). The delete predicate also invents a grace period for non-terminal jobs. | High | **Accept** | The reaper runs at **03:00 inside the window** (PRD FR-7(c), FR-22). The prohibition is removed. The delete predicate restores FR-22(a)'s two arms verbatim: EXPIRED past the 7-day grace, **or** superseded beyond the latest 2 verified. |
| F-13 | The server-rendered console has no authentication mechanism; every route requires a bearer token, which a browser page cannot supply. | High | **Accept** | Console login exchanges a validated Module 1 fixture bearer token for an **HttpOnly, SameSite=Strict session cookie**. The console route resolver reads the actor from the session and applies AD-8's single ROLE_CAPABILITY table. |
| F-14 | The PRD §6.4 decision map is stored as mutable rows in the same SQLite file, with no version or checksum, so it can drift. | High | **Accept** | The map ships as **versioned, read-only data** (a file in the image, outside the fold), checksummed; startup fails on mismatch. |
| F-15 | §5.2 commits the T-8 record *before* releasing the slot, contradicting the release-then-emit rule (a crash in between would hold a slot past 06:00). Diagrams skip the Committer. §5.1 labels a blocked-activation record T-18. | High | **Accept** | §5.2 reordered to **release → emit**. All three sequences route through the Committer. The §5.1 blocked-activation record is labelled `transition: null`. |
| Note | Five elastic or undefined terms inside Rules: "closed inventory", "batch boundary", "a recorded reason why not", "AGING_RATE-weighted age", "sustained pressure". | — | **Accept** | Each term is replaced by its definition (the enumerated inventory, one drained instant, the named reason code, PRD FR-14's formula, and removal per F-8). |

---

## Outcome

All accepted resolutions are applied to `planning/ARCHITECTURE.md`. F-4 also amends PRD FR-31(e) (403 → 404) as a recorded team decision. The AD-1…AD-8 identifiers are unchanged.
