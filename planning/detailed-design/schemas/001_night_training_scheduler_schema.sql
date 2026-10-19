-- ============================================================================
-- Module 9: Night Training Scheduler — SQLite DDL Migration (001)
-- ============================================================================
-- Physical Schema enforcing AD-1 through AD-8 and Plan-2 Data Model
-- Target Engine: SQLite 3.40+ (WAL mode, synchronous=FULL)
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Nodes Table (Fleet Profile: 31 Workstations + 1 Server = 32 Nodes)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    vram_class_gb INTEGER NOT NULL CHECK (vram_class_gb IN (24, 48)),
    total_slots INTEGER NOT NULL CHECK (total_slots IN (1, 2)),
    status TEXT NOT NULL DEFAULT 'HEALTHY' CHECK (status IN ('HEALTHY', 'DRAINING', 'CORDONED', 'RESERVED')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    -- Physical Invariant: Only server-gpu-01 can have 2 slots and 48 GB VRAM
    CONSTRAINT check_node_hardware_profile CHECK (
        (total_slots = 1 AND vram_class_gb = 24 AND node_id LIKE 'ws-gpu-%') OR
        (total_slots = 2 AND vram_class_gb = 48 AND node_id = 'server-gpu-01')
    )
);

-- ----------------------------------------------------------------------------
-- 2. GPU Slots Table (Exactly 33 Physical Allocation Slots)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gpu_slots (
    slot_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    slot_index INTEGER NOT NULL CHECK (slot_index IN (0, 1)),
    allocated_job_id TEXT REFERENCES jobs(job_id) ON DELETE SET NULL,
    held_since TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    UNIQUE (node_id, slot_index)
);

-- ----------------------------------------------------------------------------
-- 3. Jobs Table (Single-Process Core Entity)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    state TEXT NOT NULL CHECK (
        state IN (
            'REJECTED', 
            'QUEUED_PENDING_WINDOW', 
            'RUNNING', 
            'CHECKPOINTING', 
            'EVICTED_RESUMABLE', 
            'COMPLETED', 
            'FAILED', 
            'EVICTION_FAILED', 
            'EXPIRED'
        )
    ),
    state_reason TEXT,
    actor_id TEXT NOT NULL,
    idempotency_key TEXT UNIQUE NOT NULL,
    payload_digest TEXT NOT NULL CHECK (length(payload_digest) = 64),
    worker_count INTEGER NOT NULL DEFAULT 1 CHECK (worker_count = 1),
    replicas INTEGER NOT NULL DEFAULT 1 CHECK (replicas = 1),
    gpu_slots_requested INTEGER NOT NULL CHECK (gpu_slots_requested IN (1, 2)),
    required_vram_gb INTEGER NOT NULL CHECK (required_vram_gb IN (24, 48)),
    checkpoint_interval_minutes INTEGER NOT NULL CHECK (checkpoint_interval_minutes BETWEEN 1 AND 30),
    estimated_duration_s INTEGER NOT NULL CHECK (estimated_duration_s BETWEEN 60 AND 139500),
    image_digest TEXT NOT NULL CHECK (image_digest LIKE 'sha256:%' AND length(image_digest) = 71),
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    storage_request_bytes INTEGER NOT NULL CHECK (storage_request_bytes > 0),
    effective_priority INTEGER NOT NULL DEFAULT 100,
    granted_priority TEXT NOT NULL DEFAULT 'NORMAL' CHECK (granted_priority IN ('NORMAL', 'THESIS', 'URGENT')),
    consecutive_nights_missed INTEGER NOT NULL DEFAULT 0 CHECK (consecutive_nights_missed >= 0),
    admitted_nights INTEGER NOT NULL DEFAULT 0 CHECK (admitted_nights >= 0),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count BETWEEN 0 AND 1),
    preempted_in_window INTEGER NOT NULL DEFAULT 0 CHECK (preempted_in_window IN (0, 1)),
    allocated_node_id TEXT REFERENCES nodes(node_id),
    submitted_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    
    -- Physical Invariant 1 (INV-03 / AD-4): 2-GPU jobs strictly require 48GB hardware
    CONSTRAINT check_two_gpu_requires_48gb CHECK (
        (gpu_slots_requested = 1) OR 
        (gpu_slots_requested = 2 AND required_vram_gb = 48)
    ),
    -- Physical Invariant 2 (AD-1): Max 1 automatic PROCESS_EXIT retry per night
    CONSTRAINT check_retry_count_cap CHECK (retry_count <= 1)
);

-- Partial index for active job queue depth (enforcing < 500 non-terminal jobs fast)
CREATE INDEX IF NOT EXISTS idx_active_jobs_state ON jobs(state) 
WHERE state NOT IN ('COMPLETED', 'FAILED', 'REJECTED', 'EXPIRED');

-- ----------------------------------------------------------------------------
-- 4. Decision Records Table (Append-Only Durable Log per AD-2, AD-3, FR-24)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decision_records (
    decision_id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id),
    node_id TEXT REFERENCES nodes(node_id),
    sim_timestamp TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('ADMIT', 'DEFER', 'PREEMPT', 'EVICT', 'FAIL', 'COMPLETE', 'REJECT')),
    transition TEXT,
    actor_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    citations TEXT NOT NULL, -- JSON array of strings
    inputs TEXT NOT NULL,    -- JSON object of input state
    supersedes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    -- Physical Invariant (AD-3): Mandatory citation requirement (citations array cannot be empty JSON '[]')
    CONSTRAINT check_citations_non_empty CHECK (length(citations) > 2)
);

CREATE INDEX IF NOT EXISTS idx_decisions_job ON decision_records(job_id);
CREATE INDEX IF NOT EXISTS idx_decisions_sim_time ON decision_records(sim_timestamp);

-- ----------------------------------------------------------------------------
-- 5. Checkpoints Table (AD-7 5-Step Protocol Store)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    path TEXT NOT NULL UNIQUE,
    bytes INTEGER NOT NULL CHECK (bytes > 0),
    step INTEGER NOT NULL CHECK (step >= 0),
    digest TEXT NOT NULL CHECK (length(digest) = 64), -- SHA-256 hex
    sim_timestamp TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('WRITING', 'VERIFIED', 'QUARANTINED', 'DELETED')),
    written_by TEXT NOT NULL CHECK (written_by IN ('periodic', 'ramp', 'preemption')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_job_state ON checkpoints(job_id, state);

-- ----------------------------------------------------------------------------
-- 6. Cordon Requests Table (Module 3 Outbox / Node Health Isolation)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cordon_requests (
    cordon_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(node_id),
    cause TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'REQUESTED' CHECK (state IN ('REQUESTED', 'ACKNOWLEDGED', 'REJECTED', 'CLEARED')),
    cleared_by_actor_id TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now'))
);

-- ----------------------------------------------------------------------------
-- 7. Audit Events Table (System Lifecycle Events Log)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    job_id TEXT REFERENCES jobs(job_id),
    node_id TEXT REFERENCES nodes(node_id),
    actor_id TEXT NOT NULL,
    payload TEXT NOT NULL, -- JSON
    occurred_at TEXT NOT NULL, -- ISO-8601 with America/Bogota offset
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_events_occurred_at ON audit_events(occurred_at);

-- ----------------------------------------------------------------------------
-- 8. Seed Data: Fleet Profile (31 Workstations @ 1x24GB, 1 Server @ 2x48GB)
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO nodes (node_id, vram_class_gb, total_slots, status) VALUES
('ws-gpu-01', 24, 1, 'HEALTHY'), ('ws-gpu-02', 24, 1, 'HEALTHY'), ('ws-gpu-03', 24, 1, 'HEALTHY'),
('ws-gpu-04', 24, 1, 'HEALTHY'), ('ws-gpu-05', 24, 1, 'HEALTHY'), ('ws-gpu-06', 24, 1, 'HEALTHY'),
('ws-gpu-07', 24, 1, 'HEALTHY'), ('ws-gpu-08', 24, 1, 'HEALTHY'), ('ws-gpu-09', 24, 1, 'HEALTHY'),
('ws-gpu-10', 24, 1, 'HEALTHY'), ('ws-gpu-11', 24, 1, 'HEALTHY'), ('ws-gpu-12', 24, 1, 'HEALTHY'),
('ws-gpu-13', 24, 1, 'HEALTHY'), ('ws-gpu-14', 24, 1, 'HEALTHY'), ('ws-gpu-15', 24, 1, 'HEALTHY'),
('ws-gpu-16', 24, 1, 'HEALTHY'), ('ws-gpu-17', 24, 1, 'HEALTHY'), ('ws-gpu-18', 24, 1, 'HEALTHY'),
('ws-gpu-19', 24, 1, 'HEALTHY'), ('ws-gpu-20', 24, 1, 'HEALTHY'), ('ws-gpu-21', 24, 1, 'HEALTHY'),
('ws-gpu-22', 24, 1, 'HEALTHY'), ('ws-gpu-23', 24, 1, 'HEALTHY'), ('ws-gpu-24', 24, 1, 'HEALTHY'),
('ws-gpu-25', 24, 1, 'HEALTHY'), ('ws-gpu-26', 24, 1, 'HEALTHY'), ('ws-gpu-27', 24, 1, 'HEALTHY'),
('ws-gpu-28', 24, 1, 'HEALTHY'), ('ws-gpu-29', 24, 1, 'HEALTHY'), ('ws-gpu-30', 24, 1, 'HEALTHY'),
('ws-gpu-31', 24, 1, 'HEALTHY'),
('server-gpu-01', 48, 2, 'HEALTHY');

-- Seed GPU Slots (33 total slots: 31 on workstations, 2 on server-gpu-01)
INSERT OR IGNORE INTO gpu_slots (slot_id, node_id, slot_index) VALUES
('slot-ws-01-0', 'ws-gpu-01', 0), ('slot-ws-02-0', 'ws-gpu-02', 0), ('slot-ws-03-0', 'ws-gpu-03', 0),
('slot-ws-04-0', 'ws-gpu-04', 0), ('slot-ws-05-0', 'ws-gpu-05', 0), ('slot-ws-06-0', 'ws-gpu-06', 0),
('slot-ws-07-0', 'ws-gpu-07', 0), ('slot-ws-08-0', 'ws-gpu-08', 0), ('slot-ws-09-0', 'ws-gpu-09', 0),
('slot-ws-10-0', 'ws-gpu-10', 0), ('slot-ws-11-0', 'ws-gpu-11', 0), ('slot-ws-12-0', 'ws-gpu-12', 0),
('slot-ws-13-0', 'ws-gpu-13', 0), ('slot-ws-14-0', 'ws-gpu-14', 0), ('slot-ws-15-0', 'ws-gpu-15', 0),
('slot-ws-16-0', 'ws-gpu-16', 0), ('slot-ws-17-0', 'ws-gpu-17', 0), ('slot-ws-18-0', 'ws-gpu-18', 0),
('slot-ws-19-0', 'ws-gpu-19', 0), ('slot-ws-20-0', 'ws-gpu-20', 0), ('slot-ws-21-0', 'ws-gpu-21', 0),
('slot-ws-22-0', 'ws-gpu-22', 0), ('slot-ws-23-0', 'ws-gpu-23', 0), ('slot-ws-24-0', 'ws-gpu-24', 0),
('slot-ws-25-0', 'ws-gpu-25', 0), ('slot-ws-26-0', 'ws-gpu-26', 0), ('slot-ws-27-0', 'ws-gpu-27', 0),
('slot-ws-28-0', 'ws-gpu-28', 0), ('slot-ws-29-0', 'ws-gpu-29', 0), ('slot-ws-30-0', 'ws-gpu-30', 0),
('slot-ws-31-0', 'ws-gpu-31', 0),
('slot-srv-01-0', 'server-gpu-01', 0),
('slot-srv-01-1', 'server-gpu-01', 1);

-- ----------------------------------------------------------------------------
-- 9. Trigger for updated_at Auto-Refresh
-- ----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trigger_jobs_updated_at AFTER UPDATE ON jobs
BEGIN
    UPDATE jobs SET updated_at = strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now') WHERE job_id = NEW.job_id;
END;

CREATE TRIGGER IF NOT EXISTS trigger_nodes_updated_at AFTER UPDATE ON nodes
BEGIN
    UPDATE nodes SET updated_at = strftime('%Y-%m-%dT%H:%M:%S-05:00', 'now') WHERE node_id = NEW.node_id;
END;
