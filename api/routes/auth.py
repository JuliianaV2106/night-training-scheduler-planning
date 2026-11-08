"""
Driving Adapter: HTTP Session & Auth Route (`api/routes/auth.py`).
Implements AD-8 session exchange without leaking bearer tokens.
"""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from domain.entities import DomainError

router = APIRouter()


class SessionLoginRequest(BaseModel):
    actor_id: str
    bearer_token: str = "sim-token-valid"


@router.post("/auth/session")
def create_session(payload: SessionLoginRequest, request: Request, response: Response):
    delegates = request.app.state.delegates
    try:
        ent = delegates.verify_actor_entitlement(payload.actor_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message)

    response.set_cookie(
        key="m9_session_actor",
        value=payload.actor_id,
        httponly=True,
        samesite="strict",
    )
    return {
        "authenticated": True,
        "actor_id": payload.actor_id,
        "role": ent["role"],
        "granted_priority": ent["granted_priority"],
    }
