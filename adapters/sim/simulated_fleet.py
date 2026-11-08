"""
Driven Adapter: SimulatedFleetAdapter (32-node, 33-slot hardware fleet fixture per AD-4, NFR-16).
"""

from typing import Dict, List
from domain.entities import GpuSlotEntity, NodeEntity
from test.fixtures.seed_fleet import get_plan2_seed_fleet


class SimulatedFleetAdapter:
    """In-memory 32-node, 33-slot fleet profile adapter."""

    def __init__(self):
        profile = get_plan2_seed_fleet()
        self._nodes: Dict[str, NodeEntity] = {
            n["node_id"]: NodeEntity(
                node_id=n["node_id"],
                vram_class_gb=n["vram_class_gb"],
                total_slots=n["total_slots"],
                status=n["status"],
            )
            for n in profile["nodes"]
        }
        self._slots: List[GpuSlotEntity] = [
            GpuSlotEntity(
                slot_id=s["slot_id"],
                node_id=s["node_id"],
                slot_index=s["slot_index"],
                allocated_job_id=s["allocated_job_id"],
            )
            for s in profile["slots"]
        ]

    def get_nodes(self) -> List[NodeEntity]:
        return list(self._nodes.values())

    def get_slots(self) -> List[GpuSlotEntity]:
        return list(self._slots)
