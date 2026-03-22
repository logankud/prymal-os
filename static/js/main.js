// ── State ────────────────────────────────────────────
let allTasks = [];
let activeDomain = 'all';
let activePage = 'ledger';

// ── Boot ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  loadTasks();

  // Page nav
  document.querySelectorAll('.nav-item[data-page]').forEach(btn => {
    btn.addEventListener('click', () => switchPage(btn.dataset.page));
  });

  // Domain filters
  document.querySelectorAll('.nav-item[data-domain]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-item[data-domain]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeDomain = btn.dataset.domain;
      renderLedger();
    });
  });

  document.getElementById('refresh-btn').addEventListener('click', loadTasks);
  document.getElementById('drawer-close').addEventListener('click', closeDrawer);
  document.getElementById('drawer-overlay').addEventListener('click', closeDrawer);
  document.getElementById('intake-form').addEventListener('submit', submitIntake);
});

// ── Page switching ────────────────────────────────────
function switchPage(page) {
  activePage = page;

  document.querySelectorAll('.nav-item[data-page]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === page);
  });

  document.querySelectorAll('.page').forEach(el => el.classList.remove('active'));
  document.getElementById(`page-${page}`).classList.add('active');

  // Show domain filters + refresh only on ledger
  const domainNav = document.getElementById('domain-nav');
  const ledgerActions = document.getElementById('sidebar-actions-ledger');
  domainNav.style.display = page === 'ledger' ? '' : 'none';
  ledgerActions.style.display = page === 'ledger' ? '' : 'none';
}

// ── Health ────────────────────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    const el = document.getElementById('system-status');
    if (data.status === 'ok') {
      el.classList.add('online');
      el.querySelector('.status-label').textContent = 'online';
    }
  } catch {
    document.querySelector('.status-label').textContent = 'offline';
  }
}

// ── Load tasks ────────────────────────────────────────
async function loadTasks() {
  try {
    const res = await fetch('/tasks');
    allTasks = await res.json();
    allTasks.reverse();
    renderSummary();
    renderLedger();
  } catch {
    document.getElementById('ledger').innerHTML =
      '<div class="ledger-loading">Failed to load tasks.</div>';
  }
}

// ── Summary badges ────────────────────────────────────
function renderSummary() {
  const counts = { completed: 0, running: 0, queued: 0, created: 0, failed: 0 };
  allTasks.forEach(t => { if (counts[t.status] !== undefined) counts[t.status]++; });

  const badges = [
    { label: 'Total',     count: allTasks.length, always: true },
    { label: 'Completed', count: counts.completed },
    { label: 'Queued',    count: counts.queued + counts.created },
    { label: 'Failed',    count: counts.failed },
  ];

  document.getElementById('summary-badges').innerHTML = badges
    .filter(b => b.always || b.count > 0)
    .map(b => `<div class="summary-badge"><span class="count">${b.count}</span>${b.label}</div>`)
    .join('');
}

// ── Ledger ────────────────────────────────────────────
function renderLedger() {
  const tasks = activeDomain === 'all'
    ? allTasks
    : allTasks.filter(t => t.domain === activeDomain);

  if (tasks.length === 0) {
    document.getElementById('ledger').innerHTML =
      '<div class="ledger-empty">No tasks in this domain yet.</div>';
    return;
  }

  document.getElementById('ledger').innerHTML = tasks.map(task => `
    <div class="ledger-row" data-id="${task.task_id}">
      <div class="row-main">
        <div class="row-headline">
          <span class="row-action">${task.action}</span>
          <span class="row-subject">${task.subject}</span>
        </div>
        <div class="row-outcome">${task.outcome}</div>
        <div class="row-meta">
          <span class="domain-tag domain-${task.domain}">${task.domain}</span>
          ${task.owner_worker ? `<span class="worker-tag">${task.owner_worker}</span>` : ''}
          ${task.artifacts?.length ? `<span class="artifact-dot">● ${task.artifacts.length} artifact${task.artifacts.length > 1 ? 's' : ''}</span>` : ''}
          ${task.created_by ? `<span class="worker-tag">by ${task.created_by}</span>` : ''}
        </div>
      </div>
      <div class="row-right">
        <span class="status-badge status-${task.status}">${task.status}</span>
      </div>
    </div>
  `).join('');

  document.querySelectorAll('.ledger-row').forEach(row => {
    row.addEventListener('click', () => {
      const task = allTasks.find(t => t.task_id === row.dataset.id);
      if (task) openDrawer(task);
    });
  });
}

// ── Intake form ───────────────────────────────────────
async function submitIntake(e) {
  e.preventDefault();

  const btn = document.getElementById('submit-btn');
  btn.disabled = true;
  btn.textContent = 'Submitting...';

  const expectedOutputsRaw = document.getElementById('f-expected-outputs').value;
  const expectedOutputs = expectedOutputsRaw
    ? expectedOutputsRaw.split(',').map(s => s.trim()).filter(Boolean)
    : [];

  const payload = {
    action:           document.getElementById('f-action').value.trim(),
    subject:          document.getElementById('f-subject').value.trim(),
    outcome:          document.getElementById('f-outcome').value.trim(),
    domain:           document.getElementById('f-domain').value,
    created_by:       document.getElementById('f-created-by').value.trim() || 'intake',
    expected_outputs: expectedOutputs,
  };

  const resultEl = document.getElementById('intake-result');

  try {
    const res = await fetch('/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(JSON.stringify(err.detail || err));
    }

    const task = await res.json();

    resultEl.className = 'intake-result success';
    resultEl.style.display = '';
    resultEl.innerHTML = `
      <div class="intake-result-header">✓ Task created</div>
      <div class="intake-result-body">
        <div class="intake-result-row"><span class="intake-result-key">Task ID</span><span class="intake-result-val" style="font-size:0.75rem;color:var(--text-muted)">${task.task_id}</span></div>
        <div class="intake-result-row"><span class="intake-result-key">Action</span><span class="intake-result-val">${task.action}</span></div>
        <div class="intake-result-row"><span class="intake-result-key">Subject</span><span class="intake-result-val">${task.subject}</span></div>
        <div class="intake-result-row"><span class="intake-result-key">Domain</span><span class="intake-result-val"><span class="domain-tag domain-${task.domain}">${task.domain}</span></span></div>
        <div class="intake-result-row"><span class="intake-result-key">Status</span><span class="intake-result-val"><span class="status-badge status-${task.status}">${task.status}</span></span></div>
      </div>
      <div class="intake-result-actions">
        <button class="result-btn" id="view-task-btn">View in Ledger →</button>
        <button class="result-btn" id="new-task-btn">Submit another</button>
      </div>
    `;

    document.getElementById('view-task-btn').addEventListener('click', () => {
      loadTasks().then(() => {
        switchPage('ledger');
        const task_data = allTasks.find(t => t.task_id === task.task_id);
        if (task_data) openDrawer(task_data);
      });
    });

    document.getElementById('new-task-btn').addEventListener('click', () => {
      document.getElementById('intake-form').reset();
      resultEl.style.display = 'none';
    });

    document.getElementById('intake-form').reset();
    await loadTasks();

  } catch (err) {
    resultEl.className = 'intake-result error';
    resultEl.style.display = '';
    resultEl.innerHTML = `
      <div class="intake-result-header">✕ Submission failed</div>
      <div class="intake-result-body">
        <div style="font-size:0.83rem;color:var(--text)">${err.message}</div>
      </div>
    `;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Submit Task →';
  }
}

// ── Drawer ────────────────────────────────────────────
const PIPELINE_STAGES = ['created', 'queued', 'running', 'completed'];

function stageIndex(status) {
  const s = status.toLowerCase();
  if (s === 'failed' || s === 'blocked') return PIPELINE_STAGES.indexOf('running');
  return PIPELINE_STAGES.indexOf(s);
}

function openDrawer(task) {
  document.getElementById('drawer-action').textContent = task.action;
  document.getElementById('drawer-subject').textContent = task.subject;

  const currentIdx = stageIndex(task.status);
  const isFailed = task.status === 'failed' || task.status === 'blocked';

  document.getElementById('pipeline').innerHTML = PIPELINE_STAGES.map((stage, i) => {
    let dotClass = '', labelClass = '';
    if (i < currentIdx) { dotClass = 'active'; labelClass = 'active'; }
    else if (i === currentIdx) {
      dotClass = isFailed ? '' : (task.status === 'completed' ? 'active' : 'current');
      labelClass = dotClass;
    }
    const arrow = i < PIPELINE_STAGES.length - 1 ? `<span class="pipeline-arrow">›</span>` : '';
    return `
      <div class="pipeline-step">
        <div class="pipeline-node">
          <div class="pipeline-dot ${dotClass}"></div>
          <span class="pipeline-label ${labelClass}">${stage}</span>
        </div>
        ${arrow}
      </div>`;
  }).join('');

  document.getElementById('detail-objective').innerHTML = `
    <div class="detail-row"><span class="detail-key">Action</span><span class="detail-val">${task.action}</span></div>
    <div class="detail-row"><span class="detail-key">Subject</span><span class="detail-val">${task.subject}</span></div>
    <div class="detail-row"><span class="detail-key">Outcome</span><span class="detail-val">${task.outcome}</span></div>
    ${task.dependency_str ? `<div class="detail-row"><span class="detail-key">Dependencies</span><span class="detail-val">${task.dependency_str}</span></div>` : ''}
  `;

  const artifactsList = document.getElementById('artifacts-list');
  if (task.artifacts?.length) {
    artifactsList.innerHTML = task.artifacts.map(a => `<div class="artifact-item">${a}</div>`).join('');
  } else {
    artifactsList.innerHTML = '<div class="artifact-empty">No artifacts yet.</div>';
  }

  const expectedSection = document.getElementById('expected-section');
  if (task.expected_outputs?.length) {
    expectedSection.style.display = '';
    document.getElementById('expected-outputs').innerHTML =
      task.expected_outputs.map(o => `<span class="tag">${o}</span>`).join('');
  } else {
    expectedSection.style.display = 'none';
  }

  document.getElementById('detail-meta').innerHTML = `
    <div class="detail-row"><span class="detail-key">Task ID</span><span class="detail-val" style="font-size:0.75rem;color:var(--text-muted)">${task.task_id}</span></div>
    <div class="detail-row"><span class="detail-key">Domain</span><span class="detail-val"><span class="domain-tag domain-${task.domain}">${task.domain}</span></span></div>
    <div class="detail-row"><span class="detail-key">Status</span><span class="detail-val"><span class="status-badge status-${task.status}">${task.status}</span></span></div>
    <div class="detail-row"><span class="detail-key">Worker</span><span class="detail-val">${task.owner_worker || '—'}</span></div>
    <div class="detail-row"><span class="detail-key">Created by</span><span class="detail-val">${task.created_by || '—'}</span></div>
    ${task.expected_token_count ? `<div class="detail-row"><span class="detail-key">Token budget</span><span class="detail-val">${task.expected_token_count.toLocaleString()}</span></div>` : ''}
  `;

  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawer-overlay').classList.add('open');
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawer-overlay').classList.remove('open');
}
