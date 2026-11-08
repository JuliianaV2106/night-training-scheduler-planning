"""
Unit Test Suite (Flow B & Flow C): Pure Core Domain Logic (`domain/`).
Executes in-memory (< 10 ms) with zero network or database I/O.
Also includes the AST Domain Purity Gate (INV-07).
"""

import ast
import glob
from datetime import datetime
import pytest

from domain.entities import (
    CheckpointEntity,
    DecisionRecordEntity,
    DecisionVerb,
    DomainError,
    GpuSlotEntity,
    JobEntity,
    JobState,
    NodeEntity,
    NodeStatus,
    PriorityTier,
)
from domain.state_machine import (
    evaluate_preemption_eligibility,
    is_terminal_state,
    validate_eviction_instant,
    validate_transition,
    validate_window_activation_instant,
)
from domain.ranking import (
    compute_effective_priority,
    rank_candidate_jobs,
    select_preemption_victim,
)
from domain.allocation import (
    allocate_window_batch,
    find_eligible_node_and_slots,
)
from domain.emitter import build_decision_record
from domain.engine import (
    compute_spec_digest,
    evaluate_dawn_eviction,
    evaluate_preemption_cascade,
    fold_decision_log_for_recovery,
    validate_job_submission_rules,
)


def make_job(
    job_id: str = "JOB-0001",
    state: str = JobState.QUEUED_PENDING_WINDOW.value,
    gpu_slots: int = 1,
    vram_gb: int = 24,
    priority: int = 100,
    granted: str = PriorityTier.NORMAL.value,
    missed_nights: int = 0,
    admitted_nights: int = 0,
    submitted_at: str = "2026-10-18T14:00:00-05:00",
    allocated_node_id: str = None,
    last_ckpt: str = None,
    preempted_in_window: int = 0,
) -> JobEntity:
    return JobEntity(
        job_id=job_id,
        state=state,
        actor_id="student-kavita",
        idempotency_key=f"key-{job_id}",
        payload_digest="a" * 64,
        gpu_slots_requested=gpu_slots,
        required_vram_gb=vram_gb,
        checkpoint_interval_minutes=15,
        estimated_duration_s=3600,
        image_digest="sha256:" + "b" * 64,
        model_id="llama-3-8b",
        model_version="1.0",
        storage_request_bytes=1024,
        submitted_at=submitted_at,
        effective_priority=priority,
        granted_priority=granted,
        consecutive_nights_missed=missed_nights,
        admitted_nights=admitted_nights,
        allocated_node_id=allocated_node_id,
        last_checkpoint_at=last_ckpt,
        preempted_in_window=preempted_in_window,
    )


class TestDomainPurityAstGate:
    """Enforces INV-07 / AD-1: Zero forbidden I/O or wall-clock imports in domain/."""

    def test_domain_purity_ast_scan_has_zero_forbidden_imports(self):
        forbidden = {"fastapi", "starlette", "sqlite3", "sqlalchemy", "requests", "httpx", "time", "random"}
        violations = []
        files = glob.glob("domain/**/*.py", recursive=True)
        assert len(files) >= 6, "Expected all domain modules to be present"

        for f in files:
            with open(f, "r", encoding="utf-8") as fp:
                tree = ast.parse(fp.read(), filename=f)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in forbidden:
                            violations.append(f"{f}: forbidden import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in forbidden:
                        violations.append(f"{f}: forbidden from-import {node.module}")
        assert violations == [], f"Domain purity check FAILED: {violations}"


class TestStateMachineAndGuards:
    """Unit tests for domain/state_machine.py."""

    def test_terminal_states_identification(self):
        assert is_terminal_state(JobState.COMPLETED.value) is True
        assert is_terminal_state(JobState.FAILED.value) is True
        assert is_terminal_state(JobState.REJECTED.value) is True
        assert is_terminal_state(JobState.EXPIRED.value) is True
        assert is_terminal_state(JobState.RUNNING.value) is False
        assert is_terminal_state(JobState.QUEUED_PENDING_WINDOW.value) is False

    def test_legal_and_illegal_state_transitions(self):
        # Legal transitions
        validate_transition(JobState.QUEUED_PENDING_WINDOW.value, JobState.RUNNING.value, "JOB-1")
        validate_transition(JobState.RUNNING.value, JobState.CHECKPOINTING.value, "JOB-1")
        validate_transition(JobState.CHECKPOINTING.value, JobState.EVICTED_RESUMABLE.value, "JOB-1")
        validate_transition(JobState.CHECKPOINTING.value, JobState.EVICTION_FAILED.value, "JOB-1")

        # Illegal transitions raise DomainError
        with pytest.raises(DomainError) as exc:
            validate_transition(JobState.COMPLETED.value, JobState.RUNNING.value, "JOB-1")
        assert exc.value.error_code == "INVALID_STATE_FOR_EVICTION"
        assert exc.value.http_status == 409

    def test_window_activation_instant_guard(self):
        # Exact 22:00:00 and within +/- 2s pass
        validate_window_activation_instant(datetime.fromisoformat("2026-10-18T22:00:00-05:00"))
        validate_window_activation_instant(datetime.fromisoformat("2026-10-18T22:00:02-05:00"))

        # Daytime fails with 400
        with pytest.raises(DomainError) as exc:
            validate_window_activation_instant(datetime.fromisoformat("2026-10-18T14:30:00-05:00"))
        assert exc.value.error_code == "WINDOW_ACTIVATION_OUTSIDE_WINDOW"
        assert exc.value.http_status == 400

    def test_eviction_instant_guard(self):
        is_ramp, is_kill = validate_eviction_instant(datetime.fromisoformat("2026-10-19T05:45:00-05:00"))
        assert is_ramp is True
        assert is_kill is False

        is_ramp2, is_kill2 = validate_eviction_instant(datetime.fromisoformat("2026-10-19T05:46:00-05:00"))
        assert is_ramp2 is True
        assert is_kill2 is True

        with pytest.raises(DomainError) as exc:
            validate_eviction_instant(datetime.fromisoformat("2026-10-19T05:00:00-05:00"))
        assert exc.value.error_code == "EVICTION_CALLED_BEFORE_RAMP"

    def test_preemption_eligibility_guards(self):
        challenger = make_job("JOB-CHAL", priority=130, granted="THESIS")
        victim = make_job("JOB-VIC", state=JobState.RUNNING.value, priority=100, granted="NORMAL")
        ok, reason = evaluate_preemption_eligibility(challenger, victim)
        assert ok is True
        assert reason == "ELIGIBLE"

        # Victim not running
        victim_queued = make_job("JOB-VIC-Q", state=JobState.QUEUED_PENDING_WINDOW.value, priority=100)
        ok, reason = evaluate_preemption_eligibility(challenger, victim_queued)
        assert ok is False
        assert reason == "VICTIM_NOT_RUNNING"

        # Victim already preempted in window
        victim_already = make_job("JOB-VIC-A", state=JobState.RUNNING.value, priority=100, preempted_in_window=1)
        ok, reason = evaluate_preemption_eligibility(challenger, victim_already)
        assert ok is False
        assert reason == "VICTIM_ALREADY_PREEMPTED_IN_WINDOW"

        # Challenger tier not authorized on 100-scale
        normal_chal = make_job("JOB-NORM", priority=130, granted="NORMAL")
        ok, reason = evaluate_preemption_eligibility(normal_chal, victim)
        assert ok is False
        assert reason == "CHALLENGER_TIER_NOT_AUTHORIZED"

        # Margin under 20 on 100-scale
        low_margin_chal = make_job("JOB-LOW", priority=115, granted="THESIS")
        ok, reason = evaluate_preemption_eligibility(low_margin_chal, victim)
        assert ok is False
        assert reason == "PRIORITY_MARGIN_INSUFFICIENT"

        # 1-10 scale (Annex Story 9.5): Priority 10 vs Priority 1
        chal_10 = make_job("JOB-10", priority=10, granted="THESIS")
        vic_1 = make_job("JOB-1", state=JobState.RUNNING.value, priority=1, granted="EXPLORATION")
        ok, reason = evaluate_preemption_eligibility(chal_10, vic_1)
        assert ok is True

        # 1-10 scale insufficient margin
        chal_3 = make_job("JOB-3", priority=3, granted="THESIS")
        ok, reason = evaluate_preemption_eligibility(chal_3, vic_1)
        assert ok is False
        assert reason == "PRIORITY_MARGIN_INSUFFICIENT"


class TestRankingAndAllocation:
    """Unit tests for domain/ranking.py and domain/allocation.py."""

    def test_compute_effective_priority_aging_and_starvation(self):
        assert compute_effective_priority(100, consecutive_nights_missed=0) == 100
        assert compute_effective_priority(100, consecutive_nights_missed=2) == 120
        # Starvation promotion kicks in at 3 missed nights (+30 aging + 50 boost = 180)
        assert compute_effective_priority(100, consecutive_nights_missed=3) == 180

    def test_rank_candidate_jobs_deterministic_order(self):
        j1 = make_job("JOB-0002", priority=100, missed_nights=0, submitted_at="2026-10-18T15:00:00-05:00")
        j2 = make_job("JOB-0001", priority=150, missed_nights=0, submitted_at="2026-10-18T16:00:00-05:00")
        j3 = make_job("JOB-0003", priority=100, missed_nights=2, submitted_at="2026-10-18T17:00:00-05:00")
        j4 = make_job("JOB-0004", priority=100, missed_nights=0, submitted_at="2026-10-18T14:00:00-05:00")

        ranked = rank_candidate_jobs([j1, j2, j3, j4])
        assert [j.job_id for j in ranked] == ["JOB-0001", "JOB-0003", "JOB-0004", "JOB-0002"]

    def test_select_preemption_victim_picks_lowest_priority_earliest_checkpoint(self):
        chal = make_job("JOB-KAVITA", priority=10, granted="THESIS")
        v1 = make_job(
            "JOB-EXP-01",
            state=JobState.RUNNING.value,
            priority=1,
            allocated_node_id="ws-gpu-01",
            last_ckpt="2026-10-18T23:30:00-05:00",
        )
        v2 = make_job(
            "JOB-EXP-06",
            state=JobState.RUNNING.value,
            priority=1,
            allocated_node_id="ws-gpu-06",
            last_ckpt="2026-10-18T22:45:00-05:00",  # Earliest checkpoint
        )
        v3 = make_job(
            "JOB-EXP-09",
            state=JobState.RUNNING.value,
            priority=2,
            allocated_node_id="ws-gpu-09",
            last_ckpt="2026-10-18T22:15:00-05:00",
        )
        # Candidate with smaller VRAM or slots is skipped if challenger needs more
        v_small = make_job("JOB-SMALL", state=JobState.RUNNING.value, priority=1, gpu_slots=1, vram_gb=24)
        chal_2gpu = make_job("JOB-CHAL-2G", priority=10, gpu_slots=2, vram_gb=48)
        assert select_preemption_victim(chal_2gpu, [v_small]) is None

        # Candidate with matching slots (1) but smaller VRAM (24 < 48) is skipped
        chal_1gpu_48vram = make_job("JOB-CHAL-48", priority=10, gpu_slots=1, vram_gb=48)
        assert select_preemption_victim(chal_1gpu_48vram, [v_small]) is None

        victim = select_preemption_victim(chal, [v1, v2, v3])
        assert victim is not None
        assert victim.job_id == "JOB-EXP-06"
        assert victim.allocated_node_id == "ws-gpu-06"

    def test_allocate_window_batch_and_affinity_and_exhaustion(self):
        nodes = [
            NodeEntity("ws-gpu-01", 24, 1, "HEALTHY"),
            NodeEntity("ws-gpu-02", 24, 1, "HEALTHY"),
            NodeEntity("ws-gpu-03", 24, 1, "CORDONED"),
            NodeEntity("server-gpu-01", 48, 2, "HEALTHY"),
        ]
        slots = [
            GpuSlotEntity("slot-ws-01-0", "ws-gpu-01", 0),
            GpuSlotEntity("slot-ws-02-0", "ws-gpu-02", 0),
            GpuSlotEntity("slot-ws-03-0", "ws-gpu-03", 0),
            GpuSlotEntity("slot-srv-01-0", "server-gpu-01", 0),
            GpuSlotEntity("slot-srv-01-1", "server-gpu-01", 1),
        ]

        # Job with affinity to ws-gpu-02, normal 24GB job, 2-GPU 48GB job, and excess 24GB job
        j_affinity = make_job("JOB-AFF", priority=200, state=JobState.EVICTED_RESUMABLE.value, allocated_node_id="ws-gpu-02")
        j_normal = make_job("JOB-NORM", priority=150)
        j_overflow = make_job("JOB-OVER", priority=100)
        j_2gpu = make_job("JOB-2GPU", priority=180, gpu_slots=2, vram_gb=48)

        decisions = allocate_window_batch([j_affinity, j_normal, j_overflow, j_2gpu], nodes, slots, "2026-10-18T22:00:00-05:00")
        by_id = {d.job_id: d for d in decisions}

        assert by_id["JOB-AFF"].admitted is True
        assert by_id["JOB-AFF"].node_id == "ws-gpu-02"
        assert by_id["JOB-AFF"].transition == "T-12"

        assert by_id["JOB-2GPU"].admitted is True
        assert by_id["JOB-2GPU"].node_id == "server-gpu-01"
        assert len(by_id["JOB-2GPU"].slot_ids) == 2

        assert by_id["JOB-NORM"].admitted is True
        assert by_id["JOB-NORM"].node_id == "ws-gpu-01"

        assert by_id["JOB-OVER"].admitted is False
        assert by_id["JOB-OVER"].transition == "T-4b"

        # Test T-4a when no eligible node exists at all (all 48GB cordoned)
        nodes_no_48 = [NodeEntity("server-gpu-01", 48, 2, "CORDONED")]
        dec_no_node = allocate_window_batch([j_2gpu], nodes_no_48, slots, "2026-10-18T22:00:00-05:00")
        assert dec_no_node[0].admitted is False
        assert dec_no_node[0].transition == "T-4a"


class TestEmitterAndEngineRules:
    """Unit tests for domain/emitter.py and domain/engine.py."""

    def test_emitter_fails_closed_on_empty_citations_or_summary(self):
        with pytest.raises(DomainError) as exc:
            build_decision_record(
                decision_id="DEC-1",
                sim_timestamp="2026-10-18T22:00:00-05:00",
                decision="ADMIT",
                actor_id="sys",
                summary="Valid summary",
                citations=[],
                inputs={},
            )
        assert exc.value.error_code == "EXPLAINABILITY_CITATION_MISSING"

        with pytest.raises(DomainError) as exc2:
            build_decision_record(
                decision_id="DEC-2",
                sim_timestamp="2026-10-18T22:00:00-05:00",
                decision="ADMIT",
                actor_id="sys",
                summary="   ",
                citations=["self:RULE-1"],
                inputs={},
            )
        assert exc2.value.error_code == "EXPLAINABILITY_SUMMARY_MISSING"

    def test_validate_job_submission_rules_all_branches(self):
        valid_spec = {
            "worker_count": 1,
            "replicas": 1,
            "distributed_artifact_present": False,
            "gpu_slots_requested": 1,
            "required_vram_gb": 24,
            "estimated_duration_s": 3600,
            "storage_request_bytes": 1000,
        }
        digest = validate_job_submission_rules(valid_spec, active_job_count=10, available_storage_bytes=50000)
        assert len(digest) == 64

        # Same idempotency key with same digest succeeds
        existing = make_job("JOB-EXIST")
        existing.payload_digest = digest
        assert validate_job_submission_rules(valid_spec, 10, 50000, existing_job_with_key=existing) == digest

        # Idempotency conflict with different digest
        existing_diff = make_job("JOB-DIFF")
        existing_diff.payload_digest = "0" * 64
        with pytest.raises(DomainError) as exc:
            validate_job_submission_rules(valid_spec, 10, 50000, existing_job_with_key=existing_diff)
        assert exc.value.error_code == "IDEMPOTENCY_CONFLICT"

        # Distributed rejection
        dist_spec = dict(valid_spec, worker_count=4)
        with pytest.raises(DomainError) as exc:
            validate_job_submission_rules(dist_spec, 10, 50000)
        assert exc.value.error_code == "OUT_OF_SCOPE_DISTRIBUTED"

        # 2-GPU on 24GB rejection
        bad_2gpu = dict(valid_spec, gpu_slots_requested=2, required_vram_gb=24)
        with pytest.raises(DomainError) as exc:
            validate_job_submission_rules(bad_2gpu, 10, 50000)
        assert exc.value.error_code == "TWO_GPU_REQUIRES_48GB"

        # Max night span exceeded
        long_spec = dict(valid_spec, estimated_duration_s=200000)
        with pytest.raises(DomainError) as exc:
            validate_job_submission_rules(long_spec, 10, 50000)
        assert exc.value.error_code == "MAX_NIGHT_SPAN_EXCEEDED"

        # Queue cap 500 exceeded
        with pytest.raises(DomainError) as exc:
            validate_job_submission_rules(valid_spec, active_job_count=500, available_storage_bytes=50000)
        assert exc.value.error_code == "QUEUE_CAP_EXCEEDED"

        # Storage full
        with pytest.raises(DomainError) as exc:
            validate_job_submission_rules(valid_spec, active_job_count=10, available_storage_bytes=100)
        assert exc.value.error_code == "STORE_FULL"

    def test_evaluate_dawn_eviction_happy_and_failure_branches(self):
        job = make_job("JOB-EVICT", state=JobState.RUNNING.value, allocated_node_id="ws-gpu-11")
        dt = datetime.fromisoformat("2026-10-19T05:45:00-05:00")

        # Happy path
        happy = evaluate_dawn_eviction(job, dt, True, True, "DEC-H")
        assert happy.final_job_state == JobState.EVICTED_RESUMABLE.value
        assert happy.cordon_requested is False
        assert happy.sigkill_dispatched is False

        # Failure path (Plan-2 contract labels)
        fail_p2 = evaluate_dawn_eviction(job, dt, False, False, "DEC-F1", strict_story_9_4_labels=False)
        assert fail_p2.final_job_state == JobState.EVICTION_FAILED.value
        assert fail_p2.node_target_status == "CORDONED"
        assert fail_p2.cordon_requested is True
        assert fail_p2.sigkill_dispatched is True

        # Failure path (Annex Story 9.4 labels: EVICTED_FORCEFULLY & CORDONED_DIRTY)
        fail_94 = evaluate_dawn_eviction(job, dt, True, False, "DEC-F2", strict_story_9_4_labels=True)
        assert fail_94.final_job_state == JobState.EVICTED_FORCEFULLY.value
        assert fail_94.node_target_status == "CORDONED_DIRTY"
        assert fail_94.residual_gpu_processes == 0

        # Invalid job state for eviction
        completed_job = make_job("JOB-DONE", state=JobState.COMPLETED.value)
        with pytest.raises(DomainError):
            evaluate_dawn_eviction(completed_job, dt, True, True, "DEC-ERR")

    def test_evaluate_preemption_cascade_and_recovery_fold(self):
        dt = datetime.fromisoformat("2026-10-18T23:10:00-05:00")
        chal = make_job("JOB-THESIS", priority=10, granted="THESIS")
        vic = make_job("JOB-EXP", state=JobState.RUNNING.value, priority=1, allocated_node_id="ws-gpu-06")

        outcome = evaluate_preemption_cascade(chal, [vic], dt, "DEC-PRE-1")
        assert outcome.preempted is True
        assert outcome.victim_job_id == "JOB-EXP"
        assert outcome.victim_new_state == JobState.QUEUED_PREEMPTED.value
        assert outcome.assigned_node_id == "ws-gpu-06"

        # Refused preemption when no eligible victim
        outcome_refused = evaluate_preemption_cascade(chal, [], dt, "DEC-PRE-2")
        assert outcome_refused.preempted is False
        assert outcome_refused.reason_code == "PRIORITY_MARGIN_INSUFFICIENT"

        # Crash recovery fold test
        r1 = build_decision_record("D1", dt.isoformat(), "ADMIT", "sys", "s", ["r1"], {}, job_id="J1", transition="T-1")
        r2 = build_decision_record("D2", dt.isoformat(), "ADMIT", "sys", "s", ["r1"], {}, job_id="J1", transition="T-3")
        r3 = outcome.decision_record
        r4 = build_decision_record("D4", dt.isoformat(), "EVICT", "sys", "s", ["r1"], {}, job_id="J2", transition="T-8")
        r5 = build_decision_record("D5", dt.isoformat(), "EVICT", "sys", "s", ["r1"], {}, job_id="J3", transition="T-9")
        r6 = build_decision_record("D6", dt.isoformat(), "COMPLETE", "sys", "s", ["r1"], {}, job_id="J4")
        r7 = build_decision_record("D7", dt.isoformat(), "FAIL", "sys", "s", ["r1"], {}, job_id="J5")

        # Duplicate record D2 is ignored (idempotent fold without replay)
        r_no_job = build_decision_record("D8", dt.isoformat(), "DEFER", "sys", "s", ["r1"], {}, job_id=None)
        r_defer_job = build_decision_record("D9", dt.isoformat(), "DEFER", "sys", "s", ["r1"], {}, job_id="J6")
        r_preempt_no_vic = build_decision_record("D10", dt.isoformat(), "PREEMPT", "sys", "s", ["r1"], {}, job_id="J7")
        state_map = fold_decision_log_for_recovery([r1, r2, r2, r3, r4, r5, r6, r7, r_no_job, r_defer_job, r_preempt_no_vic])
        assert state_map["J1"] == JobState.RUNNING.value
        assert state_map["JOB-THESIS"] == JobState.RUNNING.value
        assert state_map["JOB-EXP"] == JobState.QUEUED_PREEMPTED.value
        assert state_map["J2"] == JobState.EVICTED_RESUMABLE.value
        assert state_map["J3"] == JobState.EVICTION_FAILED.value
        assert state_map["J4"] == JobState.COMPLETED.value
        assert state_map["J5"] == JobState.FAILED.value
        assert state_map["J7"] == JobState.RUNNING.value


class TestParameterizedDomainMatrix:
    """
    High-velocity parameterized unit tests (< 1 ms each) verifying exhaustive state machine matrix,
    priority aging curves, and allocation constraints (Flow B / Flow C 70% Unit Pyramid Layer).
    """

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            (JobState.QUEUED_PENDING_WINDOW.value, JobState.RUNNING.value),
            (JobState.QUEUED_PENDING_WINDOW.value, JobState.QUEUED_PENDING_WINDOW.value),
            (JobState.QUEUED_PENDING_WINDOW.value, JobState.EXPIRED.value),
            (JobState.QUEUED_PENDING_WINDOW.value, JobState.REJECTED.value),
            (JobState.QUEUED_PENDING_WINDOW.value, JobState.FAILED.value),
            (JobState.QUEUED_PREEMPTED.value, JobState.RUNNING.value),
            (JobState.QUEUED_PREEMPTED.value, JobState.QUEUED_PENDING_WINDOW.value),
            (JobState.QUEUED_PREEMPTED.value, JobState.EXPIRED.value),
            (JobState.RUNNING.value, JobState.COMPLETED.value),
            (JobState.RUNNING.value, JobState.FAILED.value),
            (JobState.RUNNING.value, JobState.CHECKPOINTING.value),
            (JobState.RUNNING.value, JobState.QUEUED_PREEMPTED.value),
            (JobState.RUNNING.value, JobState.EVICTED_RESUMABLE.value),
            (JobState.RUNNING.value, JobState.EVICTED_FORCEFULLY.value),
            (JobState.CHECKPOINTING.value, JobState.EVICTED_RESUMABLE.value),
            (JobState.CHECKPOINTING.value, JobState.EVICTION_FAILED.value),
            (JobState.CHECKPOINTING.value, JobState.EVICTED_FORCEFULLY.value),
            (JobState.CHECKPOINTING.value, JobState.QUEUED_PENDING_WINDOW.value),
            (JobState.CHECKPOINTING.value, JobState.QUEUED_PREEMPTED.value),
            (JobState.EVICTED_RESUMABLE.value, JobState.RUNNING.value),
            (JobState.EVICTED_RESUMABLE.value, JobState.EXPIRED.value),
        ],
    )
    def test_all_legal_state_transitions_succeed(self, from_state: str, to_state: str):
        validate_transition(from_state, to_state, "JOB-PARAM")

    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            (JobState.COMPLETED.value, JobState.RUNNING.value),
            (JobState.COMPLETED.value, JobState.CHECKPOINTING.value),
            (JobState.FAILED.value, JobState.RUNNING.value),
            (JobState.REJECTED.value, JobState.QUEUED_PENDING_WINDOW.value),
            (JobState.EXPIRED.value, JobState.RUNNING.value),
            (JobState.EVICTION_FAILED.value, JobState.COMPLETED.value),
            (JobState.EVICTED_FORCEFULLY.value, JobState.COMPLETED.value),
            (JobState.QUEUED_PENDING_WINDOW.value, JobState.COMPLETED.value),
            (JobState.QUEUED_PREEMPTED.value, JobState.COMPLETED.value),
        ],
    )
    def test_all_illegal_state_transitions_raise_domain_error(self, from_state: str, to_state: str):
        with pytest.raises(DomainError) as exc:
            validate_transition(from_state, to_state, "JOB-ILLEGAL")
        assert exc.value.http_status == 409

    @pytest.mark.parametrize(
        "base_priority,missed_nights,expected_score",
        [
            (100, 0, 100),
            (100, 1, 110),
            (100, 2, 120),
            (100, 3, 180),
            (100, 4, 190),
            (150, 0, 150),
            (150, 3, 230),
            (50, 3, 130),
        ],
    )
    def test_aging_and_starvation_promotion_curve(self, base_priority: int, missed_nights: int, expected_score: int):
        assert compute_effective_priority(base_priority, missed_nights) == expected_score

    @pytest.mark.parametrize(
        "iso_instant,should_pass",
        [
            ("2026-10-18T21:59:58-05:00", True),
            ("2026-10-18T21:59:59-05:00", True),
            ("2026-10-18T22:00:00-05:00", True),
            ("2026-10-18T22:00:01-05:00", True),
            ("2026-10-18T22:00:02-05:00", True),
            ("2026-10-18T21:59:57-05:00", False),
            ("2026-10-18T22:00:03-05:00", False),
            ("2026-10-18T06:00:00-05:00", False),
            ("2026-10-18T12:00:00-05:00", False),
        ],
    )
    def test_window_activation_boundary_instants(self, iso_instant: str, should_pass: bool):
        dt = datetime.fromisoformat(iso_instant)
        if should_pass:
            validate_window_activation_instant(dt)
        else:
            with pytest.raises(DomainError) as exc:
                validate_window_activation_instant(dt)
            assert exc.value.error_code == "WINDOW_ACTIVATION_OUTSIDE_WINDOW"

