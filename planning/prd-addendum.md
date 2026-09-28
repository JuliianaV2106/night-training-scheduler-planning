# Addendum — Module 9: Night Training Scheduler

*Companion to `planning/prd.md`. Holds depth that does not earn a place in the PRD's main narrative: real-world mechanism research with citations, measured sizing figures, and the alternatives that were considered and rejected. Nothing here is normative; where it conflicts with the PRD, the PRD wins.*

---

## A. Rejected alternatives

*Recorded because the task statement requires documented rejections, and because each of these is a decision a reviewer will challenge.*

### A.1 Reject-at-validation instead of resume-across-nights

**The alternative.** At submission, estimate the job's duration. If it exceeds the 8-hour Night Window, reject it with an explainable infeasibility proof and a suggested scope reduction.

**Why rejected.** It is simpler, has no checkpoint machinery, no resume path, and no edge case. It is also wrong for the institution. Thesis-scale fine-tunes genuinely take 30+ hours; the students who most need the GPU are the students whose work cannot fit in a night. Rejecting them pushes them back to the current workaround — an SSH session held open overnight, which is exactly the fragile, ungoverned, unobserved behaviour the platform exists to replace. The resume-across-nights model converts an unsatisfiable request into a satisfiable one at the cost of a checkpoint/resume subsystem. That trade is worth making.

**What it costs us:** FR-18 through FR-23, six of the thirty-one FRs, and the module's hardest correctness requirement (FR-23). That is the right price, but it is a price and it should be named as one.

### A.2 A hard consecutive-night cap instead of priority aging

**The alternative.** A job may hold at most K consecutive nights (say 2). On the third night it is checkpointed and skipped, letting the next job run.

**Why rejected.** It wastes the resume it just paid for. A thesis job capped at 2 nights per window would need 16 windows to finish and would spend 14 of them doing nothing — burning a Reservation-like share of the fleet's most contended resource to achieve fairness that admission ordering achieves for free. Aging is also strictly better-behaved: it is a continuous function of waiting time, so it degrades gracefully, whereas a cap is a cliff.

**Where the cap idea survives:** as `STARVATION_PROMOTION_LIMIT` (FR-15), which caps how many starved jobs may jump the admission queue in one window. The concern behind the rejected alternative — a mass-starvation event cannibalising a night — is real, and the promotion limit is the correct, narrower answer to it.

### A.3 Self-declared priority

**The alternative.** The submitting student sets their own priority tier.

**Why rejected.** Priority is the only resource in this module that can destroy someone else's work, and self-declaration makes it free. The moment a student learns that `THESIS` preempts `EXPLORATION`, every student declares `THESIS` and Annex scenario 4 becomes a no-op — the system would look like it implements preemption while actually implementing nothing. Worse, it creates an incentive to misrepresent academic intent to infrastructure staff. FR-17 makes priority administrative; a student's declaration is stored as a visible, reviewable *request* and never applied.

**Cost of this choice:** a two-step path for legitimate users. Kavita cannot self-serve her own thesis job. In a real deployment that is a support burden, and the honest fix is a better delegation to Module 2 (which can derive priority from academic standing) rather than opening self-declaration. See FR-17 and Open Question 5.

### A.4 Aging that can authorise preemption

**The alternative.** Effective Priority is the sole ordering key. A long-waiting low-priority job eventually outranks a running high-priority job and preempts it.

**Why rejected, and this is the subtlest call in the PRD.** It looks like the principled answer: one ordering key, starvation impossible. It is also exactly wrong here, because the jobs we most want to finish are the long ones. Under pure aging, a thesis job preempted on night 3 loses its warmup, restarts, and is likely to be preempted again on night 4 — it may never reach completion. The module would be systematically destroying the work it exists to protect, in the name of fairness.

The adopted model splits the two concerns: **aging guarantees access, authority gates destruction.** Starvation is fixed by Starvation Promotion at admission (FR-15), where it costs a waiting job nothing and a running job nothing. Preemption is gated by the Preemption Margin *and* by a Granted Priority of at least `THESIS` (FR-16), so no amount of waiting can ever authorise a student to kill someone else's run. The FR-16 testable condition asserts this directly: an aged `EXPLORATION` job at Effective Priority 40 is refused against a `THESIS` victim at 50 because the margin is 10 against a required 20.

**Secondary benefit:** because preemption only ever fires when no Eligible Node is free, it naturally correlates with genuine scarcity — a Module 4 class reservation taking 25 of 31 nodes. Preemption becomes rare and load-driven rather than routine.

### A.5 Wall-clock anchoring versus elapsed-time anchoring for the Eviction Ramp

**The alternative.** Anchor the Eviction Ramp to elapsed night time — 8 hours after window open — rather than to 05:45 and 05:53 wall clock.

**Why not adopted.** Elapsed-time anchoring is arguably more general, because it is immune to the DST hazard in PRD §10.2 and to any manual clock change. Wall-clock anchoring was chosen because it is directly comparable to the human institution it serves: "the machine is free at 06:00" is a fact a lab technician can verify with a wall clock, and PRD §6 requires decision summaries a human can check. An elapsed-time design produces correct timestamps nobody in the building can reason about.

**Team decision D-1 (2026-09-27): the sources name no campus location; the team sets the campus timezone to America/Bogota (UTC−05:00), the course's deployment context, which observes no daylight saving.** This is a decision, not a sourced fact (see PRD §10.2). The Night Window is therefore exactly 8 hours on every date of the year, and wall-clock anchoring is confirmed correct for this deployment rather than merely assumed. FR-19's fixed 05:45:00 and 05:53:00 constants are correct year-round. The residual value of the elapsed-time design is portability: a deployment in a DST-observing timezone would silently lose an hour of training on each spring-forward date, which is why §10.2 and §12.2 carry it as a v2 concern. Had the campus been in such a timezone, this would have been a live correctness question rather than a portability note — and FR-19's constants would have become offsets from window open.

### A.6 `self:` citations as sole justification

**The alternative.** A decision may cite only this module's own invariants — simpler, and every citation is guaranteed resolvable.

**Why rejected.** A user whose job was stopped at dawn deserves to know *which delegated authority said so*, not merely that the scheduler felt like it. PRD §6.2 requires at least one non-`self:` citation for every `PREEMPT` and `EVICT` and for a `DENY` based on a delegated verdict (a module-owned `DENY` and a Retention-Deadline `EXPIRE` may cite `self:` alone), so every consequential decision points outward to a system that can be independently asked. `self:` remains legitimate for time and self-integrity rules, where no external authority exists.

**Note the deliberate asymmetry:** `ADMIT` may cite `self:` alone. A job that runs does not owe the user an appeal trail; a job that is stopped does.

---

## B. Real-world mechanism research

*Web research conducted to ground the PRD's numbers in documented behaviour rather than intuition. Findings that changed a PRD decision are marked.*

*Sourcing caveat (F-44): every figure below is a **published estimate** — it carries the source it was drawn from, but none has been verified against this institution's hardware or telemetry. Treat them as literature values for simulation calibration (PRD §7.3, assumption A-17), not as measurements of this fleet.*

### B.1 Time-window scheduling

| Finding | Detail | Bearing on this PRD |
|---|---|---|
| Slurm partitions are the mature "window" primitive | `PartitionName`, `MinTime`, `MaxTime`, `OverTimeLimit`; `scontrol update PartitionId=… MaxTime=…` takes `HH:MM[:SS]`, `now+5minutes`, `midnight`, `tomorrow18:00`, rounded **up to the next minute** (resolution 1 min) | Confirms a 22:00–06:00 window is expressible in a real scheduler. Also shows a real scheduler quantises to 1 minute — our FR-19 ±2 s tolerance is tighter than Slurm's own model, which is fine for a simulator but worth knowing. |
| **`MaxTime` has no effect on already-running jobs** | A running job is bounded by its own `TimeLimit`, not the partition's `MaxTime` | **Changed the design.** This is the exact trap in Annex scenario 3: a window that only constrains *admission* does not stop anything. FR-19 exists because a partition-style window alone is insufficient. |
| `OverTimeLimit` makes the limit soft | Grace for backfill, then a hard cancel at soft+over | Mapped to the Checkpoint Budget: 300 s of soft allowance inside an 8-minute hard Ramp. |
| `KillWait` default is **30 s** (max 65533) | Interval between SIGTERM and SIGKILL on time limit | The default we are deliberately exceeding. |
| `GraceTime` (preemption grace) default is **zero** | Meaningful only for `PreemptMode=CANCEL`/`REQUEUE` | Confirms that a real scheduler gives a preempted job **nothing** by default. FR-16(d) requiring a verified Checkpoint before the challenger starts is a deliberate departure. |
| `EnforcePartLimits=ALL\|ANY\|NO` (default `NO`) | Makes over-limit jobs *rejected at submission* rather than left pending | Analogue for FR-7's fail-fast depth cap. |
| Kueue has no time-window field | Closest: `LocalQueue.spec.stopPolicy: None\|Hold\|HoldAndDrain` (evicts admitted workloads) and `AdmissionCheck` with `Pending\|Ready\|Retry\|Rejected` | `HoldAndDrain` is a "stop the fleet" switch; `Retry` evicts an admitted workload and releases quota. Useful vocabulary for PRD §6's decision enum. |
| *Not found* | Invenio `allowedStartWindow`/`validity`, Kyberios, Allocator, OpenPAI window fields; `MinNodes` and `PreemptExemptTime` defaults | Recorded as unconfirmed. No number was invented. |

### B.2 Checkpointing and restart

| Finding | Detail | Bearing on this PRD |
|---|---|---|
| `enable_jit_checkpoint` (default `False`) | HuggingFace `training_args.py`: "Enable JIT checkpointing on SIGTERM signal for graceful termination on **preemptible** workloads. Configure your orchestrator's graceful shutdown period accordingly. For Kubernetes, set `terminationGracePeriodSeconds` (**default 30s is usually insufficient**). For Slurm, use `--signal=TERM@`. **Required grace period ≥ longest iteration time + checkpoint save time.**" | **The single most load-bearing citation in this PRD.** It is the framework vendor naming our exact problem and telling us the platform default is too small. FR-19's 8-minute Ramp is sized from this. |
| HF Trainer defaults | `save_strategy="steps"`, **`save_steps=500`**, `save_total_limit=None` (deletes nothing) | Our `checkpoint_interval_minutes ≤ 30` validation bound (FR-2g) is a wall-clock cap the step-based vendor default does not provide: a 500-step interval on a large dataset can exceed a whole night, while a 30-minute cap bounds lost work to one interval (SM-6). |
| Measured LoRA-8B QLoRA on 24 GB | 4-bit base ~5.5 GB + adapter + paged optimizer ~3 GB; peak **~14 GB** at batch 4 / seq 2048; **~95 min** for 10k pairs × 3 epochs on one RTX 4090; ~3,800 tok/s | Calibrates PRD §7.3's duration model and FR-4. A 31-hour thesis job at these rates is a realistic multi-night job, not a hypothetical. |
| 48 GB vs 24 GB budget (NF4 base / adapter / paged optimizer / activations) | 8B: 4.5 / 0.13 / 0.6 / 3.5 GB @ 4096 → **~9–12 GB**. 70B: 18.9 / 0.84 / 3.6 / ~0.9 GB @ 1024 → **~23.4 GB** | Validates FR-2(c). A 70B QLoRA *fits* 24 GB at seq 1024 / batch 1 / grad-accum 8 / checkpointing on — so "requested VRAM exceeds 48 GB" is not the only infeasibility case, and FR-2's rejection must cite requested *and* available class, which it does. |
| Checkpoint artifact size | Adapter-only **50–200 MB**; merged 15–140 GB; a 70B QLoRA checkpoint **with full optimizer state ≈ 7 GB** | Sizes the 300 s Checkpoint Budget (FR-19) and the 20 GB store budget (FR-22). A 7 GB write is why 30 s fails. |
| Durability protocol | `fsync` ≈ **100 µs** NVMe, ≈ 1 ms SATA SSD, 5–10 ms spinning disk. Correct order: write temp → `fdatasync(fd)` → `rename()` → **`fsync(dir)`** — without the directory `fsync`, "the rename is only in memory" | **This is FR-18(a) verbatim.** The directory `fsync` is the step everyone omits, and it is the step that makes a Checkpoint a Checkpoint. FR-18's testable condition interrupts exactly this step. |
| Measured crash safety | Unsafe (no fsync) checkpoint survived **0 of 430** crash injections. `atomic_nodirsync` +56.5% median overhead; `atomic_dirsync` +84.2% median, up to 5.7× p99 tail. SHA-256 integrity guard detects **99.8–100%** of corruptions | Quantifies why FR-18 and FR-20 are non-negotiable, and honestly prices the cost: the directory `fsync` roughly doubles median checkpoint write time. Accepted. |
| Kubeflow Training Operator v1 `RunPolicy` | `activeDeadlineSeconds`, `backoffLimit`, `cleanPodPolicy`, `ttlSecondsAfterFinished`; `PyTorchJobDefaultRestartPolicy = OnFailure`; `nprocPerNode` ∈ `auto\|cpu\|gpu\|int`; int form `nProcPerNode` deprecated in v1.7+; default port 23456 | `auto` is a real trap on a 31-Node fleet — a job could claim every node. FR-3 rejects `auto` outright. |

### B.3 Preemption

| Finding | Detail | Bearing on this PRD |
|---|---|---|
| Slurm `PreemptMode` ordering | `SUSPEND` > `REQUEUE` > `CANCEL`. `OFF` is the default. `SUSPEND` requires GANG and **suspended jobs still hold memory** | Suspension is unusable here: a suspended job holding VRAM defeats the point of freeing the GPU. FR-16 selects checkpoint-then-release, not suspend. |
| Kueue preemption enums (exact) | `withinClusterQueue: Never\|LowerPriority\|LowerOrNewerEqualPriority`; `reclaimWithinCohort: Never\|LowerPriority\|Any`; `borrowWithinCohort: Never\|LowerPriority` + `maxPriorityThreshold`. **All default to `Never`.** Candidate order: borrowing queue first, then lowest priority, then most recently admitted | Useful vocabulary and a precedent: the industry default is to **not preempt**. FR-16's conservatism is the mainstream position, not a contrarian one. |
| `preemptionPolicy: Never` semantics | Means "*this pod cannot preempt others*", **not** "this pod cannot be preempted" | A persistent misreading. Recorded because a reviewer will hit it. |
| Kueue `Retry` admission state | Evicts an admitted workload and releases quota | Closest real analogue to our T-14 (preempted victim returns to the Pending Set). |
| Kubernetes termination | `terminationGracePeriodSeconds` default **30 s**; `preStop` runs inside the countdown; kubelet grants a **one-off 2 s extension** if the hook overruns; then SIGTERM to PID 1, then SIGKILL; on kubelet/runtime restart the **full original grace period is retried from the start** | The 2 s one-off extension is a trap for a hard deadline: FR-19's SIGKILL must be enforced by the scheduler, not delegated to kubelet's grace logic, or a 2 s overrun eats into the 06:00 guarantee. NFR-14 is therefore checked at every simulated minute. |
| Kubelet eviction ordering | MemoryPressure/DiskPressure evict **BestEffort before Burstable before Guaranteed** | Relevant to FR-23: a checkpoint write failing on a full disk may be the *kubelet* under pressure, not the Node being faulty. A blind cordon would be a false positive. This is a genuine weakness in FR-23 worth revisiting once Module 3's fault classification is specified. |
| Spot-instance interruption norms | EC2 gives a **2-minute** notice (IMDS `instance-action`, poll every 5 s, best-effort); AWS states automated action "must be completed within two minutes". ECS: SIGTERM then 2 min to SIGKILL. GCP ≈ 30 s notice | Our 8-minute Ramp is 4× AWS's most generous real-world notice, which is the right side to err on for a *scheduled, predictable* deadline — unlike a spot reclaim, dawn is guaranteed to arrive. |
| Interruption rate | **< 5%** of Spot instances interrupted by EC2 before intentional termination | Context only. |

### B.4 Cordon semantics

| Finding | Detail | Bearing on this PRD |
|---|---|---|
| `kubectl cordon` sets `.spec.unschedulable: true` | `kubectl get nodes` reports **`SchedulingDisabled`**; **existing pods are untouched** — it blocks new placement only | Exactly the primitive FR-23 requests and FR-12 consumes. Matches the Glossary definition of Cordon Request. |
| Implemented as a taint | `node.kubernetes.io/unschedulable`, effect **`NoSchedule`** — distinct from `not-ready`/`unreachable` (both `NoExecute`) and from kubelet's own `memory-pressure`/`disk-pressure` `pid-pressure` `NoSchedule` taints | Our `M3_CORDONED` exclusion reason is a distinct code from a health fault for a reason: the mechanisms differ, and conflating them would lose the distinction FR-23 depends on. |
| **Cordon does NOT make a node `NotReady`** | Independent axes: schedulable vs healthy. Node controller uses `--pod-eviction-timeout` default 5 min; `not-ready` taint has `tolerationSeconds: 300`; missed-heartbeat threshold **40 s**; kubelet reports conditions every **~10 s** | **A correctness point for FR-12.** A naive implementation reading node health as `Ready == True` would place jobs onto cordoned-but-healthy nodes, because cordon leaves `Ready` true. FR-12(a) requires checking the `SchedulingDisabled` condition explicitly. |
| Standard post-cordon workflow | `kubectl drain --ignore-daemonsets [--delete-emptydir-data] [--grace-period=900] [--timeout=300s]` → fix → `kubectl uncordon`. Drain cordons implicitly, evicts via the Eviction API (respects PDBs, returns **429** and retries) | The `429 and retries` detail matters for FR-23: a Cordon Request is asynchronous and may be rejected under PDB pressure. FR-23(e) assumes it succeeds; the optimistic-and-immediate treatment should be revisited against Module 3's actual contract. |
| Anti-burn-the-GPU knobs | Node annotation `cluster-autoscaler.kubernetes.io/scale-down-disabled: "true"`; pod annotation `cluster-autoscaler.kubernetes.io/safe-to-evict: "false"`; PDBs | Parallel mechanisms for the same intent. Supports FR-23's rationale. |
| Flapping (Module 3's mandatory edge case) | Node conditions update ~10 s; missed-heartbeat 40 s; eviction timeout 5 min | Relevant to FR-12: a flapping Node could pass a single eligibility check. Open — Module 3 owns hysteresis, but FR-12's re-evaluation-before-each-placement (FR-12(d)) is the second line of defence. |

### B.5 Job spec validation

| Finding | Detail | Bearing on this PRD |
|---|---|---|
| Kueue admission rules worth mirroring | Every container must declare at least one of `resources.requests` or `resources.limits`; **Kueue computes quota usage on `requests`**; Kubernetes implicitly treats `limits` as `requests` if `requests` is missing | FR-2(d) requires `requests == limits` for GPU and memory. Consequence if unenforced: quota accounting and placement can disagree, and a job could be admitted against a quota it never actually reserves. |
| Validation taxonomy (4 layers) | CRD structural schema + `x-kubernetes-validations` CEL; `ValidatingAdmissionPolicy` (in-process CEL, **on by default in k8s 1.30+**); legacy validating webhooks; `kubectl apply --dry-run=server` (`dryRun: All`) | PRD does not lock the mechanism (correctly — the task statement puts deployment architecture out of scope for the first iteration). §5's delegation table is the constraint. |
| CEL cost budget | `StaticEstimatedCostLimit = 10,000,000` per expression; `StaticEstimatedCRDCostLimit = 100,000,000` per CRD; max **64** match conditions per policy | Only relevant if Phase 3 selects CEL. Noted so the architect does not rediscover it. |
| Canonical k8s error shape | `validationActions: Deny\|Warn\|Audit` (Deny+Warn disallowed — duplicates the error); `reason` enum **`Unauthorized`, `Forbidden`, `Invalid`, `RequestEntityTooLarge`**; unset → `StatusReasonInvalid`; default message `"failed rule: {Rule}"`; `failurePolicy: Fail\|Ignore`, default **Fail** | The `failurePolicy: Fail` default and the fail-closed posture of PRD §6 are the same instinct. FR-24(b) adopts it: a citation-less decision is not applied. |
| *Not confirmed* | The `nvidia.com/gpu` device-plugin rule that it must be in `limits` with `requests == limits` (widely stated, not fetched from the official doc) | Stated as unconfirmed. FR-2(d) is justified on Kueue's confirmed `requests`-based accounting instead. |

---

## C. Simulation design notes

*Detail behind PRD §7 that Phase 3 will need and should not have to re-derive.*

### C.1 Why discrete-event, not frame-based

At 1440×, one real second is 24 simulated minutes. A frame-based loop sampling at, say, 60 Hz advances simulated time in 24-minute jumps and will step straight over the 05:45:00 SIGTERM, the 05:50:00 Checkpoint Budget expiry, and the 05:53:00 SIGKILL. Every failure path in the module would silently become unreachable in exactly the mode the Annex specifies for demonstration.

The engine therefore keeps transitions in a priority queue keyed by exact simulated instant, and wall-clock time is only a pacing layer that decides *when to drain the queue*, never *what instant to jump to*. FR-11 and NFR-6 exist to make this testable, and the test is a reconciliation: fired-event count must equal the analytic expectation for the seed's fault schedule.

### C.2 Modelling a checkpoint write that takes real time

Under Fast-Forward, a 300 s Checkpoint Budget elapses in roughly 208 ms at 1440×. If the Checkpoint write is modelled as instantaneous, the Checkpoint Budget is untestable; if it is modelled as real disk I/O it will not keep up. The correct model is a **declared duration function** of artefact size and Node storage class, evaluated once at ramp start:

```
checkpoint_write_s = (checkpoint_bytes / node_drain_rate) + 2 × fsync_latency
```

using the fsync figures in §B.2 (100 µs NVMe, 1 ms SATA, 5–10 ms spinning). A spinning-disk Node at 5–10 ms per `fsync`, with two of them, plus a 7 GB write, is a materially different budget from an NVMe Node — which is why FR-19's sizing is flagged as contingent on the real fleet's disk class (PRD §16 A-9).

### C.3 Tie-breaking and determinism

Two transitions can share an exact instant (a Checkpoint completing at 05:50:00 and another job being preempted at 05:50:00). Ordering is by a stable sequence number assigned at enqueue, itself derived from the Admission Order, so determinism does not depend on iteration order of any hash container. NFR-7's byte-identical-log test is what catches a violation.

### C.4 What the fault injector must be able to express

| Fault | Must be able to target | Exercises |
|---|---|---|
| Checkpoint write failure | a specific Node at a specific simulated instant | T-10, FR-23, UJ-5 — the mandatory edge case |
| Checkpoint corruption | a specific job's Checkpoint bytes, after write, before next read | T-13, FR-20 |
| Node fault | a specific Node at a specific instant, with a fault class the daemon can distinguish | T-16, T-17, FR-12 |
| Process exit / OOM kill | a specific job at a specific instant, with exit class (`OOM_KILLED`, `PROCESS_EXITED`) | T-22, T-23, FR-29 |
| Daemon crash | a specific instant, abrupt | T-18, FR-9, NFR-10 |

NFR-10's test — kill at 1000 seed-derived instants across a run, require zero lost and zero duplicated committed transitions — is the one that most constrains the persistence design, and it should be built before the checkpoint code, not after.

---

## D. Open items carried forward

- ~~**The DST decision is unresolved and is a correctness question**~~ **Closed by team decision D-1.** The team set the campus timezone to America/Bogota (UTC−05:00), which has no daylight saving, so the Night Window is a fixed 8 hours and wall-clock anchoring is confirmed correct. Portability to a DST-observing timezone is a v2 concern (PRD §10.2, §12.2, §A.5 above). No open question remains.
- **FR-23's cordon edge cases are now PRD requirements, not open items (F-45).** The false-positive risk (§B.3, kubelet DiskPressure) and the rejected-Cordon-Request case (§B.4, Eviction API 429) are recorded in v1 as **PRD FR-23(i) and FR-23(h)** respectively: the cordon reason surfaces the false-positive possibility to the lab administrator during clearance, and a rejected Cordon Request still keeps the Node locally not-Eligible with a recorded Decision Record. Both remain worth reconciling against Module 3's actual contract in Phase 3, but neither is an unspecified gap any more.
- **The `nvidia.com/gpu` device-plugin contract was not verified from primary documentation** (§B.5). If Phase 3 hardens against a real cluster rather than a simulator, re-verify it — FR-2(d)'s justification currently rests on Kueue's confirmed `requests`-based accounting, which is sound but is not the same rule.
- **Sourcing honesty (F-44).** Every figure in this addendum is a **published estimate — source-verified only in the literature**, or is explicitly marked as unconfirmed. The strongest claim made here is "reported in the cited source", never "measured on this campus". Where a default was unavailable in research (Slurm `MinNodes`, `PreemptExemptTime`; Invenio window fields; Kubeflow v2 `checkpointTrigger`/`PodSet`/`maxRestartPolicy`), that absence is recorded rather than filled in.
