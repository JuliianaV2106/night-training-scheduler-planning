# Wireframe 03 — Submission Form: a refusal and its contrast

**Surface:** SURF-01 Submission form · **Canonical spec:** `ux/C-UX-Scenarios/scenario-1.md`
**Theme:** **light** (the submission form is the one light-first surface in the console) · **Persona:** `STUDENT` (Kavita) · **Submitted:** `2026-09-28T14:30:00-05:00`

> **Why both states are in one wireframe.** The PRD tests this form in two directions, and a single happy-path mock would answer neither: a Job Spec declaring **31 hours** must be **admitted** with `requires_multiple_nights: true` and `estimated_completion_nights: 4`, while a Job Spec declaring **52 hours** must be **refused** with a `DENY` naming both figures and proposing a concrete scope reduction. The refusal is the design work; the admission exists here so the refusal is shown *against the thing it prevented*, because a mock that only shows refusals teaches a reader that the product refuses things.

---

## 0. The arithmetic, stated before the pixels

```
  Night Window          22:00:00 → 06:00:00 America/Bogota   =  8 h 00 min
  SIGTERM at 05:45:00 means the last 15 min are not usable training
  ─────────────────────────────────────────────────────────────────────
  Usable Night Duration                        7 h 45 min     (22:00 → 05:45)
  Max Night Span  =  5 × 7 h 45 min         = 38 h 45 min  =  38.75 h

  31 h  ÷  7.75 h  =  4.0 nights  →  requires_multiple_nights = true,  nights = 4   ✓ ADMIT
  52 h  >  38.75 h              →  over the ceiling                                    ✗ DENY
```

**The 8 h / 7 h 45 min distinction is the whole reason the ceiling is 38.75 and not 40**, and the form says so wherever it names the ceiling. A student reading "5 nights" and "8 hours" concludes 40; the module reserves the last 15 minutes before SIGTERM, so the honest number is 38.75. Quoting 40 would be a promise the scheduler cannot keep.

---

## 1. `DENY` — 52 hours declared, refused

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Skip to work region]  ● Daemon reachable  14:30:00-05:00  last update …      │
├──────────────────────────────────────────────────────────────────────────────┤
│  New Job Spec                                          Draft saved 14:28     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ ✕  DENY      Validation failed · MAX NIGHT SPAN                        │  │
│  │                                                                        │  │
│  │ Declared estimate 52 h 00 min exceeds the Max Night Span of 38 h        │  │
│  │ 45 min (5 × 7 h 45 min usable). A Job Spec above the ceiling is a       │  │
│  │ rejection, not a multi-night admission.                                 │  │
│  │                                                                        │  │
│  │ reason  VALIDATION_FAILED                                               │  │
│  │ [self:MAX-NIGHT-SPAN-v1]                                               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Reduce the scope — any one of these brings the estimate under 38 h 45 m │  │
│  │ ☐  lower `epochs`                          →  52 h  →  ~26 h             │  │
│  │ ☐  raise `gradient_accumulation_steps`    →  52 h  →  ~35 h   (memory) │  │
│  │ ☐  reduce the dataset size                 →  52 h  →  ~31 h             │  │
│  │ ☐  target a smaller base model             →  52 h  →  ~19 h             │  │
│  │                                             [ Apply selected ]          │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Model record          meta-llama/Llama-3.1-70B            sha256:4b1e…9a03  ✓  │
│  Image digest          registry…/trainer@sha256:7c1e…04aa  ✓                  │
│  gpus_per_node         1                                    ✓                  │
│  Requested VRAM        48 GB   (largest single-Node class) ✓                  │
│  Memory requests/limits 24 Gi / 24 Gi                       ✓  equal          │
│  Checkpoint interval   30 min  (must be a positive int ≤ 30) ✓                │
│  Declared estimate     52 h 00 min                           ✕  over ceiling   │
│  ────────────────────────────────────────────────────────────────────────────  │
│  Declared intent       THESIS            →  PENDING_REVIEW · not applied      │
│  Granted priority      (read from the Policy Engine on submit)                 │
│                                                                              │
│                              [ Save draft ]   [ Submit Job Spec ]             │
│                                                                              │
│  ▸ Your Pending Set is unchanged — 3 jobs. This submission was not added.     │
│                                                                              │
│  Decision record                                                               │
│    DENY · VALIDATION_FAILED · 14:30:00-05:00 · [self:MAX-NIGHT-SPAN-v1]       │
│    T-2 · transition: null                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### What this refusal is made of

| Element | Why it is there |
|---|---|
| **`DENY` in the eyebrow, `VALIDATION_FAILED` as the reason** | T-2's binding values. A refusal that renders only a red box has told the student nothing she can act on. |
| **Both numbers named — 52 h and 38 h 45 min** | FR-4(c) requires the record to name the estimate *and* the ceiling. A refusal that says only "too long" gives her nothing to divide. |
| **The ceiling shown as `5 × 7 h 45 min`, not as a bare total** | So she can see *why* it is 38.75 and not 40, and therefore whether an extension would even help. |
| **`self:MAX-NIGHT-SPAN-v1` alone, and that is legitimate** | F-1's split rule: `self:` stands alone **only for a module-owned rule**, and Max Night Span is a named module-owned class (FR-2(j), FR-4, FR-21). A refusal that *also* cited a delegated verdict would be claiming an authority the Policy Engine never exercised. |
| **A concrete scope reduction — required, not optional** | FR-4(c) names four: lower `epochs`, raise `gradient_accumulation_steps`, reduce the dataset, target a smaller base model. Each is offered **with its own projected result**, because "reduce the scope" without a number is advice, not a fix. |
| **The proposal is actionable, not a link out** | `Apply selected` edits the form in place. A student who is refused at 14:30 and sent to a wiki is a student who does not submit tonight. |
| **The Pending Set length is explicitly unchanged** | FR-4's testable condition. Stating it removes the most likely wrong inference — that a refusal consumed a queue slot. |
| **`transition: null`** | A `DENY` **refuses a request**; no job state ever existed. Contrast `PREEMPTION_REFUSED`, which refuses to *act* on a state that does — the only two records of this shape in the module. |
| **No "Try again" button, no retry affordance** | Retrying the identical spec produces the identical refusal. The affordance offered is *change something*, not *ask again*. |
| **No apology, no red field outline on the declaration** | The field is not malformed. 52 h is a perfectly valid duration; it is **over a ceiling**, which is a policy outcome, not a typo. The refusal is rendered as a decision, not as a correction of the student. |

### The one thing this form does not do

**`Declared intent: THESIS` reads `PENDING_REVIEW · not applied`, and the granted priority is read from the Policy Engine on submit** (FR-14(c), FR-17(c)). A student who typed `THESIS` must be able to see that the `THESIS` she will hold came from **Module 2's verdict on her academic standing** and not from her own keystroke — because FR-16(b) and FR-15(d) make "a self-declared tier never confers authority" a structural guarantee, and this field is where the reader either sees it or does not.

> **Open Question 11 — the refusal is correct and there is no way to appeal it.** A real thesis will eventually need a 6th night. FR-2(j) refuses it at submission and FR-4(d) refuses the job at admission, and the PRD provides **no extension mechanism for the lab administrator** — a deliberate v1 gap, recorded as OQ-11. So the form's scope-reduction proposals are not one option among several; they are currently the **only** available path. The copy says "any one of these", which is true, and the absence of an appeal route is a known v1 gap rather than an oversight. **Flagged, not designed around.**

---

## 2. `ADMIT` — 31 hours declared, accepted

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  New Job Spec                                                      14:31 -05:00│
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ ✓  ADMIT     Admitted to the Pending Set                               │  │
│  │                                                                        │  │
│  │ Estimate 31 h 00 min exceeds the 7 h 45 min usable Night Duration, so   │  │
│  │ this job will run across at least 4 nights. Your first estimated start  │  │
│  │ is 2026-09-28T22:00:00-05:00 if the fleet admits you at the next Window │  │
│  │ Activation; your position is recomputed on every recompute.              │  │
│  │                                                                        │  │
│  │ estimated_completion_nights  4      max_night_span  5                  │  │
│  │ required_vram_gb  48                  confidence  declared               │  │
│  │ [self:JOBSPEC-VALIDATION-v1] [policy:M2/…] [catalog:M5/…] [quota:M8/…]   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Model record          meta-llama/Llama-3.1-8B             sha256:b83f…21d7 ✓  │
│  Image digest          registry…/trainer@sha256:7c1e…04aa  ✓                  │
│  gpus_per_node         1                                    ✓                  │
│  Requested VRAM        24 GB   (24 GB class Node)         ✓                  │
│  Memory requests/limits 24 Gi / 24 Gi                       ✓  equal          │
│  Checkpoint interval   30 min  (positive int ≤ 30)         ✓                  │
│  Declared estimate     31 h 00 min                           ✓  4 nights      │
│  ────────────────────────────────────────────────────────────────────────────  │
│  Declared intent       THESIS            →  PENDING_REVIEW · not applied      │
│  Granted priority      THESIS  (50)      ← read from the Policy Engine       │
│  Effective Priority    THESIS 50 + 0 aged                          = 50        │
│                                                                              │
│                                            [ Submit Job Spec ]  ← enabled     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### The contrast, made explicit

| | `DENY` — 52 h | `ADMIT` — 31 h |
|---|---|---|
| Eyebrow | `DENY` · `Validation failed · MAX NIGHT SPAN` | `ADMIT` · `Admitted to the Pending Set` |
| The number that decided it | 52 h > 38 h 45 min | 31 h > 7 h 45 min, and ≤ 38 h 45 min |
| Banner border | `{colors.state-rejected}`, **1.5px**, glyph `✕` | `{colors.state-running}`, 1px, glyph `✓` |
| `requires_multiple_nights` | not returned | **`true`** |
| `estimated_completion_nights` | not returned | **`4`** |
| Scope reduction proposed | **required**, four options with projections | not applicable |
| Pending Set | **unchanged** | job added at `QUEUED_PENDING_WINDOW` |
| `transition` | `null` | `QUEUED_PENDING_WINDOW` |

**Both banners are the same `decision-banner` component.** They differ by group, glyph, weight and **word** — never by hue alone, and never by colour being the first channel.

**`requires_multiple_nights: true` is an admission, not a warning.** FR-2(i)(b) is explicit: an estimate exceeding the Usable Night Duration must set the flag and **must never be treated as a rejection on its own**. 31 hours is a legitimate thesis run; the form's job is to say *this will take four nights* and admit it, not to make a student feel she has asked for too much.

**The first estimated start is stated as an instant and hedged in the same sentence** — *"if the fleet admits you at the next Window Activation; your position is recomputed on every recompute."* A confident `22:00:00` would be a promise the Admission Order has not made yet, and FR-8 computes the order **before** any placement.

---

## 3. Validation behaviour

**Validation returns instantly and locally** — the form is not a wizard and does not block on a round trip to grade the spec.

| Rule | Feedback | Timing |
|---|---|---|
| (a) image pinned by **digest**, not tag | inline, on blur | instant |
| (b) `gpus_per_node` ∈ {1, 2} | inline select | instant |
| (c) requested VRAM ≤ 48 GB, the largest single-Node class | inline, **naming both the requested and the available class** | instant |
| (d) `requests` **==** `limits` for GPU and memory | inline, per field — quota accounting reads `requests` | instant |
| (e) `node_selector`, if present, names a Node matching a declared VRAM class | inline | instant |
| (f) `restart_policy` must not request a restart that **silently re-enters a Night Window without re-admission** | inline, with the reason | instant |
| (g) `checkpoint_interval_minutes` a positive integer **≤ 30** (F-17) | inline — a longer interval would let progress since the last Checkpoint exceed what the 300 s budget can plausibly flush at the Ramp | instant |
| (h) Module 5 model record exists **and is not deprecated** | on submit; a deprecated record is a `DENY` citing `catalog:M5/…` | delegated |
| (i) an estimated duration is declared, or derivable from the model record | inline | instant |
| (j) **estimate ≤ 38.75 h** | on submit — a `DENY` citing `self:MAX-NIGHT-SPAN-v1` | instant, local |
| Delegated verdicts | `entitlement:M1/…`, `policy:M2/…`, `catalog:M5/…`, `quota:M8/…` | delegated, **instant response** |

**Every delegated verdict consulted appears in T-1's citation list, and every one is shown on the banner** — an admitted job carries the same citation discipline as a refused one, because SM-5's target is *100%* of decisions presented to a user, absolute.

**Refusals are `aria-live="assertive"`; success is `role="status"` (polite).** A student using a screen reader must hear a refusal. A refused form that changes silently is a form that will be submitted again unchanged. **The asymmetry is the three-case assertive reservation in `EXPERIENCE.md`**: every refusal on this surface is an adverse decision on the viewer's own job — the job she is submitting, about which nothing was queued — so all of them are assertive, and none of them is someone else's record. On the board, a 22-placement activation is polite, because it is not about the viewer.

**Nothing is submitted without a decision.** There is no optimistic-accept path and no "we'll check and email you": the `DENY` in §1 is the response, and it is the response the PRD's testable condition asserts.

---

## 4. Loading · Empty · Error · Success

| State | Specification |
|---|---|
| **Loading** | Per-field skeletons at final geometry; the submit button shows a 1px `{colors.border-structure}` border and a 20px-wide indeterminate bar. **The form never greys out wholesale** — a student must be able to read and correct a field while a delegated verdict is in flight. |
| **Empty** | The form renders with declared-timeout defaults and no error treatment. Empty is a legitimate starting point, not a failure. |
| **Error — field** | Inline beneath the field, `{typography.label-sm}`, glyph `✕` + text. **Never a red border alone**, and never a red border on a field whose value is *valid but over a ceiling*. |
| **Error — delegated authority** | Announces **assertively** — an adverse decision on the viewer's own submission. Naming the module and the fact that its verdict is missing. **The form does not proceed on an unresolved authority** — the module never invents an `ALLOW` (A-15, OQ-1). |
| **Error — daemon** | `Daemon unreachable — data may be stale` in the strip; the form stays filled, the draft persists, and the submit button is `aria-disabled` but **not dimmed**. **A student who loses a typed 52-hour spec to a network blip has lost an evening's work**, so the draft autosaves locally. |
| **Success** | The `ADMIT` banner, and the Pending Set entry at `QUEUED_PENDING_WINDOW` with its position. **No confetti, no green flood** — the admission is a state, and it is stated as one. |

---

## 5. Accessibility · the refusal specifically

- **The 52 h refusal is the highest-stakes record a student will ever see**, alongside a refused Preemption. It announces **assertively on first appearance** — an adverse decision on the viewer's own job, one of the three reserved cases — because a screen-reader user who is refused and hears nothing cannot tell refusal from silence.
- **Summary ≤ 200 characters** (§6.1). SM-C4: a longer summary is not a better one. The banner summary above is 197 characters; the refusal's *reasoning* lives in the four scope-reduction options beneath it, not in a longer sentence.
- **The form is fully keyboard-operable and never validates on blur-then-submits-twice.** `Enter` in any field submits once. A second submission cannot be produced by a keypress, because a duplicate `DENY` is a duplicate Decision Record and the record log is the module's audit trail.
- **Light theme only.** The submission form is the one surface where a student arrives without prior context, often on a shared machine, in daylight. `{colors.text-primary}` on `{theme.light.bg.base}` is 16.1:1, and every field label is above 4.5:1.
- **No field relies on placeholder text as its label.** The 52 h estimate field's label reads `Declared estimate`; a placeholder reading `e.g. 31 h` would be a hint that a student could mistake for a default and then be blamed for.

---

## 6. Traceability

| Element | Source |
|---|---|
| 31 h → `requires_multiple_nights: true`, `estimated_completion_nights: 4`, admitted | FR-2(i) testable condition |
| 52 h → `DENY`, `self:MAX-NIGHT-SPAN-v1`, names both figures, ≥ 1 scope reduction, Pending Set unchanged | FR-4(c) + testable condition |
| `DENY` / `VALIDATION_FAILED` | §6.4 T-2 (binding) |
| `self:` alone legitimate for a module-owned rule | F-1 split rule, §6.2 |
| Max Night Span = 5 × 7 h 45 min = 38.75 h | §4 glossary; FR-2(j); A-12 |
| Usable Night Duration 7 h 45 min, 22:00–05:45 | FR-2(i)(b), F-15 |
| Night Window exactly 8 h, America/Bogota, no DST | §4 glossary; decision D-1; F-31 |
| The four scope reductions | FR-4(c) |
| Validation rules (a)–(k) | FR-2 — **(k)** is the 2-GPU/48 GB rule from E-3; see `scenario-1.md` SURF-01.4 |
| `checkpoint_interval_minutes` ≤ 30 | FR-2(g), F-17 |
| Requests == limits for GPU and memory | FR-2(d) |
| Declared intent is `PENDING_REVIEW`, not applied | FR-14(c), FR-17(c) |
| Granted priority read from the Policy Engine | §2.1 UJ-1, FR-17 |
| T-1 citation list incl. `quota:M8/…` | §6.4 T-1 |
| No extension mechanism; scope reduction is the only path | **Open Question 11** |
| 2-worker refusal with referral to Module 10 | §2.1 edge case |
| 200-character summary cap | §6.1; SM-C4 |
| Light theme, contrast | `ux/DESIGN.md`; `ux/EXPERIENCE.md` |
