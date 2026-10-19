"""
Module 9: Night Training Scheduler — Data Transfer Objects (DTOs)
Strict, primitive-typed models for driving adapters, inbound ports, and responses.
Zero framework (FastAPI/SQLAlchemy) objects permitted in these signatures.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator
import re


# =============================================================================
# Diagnostic & Common DTOs
# =============================================================================

class ExplanationDTO(BaseModel):
    """Encapsulates explainable decision audit citations and inputs."""
    rule_id: str = Field(..., description="Machine-readable rule identifier (e.g. self:JOBSPEC-VALIDATION-v1)")
    summary: str = Field(..., description="Concise human-readable rationale")
    observed_values: Dict[str, Any] = Field(default_factory=dict, description="Observed parameter values")
    thresholds: Dict[str, Any] = Field(default_factory=dict, description="Applicable constraint thresholds")
    citations: List[str] = Field(..., min_length=1, description="Non-empty list of cited authority URNs")


class ErrorBodyDTO(BaseModel):
    """Standardized error response body across all API endpoints."""
    error_code: str = Field(..., description="Canonical error code from Typed Error Catalog")
    message: str = Field(..., description="Formatted diagnostic explanation")
    http_status: int = Field(..., description="HTTP status code")
    retryable: bool = Field(..., description="Whether client may safely retry request")
    occurred_at: str = Field(..., description="ISO-8601 timestamp with America/Bogota -05:00 offset")
    explanation: Optional[ExplanationDTO] = Field(None, description="Optional explainability payload")


# =============================================================================
# Operation 1: submitJob DTOs
# =============================================================================

class JobSpecDTO(BaseModel):
    """Job specification submitted by client."""
    image_digest: str = Field(..., description="Container image pinned by sha256 digest")
    gpu_slots_requested: int = Field(..., ge=1, le=2, description="Number of GPU slots requested (1 or 2)")
    required_vram_gb: int = Field(..., description="VRAM class required (24 or 48 GB)")
    checkpoint_interval_minutes: int = Field(..., ge=1, le=30, description="Checkpoint cadence in minutes")
    estimated_duration_s: int = Field(..., ge=60, le=139500, description="Duration in seconds (max 38.75h)")
    model_id: str = Field(..., min_length=1, description="Model identifier in Module 5 catalog")
    model_version: str = Field(..., min_length=1, description="Model version string")
    storage_request_bytes: int = Field(..., gt=0, description="Estimated checkpoint storage needed in bytes")
    worker_count: int = Field(1, description="Single-node worker count (strictly 1)")
    replicas: int = Field(1, description="Replica count (strictly 1)")
    distributed_artifact_present: bool = Field(False, description="Flag for distributed training primitives")

    @field_validator("image_digest")
    @classmethod
    def validate_image_digest(cls, v: str) -> str:
        if not re.match(r"^sha256:[a-f0-9]{64}$", v):
            raise ValueError("image_digest must match format sha256:<64 hex characters>")
        return v

    @field_validator("required_vram_gb")
    @classmethod
    def validate_vram_class(cls, v: int) -> int:
        if v not in (24, 48):
            raise ValueError("required_vram_gb must be either 24 or 48")
        return v


class JobSubmissionRequestDTO(BaseModel):
    """Inbound request payload for submitJob."""
    idempotency_key: str = Field(..., min_length=1, max_length=64, description="Unique client idempotency token")
    actor_id: str = Field(..., min_length=1, description="Authenticated actor identifier (e.g. user-123)")
    spec: JobSpecDTO = Field(..., description="Job execution specification")


class JobSubmissionResponseDTO(BaseModel):
    """Response payload returned upon successful job submission."""
    job_id: str = Field(..., description="Unique job identifier (e.g. JOB-0042)")
    state: Literal["QUEUED_PENDING_WINDOW"] = "QUEUED_PENDING_WINDOW"
    idempotency_key: str = Field(..., description="Echoed client idempotency token")
    payload_digest: str = Field(..., description="SHA-256 digest of submitted specification")
    admitted_at: str = Field(..., description="ISO-8601 timestamp with America/Bogota -05:00 offset")
    queue_position: int = Field(..., ge=1, le=500, description="1-based position in admission queue")
    estimated_first_window: str = Field(..., description="Estimated window date string (YYYY-MM-DD)")


# =============================================================================
# Operation 2: activateWindow DTOs
# =============================================================================

class PlacementDTO(BaseModel):
    """Records the deterministic slot placement of an admitted job."""
    job_id: str = Field(..., description="Assigned job ID")
    node_id: str = Field(..., description="Selected node identifier (e.g. ws-gpu-05 or server-gpu-01)")
    slot_ids: List[str] = Field(..., min_length=1, max_length=2, description="Assigned GPU slot IDs")
    vram_class_gb: int = Field(..., description="VRAM class of placed node")
    transition: Literal["T-3", "T-12"] = Field(..., description="Transition code (T-3 fresh, T-12 resume)")
    decision_id: str = Field(..., description="Associated DecisionRecord ID")


class WindowActivationRequestDTO(BaseModel):
    """Inbound payload to trigger or simulate 22:00:00 window activation."""
    sim_instant: str = Field(..., description="Simulated instant ISO-8601 timestamp (must be 22:00:00)")


class WindowActivationResultDTO(BaseModel):
    """Response payload describing the result of a window activation."""
    activation_id: str = Field(..., description="Unique activation event identifier")
    sim_instant: str = Field(..., description="Exact simulated execution instant")
    total_evaluated: int = Field(..., ge=0, description="Total candidate jobs evaluated")
    admitted_count: int = Field(..., ge=0, description="Number of jobs placed into slots")
    deferred_count: int = Field(..., ge=0, description="Number of jobs deferred due to capacity or eligibility")
    placements: List[PlacementDTO] = Field(default_factory=list, description="List of successful job placements")


# =============================================================================
# Operation 3: evictAtDeadline DTOs (Mandatory Edge Case)
# =============================================================================

class EvictionRequestDTO(BaseModel):
    """Inbound payload to execute dawn eviction or deadline kill."""
    sim_instant: str = Field(..., description="Simulated instant ISO-8601 timestamp (05:45:00 or 05:53:00)")
    job_id: Optional[str] = Field(None, description="Optional target job ID; if omitted, evaluates all running jobs")


class EvictionResultDTO(BaseModel):
    """Result of an eviction execution for a single job."""
    job_id: str = Field(..., description="Target job identifier")
    node_id: str = Field(..., description="Node where job was running")
    checkpoint_id: Optional[str] = Field(None, description="ID of verified checkpoint if written")
    checkpoint_status: Literal["VERIFIED", "FAILED"] = Field(..., description="Outcome of checkpoint protocol")
    slots_released: int = Field(..., ge=1, le=2, description="Number of GPU slots released back to fleet")
    cordon_requested: bool = Field(..., description="Whether a CordonRequest was issued to Module 3")
    final_job_state: Literal["EVICTED_RESUMABLE", "EVICTION_FAILED"] = Field(..., description="State post-eviction")
    decision_id: str = Field(..., description="Associated DecisionRecord ID")
    allocations_held_after: int = Field(..., ge=0, description="Remaining allocations held on this node (must be 0 at 06:00:00)")
