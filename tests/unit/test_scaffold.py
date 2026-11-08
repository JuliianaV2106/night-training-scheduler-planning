"""
Scaffold foundation: migrations, fleet fixtures, health probe, configuration and domain purity (INV-07).
"""

import ast
from pathlib import Path

import pytest

from src.config import Settings

DOMAIN_DIR = Path(__file__).resolve().parents[2] / "src" / "domain"
FORBIDDEN_IN_DOMAIN = {
    "fastapi", "starlette", "sqlite3", "sqlalchemy", "pydantic", "requests", "httpx", "time", "random",
}


def test_migration_seeds_the_fleet_exactly_as_the_json_fixture(db, seed_fleet):
    nodes = db.execute("SELECT node_id, vram_class_gb, total_slots, status FROM nodes ORDER BY node_id").fetchall()
    slots = db.execute("SELECT slot_id, node_id FROM gpu_slots ORDER BY slot_id").fetchall()

    expected_nodes = sorted(
        (n["node_id"], n["vram_class_gb"], n["total_slots"], n["status"]) for n in seed_fleet["nodes"]
    )
    assert nodes == expected_nodes
    assert len(nodes) == 32 and len(slots) == 33
    assert sorted(slots) == sorted((s["slot_id"], s["node_id"]) for s in seed_fleet["slots"])


def test_health_probe_reports_simulated_instant(client):
    res = client.get("/api/v1/health")

    assert res.status_code == 200
    assert res.json() == {"status": "HEALTHY", "sim_instant": "2026-10-18T14:30:00-05:00", "pacer_rate": 1}


def test_app_refuses_to_start_with_a_broken_fleet_seed(db, fake_clock):
    from src.main import create_app

    db.execute("DELETE FROM gpu_slots WHERE node_id = 'ws-gpu-31'")
    db.execute("DELETE FROM nodes WHERE node_id = 'ws-gpu-31'")

    with pytest.raises(RuntimeError, match="Fleet seed mismatch"):
        create_app(db, fake_clock)


def test_settings_reject_naive_sim_instant(monkeypatch):
    monkeypatch.setenv("SIM_START_INSTANT", "2026-10-18T14:30:00")

    with pytest.raises(ValueError, match="-05:00"):
        Settings.from_env()


def test_domain_layer_imports_no_framework_io_or_clock():
    violations = []
    for path in DOMAIN_DIR.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            violations += [f"{path.name}: {n}" for n in names if n.split(".")[0] in FORBIDDEN_IN_DOMAIN]
            if isinstance(node, ast.Attribute) and node.attr in {"now", "utcnow", "today"}:
                violations.append(f"{path.name}: reads the host clock via .{node.attr}()")

    assert violations == []
