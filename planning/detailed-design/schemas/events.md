---
title: "Module 9 — Night Training Scheduler: Event & Telemetry Schemas"
status: final
version: "1.0.0"
created: 2026-10-18
module: "Module 9 — Night Training Scheduler"
---

# Event & Telemetry Payloads Specification

This document defines the formal event schemas emitted and ingested by **Module 9: Night Training Scheduler**. All payloads adhere to the CloudEvents / enterprise telemetry standard, carrying `eventId`, `occurredAt` (UTC ISO-8601 timestamp), and a strict `schemaVersion`.

---

## 1. Common Event Header Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CommonEventHeader",
  "type": "object",
  "required": ["eventId", "eventType", "occurredAt", "schemaVersion", "source", "payload"],
  "properties": {
    "eventId": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this event instance (UUIDv4)"
    },
    "eventType": {
      "type": "string",
      "enum": [
        "JOB_SUBMITTED",
        "WINDOW_ACTIVATED",
        "JOB_STARTED",
        "CHECKPOINT_STARTED",
        "CHECKPOINT_VERIFIED",
        "CHECKPOINT_FAILED",
        "NODE_CORDON_REQUESTED",
        "JOB_EVICTED",
        "JOB_COMPLETED",
        "NIGHT_CLOSED"
      ]
    },
    "occurredAt": {
      "type": "string",
      "format": "date-time",
      "description": "UTC ISO-8601 timestamp at which the event occurred"
    },
    "schemaVersion": {
      "type": "string",
      "const": "1.0.0"
    },
    "source": {
      "type": "string",
      "const": "urn:university-ai-compute:module9:scheduler"
    },
    "payload": {
      "type": "object"
    }
  }
}
```

---

## 2. Emitted Event Payloads

### 2.1 `JOB_SUBMITTED`
Emitted immediately when a job passes all admission preconditions and is persisted in `QUEUED_PENDING_WINDOW`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "JobSubmittedPayload",
  "type": "object",
  "required": ["jobId", "actorId", "idempotencyKey", "payloadDigest", "gpuSlotsRequested", "requiredVramGb", "queuePosition"],
  "properties": {
    "jobId": { "type": "string", "pattern": "^JOB-[0-9]{4}$" },
    "actorId": { "type": "string" },
    "idempotencyKey": { "type": "string" },
    "payloadDigest": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "gpuSlotsRequested": { "type": "integer", "enum": [1, 2] },
    "requiredVramGb": { "type": "integer", "enum": [24, 48] },
    "queuePosition": { "type": "integer", "minimum": 1, "maximum": 500 }
  }
}
```

### 2.2 `WINDOW_ACTIVATED`
Emitted at `22:00:00` upon completion of the deterministic Admission Order fold and slot allocation.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WindowActivatedPayload",
  "type": "object",
  "required": ["activationId", "simInstant", "totalEvaluated", "admittedCount", "deferredCount", "allocatedSlotsCount"],
  "properties": {
    "activationId": { "type": "string" },
    "simInstant": { "type": "string" },
    "totalEvaluated": { "type": "integer", "minimum": 0 },
    "admittedCount": { "type": "integer", "minimum": 0, "maximum": 33 },
    "deferredCount": { "type": "integer", "minimum": 0 },
    "allocatedSlotsCount": { "type": "integer", "minimum": 0, "maximum": 33 }
  }
}
```

### 2.3 `CHECKPOINT_STARTED`
Emitted at `05:45:00` during dawn eviction ramp or at periodic intervals.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CheckpointStartedPayload",
  "type": "object",
  "required": ["checkpointId", "jobId", "nodeId", "step", "triggerType"],
  "properties": {
    "checkpointId": { "type": "string" },
    "jobId": { "type": "string", "pattern": "^JOB-[0-9]{4}$" },
    "nodeId": { "type": "string" },
    "step": { "type": "integer", "minimum": 0 },
    "triggerType": { "type": "string", "enum": ["ramp", "periodic", "preemption"] }
  }
}
```

### 2.4 `CHECKPOINT_VERIFIED`
Emitted when the 5-step durability protocol succeeds and SHA-256 digest is confirmed.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CheckpointVerifiedPayload",
  "type": "object",
  "required": ["checkpointId", "jobId", "nodeId", "step", "bytesWritten", "sha256Digest", "durationMs"],
  "properties": {
    "checkpointId": { "type": "string" },
    "jobId": { "type": "string" },
    "nodeId": { "type": "string" },
    "step": { "type": "integer" },
    "bytesWritten": { "type": "integer", "minimum": 1 },
    "sha256Digest": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
    "durationMs": { "type": "integer", "minimum": 0 }
  }
}
```

### 2.5 `CHECKPOINT_FAILED` (Mandatory Edge Case)
Emitted at `05:53:00` or upon I/O write error during eviction ramp.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CheckpointFailedPayload",
  "type": "object",
  "required": ["jobId", "nodeId", "failureReason", "elapsedSeconds", "slotsToRelease"],
  "properties": {
    "jobId": { "type": "string" },
    "nodeId": { "type": "string" },
    "failureReason": { "type": "string", "enum": ["CHECKPOINT_DEADLINE_MISSED", "CHECKPOINT_IO_ERROR", "CHECKPOINT_CORRUPT"] },
    "elapsedSeconds": { "type": "number" },
    "slotsToRelease": { "type": "integer", "enum": [1, 2] }
  }
}
```

### 2.6 `NODE_CORDON_REQUESTED`
Dispatched to Module 3 (Digital Twin) when a node experiences checkpoint write failure.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "NodeCordonRequestedPayload",
  "type": "object",
  "required": ["cordonId", "nodeId", "cause", "originatingJobId", "cordonState"],
  "properties": {
    "cordonId": { "type": "string" },
    "nodeId": { "type": "string" },
    "cause": { "type": "string", "const": "EVICTION_CHECKPOINT_WRITE_FAILED" },
    "originatingJobId": { "type": "string" },
    "cordonState": { "type": "string", "const": "REQUESTED" }
  }
}
```

### 2.7 `JOB_EVICTED`
Emitted when GPU slots are freed and job moves to `EVICTED_RESUMABLE` or `EVICTION_FAILED`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "JobEvictedPayload",
  "type": "object",
  "required": ["jobId", "nodeId", "finalState", "slotsReleased", "checkpointStatus", "allocationsHeldRemaining"],
  "properties": {
    "jobId": { "type": "string" },
    "nodeId": { "type": "string" },
    "finalState": { "type": "string", "enum": ["EVICTED_RESUMABLE", "EVICTION_FAILED"] },
    "slotsReleased": { "type": "integer", "enum": [1, 2] },
    "checkpointStatus": { "type": "string", "enum": ["VERIFIED", "FAILED"] },
    "allocationsHeldRemaining": { "type": "integer", "minimum": 0 }
  }
}
```

### 2.8 `NIGHT_CLOSED`
Emitted at `06:00:00` asserting Invariant S-1 (`allocationsHeld == 0`) and updating consecutive nights missed counters.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "NightClosedPayload",
  "type": "object",
  "required": ["closedInstant", "activeAllocationsAsserted", "jobsAgedCount"],
  "properties": {
    "closedInstant": { "type": "string" },
    "activeAllocationsAsserted": { "type": "integer", "const": 0 },
    "jobsAgedCount": { "type": "integer", "minimum": 0 }
  }
}
```
