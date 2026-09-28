# Wireframe 01 — Status Board at 05:46:01

**Surface:** SURF-02 (+ SURF-02a, SURF-02b) · **Canonical spec:** `ux/C-UX-Scenarios/scenario-2.md`
**Theme:** dark, `{theme.dark.bg.base}` · **Persona:** `LAB_ADMIN` (Ines) · **Instant:** `2026-09-28T05:46:01-05:00`

> **Why this instant.** One minute after the Eviction Ramp began and one second after the mandatory edge case released its Node. It is the only frame in which a `draining` slot, a `cordoned`-and-released slot, a `EVICTION_FAILED` badge and twenty released slots are on screen **at the same time** — so the roll-up arithmetic below is fully auditable, which is the whole purpose of this wireframe.

---

## 1. The frame

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Skip to work region]                                                                            │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ● Daemon reachable   last update 05:46:01-05:00   05:46:01-05:00   [1×][60×][360×][1440×][⏸]   │  SURF-02a
│   next decision point 05:53:00 in 6m 59s                        Run ▸ · LAB_ADMIN only            │   + SURF-02b
│   Simulated clock — v1 models no real GPU, no container execution, no telemetry, no weights.    │
├──────────────┬─────────────────────────────────────────────────────────────────────────────────┤
│ Board        │  ╔═════════════════════════════════════════════════════════════════════════╗  │
│ Admission …  │  ║ 33 slots · 0 held · 0 reserved · 1 draining · 1 cordoned · 31 idle          ║  │  roll-up
│ Pending Set  │  ╚═════════════════════════════════════════════════════════════════════════╝  │
│ Event log    │                                                                                 │
│ ─────────    │  ┌───────────────────────────────────────────────────────────────────────────┐  │
│ Handover     │  │ ⛔ FAIL   Decision · fail        JOB-0417   CHECKPOINT_WRITE_FAILED        │  │  adverse
│ Node detail  │  │ Checkpoint write failed on ws-gpu-19. Allocation released 05:46:01;      │  │  banner
│ Run          │  │ last verified Checkpoint retained, byte-identical.                        │  │
│              │  │ [node-state:M3/…] [self:EVICTION-RAMP-v1]                                │  │
│              │  └───────────────────────────────────────────────────────────────────────────┘  │
│              │  ┌───────────────────────────────────────────────────────────────────────────┐  │
│              │  │ ⊘ CORDON  ws-gpu-19   EVICTION_CHECKPOINT_WRITE_FAILED   05:46:00         │  │
│              │  │ Cordon Request issued to Module 3;     Node not Eligible for the        │  │  adverse
│              │  │ remainder of the night and until a human clears it.                      │  │
│              │  │ [node-state:M3/…] [self:EVICTION-RAMP-v1]                                │  │
│              │  └───────────────────────────────────────────────────────────────────────────┘  │
│              │                                                                                 │
│              │   ws-gpu-01   ws-gpu-02   ws-gpu-03   ws-gpu-04   ws-gpu-05   ws-gpu-06  …    │  │
│              │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐         │  │
│              │  │○ FREE  │  │○ FREE  │  │○ FREE  │  │○ FREE  │  │○ FREE  │  │○ FREE  │         │  │
│              │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘         │  │
│              │                                                                                 │
│              │   ws-gpu-07   ws-gpu-08   ws-gpu-09   ws-gpu-10   ws-gpu-11   ws-gpu-12  …    │  │
│              │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐         │  │
│              │  │▼ DRAIN │  │○ FREE  │  │○ FREE  │  │○ FREE  │  │○ FREE  │  │○ FREE  │         │  │
│              │  │  1/61s │  │        │  │        │  │        │  │        │  │        │         │  │
│              │  │ 4m 39s │  │        │  │        │  │        │  │        │  │        │         │  │
│              │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘         │  │
│              │   …                                                                             │  │
│              │   ws-gpu-19                                                                              │
│              │  ┌────────────────────────┐                                                                  │
│              │  │⊘  CORDONED  ⚡          │  cordoned · EVICTION_CHECKPOINT_WRITE_FAILED                   │
│              │  │   JOB-0417              │  EVICTION_FAILED · not terminal · released 05:46:01            │
│              │  │   0 held                │  FAILED-JOB BADGE, node-global reason, no slot label           │
│              │  └────────────────────────┘                                                                  │
│              │   …                                                                             │  │
│              │   server-gpu-01                                                                           │
│              │  ┌────────┐  ┌────────┐                                                                 │
│              │  │○ FREE  │  │○ FREE  │  1 × 48 GB   2 × 48 GB                                              │  │
│              │  └────────┘  └────────┘                                                                 │
│              └─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Status strip — SURF-02a

| Field | Value | Rule it demonstrates |
|---|---|---|
| Daemon | `● Daemon reachable` | `{colors.text-secondary}`. The unreachable treatment is `{colors.ui-adverse}` at label weight — a **dedicated token**, so a connection problem never looks like an `EVICTION_FAILED` job. |
| Last update | `05:46:01-05:00` | `{typography.mono-data}`. **The `-05:00` offset is present on every simulated instant.** An operator must never be unsure whether she is reading simulated or wall-clock time. |
| Simulated clock | `05:46:01-05:00` | `{typography.mono-data-lg}`, `aria-live="off"` per tick. Readable on demand; a separate throttled node announces at most once per 30 s. |
| Rate | `[1×][60×][360×][1440×][⏸]` | Rendered order **is** the digit-key order: `1`→1× … `4`→1440×, `Space`/`0`→pause. `role="radiogroup"`, 5 radios, `360×` checked. `⏸` is deliberately not a digit. |
| Countdown | `05:53:00 in 6m 59s` | The next decision point is the **SIGKILL instant**, so this countdown is real. `aria-live="off"`. It **stops at 05:53:00 and stays visible** — nothing in this console expires. |
| Disclaimer | `v1 models no real GPU, no container execution, no telemetry, no weights.` | A-3. Un-dismissable, in the strip, on every route. |
| Run | `Run ▸` | `LAB_ADMIN` only → SURF-10. |

**The clock is chosen deliberately for this frame.** At 1440× an operator watching an eight-minute Ramp may never see the 05:50:00–05:53:00 reserve at all (**S3-Q5**), and FR-16(c)'s Checkpoint Budget judgement is the one decision that benefits from being watched in real time.

---

## 3. The roll-up arithmetic — auditable on purpose

```
33 slots · 0 held · 0 reserved · 1 draining · 1 cordoned · 31 idle
```

| Bucket | Count | Which slots |
|---|---|---|
| `held` | **0** | no slot holds a `RUNNING` job at 05:46:01 — SIGTERM reached all 22 placements at 05:45:00 |
| `reserved` | **0** | no Module 4 reservation overlaps this window |
| `draining` | **1** | `ws-gpu-07` — still `CHECKPOINTING` at 61 s of its 300 s budget |
| `cordoned` | **1** | `ws-gpu-19` — released at 05:46:01, locally not-Eligible |
| `idle` | **31** | 20 released placements + 11 never-placed slots |
| | **33** | |

**Reconciliation against the 22:00 activation** (FR-13's placement order: lowest slot-allocation count, ties by `node_id` ascending, so all 33 slots start at 0 and the order is deterministic):

```
22 placements at 22:00:00
  20  released, now idle      (ws-gpu-01…06, 08…18, 20, server-gpu-01 slot 0, server-gpu-01 slot 1)
   1  draining                (ws-gpu-07)
   1  EVICTION_FAILED, released, cordoned   (ws-gpu-19)
  ──
  22  ✓   +  11 never placed  =  33 slots
```

**Two rules this frame exists to prove:**

1. **D-c — a `draining` slot is never shown as idle.** `ws-gpu-07` is past SIGTERM and still holds its allocation. Invariant S-1 permits that hold until 06:00:00, so a tile reading `○ available` here would be **lying during the most safety-critical eight minutes of the night**. It is `▼` and it is counted `draining`, not `held` — `held` means a `RUNNING` job, so a draining count that always read 0 would be a roll-up that can never report a drain.
2. **D-a — bucket precedence `held → draining → reserved → cordoned → idle`.** `ws-gpu-19` is *idle* **and** *cordoned*. It counts once, as `cordoned`, so the operator sees the condition on the roll-up — while its **tile** still shows its occupancy through the eligibility mark, per `EXPERIENCE.md`'s rule: *occupancy paints the tile, eligibility adds a mark on it.*

**The roll-up is never the only place a count appears.** Every number above is also derivable from the tiles, and every idle tile carries a reason — so a wrong roll-up cannot be the only evidence of a wrong board.

---

## 4. The two adverse banners

Both are `decision-banner` instances at the SURF-04.6 anatomy: eyebrow · summary ≤ 200 chars · reason code · full citation list. **Neither navigates away** — the board does not change route under the person reading it.

**`FAIL` — JOB-0417, `CHECKPOINT_WRITE_FAILED`** (T-10, FR-23)

- **Left border `{colors.state-rejected}`** (red). The *decision* is `FAIL`, and DESIGN.md's later, reasoned paragraph puts the `FAIL` **banner** in `state-rejected` while the `FAILED` **job badge** stays pink — a different component carrying a different fact. Recorded as conflict #4 in `ux/_progress/00-design-log.md` §4.
- **Citations: `node-state:M3/…` first, then `self:EVICTION-RAMP-v1`.** Both are mandatory — FR-24(a) requires at least one non-`self:` citation on every `EVICT` and `PREEMPT`, and stopping a user's work may never be justified by a module-owned rule alone.
- The summary states what is **retained**, not only what failed.

**`CORDON` — ws-gpu-19** (FR-23(c))

- A non-transition record. The banner states the exclusion is **optimistically pending Module 3's acknowledgement** (A-15) — this module's decision until Module 3 agrees, not a health verdict Module 3 never returned.
- The **cause string is the load-bearing text**, because FR-23(i)'s false positive is a kubelet DiskPressure condition rather than a faulty Node. "Unhealthy" would not be actionable; this string is.

---

## 5. The three tiles that carry the design

### `ws-gpu-07` — `draining`

```
  ┌──────────────┐
  │ ▼  DRAINING  │     occupancy:  ▼  ·  label "DRAINING"
  │  1/61s       │     {colors.node-draining} = {colors.state-checkpointing}
  │  4m 39s      │     + 1px {colors.border-structure} edge
  └──────────────┘
  accessible name:
    ws-gpu-07 slot 1, draining, occupied by another job, checkpointing 61 of 300 seconds
```

- **The countdown is budget-scoped, not Ramp-scoped-looking.** The tile shows *elapsed against the 300 s Checkpoint Budget*. The SIGKILL instant is carried **once, in the status strip** — where it belongs — so the tile is not quoting a deadline twice.
- `ws-gpu-07` is **not Kavita's job**, so FR-31(b) applies: the `job_id` is **absent**, replaced by `occupied by another job` with no identifier to mask (**D-b**).

### `ws-gpu-19` — released, cordoned, and the reason is legible

```
  ┌──────────────────────────────┐
  │ ⊘   CORDONED    ⚡           │   eligibility mark + job badge
  │     JOB-0417                 │   {colors.node-cordoned} · {colors.state-eviction-failed}
  │     0 held                   │   EVICTION_FAILED
  └──────────────────────────────┘
  cordoned · EVICTION_CHECKPOINT_WRITE_FAILED
  EVICTION_FAILED · not terminal · released 05:46:01
```

- **Occupancy and eligibility are visibly different axes.** The slot is **free** — released at 05:46:01, `0 held` — and the `⊘` is an *eligibility* mark. A red-brown `cordoned` tile next to an orange `⚡` badge in the same 44px box is the composition rule doing its job: the machine is out of service, the job is not finished, and neither fact is the other's.
- **The job badge is `{colors.state-eviction-failed}` `#FFA657`, glyph `⚡`, label "Eviction failed" — and carries NO 1px terminal ring**, because T-20 returns it to the Pending Set tonight. A ring here would tell Ines the student is out of options when she is not.
- **Its name reads as terminal and it is not** — which is why `#FFA657` appears nowhere else in either job-state set. The documented limit: under deuteranopia `{colors.state-rejected-light}` and `{colors.state-eviction-failed-light}` converge to roughly **dE 1.6**, so the `⚡`/`✕` glyph and the label carry the distinction. Colour is the third channel and never the first.
- **The GPU is free. The job is not waiting on a human.** It re-admits tonight onto a *different* Eligible Node.

### A released slot — `ws-gpu-01`

```
  ┌──────────────┐
  │ ○  FREE      │     {colors.node-available}
  └──────────────┘
  reason: FREE · released 05:45:58
```

- **An idle slot is never blank, at any hour** (FR-25(d), unconditional). The reason string is not a tooltip; it is in the accessible name.
- The reason here is a timestamp, because this slot was *released by the Ramp* — different information from a slot that was never occupied, and the tile should not flatten the two.

> ⚠ **Finding for `[V]` — the reason vocabulary has a hole.** The six codes in `EXPERIENCE.md`'s Reason panel (`M3_CORDONED`, `M4_RESERVED`, `VRAM_CLASS_INSUFFICIENT`, `NO_ELIGIBLE_NODE`, `CAPACITY_EXHAUSTED`, `PRIOR_NODE_INELIGIBLE`) all describe **why a Node was excluded**. None describes a slot that was **Eligible, free, and simply not needed** — the `ws-gpu-21…31` case at 22:00, and every slot here at 05:46. The wireframe renders `FREE` and the timestamp, which is honest, but **`FREE` is not a PRD reason code** and a code for *surplus capacity* is missing from the spine. Carried to `ux/_progress/validation-report.md`; not invented here.

---

## 6. Geometry · accessibility · states

**No horizontal scroll, ever.** 33 tiles × 44px = **1452px**, which already exceeds a 1440px viewport before one gap and before the left rail. A board whose right edge is off-screen cannot answer *are all GPUs released* — the first thing Ines checks at 07:00. The production layout therefore **wraps into node-labelled row groups**; the grid above is shown in 8 columns for width.

- `role="grid"`, **one row per Node, one cell per GPU slot**, roving `tabindex` — the grid is **one tab stop**. `server-gpu-01` is announced as two slots of one node and reached with `←`/`→`.
- Every cell name is `‹node_id› slot ‹n›, ‹occupancy label›, ‹eligibility label if any›, ‹job_id or reason›` — four fields, because a name that can hold only one attribute is a name that lies.
- **Every state carries colour *and* glyph *and* text label** (NFR-15). Glyphs are `aria-hidden` throughout: a `⚡` announced as "high voltage" and a `⏸` announced as "check mark button" are worse than no glyph.
- Tile **44px height floor, no width floor**; the ordinal, glyph and state label never leave the tile, and the `job_id` truncates to 8 characters visually while staying whole in the accessible name.
- `Skip to work region` is the first focusable element on every route — without it a keyboard user crosses eight-plus controls in the strip and rail on each one. That is SC 2.4.1 Bypass Blocks at Level A, already inside the AA claim NFR-15 makes.
- **The frame does not collapse** at any width: no sheet, no drawer, no stacked column. Below the stated desktop floor the console renders a **viewport notice rather than silently clipping**, because a clipped operations board is worse than an honest refusal.

**The other board states.** *Loading* — 33 outlined placeholders at final geometry, never a spinner over a blank field, because layout shift during a Fast-Forward drain is disorienting. *Error* — `Daemon unreachable — data may be stale` with the last-update instant, controls `aria-disabled` but **not dimmed** (at 40% `{colors.text-secondary}` composites to 2.40:1, and a control the operator cannot read is the vanished control), and **no slot, badge or counter updates** while in that state. *Success* — **no flash, no celebration**; the success signal is the countdown marker and the tiles reaching their terminal state, with a single 120 ms background wash on a changed tile that `prefers-reduced-motion` replaces with a 1px border.

---

## 7. Traceability

| Element | Source |
|---|---|
| 33 slots · F-42 · `A-4` | §2, §7.2 |
| 05:45:00 SIGTERM · 05:53:00 SIGKILL · ±2 s | FR-19(a), NFR-5 |
| `ws-gpu-19` released 05:46:01 | FR-23(a) — release before diagnosis, **0 ms** delay |
| Two notifications, one each party | FR-23(f), FR-27 |
| `CORDON` then exactly one `CORDON_CLEARED` | FR-23 testable condition, FR-26(c) |
| Roll-up format | scenario 2 step 1, verbatim |
| Bucket precedence | **D-a**, `00-design-log.md` §5 |
| `draining` never idle | **D-c**, Invariant S-1 |
| Foreign `job_id` suppressed | FR-31(b), **D-b** |
| `FAIL` banner red, `FAILED` badge pink | DESIGN.md conflict **#4** |
| Tile edge token | DESIGN.md conflict **#1** — `{colors.border-structure}` |
| Rate set and key order | FR-28(a), NFR-5 at every rate |
| Four-field cell name | EXPERIENCE.md accessibility |
| No scroll, wrapping rows | **design decision**, SURF-02.2 |
