"""
Story 1.2 — Single-Node Scope Boundary Enforcement (POST /api/v1/jobs, precondition P1).
"""

import pytest

from tests.unit.helpers import ERROR_BODY_KEYS, JOBS_URL, count_jobs, job_payload


def test_single_node_spec_passes_to_queue_evaluation(client, db):
    """Scenario (happy): Given worker_count = 1 and replicas = 1, When submitted, Then it is queued."""
    res = client.post(JOBS_URL, json=job_payload("single-node", worker_count=1, replicas=1))

    assert res.status_code == 201
    assert count_jobs(db) == 1


@pytest.mark.parametrize(
    "override",
    [{"worker_count": 4}, {"replicas": 2}, {"distributed_artifact_present": True}],
    ids=["worker_count=4", "replicas=2", "distributed_artifact"],
)
def test_distributed_spec_is_400_with_zero_mutation(client, db, override):
    """Scenario (failure): Given a distributed spec, When submitted,
    Then 400 OUT_OF_SCOPE_DISTRIBUTED citing self:SCOPE-BOUNDARY-v1 and zero database mutations."""
    res = client.post(JOBS_URL, json=job_payload("dist-key", actor="student-dist", **override))

    assert res.status_code == 400
    body = res.json()
    assert ERROR_BODY_KEYS <= body.keys()
    assert body["error_code"] == "OUT_OF_SCOPE_DISTRIBUTED"
    assert "Module 10" in body["message"]
    assert body["explanation"]["rule_id"] == "self:SCOPE-BOUNDARY-v1"
    assert body["explanation"]["citations"] == ["self:SCOPE-BOUNDARY-v1"]
    assert count_jobs(db) == 0
    assert db.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0] == 0


def test_scope_check_runs_before_idempotency_lookup(client, db):
    """A rejected distributed spec must not consume its idempotency key."""
    client.post(JOBS_URL, json=job_payload("reused-key", worker_count=4))

    res = client.post(JOBS_URL, json=job_payload("reused-key"))

    assert res.status_code == 201
    assert count_jobs(db) == 1


@pytest.mark.parametrize("override", [{"worker_count": 0}, {"replicas": 0}], ids=["worker_count=0", "replicas=0"])
def test_count_below_one_is_422_validation_not_out_of_scope(client, db, override):
    """Impl-1 inspection finding F-2: the catalog triggers OUT_OF_SCOPE_DISTRIBUTED on `> 1`.
    Zero workers is not a distributed job, so it must be a 422 range violation, not a 400 routed to Module 10."""
    res = client.post(JOBS_URL, json=job_payload("zero-key", **override))

    assert res.status_code == 422
    body = res.json()
    assert body["error_code"] == "VALIDATION_FAILED"
    assert "Module 10" not in body["message"]
    assert count_jobs(db) == 0
