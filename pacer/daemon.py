"""Driving Adapter: Simulation Engine Pacer Loop (`pacer/daemon.py`)."""

from adapters.db.sqlite_repository import SQLiteRepositoryAdapter
from adapters.sim.simulated_clock import SimulatedClockAdapter
from ports import load_inbound_port_module

EvictionService = load_inbound_port_module("eviction").EvictionService
SimulationControlService = load_inbound_port_module("simulation_control").SimulationControlService
WindowActivationService = load_inbound_port_module("window_activation").WindowActivationService


class NightSchedulerDaemon:
    """Discrete-event simulation pacer coordinating 22:00 activation and 05:45/06:00 eviction."""

    def __init__(self, repo: SQLiteRepositoryAdapter, clock: SimulatedClockAdapter):
        self._repo = repo
        self._clock = clock
        self._window_svc = WindowActivationService(repo=repo, raise_on_error=True)
        self._evict_svc = EvictionService(repo=repo, raise_on_error=True)
        self._sim_svc = SimulationControlService(
            repo=repo,
            clock=clock,
            window_service=self._window_svc,
            eviction_service=self._evict_svc,
        )

    @property
    def simulation_service(self):
        return self._sim_svc
