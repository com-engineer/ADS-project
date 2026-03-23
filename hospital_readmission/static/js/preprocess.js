/* ═══════════════════════════════════════════════════
   preprocess.js  —  step-by-step pipeline UI
═══════════════════════════════════════════════════ */

async function apiPost(url) {
  const r = await fetch(url, { method: 'POST' });
  return r.json();
}

/* ── Refresh the top status bar numbers ── */
async function refreshPipelineStatus() {
  const s = await fetch('/api/preprocess/state').then(r => r.json());
  document.getElementById('pipe-rows').textContent    = s.rows.toLocaleString();
  document.getElementById('pipe-cols').textContent    = s.cols;
  document.getElementById('pipe-missing').textContent = s.missing.toLocaleString();
  document.getElementById('pipe-step').textContent    = s.step + ' / 7';
}

/* ── Reset pipeline back to original data ── */
async function resetPipeline() {
  await apiPost('/api/preprocess/reset');
  for (let i = 1; i <= 7; i++) {
    document.getElementById('result-' + i).innerHTML = '';
    const card = document.getElementById('step-card-' + i);
    card.classList.remove('done');
    const pill = document.getElementById('pill-' + i);
    pill.classList.remove('done');
    card.querySelector('.step-btn').disabled = false;
    card.querySelector('.step-btn').textContent = 'Apply';
  }
  await refreshPipelineStatus();
}

/* ── Apply a step and render before/after ── */
async function applyStep(n) {
  const btn = document.querySelector(`#step-card-${n} .step-btn`);
  btn.textContent = 'Running...';
  btn.disabled = true;

  const data = await apiPost(`/api/preprocess/step/${n}`);

  if (data.error) {
    btn.textContent = 'Error';
    alert(data.error);
    return;
  }

  renderStepResult(n, data);
  markStepDone(n);
  await refreshPipelineStatus();
}

/* ── Mark step pill and card as done ── */
function markStepDone(n) {
  const card = document.getElementById('step-card-' + n);
  card.classList.add('done');
  const pill = document.getElementById('pill-' + n);
  pill.classList.add('done');
  const btn = card.querySelector('.step-btn');
  btn.textContent = 'Done';
  btn.disabled = true;
}

/* ── Render before/after result panel ── */
function renderStepResult(n, data) {
  const el = document.getElementById('result-' + n);
  const b  = data.before;
  const a  = data.after;

  // before/after shape row
  let html = `
    <div class="ba-grid">
      <div class="ba-box before">
        <div class="ba-label">Before</div>
        <div class="ba-stat">${b.rows.toLocaleString()} rows &nbsp;|&nbsp; ${b.cols} cols</div>
        ${b.target ? targetBadges(b.target) : ''}
      </div>
      <div class="ba-arrow">→</div>
      <div class="ba-box after">
        <div class="ba-label">After</div>
        <div class="ba-stat">${a.rows.toLocaleString()} rows &nbsp;|&nbsp; ${a.cols} cols</div>
        ${a.target ? targetBadges(a.target) : ''}
      </div>
    </div>`;

  // step-specific detail panels
  html += buildDetail(n, data.detail);

  el.innerHTML = html;
  el.style.display = 'block';
}

/* ── Small target class badges ── */
function targetBadges(target) {
  return '<div class="ba-target">' +
    Object.entries(target).map(([k, v]) =>
      `<span class="tgt-badge">${k}: ${v.toLocaleString()}</span>`
    ).join('') + '</div>';
}

/* ── Detail panel per step ── */
function buildDetail(n, d) {
  if (!d) return '';
  let html = '<div class="detail-panel">';

  if (n === 1) {
    html += `<div class="detail-title">Dropped columns</div>`;
    html += d.dropped.map(c =>
      `<span class="detail-tag tag-red">${c}</span>`).join('');
    html += `<div class="detail-note">${d.reason}</div>`;
  }

  if (n === 2) {
    html += `<div class="detail-title">Actions taken</div>`;
    Object.entries(d.filled).forEach(([col, info]) => {
      html += `<div class="detail-row">
        <span class="detail-tag tag-blue">${col}</span>
        <span class="detail-val">${info.count.toLocaleString()} nulls → strategy: <strong>${info.strategy}</strong></span>
      </div>`;
    });
  }

  if (n === 3) {
    html += `<div class="detail-title">Target encoding</div>`;
    html += `<div class="ba-grid small">
      <div class="ba-box before">
        <div class="ba-label">Before (3 classes)</div>
        ${Object.entries(d.before_dist).map(([k,v]) =>
          `<div class="ba-row"><span>${k}</span><span>${v.toLocaleString()}</span></div>`).join('')}
      </div>
      <div class="ba-arrow">→</div>
      <div class="ba-box after">
        <div class="ba-label">After (binary)</div>
        ${Object.entries(d.after_dist).map(([k,v]) =>
          `<div class="ba-row"><span>${k === '1' ? '1 (readmitted <30d)' : '0 (other)'}</span><span>${v.toLocaleString()}</span></div>`).join('')}
      </div>
    </div>`;
  }

  if (n === 4) {
    html += `<div class="detail-title">Duplicates removed</div>`;
    html += `<div class="detail-row">
      <span class="detail-tag tag-red">${d.removed.toLocaleString()} rows removed</span>
      <span class="detail-val">${d.remaining.toLocaleString()} rows remaining</span>
    </div>`;
  }

  if (n === 5) {
    html += `<div class="detail-title">Encoded columns</div>`;
    Object.entries(d.encoded_columns).forEach(([col, info]) => {
      html += `<div class="detail-row">
        <span class="detail-tag tag-blue">${col}</span>
        <span class="detail-val">${info}</span>
      </div>`;
    });
  }

  if (n === 6) {
    html += `<div class="detail-title">Scaled columns (mean before → after)</div>`;
    d.scaled_columns.slice(0, 5).forEach(col => {
      const before = d.mean_before[col];
      const after  = d.mean_after[col];
      html += `<div class="detail-row">
        <span class="detail-tag tag-blue">${col}</span>
        <span class="detail-val">${before} → <strong>${after}</strong></span>
      </div>`;
    });
  }

  if (n === 7) {
    html += `<div class="detail-title">Class balance</div>`;
    html += `<div class="ba-grid small">
      <div class="ba-box before">
        <div class="ba-label">Before (imbalanced)</div>
        ${Object.entries(d.before_dist).map(([k,v]) =>
          `<div class="ba-row"><span>Class ${k}</span><span>${v.toLocaleString()}</span></div>`).join('')}
      </div>
      <div class="ba-arrow">→</div>
      <div class="ba-box after">
        <div class="ba-label">After (balanced)</div>
        ${Object.entries(d.after_dist).map(([k,v]) =>
          `<div class="ba-row"><span>Class ${k}</span><span>${v.toLocaleString()}</span></div>`).join('')}
      </div>
    </div>`;
    html += `<div class="detail-note">${d.strategy}</div>`;
  }

  html += '</div>';
  return html;
}
