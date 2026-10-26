"""
Story 1.1 — Job Submission Ingress & Validation Skeleton (POST /api/v1/jobs).

Each test names the Gherkin scenario (planning/epics.md) or contract clause it verifies.
"""

import json

from tests.unit.helpers import ERROR_BODY_KEYS, JOBS_URL, count_jobs, job_payload


class TestHappyPath:
    """Scenario: Given student-kavita and a valid 1-GPU 24 GB spec,
    When she posts to /api/v1/jobs with key idemp-key-happy-001,
    Then 201 returns JOB-0001 in QUEUED_PENDING_WINDOW and exactly one jobs row is committed."""

    def test_returns_201_with_contract_payload(self, client):
        res = client.post(JOBS_URL, json=job_payload("idemp-key-happy-001"))

        assert res.status_code == 201
        body = res.json()
        assert body["job_id"] == "JOB-0001"
        assert body["state"] == "QUEUED_PENDING_WINDOW"
        assert body["idempotency_key"] == "idemp-key-happy-001"
        assert len(body["payload_digest"]) == 64
        assert body["admitted_at"] == "2026-10-18T14:30:00-05:00"
        assert body["queue_position"] == 1
        assert body["estimated_first_window"] == "2026-10-18"

    def test_commits_exactly_one_job_decision_and_audit_event(self, client, db):
        client.post(JOBS_URL, json=job_payload("idemp-key-happy-001"))

        assert db.execute(
            "SELECT state, actor_id, consecutive_nights_missed, admitted_nights, retry_count FROM jobs"
        ).fetchall() == [("QUEUED_PENDING_WINDOW", "student-kavita", 0, 0, 0)]
        decision = db.execute("SELECT decision, transition, citations FROM decision_records").fetchall()
        assert len(decision) == 1
        assert decision[0][:2] == ("ADMIT", "T-1")
        assert json.loads(decision[0][2]) == [
            "self:JOBSPEC-VALIDATION-v1", "policy:M2/night-window@v1", "catalog:M5/llama-3-8b-instruct@1.0.0",
        ]
        event = db.execute("SELECT event_type, payload FROM audit_events").fetchone()
        assert event[0] == "JOB_SUBMITTED"
        assert json.loads(event[1])["job_id"] == "JOB-0001"

    def test_job_ids_and_queue_positions_are_sequential(self, client):
        bodies = [client.post(JOBS_URL, json=job_payload(f"key-{i}")).json() for i in range(3)]

        assert [b["job_id"] for b in bodies] == ["JOB-0001", "JOB-0002", "JOB-0003"]
        assert [b["queue_position"] for b in bodies] == [1, 2, 3]

    def test_submission_after_window_open_targets_next_night(self, client, fake_clock):
        fake_clock.jump_to("2026-10-18T23:10:00-05:00")

        body = client.post(JOBS_URL, json=job_payload("late-key")).json()

        assert body["estimated_first_window"] == "2026-10-19"


class TestIdempotency:
    def test_identical_resubmission_returns_200_with_original_job(self, client, db):
        first = client.post(JOBS_URL, json=job_payload("idemp-key-happy-001"))
        replay = client.post(JOBS_URL, json=job_payload("idemp-key-happy-001"))

        assert first.status_code == 201
        assert replay.status_code == 200
        assert replay.json()["job_id"] == first.json()["job_id"]
        assert count_jobs(db) == 1

    def test_same_key_different_payload_is_409_with_zero_inserts(self, client, db):
        """Scenario (failure path): same key, differing digest -> 409 IDEMPOTENCY_CONFLICT, zero rows."""
        client.post(JOBS_URL, json=job_payload("idemp-key-happy-001"))

        res = client.post(JOBS_URL, json=job_payload("idemp-key-happy-001", estimated_duration_s=9000))

        assert res.status_code == 409
        body = res.json()
        assert ERROR_BODY_KEYS <= body.keys()
        assert body["error_code"] == "IDEMPOTENCY_CONFLICT"
        assert body["http_status"] == 409
        assert body["retryable"] is False
        assert count_jobs(db) == 1
        assert db.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0] == 1


class TestValidationGates:
    def test_malformed_image_digest_is_422_structured_error(self, client, db):
        res = client.post(JOBS_URL, json=job_payload("bad-digest", image_digest="latest"))

        assert res.status_code == 422
        body = res.json()
        assert body["error_code"] == "VALIDATION_FAILED"
        assert "spec.image_digest" in body["message"]
        assert body["explanation"]["citations"] == ["self:JOBSPEC-VALIDATION-v1"]
        assert count_jobs(db) == 0

    def test_two_gpu_on_24gb_is_422_two_gpu_requires_48gb(self, client, db):
        res = client.post(JOBS_URL, json=job_payload("two-gpu", gpu_slots_requested=2, required_vram_gb=24))

        assert res.status_code == 422
        assert res.json()["error_code"] == "TWO_GPU_REQUIRES_48GB"
        assert count_jobs(db) == 0

    def test_duration_over_max_night_span_is_422(self, client, db):
        res = client.post(JOBS_URL, json=job_payload("too-long", estimated_duration_s=139_501))

        assert res.status_code == 422
        assert res.json()["error_code"] == "MAX_NIGHT_SPAN_EXCEEDED"
        assert count_jobs(db) == 0

    def test_missing_spec_is_422_not_a_stack_trace(self, client):
        res = client.post(JOBS_URL, json={"idempotency_key": "k", "actor_id": "a"})

        assert res.status_code == 422
        assert res.json()["error_code"] == "VALIDATION_FAILED"

    def test_queue_cap_is_429_and_retryable(self, client, submission_service, fake_clock, db):
        from src.ports.dto import JobSubmissionRequestDTO

        for i in range(500):
            submission_service.submit_job(
                JobSubmissionRequestDTO.model_validate(job_payload(f"fill-{i}")), at=fake_clock.now()
            )

        res = client.post(JOBS_URL, json=job_payload("one-too-many"))

        assert res.status_code == 429
        assert res.json()["error_code"] == "QUEUE_CAP_EXCEEDED"
        assert res.json()["retryable"] is True
        assert count_jobs(db) == 500
