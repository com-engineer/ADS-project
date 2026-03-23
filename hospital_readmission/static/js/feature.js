async function apiPost(url) {
  const r = await fetch(url, { method: 'POST' });
  return r.json();
}

async function initFeature() {
  await apiPost('/api/feature/init');

  for (let i = 1; i <= 4; i++) {
    document.getElementById('fe-result-' + i).innerHTML = '';
    document.getElementById('fe-card-' + i).classList.remove('done');
    document.getElementById('fe-pill-' + i).classList.remove('done');
  }

  await refreshFeatureStatus();
}

async function refreshFeatureStatus() {
  const s = await fetch('/api/feature/state').then(r => r.json());

  document.getElementById('fe-rows').textContent = s.rows.toLocaleString();
  document.getElementById('fe-cols').textContent = s.cols;
  document.getElementById('fe-missing').textContent = s.missing;
  document.getElementById('fe-step').textContent = s.step + ' / 4';
}

async function applyFeatureStep(n) {
  const btn = document.querySelector(`#fe-card-${n} .step-btn`);
  btn.textContent = 'Running...';
  btn.disabled = true;

  const data = await apiPost(`/api/feature/step/${n}`);

  renderFEResult(n, data);
  markFEDone(n);
  await refreshFeatureStatus();
}

function markFEDone(n) {
  document.getElementById('fe-card-' + n).classList.add('done');
  document.getElementById('fe-pill-' + n).classList.add('done');

  const btn = document.querySelector(`#fe-card-${n} .step-btn`);
  btn.textContent = 'Done';
}

function renderFEResult(n, data) {
  const el = document.getElementById('fe-result-' + n);

  let html = `
    <div class="ba-grid">
      <div class="ba-box before">
        <div class="ba-label">Before</div>
        <div class="ba-stat">${data.before.rows} rows | ${data.before.cols} cols</div>
      </div>
      <div class="ba-arrow">→</div>
      <div class="ba-box after">
        <div class="ba-label">After</div>
        <div class="ba-stat">${data.after.rows || data.after.X_shape?.[0]} rows</div>
      </div>
    </div>
  `;

  if (data.detail) {
    html += `<div class="detail-panel">`;

    Object.entries(data.detail).forEach(([k, v]) => {
      html += `<div class="detail-row">
        <span class="detail-tag tag-blue">${k}</span>
        <span class="detail-val">${JSON.stringify(v)}</span>
      </div>`;
    });

    html += `</div>`;
  }

  el.innerHTML = html;
  el.style.display = 'block';
}