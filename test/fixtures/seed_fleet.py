"""
Mandatory Test Fixture: seed_fleet
Provides the Plan-2 fleet profile: 31 x (1 x 24 GB) + 1 x (2 x 48 GB) = 33 slots, all HEALTHY.
"""

from typing import Dict, List, Any


def get_plan2_seed_fleet() -> Dict[str, Any]:
    """Returns the canonical fleet profile for Module 9."""
    nodes: List[Dict[str, Any]] = []
    slots: List[Dict[str, Any]] = []

    # 31 Workstations (ws-gpu-01 through ws-gpu-31)
    for i in range(1, 32):
        node_id = f"ws-gpu-{i:02d}"
        nodes.append({
            "node_id": node_id,
            "vram_class_gb": 24,
            "total_slots": 1,
            "status": "HEALTHY"
        })
        slots.append({
            "slot_id": f"slot-ws-{i:02d}-0",
            "node_id": node_id,
            "slot_index": 0,
            "allocated_job_id": None
        })

    # 1 Dual-GPU Server (server-gpu-01)
    server_node_id = "server-gpu-01"
    nodes.append({
        "node_id": server_node_id,
        "vram_class_gb": 48,
        "total_slots": 2,
        "status": "HEALTHY"
    })
    slots.append({
        "slot_id": "slot-srv-01-0",
        "node_id": server_node_id,
        "slot_index": 0,
        "allocated_job_id": None
    })
    slots.append({
        "slot_id": "slot-srv-01-1",
        "node_id": server_node_id,
        "slot_index": 1,
        "allocated_job_id": None
    })

    return {
        "total_nodes": 32,
        "total_slots": 33,
        "nodes": nodes,
        "slots": slots
    }
