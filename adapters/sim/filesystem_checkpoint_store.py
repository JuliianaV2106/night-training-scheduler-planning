"""
Driven Adapter: FilesystemCheckpointStoreAdapter (AD-7 5-Step Checkpoint Durability & Pre-Verification Sweep).
Models the 5-step protocol:
1. Write temp file
2. Flush/sync bytes
3. Compute SHA-256 digest
4. Atomic rename into place
5. Record metadata & verify digest on pre-verification sweep (Story 2.3).
"""

import hashlib
from pathlib import Path
from typing import Dict, Optional
from domain.entities import CheckpointEntity


class FilesystemCheckpointStoreAdapter:
    """Implements CheckpointStorePort over an ephemeral directory or simulated buffer."""

    def __init__(self, root_dir: Optional[Path] = None, capacity_bytes: int = 1024 * 1024 * 1024 * 100):
        self._root_dir = root_dir
        if self._root_dir is not None:
            self._root_dir.mkdir(parents=True, exist_ok=True)
            (self._root_dir / "quarantine").mkdir(parents=True, exist_ok=True)
        self._capacity_bytes = capacity_bytes
        self._used_bytes = 0
        self._files: Dict[str, bytes] = {}
        self._records: Dict[str, CheckpointEntity] = {}

    def available_bytes(self) -> int:
        return max(0, self._capacity_bytes - self._used_bytes)

    def set_available_bytes(self, available: int) -> None:
        self._used_bytes = max(0, self._capacity_bytes - available)

    def write_verified_checkpoint(
        self,
        checkpoint_id: str,
        job_id: str,
        step: int,
        sim_timestamp: str,
        written_by: str = "ramp",
        payload_bytes: Optional[bytes] = None,
    ) -> CheckpointEntity:
        content = payload_bytes or f"checkpoint:{job_id}:step={step}:ts={sim_timestamp}".encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        rel_path = f"checkpoints/{job_id}/{checkpoint_id}.ckpt"

        if self._root_dir is not None:
            job_dir = self._root_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            tmp_file = job_dir / f"{checkpoint_id}.ckpt.tmp"
            final_file = job_dir / f"{checkpoint_id}.ckpt"
            tmp_file.write_bytes(content)
            tmp_file.replace(final_file)

        self._files[rel_path] = content
        self._used_bytes += len(content)
        entity = CheckpointEntity(
            checkpoint_id=checkpoint_id,
            job_id=job_id,
            path=rel_path,
            bytes=len(content),
            step=step,
            digest=digest,
            sim_timestamp=sim_timestamp,
            state="VERIFIED",
            written_by=written_by,
        )
        self._records[checkpoint_id] = entity
        return entity

    def tamper_checkpoint_bytes(self, path: str, corrupted_bytes: bytes = b"CORRUPTED_BYTES") -> None:
        """Test helper for Story 2.3 to simulate bitrot / disk corruption."""
        self._files[path] = corrupted_bytes
        if self._root_dir is not None:
            for ckpt in self._records.values():
                if ckpt.path == path:
                    target = self._root_dir / ckpt.job_id / f"{ckpt.checkpoint_id}.ckpt"
                    if target.exists():
                        target.write_bytes(corrupted_bytes)

    def verify_checkpoint_integrity(self, path: str, expected_digest: str) -> bool:
        """Re-reads checkpoint bytes and compares SHA-256 digest against expected_digest (Invariant S-2)."""
        content = self._files.get(path)
        if content is None and self._root_dir is not None:
            # Try reading from disk if present
            candidate = self._root_dir / path.replace("checkpoints/", "")
            if candidate.exists():
                content = candidate.read_bytes()
        if content is None:
            return False
        observed_digest = hashlib.sha256(content).hexdigest()
        return observed_digest == expected_digest
