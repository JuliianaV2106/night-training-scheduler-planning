"""
Mandatory Test Fixture: sim_telemetry
Scripted GPU, heartbeat, and fault injector for deterministic failure testing.
"""



class SimTelemetry:
    """Scriptable fault generator for testing edge cases and failures."""

    def __init__(self):
        self._failing_nodes: set[str] = set()
        self._checkpoint_write_faults: set[str] = set()
        self._checkpoint_delays_s: dict[str, int] = {}

    def inject_node_fault(self, node_id: str) -> None:
        """Simulates node hardware failure or unreachability."""
        self._failing_nodes.add(node_id)

    def inject_checkpoint_failure(self, job_id: str) -> None:
        """Forces 5-step checkpoint write to fail with I/O error or timeout."""
        self._checkpoint_write_faults.add(job_id)

    def inject_checkpoint_delay(self, job_id: str, delay_s: int) -> None:
        """Injects simulated duration into checkpoint write."""
        self._checkpoint_delays_s[job_id] = delay_s

    def is_node_faulty(self, node_id: str) -> bool:
        return node_id in self._failing_nodes

    def should_checkpoint_fail(self, job_id: str) -> bool:
        return job_id in self._checkpoint_write_faults

    def get_checkpoint_delay(self, job_id: str) -> int:
        return self._checkpoint_delays_s.get(job_id, 0)

    def reset(self) -> None:
        self._failing_nodes.clear()
        self._checkpoint_write_faults.clear()
        self._checkpoint_delays_s.clear()
