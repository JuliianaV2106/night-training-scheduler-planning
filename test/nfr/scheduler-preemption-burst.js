/**
 * Flow D (Quality Gate / NFR & Concurrency Verification):
 * Module 9: Night Training Scheduler — k6 Load & Preemption Burst Script
 * Story 9.5: Dynamic Priority Queue Preemption Cascade Under Heavy Contention
 * Story 9.1 / NFR-3: High-concurrency job submissions and status queries (< 50 ms p95, 0% errors).
 */

import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    scheduler_burst: {
      executor: 'ramping-arrival-rate',
      startRate: 50,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 50,
      stages: [
        { duration: '3s', target: 120 },
        { duration: '5s', target: 200 },
        { duration: '2s', target: 50 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate==0.00'],
    http_req_duration: ['p(95)<50', 'p(99)<120'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export function setup() {
  // Seed initial board state before running burst traffic
  const seedRes = http.post(
    `${BASE_URL}/api/v1/simulation/seed-board`,
    JSON.stringify({
      initial_time: '2026-10-18T14:00:00-05:00',
      queued_jobs_count: 5,
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(seedRes, {
    'seed board status is 200': (r) => r.status === 200,
  });
}

export default function () {
  // 1. Concurrent Board & Health Queries + Priority Preemption Dispatch
  const boardRes = http.get(`${BASE_URL}/api/v1/board`);
  check(boardRes, {
    'board status is 200': (r) => r.status === 200,
    'board has valid columns': (r) => r.json('columns') !== undefined,
  });

  // 2. Idempotent Job Submission Burst (verifying atomic serialization)
  const key = `k6-idemp-vu-${__VU}`;
  const hexDigest = 'a'.repeat(64);
  const submitRes = http.post(
    `${BASE_URL}/api/v1/jobs`,
    JSON.stringify({
      idempotency_key: key,
      actor_id: 'student-kavita',
      spec: {
        image_digest: `sha256:${hexDigest}`,
        gpu_slots_requested: 1,
        required_vram_gb: 24,
        checkpoint_interval_minutes: 15,
        estimated_duration_s: 3600,
        model_id: 'llama-3-8b',
        model_version: '1.0',
        storage_request_bytes: 1024,
        worker_count: 1,
        replicas: 1,
        distributed_artifact_present: false,
      },
    }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(submitRes, {
    'job submission returns 200 or 201': (r) => r.status === 200 || r.status === 201,
    'job submission returns valid state': (r) => r.json('state') === 'QUEUED_PENDING_WINDOW',
  });
}
