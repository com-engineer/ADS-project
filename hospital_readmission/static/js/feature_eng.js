async function apiPost(url) {
  const r = await fetch(url, { method: 'POST' });
  return r.json();
}

async function refreshFEStatus() {
  const s = await fetch('/api/fe/state').then(r => r.json());
  document.getElementById('fe-rows').textContent = s.rows.toLocaleString();
  document.getElementById('fe-cols').textContent = s.cols;
  document.getElementById('fe-new').textContent  = s.new_features;
  document.getElementById('fe-step').textContent = s.step + ' / 6';
}

async function initFE() {
  const s = await apiPost('/api/fe/init');
  document.getElementById('fe-rows').textContent = s.rows.toLocaleString();
  document.getElementById('fe-cols').textContent = s.cols;
  document.getElementById('fe-new').textContent  = 0;
  document.getElementById('fe-step').textContent = '0 / 6';
  for (let i = 1; i <= 6; i++) {
    document.getElementById('fe-result-' + i).innerHTML = '';
    document.getElementById('fe-result-' + i).style.display = 'none';
    const card = document.getElementById('fe-card-' + i);
    card.classList.remove('done');
    card.querySelector('.step-btn').disabled = false;
    card.querySelector('.step-btn').textContent = 'Apply';
  }
  document.getElementById('fe-feature-list-card').style.display = 'none';
}

async function applyFE(n) {
  const btn = document.querySelector(`#fe-card-${n} .step-btn`);
  btn.textContent = 'Running...';
  btn.disabled = true;

  const data = await apiPost(`/api/fe/step/${n}`);
  if (data.error) { btn.textContent = 'Error'; alert(data.error); return; }

  renderFEResult(n, data);
  document.getElementById('fe-card-' + n).classList.add('done');
  btn.textContent = 'Done';
  await refreshFEStatus();

  if (n === 6) showFeatureList();
}

function renderFEResult(n, data) {
  const el = document.getElementById('fe-result-' + n);
  const b = data.before, a = data.after;

  let html = `<div class="ba-grid">
    <div class="ba-box before">
      <div class="ba-label">Before</div>
      <div class="ba-stat">${b.rows.toLocaleString()} rows | ${b.cols} cols</div>
    </div>
    <div class="ba-arrow">→</div>
    <div class="ba-box after">
      <div class="ba-label">After</div>
      <div class="ba-stat">${a.rows.toLocaleString()} rows | ${a.cols} cols
        <span style="color:#3B6D11;font-size:11px;margin-left:6px">
          ${a.cols > b.cols ? '+' + (a.cols - b.cols) + ' col' : a.cols < b.cols ? '-' + (b.cols - a.cols) + ' cols' : ''}
        </span>
      </div>
    </div>
  </div>`;

  html += '<div class="detail-panel">';
  const d = data.detail;

  if (d.new_col) {
    html += `<div class="detail-title">New column: <span class="detail-tag tag-blue">${d.new_col}</span></div>`;
  }
  if (d.formula)  html += `<div class="detail-row"><span class="detail-val">Formula: <strong>${d.formula}</strong></span></div>`;
  if (d.rule)     html += `<div class="detail-row"><span class="detail-val">Rule: <strong>${d.rule}</strong></span></div>`;
  if (d.mapping && typeof d.mapping === 'string') {
    html += `<div class="detail-row"><span class="detail-val">${d.mapping}</span></div>`;
  }
  if (d.mapping && typeof d.mapping === 'object') {
    html += '<div class="detail-row">' +
      Object.entries(d.mapping).map(([k,v]) =>
        `<span class="detail-tag tag-blue">${k} → ${v}</span>`).join(' ') +
    '</div>';
  }
  if (d.distribution || d.sample) {
    const dist = d.distribution || d.sample;
    html += `<div class="detail-title" style="margin-top:8px">Distribution</div>
      <div class="detail-row">` +
      Object.entries(dist).slice(0, 6).map(([k, v]) =>
        `<span class="detail-tag tag-blue">${k}: ${v.toLocaleString()}</span>`
      ).join('') + '</div>';
  }
  if (d.min !== undefined) {
    html += `<div class="detail-row">
      <span class="detail-val">Min: <strong>${d.min}</strong></span>
      <span class="detail-val">Max: <strong>${d.max}</strong></span>
      <span class="detail-val">Mean: <strong>${d.mean}</strong></span>
    </div>`;
  }
  if (d.dropped) {
    html += `<div class="detail-title">Dropped</div>` +
      d.dropped.map(c => `<span class="detail-tag tag-red">${c}</span>`).join(' ');
    if (d.reason) html += `<div class="detail-note">${d.reason}</div>`;
  }

  html += '</div>';
  el.innerHTML = html;
  el.style.display = 'block';
}

async function showFeatureList() {
  const data = await fetch('/api/fe/features').then(r => r.json());
  const card = document.getElementById('fe-feature-list-card');
  const tags = document.getElementById('fe-feature-tags');
  const newFeatures = ['total_visits','age_risk','glucose_risk','is_high_utilizer','diagnosis_count'];
  tags.innerHTML = data.features.map(f =>
    `<span class="detail-tag ${newFeatures.includes(f) ? 'tag-green' : 'tag-blue'}"
      style="display:inline-block;margin:4px">${f}</span>`
  ).join('');
  card.style.display = 'block';
}