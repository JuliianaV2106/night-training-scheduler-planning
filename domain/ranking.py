"""
Pure Deterministic Ranking & Victim Selection for Module 9: Night Training Scheduler.
Implements Admission Order (FR-8, FR-14, FR-15) and Preemption Victim Comparator (Story 9.5, AD-6, AD-22).
Zero external I/O or wall-clock imports.
"""

from __future__ import annotations
from typing import List, Optional
from domain.entities import JobEntity
from domain.state_machine import evaluate_preemption_eligibility


def compute_effective_priority(
    base_priority: int,
    consecutive_nights_missed: int,
    aging_bonus_per_night: int = 10,
    starvation_threshold_nights: int = 3,
    starvation_boost: int = 50,
) -> int:
    """
    Calculates Effective Priority per FR-14 / FR-15:
    Applies aging per missed night and starvation promotion if missed nights >= threshold.
    """
    score = base_priority + (consecutive_nights_missed * aging_bonus_per_night)
    if consecutive_nights_missed >= starvation_threshold_nights:
        score += starvation_boost
    return score


def rank_candidate_jobs(candidates: List[JobEntity]) -> List[JobEntity]:
    """
    Sorts candidate jobs into deterministic Admission Order (Contract activateWindow Q2):
    1. effective_priority descending
    2. consecutive_nights_missed descending
    3. submitted_at ascending (lexicographical ISO-8601)
    4. job_id ascending
    """
    return sorted(
        candidates,
        key=lambda j: (
            -j.effective_priority,
            -j.consecutive_nights_missed,
            j.submitted_at,
            j.job_id,
        ),
    )


def select_preemption_victim(
    challenger: JobEntity,
    running_jobs: List[JobEntity],
    minimum_margin: int = 20,
) -> Optional[JobEntity]:
    """
    Selects the deterministic preemption victim for Story 9.5 / AD-6 / AD-22:
    Identifies eligible running jobs and selects:
    1. Lowest effective_priority ascending
    2. Earliest checkpoint timestamp ascending (jobs with earliest/oldest checkpoint first; None treated as last)
    3. Latest submitted_at descending (youngest exploration run) or allocated_node_id ascending for tie-breaking
    4. job_id ascending
    """
    eligible_victims: List[JobEntity] = []
    for candidate in running_jobs:
        if candidate.gpu_slots_requested < challenger.gpu_slots_requested:
            continue
        if candidate.required_vram_gb < challenger.required_vram_gb:
            continue
        ok, _ = evaluate_preemption_eligibility(challenger, candidate, minimum_margin=minimum_margin)
        if ok:
            eligible_victims.append(candidate)

    if not eligible_victims:
        return None

    # Sort by: lowest priority -> earliest checkpoint timestamp -> node_id -> job_id
    def victim_sort_key(j: JobEntity):
        # If last_checkpoint_at is present, sort earliest first; if None, sort after checkpointed ones
        ckpt_key = (0, j.last_checkpoint_at) if j.last_checkpoint_at else (1, "9999-12-31T23:59:59")
        return (
            j.effective_priority,
            ckpt_key,
            j.allocated_node_id or "",
            j.job_id,
        )

    eligible_victims.sort(key=victim_sort_key)
    return eligible_victims[0]
