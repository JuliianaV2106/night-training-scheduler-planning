"""
Driving Adapter: Interactive Scheduler Kanban Status Board (`api/routes/board.py`).
Serves `/admin/scheduler-board` and `/board` (Story 9.6 & Story 4.1) and JSON state at `/api/v1/board`.
"""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()


@router.get("/presentation", response_class=HTMLResponse)
async def render_presentation_deck():
    deck_path = Path(__file__).resolve().parents[2] / "presentation" / "index.html"
    return HTMLResponse(content=deck_path.read_text(encoding="utf-8"))


@router.get("/api/v1/board")
async def get_board_json(request: Request):
    sim_service = request.app.state.simulation_service
    return JSONResponse(status_code=200, content=sim_service.get_board_snapshot())


@router.get("/admin/scheduler-board", response_class=HTMLResponse)
@router.get("/board", response_class=HTMLResponse)
async def render_scheduler_board(request: Request):
    sim_service = request.app.state.simulation_service
    repo = request.app.state.repo

    # If the database has zero jobs on initial visit, auto-seed the 5 default queued jobs at 14:00 for Story 9.6
    if len(repo.list_jobs()) == 0:
        clock = request.app.state.clock
        clock.set_time("2026-10-18T14:00:00-05:00")
        with repo.atomic_transaction() as cur:
            for i in range(1, 6):
                job_id = f"JOB-KANBAN-{i:02d}"
                cur.execute(
                    """
                    INSERT OR IGNORE INTO jobs (
                        job_id, state, actor_id, idempotency_key, payload_digest,
                        gpu_slots_requested, required_vram_gb, checkpoint_interval_minutes,
                        estimated_duration_s, image_digest, model_id, model_version,
                        storage_request_bytes, submitted_at, effective_priority, granted_priority
                    ) VALUES (
                        ?, 'QUEUED_PENDING_WINDOW', 'student-kavita', ?, ?,
                        1, 24, 15, ?, ?, ?, '1.0', 1024, '2026-10-18T14:00:00-05:00', ?, 'THESIS'
                    )
                    """,
                    (
                        job_id,
                        f"idemp-kanban-{i:02d}",
                        f"{i:064d}",
                        14400 if i <= 3 else 43200,
                        "sha256:" + f"{i:064x}",
                        f"llama-3-8b-ft-{i:02d}",
                        150 - i,
                    ),
                )

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Module 9 — Night Training Scheduler Status Board</title>
  <style>
    :root {
      --bg: #0f172a;
      --panel: #1e293b;
      --card: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --green: #22c55e;
      --amber: #f59e0b;
      --purple: #a855f7;
    }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 24px;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--panel);
      padding: 16px 24px;
      border-radius: 12px;
      margin-bottom: 24px;
      border: 1px solid #475569;
    }
    .clock-box {
      font-size: 1.75rem;
      font-weight: 700;
      color: var(--accent);
      font-variant-numeric: tabular-nums;
    }
    .controls {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    button {
      background: #0284c7;
      color: white;
      border: none;
      padding: 10px 16px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }
    button:hover { background: #0369a1; }
    button.speed-btn { background: #475569; }
    button.speed-btn.active { background: var(--purple); }
    .kanban-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-bottom: 28px;
    }
    .kanban-column {
      background: var(--panel);
      border-radius: 12px;
      padding: 16px;
      min-height: 260px;
      border: 1px solid #475569;
    }
    .kanban-column h2 {
      margin-top: 0;
      font-size: 1.1rem;
      border-bottom: 1px solid #475569;
      padding-bottom: 10px;
      display: flex;
      justify-content: space-between;
    }
    .job-card {
      background: var(--card);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
      border-left: 4px solid var(--accent);
    }
    .job-card[data-status="Running"] { border-left-color: var(--green); }
    .job-card[data-status="Completed"], .job-card[data-status="Evicted"] { border-left-color: var(--amber); }
    .fleet-section {
      background: var(--panel);
      border-radius: 12px;
      padding: 16px;
      border: 1px solid #475569;
    }
    .fleet-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 10px;
    }
    .node-card {
      background: var(--card);
      padding: 10px;
      border-radius: 8px;
      font-size: 0.85rem;
    }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
      background: #0f172a;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1 style="margin: 0; font-size: 1.35rem;">Night Training Scheduler — Kanban Status Board</h1>
      <small style="color: var(--muted);">SIMULATION MODE (31x24GB Workstations + 1x2x48GB Server)</small>
    </div>
    <div class="clock-box" data-testid="cluster-clock" id="cluster-clock">14:00</div>
    <div class="controls">
      <label for="time-scrubber" style="font-size: 0.85rem;">Time Scrubber:</label>
      <input type="range" id="time-scrubber" data-testid="time-scrubber" min="0" max="24" value="14" />
      <button type="button" class="speed-btn active" data-testid="speed-1x" onclick="setSpeed(1)">1x</button>
      <button type="button" class="speed-btn" data-testid="speed-10x" onclick="setSpeed(10)">10x</button>
      <button type="button" class="speed-btn" data-testid="speed-60x" onclick="setSpeed(60)">60x</button>
      <button type="button" data-testid="btn-fast-forward-2200" onclick="warpTo('22:00')">Fast-Forward to 22:00</button>
      <button type="button" data-testid="btn-advance-0600" onclick="warpTo('06:00')">Advance to 06:00</button>
    </div>
  </header>

  <section class="kanban-grid">
    <div class="kanban-column" data-testid="column-queued" id="col-queued">
      <h2><span>Queued</span> <span class="badge" data-testid="count-queued" id="count-queued">0</span></h2>
      <div class="card-list" id="list-queued"></div>
    </div>
    <div class="kanban-column" data-testid="column-running" id="col-running">
      <h2><span>Running</span> <span class="badge" data-testid="count-running" id="count-running">0</span></h2>
      <div class="card-list" id="list-running"></div>
    </div>
    <div class="kanban-column" data-testid="column-completed" id="col-completed">
      <h2><span>Completed / Evicted</span> <span class="badge" data-testid="count-completed" id="count-completed">0</span></h2>
      <div class="card-list" id="list-completed"></div>
    </div>
  </section>

  <section class="fleet-section">
    <h2 style="margin-top: 0; font-size: 1.1rem;">32-Node Cluster Fleet Status</h2>
    <div class="fleet-grid" data-testid="fleet-nodes-grid" id="fleet-nodes-grid"></div>
  </section>

  <script>
    function renderBoard(data) {
      document.getElementById('cluster-clock').textContent = data.clock_hhmm;

      const renderCards = (items) => items.map(j => `
        <div class="job-card" data-testid="job-card" data-job-id="${j.job_id}" data-status="${j.display_status}">
          <div><strong>${j.job_id}</strong> <span class="badge">${j.display_status}</span></div>
          <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 4px;">
            Model: ${j.model_id} | Node: ${j.allocated_node_id || 'Pending'}
          </div>
          <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
            Cite: policy:M2/night-window@v1
          </div>
        </div>
      `).join('');

      document.getElementById('list-queued').innerHTML = renderCards(data.columns.queued);
      document.getElementById('list-running').innerHTML = renderCards(data.columns.running);
      document.getElementById('list-completed').innerHTML = renderCards(data.columns.completed_or_evicted);

      document.getElementById('count-queued').textContent = data.columns.queued.length;
      document.getElementById('count-running').textContent = data.columns.running.length;
      document.getElementById('count-completed').textContent = data.columns.completed_or_evicted.length;

      document.getElementById('fleet-nodes-grid').innerHTML = data.nodes.map(n => `
        <div class="node-card" data-testid="node-card" data-node-id="${n.node_id}" data-node-status="${n.status}">
          <div><strong>${n.node_id}</strong> (${n.vram_class_gb}GB)</div>
          <div>Status: <span class="badge" data-testid="node-status-badge">${n.status}</span></div>
        </div>
      `).join('');

      document.querySelectorAll('.speed-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === data.speed_multiplier + 'x');
      });
    }

    async function loadInitial() {
      const res = await fetch('/api/v1/board');
      const data = await res.json();
      renderBoard(data);
    }

    async function warpTo(targetTime) {
      const res = await fetch('/api/v1/simulation/time-warp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_time: targetTime })
      });
      const data = await res.json();
      renderBoard(data);
    }

    async function setSpeed(mult) {
      const res = await fetch('/api/v1/simulation/time-warp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed_multiplier: mult })
      });
      const data = await res.json();
      renderBoard(data);
    }

    loadInitial();
  </script>
</body>
</html>"""
    return HTMLResponse(content=html)
