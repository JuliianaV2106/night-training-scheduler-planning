"""
Window Activation fold (Story 1.3): deterministic Admission Order and AD-4 node placement.

Pure: takes snapshots of jobs and nodes, returns placements and deferrals.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from src.domain.entities import ADMISSIBLE_STATES, Deferral, Job, Node, Placement


def admission_order(jobs: Iterable[Job]) -> list[Job]:
    """contracts.md §2.2 Q2: priority desc, nights missed desc, submitted_at asc, job_id asc."""
    candidates = [j for j in jobs if j.state in ADMISSIBLE_STATES]
    return sorted(
        candidates,
        key=lambda j: (-j.effective_priority, -j.consecutive_nights_missed, j.submitted_at, j.job_id),
    )


def _can_host(node: Node, job: Job) -> bool:
    """Static eligibility: healthy, VRAM class satisfies the spec, enough physical slots."""
    return (
        node.status == "HEALTHY"
        and node.vram_class_gb >= job.required_vram_gb
        and len(node.slots) >= job.gpu_slots_requested
    )


def plan_window(jobs: Iterable[Job], nodes: Iterable[Node]) -> tuple[list[Placement], list[Deferral]]:
    """
    Places every admissible job in Admission Order onto the first node of the AD-4 total order:
    (1) previously assigned node, (2) lowest allocations_held, (3) node_id ascending.
    A 2-GPU job takes both server slots atomically or none (INV-03).
    """
    fleet = {n.node_id: n for n in nodes}
    placements: list[Placement] = []
    deferrals: list[Deferral] = []

    for rank, job in enumerate(admission_order(jobs), start=1):
        eligible = [n for n in fleet.values() if _can_host(n, job)]
        if not eligible:
            deferrals.append(Deferral(job.job_id, "T-4a", "NO_ELIGIBLE_NODE", rank))
            continue

        with_room = [n for n in eligible if len(n.free_slot_ids) >= job.gpu_slots_requested]
        if not with_room:
            deferrals.append(Deferral(job.job_id, "T-4b", "CAPACITY_EXHAUSTED", rank))
            continue

        chosen = min(
            with_room,
            key=lambda n: (n.node_id != job.last_node_id, n.allocations_held, n.node_id),
        )
        won_on = _winning_key(chosen, with_room, job)
        slot_ids = tuple(chosen.free_slot_ids[: job.gpu_slots_requested])
        fleet[chosen.node_id] = replace(
            chosen, slots={**chosen.slots, **{s: job.job_id for s in slot_ids}}
        )
        placements.append(
            Placement(
                job_id=job.job_id,
                node_id=chosen.node_id,
                slot_ids=slot_ids,
                vram_class_gb=chosen.vram_class_gb,
                transition=ADMISSIBLE_STATES[job.state],
                rank=rank,
                prior_node_preferred=chosen.node_id == job.last_node_id,
                won_on=won_on,
                candidates_considered=len(with_room),
            )
        )

    return placements, deferrals


def _winning_key(chosen: Node, candidates: list[Node], job: Job) -> str:
    """Names the first AD-4 key that separated the winner from the runner-up (ARCHITECTURE AD-4, FR-13(c))."""
    if len(candidates) == 1:
        return "only_candidate"
    if chosen.node_id == job.last_node_id:
        return "prior_node"
    others = [n for n in candidates if n is not chosen]
    if all(n.allocations_held > chosen.allocations_held for n in others):
        return "lowest_allocations_held"
    return "node_id_asc"
