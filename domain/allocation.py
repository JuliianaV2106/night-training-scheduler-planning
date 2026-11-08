"""
Pure Deterministic GPU Slot Allocation Logic for Module 9: Night Training Scheduler.
Enforces AD-4 (31 x 24GB Workstations + 1 x 2x48GB Server = 33 Slots),
atomic 2-GPU spanning on server-gpu-01, and total-order tie-breaking.
Zero external I/O or wall-clock imports.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from domain.entities import GpuSlotEntity, JobEntity, NodeEntity
from domain.ranking import rank_candidate_jobs


@dataclass(frozen=True)
class AllocationDecision:
    """Pure allocation outcome for a single candidate job."""
    job_id: str
    admitted: bool
    node_id: Optional[str]
    slot_ids: Tuple[str, ...]
    vram_class_gb: Optional[int]
    transition: str
    reason_code: str


def find_eligible_node_and_slots(
    job: JobEntity,
    nodes: Dict[str, NodeEntity],
    slots_by_node: Dict[str, List[GpuSlotEntity]],
) -> Tuple[Optional[NodeEntity], List[GpuSlotEntity], str]:
    """
    Finds the best eligible node and free slots for `job` following Contract activateWindow Q2:
    Total Order:
    1. Previously assigned node (affinity, if eligible and has required free slots)
    2. Lowest current `allocations_held` on the node
    3. `node_id` ascending (lexicographical string comparison)
    """
    healthy_matching_nodes: List[NodeEntity] = []
    for node in nodes.values():
        if node.status not in ("HEALTHY", "IDLE"):
            continue
        if job.gpu_slots_requested == 2:
            if node.vram_class_gb == 48 and node.total_slots >= 2:
                healthy_matching_nodes.append(node)
        else:
            # 1-GPU job: must match required VRAM class (24GB prefers 24GB nodes; 48GB requires 48GB node)
            if node.vram_class_gb == job.required_vram_gb:
                healthy_matching_nodes.append(node)

    if not healthy_matching_nodes:
        return None, [], "T-4a_NO_ELIGIBLE_NODE"

    # Filter nodes that currently have enough free slots
    candidates_with_slots: List[Tuple[int, int, str, NodeEntity, List[GpuSlotEntity]]] = []
    for node in healthy_matching_nodes:
        node_slots = slots_by_node.get(node.node_id, [])
        free_slots = [s for s in node_slots if s.allocated_job_id is None]
        held_count = len(node_slots) - len(free_slots)
        if len(free_slots) >= job.gpu_slots_requested:
            # Priority 0 if prior node matches, 1 otherwise
            affinity_rank = 0 if (job.allocated_node_id and job.allocated_node_id == node.node_id) else 1
            selected_slots = sorted(free_slots, key=lambda s: s.slot_index)[: job.gpu_slots_requested]
            candidates_with_slots.append((affinity_rank, held_count, node.node_id, node, selected_slots))

    if not candidates_with_slots:
        return None, [], "T-4b_CAPACITY_EXHAUSTED"

    candidates_with_slots.sort(key=lambda item: (item[0], item[1], item[2]))
    _, _, _, best_node, chosen_slots = candidates_with_slots[0]
    return best_node, chosen_slots, "PLACED"


def allocate_window_batch(
    candidate_jobs: List[JobEntity],
    nodes: List[NodeEntity],
    slots: List[GpuSlotEntity],
    sim_instant: str,
) -> List[AllocationDecision]:
    """
    Pure batch reducer that ranks all candidate jobs and assigns up to 33 GPU slots
    deterministically without mutating external state.
    """
    node_map: Dict[str, NodeEntity] = {n.node_id: n for n in nodes}
    slots_by_node: Dict[str, List[GpuSlotEntity]] = {}
    for s in slots:
        slots_by_node.setdefault(s.node_id, []).append(
            GpuSlotEntity(
                slot_id=s.slot_id,
                node_id=s.node_id,
                slot_index=s.slot_index,
                allocated_job_id=s.allocated_job_id,
                held_since=s.held_since,
            )
        )

    ordered_jobs = rank_candidate_jobs(candidate_jobs)
    decisions: List[AllocationDecision] = []

    for job in ordered_jobs:
        best_node, chosen_slots, reason = find_eligible_node_and_slots(job, node_map, slots_by_node)
        if best_node is not None and chosen_slots:
            for s in chosen_slots:
                s.allocated_job_id = job.job_id
                s.held_since = sim_instant
            transition = "T-12" if job.state == "EVICTED_RESUMABLE" or job.admitted_nights > 0 else "T-3"
            decisions.append(
                AllocationDecision(
                    job_id=job.job_id,
                    admitted=True,
                    node_id=best_node.node_id,
                    slot_ids=tuple(s.slot_id for s in chosen_slots),
                    vram_class_gb=best_node.vram_class_gb,
                    transition=transition,
                    reason_code="ADMITTED_TO_WINDOW",
                )
            )
        else:
            transition = "T-4a" if reason == "T-4a_NO_ELIGIBLE_NODE" else "T-4b"
            decisions.append(
                AllocationDecision(
                    job_id=job.job_id,
                    admitted=False,
                    node_id=None,
                    slot_ids=(),
                    vram_class_gb=None,
                    transition=transition,
                    reason_code=reason,
                )
            )

    return decisions
