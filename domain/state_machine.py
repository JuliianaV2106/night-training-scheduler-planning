"""
Pure State Machine & Transition Guards for Module 9: Night Training Scheduler.
Enforces legal state transitions (T-1 through T-20), temporal window boundaries,
and priority preemption margins (AD-1, AD-6, Invariant S-1).
Zero external I/O or wall-clock imports.
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Set, Tuple
from domain.entities import DomainError, JobEntity, JobState


# Legal state transitions map
LEGAL_TRANSITIONS: Dict[str, Set[str]] = {
    JobState.QUEUED_PENDING_WINDOW.value: {
        JobState.RUNNING.value,
        JobState.QUEUED_PENDING_WINDOW.value,
        JobState.EXPIRED.value,
        JobState.REJECTED.value,
        JobState.FAILED.value,
    },
    JobState.QUEUED_PREEMPTED.value: {
        JobState.RUNNING.value,
        JobState.QUEUED_PENDING_WINDOW.value,
        JobState.EXPIRED.value,
    },
    JobState.RUNNING.value: {
        JobState.CHECKPOINTING.value,
        JobState.COMPLETED.value,
        JobState.FAILED.value,
        JobState.EVICTED_RESUMABLE.value,
        JobState.EVICTION_FAILED.value,
        JobState.EVICTED_FORCEFULLY.value,
        JobState.QUEUED_PREEMPTED.value,
    },
    JobState.CHECKPOINTING.value: {
        JobState.EVICTED_RESUMABLE.value,
        JobState.EVICTION_FAILED.value,
        JobState.EVICTED_FORCEFULLY.value,
        JobState.QUEUED_PENDING_WINDOW.value,
        JobState.QUEUED_PREEMPTED.value,
        JobState.FAILED.value,
    },
    JobState.EVICTED_RESUMABLE.value: {
        JobState.RUNNING.value,
        JobState.QUEUED_PENDING_WINDOW.value,
        JobState.FAILED.value,
        JobState.EXPIRED.value,
    },
    JobState.EVICTION_FAILED.value: {
        JobState.QUEUED_PENDING_WINDOW.value,
        JobState.RUNNING.value,
        JobState.FAILED.value,
    },
    JobState.EVICTED_FORCEFULLY.value: {
        JobState.QUEUED_PENDING_WINDOW.value,
        JobState.FAILED.value,
    },
    JobState.COMPLETED.value: set(),
    JobState.FAILED.value: set(),
    JobState.REJECTED.value: set(),
    JobState.EXPIRED.value: set(),
}

TERMINAL_STATES: Set[str] = {
    JobState.COMPLETED.value,
    JobState.FAILED.value,
    JobState.REJECTED.value,
    JobState.EXPIRED.value,
}


def is_terminal_state(state: str) -> bool:
    """Returns True if the state is terminal and does not count toward active queue cap."""
    return state in TERMINAL_STATES


def validate_transition(current_state: str, target_state: str, job_id: str = "") -> None:
    """Validates that a state transition is legal in the state machine."""
    allowed = LEGAL_TRANSITIONS.get(current_state, set())
    if target_state not in allowed:
        raise DomainError(
            error_code="INVALID_STATE_FOR_EVICTION",
            message=f"Job '{job_id}' is in state '{current_state}', cannot transition to '{target_state}'.",
            http_status=409,
            retryable=False,
            rule_id="self:STATE-MACHINE-GUARD-v1",
            citations=("self:STATE-MACHINE-GUARD-v1",),
            observed_values={"current_state": current_state, "target_state": target_state},
        )


def validate_window_activation_instant(sim_dt: datetime) -> None:
    """
    Contract P1 for activateWindow:
    Time component of clock.now() must be 22:00:00 within tolerance of +/- 2 simulated seconds.
    """
    seconds_since_midnight = sim_dt.hour * 3600 + sim_dt.minute * 60 + sim_dt.second
    target_2200 = 22 * 3600  # 79200
    if abs(seconds_since_midnight - target_2200) > 2:
        raise DomainError(
            error_code="WINDOW_ACTIVATION_OUTSIDE_WINDOW",
            message=(
                f"Window activation invoked at invalid simulated instant '{sim_dt.isoformat()}'. "
                "Window activation occurs strictly at 22:00:00."
            ),
            http_status=400,
            retryable=False,
            rule_id="policy:M2/night-window@v1",
            citations=("policy:M2/night-window@v1", "self:WINDOW-BOUNDARY-v1"),
            observed_values={"sim_instant": sim_dt.isoformat()},
            thresholds={"expected_instant": "22:00:00", "tolerance_s": 2},
        )


def validate_eviction_instant(sim_dt: datetime) -> Tuple[bool, bool]:
    """
    Contract P1 for evictAtDeadline:
    Time component must be within [05:45:00, 06:00:00].
    Returns (is_ramp_start, is_hard_kill_deadline).
    - 05:45:00 marks SIGTERM ramp start.
    - >= 05:46:00 (container 60s timeout) or >= 05:53:00 (ramp deadline) marks SIGKILL eligibility.
    """
    seconds_since_midnight = sim_dt.hour * 3600 + sim_dt.minute * 60 + sim_dt.second
    ramp_start_0545 = 5 * 3600 + 45 * 60  # 20700
    window_end_0600 = 6 * 3600             # 21600

    if seconds_since_midnight < ramp_start_0545 - 2 or seconds_since_midnight > window_end_0600 + 2:
        raise DomainError(
            error_code="EVICTION_CALLED_BEFORE_RAMP",
            message=(
                f"Eviction ramp invoked at simulated instant '{sim_dt.isoformat()}', "
                "preceding scheduled ramp threshold 05:45:00."
            ),
            http_status=400,
            retryable=False,
            rule_id="policy:M2/day-reclaim@v1",
            citations=("policy:M2/day-reclaim@v1", "self:EVICTION-RAMP-v1"),
            observed_values={"sim_instant": sim_dt.isoformat()},
            thresholds={"ramp_threshold": "05:45:00"},
        )

    is_deadline = seconds_since_midnight >= (5 * 3600 + 46 * 60)
    return True, is_deadline


def evaluate_preemption_eligibility(
    challenger: JobEntity,
    victim: JobEntity,
    minimum_margin: int = 20,
) -> Tuple[bool, str]:
    """
    Evaluates Invariant INV-08 / AD-6 & Story 9.5 Preemption rules:
    - Victim must be in RUNNING state and not already preempted in the current window.
    - Challenger must hold higher priority (either THESIS/URGENT with margin >= 20,
      or Story 9.5 Priority 10 vs Priority 1 where delta >= 9 on the 1-10 scale or >= 20 on 100-scale).
    """
    if victim.state != JobState.RUNNING.value:
        return False, "VICTIM_NOT_RUNNING"
    if victim.preempted_in_window >= 1:
        return False, "VICTIM_ALREADY_PREEMPTED_IN_WINDOW"

    # Support both 0-100 scale (PRD AD-6 margin >= 20) and 1-10 scale (Annex Story 9.5 Priority 10 vs 1)
    delta = challenger.effective_priority - victim.effective_priority
    if challenger.effective_priority <= 10 and victim.effective_priority <= 10:
        # 1-10 priority scale from Annex Story 9.5 (Priority 10 preempts Priority 1)
        if delta < 5:
            return False, "PRIORITY_MARGIN_INSUFFICIENT"
    else:
        if challenger.granted_priority not in ("THESIS", "URGENT"):
            return False, "CHALLENGER_TIER_NOT_AUTHORIZED"
        if delta < minimum_margin:
            return False, "PRIORITY_MARGIN_INSUFFICIENT"

    return True, "ELIGIBLE"
