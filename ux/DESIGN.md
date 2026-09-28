---
name: Night Training Scheduler
description: Visual identity for a GPU night-window operations console and student submission surface. Dark-first for the lab admin on night shift, light for the student submitting at 14:30. Every one of the 9 job states and 5 node-slot states carries colour + glyph + text label, never colour alone.

# ---------------------------------------------------------------- theme: dark
# Operations console (Ines, night shift). Default theme.
colors:
  surface-base: '#0E1116'
  surface-sunken: '#090C10'
  surface-raised: '#161B22'
  surface-overlay: '#1C2330'
  border-subtle: '#2A323D'
  border-strong: '#3D4757'
  border-structure: '#667485'
  text-primary: '#E6EDF3'
  text-secondary: '#A9B4C0'
  text-muted: '#7D8894'
  citation-ink: '#8B95A1'
  text-on-accent: '#0E1116'
  accent: '#58A6FF'
  accent-hover: '#79C0FF'
  focus-ring: '#79C0FF'
  ui-adverse: '#FFB3C1'

  # --- job states: the 9 of PRD section 4.1, verbatim ---------------------
  state-rejected: '#F85149'
  state-queued-pending-window: '#7EA6D9'
  state-running: '#3FB950'
  state-checkpointing: '#D29922'
  state-evicted-resumable: '#A371F7'
  state-completed: '#56D364'
  state-failed: '#DB61A2'
  state-eviction-failed: '#FFA657'
  state-expired: '#8B949E'

  # --- node-slot states: 5, rendered per GPU slot (F-42) ------------------
  node-available: '#4CC9A0'
  node-running: '#3FB950'
  node-draining: '#D29922'
  node-reserved: '#79C0FF'
  node-cordoned: '#C2884A'

  # --- light theme: student submission surface + export ------------
  surface-base-light: '#FFFFFF'
  surface-sunken-light: '#F6F8FA'
  surface-raised-light: '#F6F8FA'
  surface-overlay-light: '#FFFFFF'
  border-subtle-light: '#D0D7DE'
  border-strong-light: '#AFB8C1'
  border-structure-light: '#7D8792'
  text-primary-light: '#1F2328'
  text-secondary-light: '#59636E'
  text-muted-light: '#636C76'
  citation-ink-light: '#5B6570'
  text-on-accent-light: '#FFFFFF'
  accent-light: '#0969DA'
  accent-hover-light: '#0550AE'
  focus-ring-light: '#0550AE'
  ui-adverse-light: '#82071E'
  state-rejected-light: '#CF222E'
  state-queued-pending-window-light: '#41719F'
  state-running-light: '#1A7F37'
  state-checkpointing-light: '#9A6700'
  state-evicted-resumable-light: '#8250DF'
  state-completed-light: '#116329'
  state-failed-light: '#BF3989'
  state-eviction-failed-light: '#BC4C00'
  state-expired-light: '#72603A'
  node-available-light: '#0F7B6C'
  node-running-light: '#1A7F37'
  node-draining-light: '#9A6700'
  node-reserved-light: '#0550AE'
  node-cordoned-light: '#8F4A12'

typography:
  display:
    fontFamily: 'Inter'
    fontSize: 28px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  title:
    fontFamily: 'Inter'
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.3'
  heading:
    fontFamily: 'Inter'
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.4'
  body:
    fontFamily: 'Inter'
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.5'
  label:
    fontFamily: 'Inter'
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.4'
  caption:
    fontFamily: 'Inter'
    fontSize: 11px
    fontWeight: '400'
    lineHeight: '1.4'
  # Monospace is a SEMANTIC class, not a decorative one. Anything that is a
  # timestamp, a job_id, a digest, or a node_id renders in mono-data.
  mono-data:
    fontFamily: 'JetBrains Mono'
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.45'
  mono-data-lg:
    fontFamily: 'JetBrains Mono'
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.45'
  mono-label:
    fontFamily: 'JetBrains Mono'
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.04em
  mono-column:
    fontFamily: 'JetBrains Mono'
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.45'
    fontVariantNumeric: 'tabular-nums'

rounded:
  xs: 2px
  sm: 3px
  DEFAULT: 3px
  md: 4px
  lg: 6px
  full: 9999px

spacing:
  '0.5': 2px
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 20px
  '6': 24px
  '8': 32px
  '10': 40px
  row-dense: 28px
  row-default: 36px
  gutter: 16px
  panel-gap: 12px
  banner-inset: 12px

components:
  # Every colour-valued key below is written as a pair: the dark binding is the
  # literal that stands, the `light:` sibling is what a STUDENT surface resolves
  # it to. A component with no `light:` key resolves to its own literal in both
  # themes, which is why the structural neutrals are named here once and themed
  # once. Pairs are listed in `colors:` in the same order.
  glyph-font: 'JetBrains Mono'
  status-badge:
    radius: '{rounded.full}'
    height: 20px
    paddingX: '{spacing.2}'
    font: '{typography.mono-label}'
    glyph: 'aria-hidden decorative; the text label carries the meaning'
    label: 'always rendered; never icon-only'
  node-slot-tile:
    radius: '{rounded.md}'
    size: 44px
    border: '1px solid {colors.border-structure}'
    borderLight: '1px solid {colors.border-structure-light}'
    font: '{typography.mono-label}'
  decision-banner:
    radius: '{rounded.md}'
    padding: '{spacing.banner-inset}'
    borderLeft: '3px solid'
    summary: '{typography.body}'
    citation: '{typography.mono-label}'
    groupGlyph: 'one per group, aria-hidden; the group word in the eyebrow is the accessible channel'
  citation-chip:
    radius: '{rounded.sm}'
    paddingX: '{spacing.1}'
    paddingY: '2px'
    font: '{typography.mono-label}'
    background: '{colors.surface-overlay}'
    backgroundLight: '{colors.surface-raised-light}'
    ink: '{colors.citation-ink}'
    inkLight: '{colors.citation-ink-light}'
  clock-control:
    radius: '{rounded.sm}'
    height: 28px
    font: '{typography.mono-data}'
    activeBackground: '{colors.accent}'
    activeBackgroundLight: '{colors.accent-light}'
    activeForeground: '{colors.text-on-accent}'
    activeForegroundLight: '{colors.text-on-accent-light}'
  data-table:
    rowHeight: '{spacing.row-dense}'
    headerHeight: 24px
    cellPaddingX: '{spacing.2}'
    numericAlign: 'right'
    rowRule: '1px solid {colors.border-structure}'
    rowRuleLight: '1px solid {colors.border-structure-light}'
  reason-panel:
    radius: '{rounded.md}'
    background: '{colors.surface-raised}'
    backgroundLight: '{colors.surface-raised-light}'
    border: '1px solid {colors.border-structure}'
    borderLight: '1px solid {colors.border-structure-light}'
    padding: '{spacing.3}'
  focus-ring:
    outline: '2px solid {colors.focus-ring}'
    outlineLight: '2px solid {colors.focus-ring-light}'
    outlineOffset: '2px'
  daemon-status-strip:
    ink: '{colors.ui-adverse}'
    inkLight: '{colors.ui-adverse-light}'
    disabledInk: '{colors.text-secondary}'
    disabledInkLight: '{colors.text-secondary-light}'
    note: 'disabled controls stay above 4.5:1; unavailability is carried by aria-disabled plus the label, never by opacity alone'
---

# Night Training Scheduler — Design System

Visual identity for two surfaces that serve two people at two hours of the same day. Ines Okonkwo watches this at 21:59:50 on a dark room; Kavita fills in a Job Spec at 14:30 on a bright one. Everything below serves the constraint that governs this module: **a person must be able to check a machine's reasoning against a source.** NFR-15 forbids colour as the sole encoding, and that rule is not a compliance footnote here — it is the design thesis. If a state cannot be read without colour, it has not been designed.

## Brand & Style

**Instrument panel, not dashboard.** This is a console for reading a machine's decisions at speed, under time pressure, at night. The posture is *dense, quiet, and evidentiary*: high information density, low ornament, and every claim traceable to a citation the reader can expand. It borrows the visual discipline of an air-traffic control display and the citation discipline of a court transcript, and it explicitly rejects the consumer-dashboard idiom — no cards with drop shadows floating on a gradient, no donut charts, no celebratory colour on a routine outcome.

Two commitments shape every token below.

**Commitment 1 — the machine is always right about its own state, never about the user's.** A 05:45 Eviction is not rendered as an error. It is a scheduled, cited event that the system announced in advance. Adverse states get visual weight because they demand attention, not because the system thinks it made a mistake. This is why `EVICTED_RESUMABLE` is a calm violet and not a red: a clean stop that kept the work is the module working correctly.

**Commitment 2 — monospace is a promise about verifiability.** Anything set in `mono-data` is a value the reader might copy into a search, compare against a log line, or check character by character: `sim_timestamp`, `job_id`, `node_id`, the SHA-256 digest, the `decision_id`. Proportional type is for language; monospace is for evidence. The distinction is semantic and non-negotiable — a `job_id` set in Inter is a bug, because the reader can no longer trust that `JOB-0417` and `JOB-041 7` are visually distinct at a glance in a dense column.

The tone is plain and technical. Copy says `Checkpointing`, not "Saving your progress…". Nothing in this system congratulates the user, apologises to them, or celebrates.

## Colors

Two complete token sets, both carrying the full 9 job states and 5 node-slot states. They are not derived from each other by inversion; each was chosen against its own ground to clear the contrast floor independently. That is why `{colors.state-checkpointing}` is `#D29922` and `{colors.state-checkpointing-light}` is `#9A6700` — the same concept, tuned to its own background.

### Surfaces and ink (dark, default)

`{colors.surface-base}` `#0E1116` is the console ground: deep blue-black, not neutral grey, so that the warm hues in the status set (`{colors.state-checkpointing}`, `{colors.state-eviction-failed}`) do not read as dirty. `{colors.surface-raised}` and `{colors.surface-overlay}` step up for panels and popovers; `{colors.surface-sunken}` recesses the Night Window timeline. Ink runs `{colors.text-primary}` → `{colors.text-secondary}` → `{colors.text-muted}` for a three-step hierarchy that survives at 11px. `{colors.accent}` is reserved for interactive affordance and the clock controls — never for state.

### Surfaces and ink (light, submission)

`{colors.surface-base-light}` `#FFFFFF` with `{colors.surface-raised-light}` `#F6F8FA` for field groups. Kavita reads this surface for perhaps ninety seconds; it is deliberately calmer and lower-contrast than the console, because a submission form is not an instrument panel and should not feel like one.

### Job states — 9, one per PRD §4.1 state

Each state has a hue, a glyph, and a fixed English label. The label is not a translation of the token name; it is what the operator reads.

| State (verbatim) | Dark | Light | Glyph | Label | Reading |
|---|---|---|---|---|---|
| `REJECTED` | `{colors.state-rejected}` | `{colors.state-rejected-light}` | `✕` | Refused | Terminal. Never entered the Pending Set. |
| `QUEUED_PENDING_WINDOW` | `{colors.state-queued-pending-window}` | `{colors.state-queued-pending-window-light}` | `◷` | Queued | Waiting for a Night Window. Carries a Pending Set position. |
| `RUNNING` | `{colors.state-running}` | `{colors.state-running-light}` | `▶` | Running | Holds a GPU slot. |
| `CHECKPOINTING` | `{colors.state-checkpointing}` | `{colors.state-checkpointing-light}` | `▼` | Checkpointing | Draining, writing a Checkpoint. Time-boxed. |
| `EVICTED_RESUMABLE` | `{colors.state-evicted-resumable}` | `{colors.state-evicted-resumable-light}` | `‖` | Evicted, resumable | Clean stop, verified Checkpoint held. **Not a failure.** |
| `COMPLETED` | `{colors.state-completed}` | `{colors.state-completed-light}` | `✔` | Completed | Terminal, successful. |
| `FAILED` | `{colors.state-failed}` | `{colors.state-failed-light}` | `⚠` | Failed | Terminal, non-resumable. Last verified Checkpoint retained. |
| `EVICTION_FAILED` | `{colors.state-eviction-failed}` | `{colors.state-eviction-failed-light}` | `⚡` | Eviction failed | Recoverable via T-20. The **node** is lost, not the job. |
| `EXPIRED` | `{colors.state-expired}` | `{colors.state-expired-light}` | `⊗` | Expired | Terminal. Retention Deadline passed. Inert, so neutral. |

Three of these deserve their reasoning stated, because a first-time reader will get them wrong.

`EVICTED_RESUMABLE` and `FAILED` both mean "not running". The module's whole thesis is that a job stopped at dawn is *not* a failed job (UJ-3: "not 'stopped'"). Purple `{colors.state-evicted-resumable}` with a `‖` pause-bar glyph says *paused with your work intact*; pink `{colors.state-failed}` with a `⚠` says *something is unrecoverable*. If a reader confuses the two, the design has failed even though both are technically "not running".

`EVICTION_FAILED` is the most dangerous badge in the set, because its name reads as terminal and it is not. PRD §4.1 and T-20 make it non-terminal and recoverable: the job holds a retained verified Checkpoint and is re-admitted at the next Window Activation, onto a *different* node. It therefore gets the loudest non-red treatment in the palette - `{colors.state-eviction-failed}` orange with a `⚡` - and holds no hue that a terminal state uses, which is checkable: `#FFA657` appears nowhere else in either job-state set. That claim is about the normal-vision palette and the limit is worth stating: under deuteranopia `{colors.state-rejected-light}` and `{colors.state-eviction-failed-light}` converge to roughly dE 1.6, so hue alone would not separate a refusal from a failed eviction in the light theme. The glyph (`⚡` against `✕`) and the label carry it there, which is the same redundancy NFR-15 already requires, and it is why colour is the third channel in this system and never the first. The accompanying label is fixed at "Eviction failed" and is always followed by the retained Checkpoint step, so the operator reads "failed to stop cleanly on a node" rather than "job lost".

`EXPIRED` is the only state rendered in near-neutral `{colors.state-expired}`. It is an absence — the Retention Deadline passed and nothing happened — and it should carry no more visual energy than the absence deserves. A saturated red here would be a lie about severity.

### Node-slot states — 5, rendered per GPU slot

Node state is shown **per GPU slot**, not per node. `server-gpu-01` carries two 48 GB slots while each `ws-gpu-NN` carries one 24 GB slot, and PRD F-42 fixes the fleet at 32 Nodes and 33 GPU slots. The two slots of `server-gpu-01` render independently, because a job on slot 0 and a reservation on slot 1 are genuinely different facts and a single per-node badge would have to lie about one of them.

Two orthogonal attributes compose on every slot tile, because the PRD keeps them separate: **occupancy** (Invariant S-1 — which states hold a Node) and **eligibility** (FR-12 — why a Node is not Eligible).

| Slot state | Dark | Light | Glyph | Label | Axis |
|---|---|---|---|---|---|
| available | `{colors.node-available}` | `{colors.node-available-light}` | `○` | available | occupancy |
| running | `{colors.node-running}` | `{colors.node-running-light}` | `▶` | running | occupancy |
| draining | `{colors.node-draining}` | `{colors.node-draining-light}` | `▼` | draining | occupancy |
| reserved | `{colors.node-reserved}` | `{colors.node-reserved-light}` | `▨` | reserved · M4 | eligibility |
| cordoned | `{colors.node-cordoned}` | `{colors.node-cordoned-light}` | `⊘` | cordoned · ‹cause› | eligibility |

Four hues are deliberately shared across the two axes, and all four are intentional, because the PRD keeps the axes separate while the operator still has to learn one vocabulary rather than two. `{colors.node-running}` = `{colors.state-running}`: a running slot is running a job. `{colors.node-draining}` = `{colors.state-checkpointing}`: a draining slot is running a `CHECKPOINTING` job. `{colors.node-reserved}` = `{colors.accent-hover}`: a held-back slot is held back on purpose, like a control awaiting a click. `{colors.node-cordoned}` is a brown held deliberately apart from `{colors.state-rejected}` red, so a cordoned *machine* is never mistakable for a refused *job* - the two appear on screen together, and this file insists elsewhere that a reader must be able to tell "refused" from "unrecoverable". The container differs (a 44px tile versus a 20px badge) and the label differs in every case, so nothing is ambiguous.

`draining` exists because Annex Scenario 3 and the mandatory edge case happen precisely inside it. Between 05:45:00 and 05:53:00 a slot is still held — by a job in `CHECKPOINTING` — and Invariant S-1 permits exactly that until 06:00:00. A board that showed such a slot as `available` would be lying during the most safety-critical eight minutes of the night. It shows `draining` in `{colors.node-draining}` with the `▼` glyph the `CHECKPOINTING` badge uses, and the tile carries the remaining seconds to the 05:53:00 SIGKILL instant.

`reserved` cites Module 4 and `cordoned` folds a Module 3 health fault into itself per FR-12(a), always carrying the cause string as its label — `cordoned · EVICTION_CHECKPOINT_WRITE_FAILED` is the real shape of a cordon from FR-23, and the cause is what lets Ines distinguish a genuinely faulty node from a kubelet DiskPressure false positive (FR-23(i), known limitation 2).

**`VRAM_CLASS_INSUFFICIENT` is deliberately absent from this table.** It is not a node-global state: a 48 GB slot is `available` to a job requesting 24 GB and insufficient for one requesting 64 GB. It renders as a per-job exclusion reason on the placement panel, never as a slot colour. Painting a healthy 48 GB slot red because one job cannot use it would make the board lie about the other 32.

### Contrast — verified, not asserted

Every load-bearing pair, measured against its own ground, and the method is stated so it can be re-run: relative luminance per WCAG 2.1, then (L1+0.05)/(L2+0.05). WCAG 2.1 AA: 4.5:1 for normal text, 3:1 for non-text (SC 1.4.11 - focus rings, slot borders, glyph strokes).

The two border tokens are not interchangeable, and an earlier draft of this file got that wrong. `{colors.border-subtle}` and `{colors.border-strong}` are *decorative hairlines* - chip outlines, group separators - and sit at 1.22-2.01:1, which is acceptable because SC 1.4.11 governs the boundary of a control, not its ornament. `{colors.border-structure}` is the token that carries a boundary a reader must see: slot-tile edges and data-table row rules. It clears 3:1 on all three dark grounds, and `{colors.border-structure-light}` clears 3:1 on both light grounds. A row rule you cannot see is a row you cannot count, and counting rows is the whole job at 07:00.

| Pair | Ratio | Floor |
|---|---|---|
| `{colors.text-primary}` on `{colors.surface-base}` | 16.00:1 | 4.5 ✓ |
| `{colors.text-secondary}` on `{colors.surface-base}` | 8.98:1 | 4.5 ✓ |
| `{colors.text-muted}` on `{colors.surface-base}` | 5.24:1 | 4.5 ✓ |
| every one of the 9 `{colors.state-*}` on `{colors.surface-base}` | 5.62 – 9.81:1 | 4.5 ✓ |
| every one of the 5 `{colors.node-*}` on `{colors.surface-base}` | 6.23 – 9.72:1 | 4.5 ✓ |
| `{colors.focus-ring}` on `{colors.surface-base}` | 9.72:1 | 3 ✓ |
| `{colors.focus-ring}` on `{colors.surface-raised}` | 8.89:1 | 3 ✓ |
| `{colors.text-primary-light}` on `{colors.surface-base-light}` | 15.79:1 | 4.5 ✓ |
| `{colors.text-muted-light}` on `{colors.surface-base-light}` | 5.33:1 | 4.5 ✓ |
| the 9 `-light` job-state tokens, on `{colors.surface-base-light}` | 4.87 – 7.39:1 | 4.5 ✓ |
| the 9 `-light` job-state tokens, on `{colors.surface-raised-light}` | 4.57 – 6.94:1 | 4.5 ✓ |
| `{colors.citation-ink}` on `{colors.surface-overlay}` (the `self:` chip ground) | 5.19:1 | 4.5 ✓ |
| `{colors.citation-ink-light}` on `{colors.surface-raised-light}` | 5.57:1 | 4.5 ✓ |
| `{colors.border-structure}` on base / raised / overlay | 3.96 / 3.63 / 3.30:1 | 3 ✓ |
| `{colors.border-structure-light}` on base / raised | 3.65 / 3.43:1 | 3 ✓ |
| `{colors.focus-ring-light}` on base / raised | 7.59 / 7.13:1 | 3 ✓ |

Every state token clears its text floor at `{typography.mono-label}` 11px in both themes, so the size caveat this section used to carry is gone. The tightest pairs in the system are the light state badges, and the binding one is `{colors.state-checkpointing-light}` / `{colors.node-draining-light}` at 4.87:1 on `{colors.surface-base-light}` and 4.57:1 on `{colors.surface-raised-light}`. An earlier draft pinned `state-expired-light` at 4.55:1 while simultaneously specifying the `status-badge` at 11px - a rule the file then forbade itself from applying to its own most-used component. The token was re-picked rather than the component downgraded.

## Typography

Two families, one rule for choosing between them.

**Inter** carries language: `{typography.display}` down to `{typography.caption}`. **JetBrains Mono** carries evidence: `{typography.mono-data}`, `{typography.mono-data-lg}`, `{typography.mono-label}`, `{typography.mono-column}`.

The base body size is 13px, below the web-typical 16px, and this is a deliberate density decision for a surface that must show 32 Nodes, 33 slots, and a 500-job Pending Set at once. The offsetting rule is that nothing in the console is below `{typography.caption}` 11px, and monospace columns use `{typography.mono-column}` with tabular numerals so that digits align vertically without the reader tracking glyph widths.

`{typography.mono-label}` at 11px with 0.04em tracking is the workhorse of the state system: it is the face inside every `status-badge` and every `citation-chip`. Uppercase is reserved for this role and for column headers, so that a tracked uppercase string is itself a signal that the reader is looking at an identifier rather than a sentence.

`{typography.mono-data-lg}` at 14px is used in exactly three places: the simulated clock readout, a `job_id` in a page title, and a SHA-256 digest rendered in full. These are the values a reader may copy or compare character by character, and they get the extra pixel of size to make that possible.

The scale is compressed rather than modular. There is no 18px body and no 22px anything; `{typography.title}` at 18px is the largest step below `{typography.display}`, because panel titles should not compete with the state they describe.

## Layout & Spacing

A 4px base with a single 2px half-step — the `'0.5'` scale level. It is referenced as `spacing['0.5']`, in bracket form, and never as a dotted token path: a dotted path cannot carry a dotted key unambiguously, and every resolver would read such a reference as `spacing.0` followed by a stray `.5`. Reserved for the interior of dense badges and for the 1px-plus-gap rhythm inside table cells. Named tokens do the work that a scale cannot express:

- `{spacing.row-dense}` (28px) is the table row height for the board, the Pending Set, the Admission Order, and the event log. The PRD fixes no viewport, so the honest statement is the constraint rather than a row count: 28px is the floor at which `{typography.mono-data}` 12px plus a 20px badge still sit on the line without clipping, and the Pending Set and event log scroll at that density by design (FR-7 allows `QUEUE_DEPTH_CAP = 500`).
- `{spacing.row-default}` (36px) is for interactive list rows that carry a secondary action.
- `{spacing.gutter}` (16px) is the panel gutter. `{spacing.panel-gap}` (12px) separates stacked panels inside a region — deliberately one step tighter than the gutter, so nesting reads.

The console is a fixed three-region frame: a persistent **status strip** across the top (daemon connection, simulated clock, rate control, countdown), a **left rail** of region selectors, and the **work region** that fills the remainder. The work region is where the density lives. Within it, the board is a dense grid and the detail surfaces are a two-column split — the subject on the left, the Decision Record evidence on the right. That split is not decorative: FR-25(b) requires the citation list to render alongside any decision the surface displays, and a two-column layout means the citation is never behind a disclosure the operator has to remember to open.

Horizontal scroll is never used for the board, because a board whose right edge is off-screen cannot answer "are all GPUs released" - which is the first thing Ines checks at 07:00. The arithmetic is unforgiving and is worth stating: 33 tiles at 44px is 1452px, which already exceeds a 1440px viewport before a single gap and before the left rail. The board therefore wraps into labelled rows of slots rather than laying out on one line, and the tile keeps a 44px *height* floor with no width floor - the ordinal, the glyph and the state label are mandatory on the tile, while the `job_id` moves into the accessible name and the slot inspector as the tile narrows. OQ-5 records that the PRD names no viewport for the status board, so this is a stated design decision, not a derived one.

## Elevation & Depth

Depth is expressed by **tonal layering and a 1px border**, never by shadow. `{colors.surface-base}` → `{colors.surface-raised}` → `{colors.surface-overlay}` is the whole depth system. A shadow is permitted in exactly one case: a popover or tooltip that must detach from its anchor, and even then at the lowest opacity the platform offers.

The reason is legibility under low light. Shadows on a near-black ground do not read as elevation - they read as smudges, and at 2am on a lab monitor a smudge is noise. A 1px line is unambiguous at any brightness only if the line is bright enough to see, which is why boundary-bearing edges take `{colors.border-structure}` at 3.30:1 and not `{colors.border-subtle}` at 1.22:1. A hairline that vanishes on a dark overlay is not subtle, it is missing, and an operator scanning for one cordoned slot at 05:44 needs it to be there.

Overlays dim the base with a 60% `{colors.surface-sunken}` scrim. Stacking never exceeds one level: a Decision Record detail opens as a panel, not as a dialog on top of a dialog.

## Shapes

Tight. `{rounded.xs}` 2px for the inner fill of a badge, `{rounded.sm}` and `{rounded.DEFAULT}` 3px for controls, `{rounded.md}` 4px for slot tiles and panels, `{rounded.lg}` 6px for popovers. `{rounded.full}` is used for one thing only: the `status-badge` pill.

The pill is reserved for state. Nothing else in the system is fully rounded — buttons, inputs, tiles, and panels are all ≤6px. This keeps the pill meaningful: in a dense table, a rounded capsule means *this is a state*, and nothing competes with that signal. Sharpness elsewhere reads as instrument; a field of pills would read as a marketing page.

## Components

### `status-badge` — the 9 job states

Anatomy, left to right: **glyph** -> **text label** -> optional **count** for repeated states in a roll-up. Height `{spacing.row-dense}` minus padding, i.e. 20px. `{rounded.full}`. The state's colour is applied as the **text and glyph colour** on a transparent ground; the badge carries no fill, because a tinted fill would put a second, lower-contrast copy of the same hue behind the label and re-open the desaturation question this system is trying to close. The ground is whatever the surface provides, so the badge stays legible on `{colors.surface-base}` and on `{colors.surface-raised}` without a variant.

The text label is mandatory and never truncated, in every surface, with no narrow-width exception. NFR-15 requires a non-colour encoding with a distinct glyph *and* text label for every one of the nine states, so an icon-only badge is a spec violation, not a space-saving measure - and a badge that degrades to a glyph plus a hover tooltip is that same violation made worse, because the information then exists only for a mouse user. An earlier draft licensed exactly that collapse for a narrow roll-up; it is withdrawn. Where horizontal room is genuinely short the relief is the `count` affordance in the anatomy above: `Evicted, resumable x14` says the same thing in fewer pixels without hiding the word.

Terminality is carried by the **label and the border**, never by a background fill and never by desaturation. All nine badges render their own hue identically; the four terminal states (`REJECTED`, `COMPLETED`, `FAILED`, `EXPIRED`) take a 1px `{colors.border-structure}` ring, the five non-terminal states take no ring. A border is the right channel because it is a shape difference, it survives greyscale and colour blindness, and it does not spend a second colour. A badge never becomes grey because it is terminal - grey already means `EXPIRED`, and one token must mean one thing.

An earlier draft expressed terminality as "non-terminal badges sit on `{colors.surface-raised}` when stacked". That was wrong twice: a background *is* a colour, so it was a second colour axis by another name, and it applied only when badges were stacked, which made terminality a property of layout rather than of state. Note also that `EXPIRED`'s fixed label, "Expired", already reads as terminal in plain English - so the `EVICTION_FAILED` argument below that it is "the loudest non-red treatment in the palette" cannot lean on its label being non-terminal. The ring does that work instead.

### `node-slot-tile` — the 5 slot states

A 44px `{rounded.md}` tile, 1px `{colors.border-structure}`, carrying the slot's ordinal, its state glyph, its state label at `{typography.mono-label}`, and — when occupied — the `job_id` at `{typography.mono-data}` truncated to 8 characters with the full value in the accessible name and the tooltip.

`server-gpu-01` renders as a paired tile with a shared node header above both slots, because the two slots are independent but the node is one machine and Ines reasons about the machine. The per-slot independence is preserved inside the pair: slot 0 `running` and slot 1 `reserved` is a legal and common display, and the two tiles are visually independent even though they share a header.

A slot in `draining` carries a mono countdown, but only inside the Eviction Ramp, where the deadline is real: from 05:45:00 to the 05:53:00 SIGKILL instant, the tile reads `draining - SIGKILL in mm:ss`. Outside the Ramp the deadline is the 300 s Checkpoint Budget of FR-16(c)/(d), not a wall-clock instant, so the tile reads `draining - checkpointing` with elapsed seconds and no SIGKILL reference. A `draining` tile that always showed a 05:53:00 countdown would be quoting a deadline that does not exist at 23:10. A slot in `cordoned` carries the cause string in place of the state label.

### `decision-banner` — 10 decision variants, 2 groups

One component, `{rounded.md}`, `{spacing.banner-inset}` padding, a 3px left border in the group's colour, the decision value as a `{typography.mono-label}` eyebrow, the `summary` at `{typography.body}`, and the citation list as `citation-chip` elements at `{typography.mono-label}` - the chip's own token, which an earlier draft contradicted in two other places.

| Group | Variants | Left border | Weight |
|---|---|---|---|
| adverse | `DENY` `DEFER` `PREEMPT` `EVICT` `EXPIRE` `FAIL` `CORDON` | `{colors.state-rejected}` for `DENY`/`DEFER`/`FAIL`, `{colors.state-eviction-failed}` for `EXPIRE`/`CORDON`, `{colors.state-failed}` for `PREEMPT`/`EVICT` | group glyph `!`, full-opacity 3px border, `{colors.surface-raised}` fill |
| neutral / positive | `ADMIT` `RESUME` `COMPLETE` | `{colors.node-available}` | group glyph `✓`, 3px border at 60% opacity, `{colors.surface-base}` fill |

**Every variant renders the `summary` and the full `citations` list. Only the visual weight differs between groups - and the group is never signalled by hue alone.** A `PREEMPT` banner and an `ADMIT` banner carry the same eyebrow, the same summary treatment and the same citation row, so if the group lived only in the border colour it would live only in colour. It does not: the eyebrow opens with a group glyph and the group word (`Decision · deny` against `Decision · admit`), and the border weight differs. The fill difference between `{colors.surface-raised}` and `{colors.surface-base}` is 1.09:1 and is therefore treated as decoration, never as a signal. An earlier draft leaned on it, which would have left the two groups identical to any reader who cannot separate the hues - and under deuteranopia the adverse and positive borders land roughly dE 6.8 apart. A refusal that looks like an admission is the worst failure this component can have.

`DENY`/`DEFER` and `FAIL` deliberately share the `{colors.state-rejected}` left border, because both are refusals of a request rather than reports of a broken machine, and both are separated from the job-state hue vocabulary by the group glyph and the summary text. This file insists elsewhere that red and pink must stay distinct so a reader can tell "refused" from "unrecoverable", and the resolution is that the *job badge* for `FAILED` is `{colors.state-failed}` pink while the *banner* for a `FAIL` decision is red-bordered - a different component, carrying a different fact, and never shown as a state badge. That is the rule, and it follows from the PRD rather than from taste: SM-5 sets a target of 100% of decisions presented to the user carrying a citation and a one-sentence summary, and FR-25(b) requires the citation list rendered for any decision the surface displays. A quieter `ADMIT` banner is a de-emphasis, never a citation-stripped summary. §6.1 caps `summary` at 200 characters, so a banner's summary never wraps past three lines and the citation row is always reachable without scrolling.

`self:` citations render in `{colors.citation-ink}`; every non-`self:` authority - `policy:M2/…`, `quota:M8/…`, `entitlement:M1/…`, `node-state:M3/…`, `reservation:M4/…`, `catalog:M5/…` - renders in the delegated-authority ink, which is `{colors.citation-ink}` weighted heavier, not `{colors.accent}`. Neither channel uses `{colors.accent}`, which is reserved for interactive affordance and the clock controls. A citation is evidence, not a control; if delegated-authority evidence were painted in the affordance colour then a `policy:M2/…` chip and a clickable button would be the same blue, blurring exactly the F-1 split §6.2 says must stay sharp. `{colors.citation-ink}` exists because `{colors.text-muted}` measures 4.37:1 on the chip's own `{colors.surface-overlay}` ground - under the 4.5 floor, on the one component the whole design thesis rests on. This is a direct rendering of the §6.2 split rule (F-1) and of NFR-4: a reader can see at a glance whether a decision rests on a delegated authority or on the module's own bookkeeping, which is precisely the distinction §6.2 says must never be blurred.

### `citation-chip`

`{rounded.sm}`, 2px vertical padding, `{typography.mono-label}`, `{colors.surface-overlay}` ground (`{colors.surface-raised-light}` in the light theme), `{colors.border-subtle}` decorative hairline, `{colors.citation-ink}` text. The chip renders 19.4px tall, below the WCAG 2.2 SC 2.5.8 24px target floor, and the design accepts that: a citation is a copy target rather than a pointer target, and the full `authority:identifier@version` string is also reachable as selectable text in Decision Record detail. Carries the full `authority:identifier@version` string unabbreviated — `policy:M2/class-schedule@policy-v3` is copyable and checkable, and an ellipsised citation defeats the entire purpose of §6. Chips wrap; they never truncate.

### `clock-control`

A segmented control of `⏸` `1×` `60×` `360×` `1440×` at 28px height in `{typography.mono-data}`. The active segment is `{colors.accent}` fill with `{colors.text-on-accent}` text; inactive segments are `{colors.surface-raised}` with `{colors.text-secondary}`. The simulated clock readout sits immediately left of it in `{typography.mono-data-lg}` and is always present — an operator must never be unsure whether they are reading simulated or wall-clock time.

### `data-table`

`{spacing.row-dense}` rows, 24px header, `{spacing.2}` horizontal cell padding, numeric cells right-aligned in `{typography.mono-column}`. Row hover is a `{colors.surface-raised}` wash, never a border colour change. The currently focused row (keyboard) carries the `{colors.focus-ring}` outline at 2px with 2px offset. Zebra striping is not used; row separation is a 1px `{colors.border-structure}` bottom border only, which clears 3:1 on every ground the table sits on.

### `reason-panel`

`{rounded.md}`, `{colors.surface-raised}`, 1px `{colors.border-structure}`, `{spacing.3}` padding. Carries a per-Node or per-job exclusion reason as a `{typography.mono-label}` code plus a one-sentence human sentence. FR-25(d) is a hard rule here: an idle slot is never blank, it always carries a reason. The panel is the component that makes that rule expressible.

### `daemon-status-strip`

Persistent, full-width, `{typography.mono-label}`. Carries the daemon connection state, the last-received-update timestamp, the simulated clock, the rate control, and the countdown to the next decision point. In the unreachable state it swaps to `{colors.ui-adverse}` at the label weight - a dedicated token, because borrowing a job-state hue would have made a *connection* problem look like an `EVICTION_FAILED` *job* - and the control cluster stays present and readable, disabled with `aria-disabled="true"` rather than dimmed. The controls are not painted at 40% opacity: `{colors.text-secondary}` at that opacity composites to 2.40:1, and a control the operator cannot read is the vanished control this design refuses to create. Unavailability is carried by the label text and the ARIA state, not by legibility.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Render colour **and** glyph **and** text label for all 9 job states and all 5 slot states | Ship an icon-only or colour-only state indicator — violates NFR-15 outright |
| Set every `sim_timestamp`, `job_id`, `node_id`, `decision_id` and digest in `{typography.mono-data}` | Set an identifier in Inter; the reader can no longer distinguish `JOB-0417` from `JOB-041 7` in a dense column |
| Use the fixed English label from the state table, unabbreviated | Invent per-surface label variants; one state has one name everywhere |
| Show `EVICTED_RESUMABLE` in `{colors.state-evicted-resumable}` with the retained Checkpoint step adjacent | Render a clean dawn eviction in a terminal or error colour — it is the module working correctly |
| Show `EVICTION_FAILED` with the retained Checkpoint step and the "re-admitted tonight" note | Let `EVICTION_FAILED` read as terminal; T-20 returns it to the Pending Set |
| Render `VRAM_CLASS_INSUFFICIENT` as a per-job exclusion reason in a `reason-panel` | Paint a healthy 48 GB slot red because one job cannot use it |
| Show node state per GPU slot, both slots of `server-gpu-01` independently | Collapse `server-gpu-01` to one badge; it has 2 slots (F-42) |
| Show a `draining` slot for the whole 05:45:00–05:53:00 Ramp, with a countdown to SIGKILL | Show a slot held by a `CHECKPOINTING` job as `available`; S-1 permits the hold until 06:00:00 |
| Give every idle slot a reason string (FR-25(d)) | Render an idle slot blank, or with a bare en dash |
| Render `summary` + full `citations` on **all 10** banner variants | Strip citations from a low-weight `ADMIT` or `RESUME`; SM-5 and FR-25(b) are absolute |
| Render every citation in `{colors.citation-ink}`, with non-`self:` authorities weighted heavier than `self:` | Style all citations identically (the F-1 split rule stops being visible), or use `{colors.accent}` / `{colors.text-muted}` for citations (`text-muted` is 4.37:1 on the chip ground, under the 4.5:1 floor) |
| Use `{rounded.full}` for `status-badge` only | Round buttons, tiles, or panels into pills |
| Separate depth with tonal steps and 1px borders | Use drop shadows to build hierarchy on the dark ground |
| Keep the clock readout and rate control visible at all times, disabled when unreachable | Hide the control cluster on disconnect |
