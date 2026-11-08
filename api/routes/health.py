"""
Driving Adapter: HTTP Probe (`api/routes/health.py`).
Performs zero scheduling mutations (AD-1, NFR-16).
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def get_health(request: Request):
    clock = request.app.state.clock
    repo = request.app.state.repo
    return {
        "status": "OK",
        "module": "Module 9 — Night Training Scheduler",
        "sim_instant": clock.now_iso(),
        "speed_multiplier": clock.speed_multiplier,
        "active_jobs": repo.count_active_jobs(),
    }
