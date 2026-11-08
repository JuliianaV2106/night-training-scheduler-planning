"""
Story 1.3 — Night Window Activation at 22:00:00 & Deterministic Allocation Fold
(POST /api/v1/window/activate).
"""

import json

from tests.unit.helpers import ACTIVATE_URL, JOBS_URL, WINDOW_OPEN, job_payload


def queue_jobs(client, fake_clock, n: int, **spec) -> list[str]:
    ids = []
    for i in range(n):
        fake_clock.advance(60)
        ids.append(client.post(JOBS_URL, json=job_payload(f"key-{len(spec)}-{i}", **spec)).json()["job_id"])
    return ids


def activate(client, instant: str = WINDOW_OPEN):
    return client.post(ACTIVATE_URL, json={"sim_instant": instant})


class TestHappyPath:
    """Scenario: Given 22:00:00-05:00 with 5 queued jobs and a healthy fleet,
    When activateWindow runs, Then jobs are placed in Admission Order, become RUNNING,
    and one transaction commits all placements."""

    def test_places_all_queued_jobs_and_marks_them_running(self, client, db, fake_clock):
        job_ids = queue_jobs(client, fake_clock, 5)

        res = activate(client)

        assert res.status_code == 200
        body = res.json()
        assert body["activation_id"] == "ACT-20261018"
        assert (body["total_evaluated"], body["admitted_count"], body["deferred_count"]) == (5, 5, 0)
        assert [p["job_id"] for p in body["placements"]] == job_ids
        assert all(p["transition"] == "T-3" for p in body["placements"])
        states = db.execute("SELECT DISTINCT state FROM jobs").fetchall()
        assert states == [("RUNNING",)]
        held = db.execute("SELECT COUNT(*) FROM gpu_slots WHERE allocated_job_id IS NOT NULL").fetchone()[0]
        assert held == 5

    def test_node_choice_follows_ad4_total_order(self, client, db, fake_clock):
        """Gherkin (epics.md Story 1.3, amended in Impl-1): 5 queued 1-GPU jobs land on
        server-gpu-01, ws-gpu-01..04. AD-4: lowest allocations_held, then node_id ascending;
        'server-gpu-01' < 'ws-gpu-01', and the server then holds one allocation so later jobs move on."""
        job_ids = queue_jobs(client, fake_clock, 5)

        nodes = [p["node_id"] for p in activate(client).json()["placements"]]

        assert nodes == ["server-gpu-01", "ws-gpu-01", "ws-gpu-02", "ws-gpu-03", "ws-gpu-04"]
        won_on = [
            json.loads(db.execute(
                "SELECT inputs FROM decision_records WHERE job_id = ? AND transition = 'T-3'", (j,)
            ).fetchone()[0])["won_on"]
            for j in job_ids
        ]
        # Each winner ties its runner-up on allocations_held (0), so node_id is the deciding key.
        assert won_on == ["node_id_asc"] * 5

    def test_admission_order_prefers_higher_priority_then_older_submission(self, client, db, fake_clock):
        first, second, third = queue_jobs(client, fake_clock, 3)
        db.execute("UPDATE jobs SET effective_priority = 150 WHERE job_id = ?", (third,))
        db.commit()

        placements = activate(client).json()["placements"]

        assert [p["job_id"] for p in placements] == [third, first, second]

    def test_each_placement_writes_a_cited_decision_record(self, client, db, fake_clock):
        (job_id,) = queue_jobs(client, fake_clock, 1)

        decision_id = activate(client).json()["placements"][0]["decision_id"]

        row = db.execute(
            "SELECT job_id, decision, transition, citations, inputs FROM decision_records WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()
        assert row[:3] == (job_id, "ADMIT", "T-3")
        assert json.loads(row[3]) == ["policy:M2/night-window@v1", "self:ADMISSION-RANKING-v1"]
        assert json.loads(row[4])["rank"] == 1


class TestCapacityAndInvariants:
    def test_overflow_beyond_33_slots_is_deferred_capacity_exhausted(self, client, db, fake_clock):
        queue_jobs(client, fake_clock, 35)

        body = activate(client).json()

        assert (body["admitted_count"], body["deferred_count"]) == (33, 2)
        deferred = db.execute(
            "SELECT transition, inputs FROM decision_records WHERE decision = 'DEFER'"
        ).fetchall()
        assert {t for t, _ in deferred} == {"T-4b"}
        assert {json.loads(i)["reason_code"] for _, i in deferred} == {"CAPACITY_EXHAUSTED"}
        assert db.execute(
            "SELECT COUNT(*) FROM jobs WHERE state = 'QUEUED_PENDING_WINDOW'"
        ).fetchone()[0] == 2

    def test_two_gpu_job_takes_both_server_slots_atomically(self, client, db, fake_clock):
        (big,) = queue_jobs(client, fake_clock, 1, gpu_slots_requested=2, required_vram_gb=48)

        placement = activate(client).json()["placements"][0]

        assert placement["node_id"] == "server-gpu-01"
        assert placement["slot_ids"] == ["slot-srv-01-0", "slot-srv-01-1"]
        rows = db.execute("SELECT allocated_job_id FROM gpu_slots WHERE node_id = 'server-gpu-01'").fetchall()
        assert rows == [(big,), (big,)]

    def test_two_gpu_job_never_holds_one_slot_when_server_is_half_full(self, client, db, fake_clock):
        """INV-03: a 1-GPU job ranked first takes one server slot; the 2-GPU job is deferred, not split."""
        (small,) = queue_jobs(client, fake_clock, 1)
        (big,) = queue_jobs(client, fake_clock, 1, gpu_slots_requested=2, required_vram_gb=48)

        body = activate(client).json()

        assert [p["job_id"] for p in body["placements"]] == [small]
        assert db.execute("SELECT state FROM jobs WHERE job_id = ?", (big,)).fetchone() == ("QUEUED_PENDING_WINDOW",)

    def test_48gb_job_with_server_cordoned_is_deferred_no_eligible_node(self, client, db, fake_clock):
        db.execute("UPDATE nodes SET status = 'CORDONED' WHERE node_id = 'server-gpu-01'")
        db.commit()
        queue_jobs(client, fake_clock, 1, required_vram_gb=48)

        body = activate(client).json()

        assert body["deferred_count"] == 1
        transition = db.execute("SELECT transition FROM decision_records WHERE decision = 'DEFER'").fetchone()
        assert transition == ("T-4a",)

    def test_cordoned_workstation_is_never_selected(self, client, db, fake_clock):
        db.execute("UPDATE nodes SET status = 'CORDONED' WHERE node_id IN ('server-gpu-01', 'ws-gpu-01')")
        db.commit()
        queue_jobs(client, fake_clock, 2)

        nodes = [p["node_id"] for p in activate(client).json()["placements"]]

        assert nodes == ["ws-gpu-02", "ws-gpu-03"]

    def test_repeated_activation_is_idempotent(self, client, db, fake_clock):
        queue_jobs(client, fake_clock, 2)

        first = activate(client).json()
        second = activate(client).json()

        assert first == second
        assert db.execute("SELECT COUNT(*) FROM decision_records WHERE transition = 'T-3'").fetchone()[0] == 2


class TestOutsideWindow:
    """Scenario (failure): Given 14:00:00-05:00, When activateWindow is triggered,
    Then 400 WINDOW_ACTIVATION_OUTSIDE_WINDOW and zero placements occur."""

    def test_daytime_activation_is_400_with_zero_placements(self, client, db, fake_clock):
        queue_jobs(client, fake_clock, 2)

        res = activate(client, "2026-10-18T14:00:00-05:00")

        assert res.status_code == 400
        assert res.json()["error_code"] == "WINDOW_ACTIVATION_OUTSIDE_WINDOW"
        assert db.execute("SELECT COUNT(*) FROM gpu_slots WHERE allocated_job_id IS NOT NULL").fetchone()[0] == 0
        assert db.execute("SELECT DISTINCT state FROM jobs").fetchall() == [("QUEUED_PENDING_WINDOW",)]

    def test_two_second_tolerance_is_accepted_and_three_seconds_rejected(self, client):
        assert activate(client, "2026-10-18T22:00:02-05:00").status_code == 200
        assert activate(client, "2026-10-19T22:00:03-05:00").status_code == 400

    def test_malformed_or_naive_instant_is_400_structured_error(self, client):
        for instant in ("not-a-date", "2026-10-18T22:00:00"):
            res = activate(client, instant)

            assert res.status_code == 400
            assert res.json()["error_code"] == "WINDOW_ACTIVATION_OUTSIDE_WINDOW"
