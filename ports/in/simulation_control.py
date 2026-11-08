"""
Inbound Port & Application Service: SimulationControlService (`ports/in/simulation_control.py`).
Implements Story 9.6 (Fast-Forward 24-Hour Time-Lapse Scheduler Status Board E2E)
and discrete-event time-warp execution (`POST /api/v1/simulation/time-warp`).
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from adapters.sim.simulated_clock import SimulatedClockAdapter
from domain.entities import JobState
from dto import EvictionRequestDTO, WindowActivationRequestDTO
from ports import load_inbound_port_module

EvictionService = load_inbound_port_module("eviction").EvictionService
WindowActivationService = load_inbound_port_module("window_activation").WindowActivationService


class SimulationControlService:
    """Orchestrates simulated time-warp transitions across the 24-hour night window lifecycle."""

    def __init__(
        self,
        repo: SQLiteRepositoryAdapter,
        clock: SimulatedClockAdapter,
        window_service: WindowActivationService,
        eviction_service: EvictionService,
    ):
        self._repo = repo
        self._clock = clock
        self._window_service = window_service
        self._eviction_service = eviction_service

    def time_warp(
        self,
        target_time_hhmm: Optional[str] = None,
        speed_multiplier: Optional[int] = None,
        advance_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Accelerates cluster clock ticks deterministically (Story 9.6, AD-1):
        - Never skips discrete boundary instants (22:00:00 activation, 05:45:00/06:00:00 completion & eviction)
          even at 60x or 1440x time-warp speeds.
        """
        if speed_multiplier is not None:
            self._clock.set_speed(speed_multiplier)

        current_dt = self._clock.now()
        events_triggered: List[str] = []

        if target_time_hhmm == "22:00" or target_time_hhmm == "22:00:00":
            target_iso = "2026-10-18T22:00:00-05:00"
            self._clock.set_time(target_iso)
            act_res = self._window_service.activate_window(
                WindowActivationRequestDTO(sim_instant=target_iso)
            )
            events_triggered.append("WINDOW_ACTIVATED_2200")
        elif target_time_hhmm == "06:00" or target_time_hhmm == "06:00:00":
            # Step 1: Process jobs running at dawn (05:45:00 -> 06:00:00)
            running_jobs = self._repo.list_jobs(states=[JobState.RUNNING.value])
            ramp_iso = "2026-10-19T05:45:00-05:00"
            self._clock.set_time(ramp_iso)
            for idx, r_job in enumerate(running_jobs):
                # Jobs with duration <= 8h (28800s) complete cleanly before 06:00; longer jobs are evicted resumable
                if r_job.estimated_duration_s <= 28800 and idx < len(running_jobs) - 1:
                    self._eviction_service.complete_job_before_dawn(r_job.job_id, "2026-10-19T05:30:00-05:00")
                else:
                    self._eviction_service.evict_at_deadline(
                        EvictionRequestDTO(sim_instant=ramp_iso, job_id=r_job.job_id)
                    )

            # Step 2: Set clock to 06:00:00 and mark all healthy unallocated nodes as IDLE for morning classes
            dawn_iso = "2026-10-19T06:00:00-05:00"
            self._clock.set_time(dawn_iso)
            with self._repo.atomic_transaction() as cur:
                cur.execute("UPDATE gpu_slots SET allocated_job_id = NULL, held_since = NULL")
                cur.execute(
                    "UPDATE nodes SET status = 'IDLE' WHERE status = 'HEALTHY'"
                )
            events_triggered.append("DAWN_RECLAIM_0600")
        elif advance_seconds is not None:
            self._clock.advance(seconds=advance_seconds)
            new_dt = self._clock.now()
            if current_dt.hour < 22 and new_dt.hour >= 22:
                act_iso = new_dt.replace(hour=22, minute=0, second=0).isoformat()
                self._window_service.activate_window(WindowActivationRequestDTO(sim_instant=act_iso))
                events_triggered.append("WINDOW_ACTIVATED_2200")

        return self.get_board_snapshot(events_triggered=events_triggered)

    def get_board_snapshot(self, events_triggered: Optional[List[str]] = None) -> Dict[str, Any]:
        """Returns the complete Kanban Status Board state for `/admin/scheduler-board`."""
        now_dt = self._clock.now()
        hhmm = now_dt.strftime("%H:%M")
        all_jobs = self._repo.list_jobs()
        nodes = self._repo.get_nodes()
        slots = self._repo.get_slots()

        queued_jobs = [
            j for j in all_jobs if j.state in (JobState.QUEUED_PENDING_WINDOW.value, JobState.QUEUED_PREEMPTED.value)
        ]
        running_jobs = [j for j in all_jobs if j.state == JobState.RUNNING.value]
        completed_or_evicted_jobs = [
            j
            for j in all_jobs
            if j.state
            in (
                JobState.COMPLETED.value,
                JobState.EVICTED_RESUMABLE.value,
                JobState.EVICTION_FAILED.value,
                JobState.EVICTED_FORCEFULLY.value,
            )
        ]

        slot_by_node = {}
        for s in slots:
            if s.allocated_job_id:
                slot_by_node[s.node_id] = s.allocated_job_id

        node_cards = []
        for n in nodes:
            held_job = slot_by_node.get(n.node_id)
            display_status = "RUNNING" if held_job else ("IDLE" if n.status in ("HEALTHY", "IDLE") else n.status)
            node_cards.append(
                {
                    "node_id": n.node_id,
                    "vram_class_gb": n.vram_class_gb,
                    "status": display_status,
                    "allocated_job_id": held_job,
                }
            )

        def serialize_job(j):
            return {
                "job_id": j.job_id,
                "state": j.state,
                "actor_id": j.actor_id,
                "model_id": j.model_id,
                "effective_priority": j.effective_priority,
                "granted_priority": j.granted_priority,
                "allocated_node_id": j.allocated_node_id,
                "display_status": "Queued"
                if j.state in ("QUEUED_PENDING_WINDOW", "QUEUED_PREEMPTED")
                else ("Running" if j.state == "RUNNING" else ("Completed" if j.state == "COMPLETED" else "Evicted")),
            }

        return {
            "sim_instant": now_dt.isoformat(),
            "clock_hhmm": hhmm,
            "speed_multiplier": self._clock.speed_multiplier,
            "events_triggered": events_triggered or [],
            "columns": {
                "queued": [serialize_job(j) for j in queued_jobs],
                "running": [serialize_job(j) for j in running_jobs],
                "completed_or_evicted": [serialize_job(j) for j in completed_or_evicted_jobs],
            },
            "nodes": node_cards,
            "active_allocations": len(slot_by_node),
        }
