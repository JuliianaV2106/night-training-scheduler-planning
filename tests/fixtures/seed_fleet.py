"""
Mandatory Test Fixture: seed_fleet
Loads the Plan-2 fleet profile from fleet.json: 31 x (1 x 24 GB) + 1 x (2 x 48 GB) = 33 slots, all HEALTHY.
"""

import json
from pathlib import Path
from typing import Any

FLEET_JSON = Path(__file__).parent / "fleet.json"


def get_plan2_seed_fleet() -> dict[str, Any]:
    """Returns the canonical fleet profile for Module 9."""
    nodes = json.loads(FLEET_JSON.read_text(encoding="utf-8"))["nodes"]
    slots = [
        {"slot_id": slot_id, "node_id": n["node_id"], "slot_index": index, "allocated_job_id": None}
        for n in nodes
        for index, slot_id in enumerate(n["slot_ids"])
    ]
    return {"total_nodes": len(nodes), "total_slots": len(slots), "nodes": nodes, "slots": slots}
