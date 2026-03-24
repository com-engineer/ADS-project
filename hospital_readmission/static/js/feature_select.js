async function apiPost(url, body = null) {
  const opts = { method: 'POST' };
  if (body) {
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(url, opts);
  return r.json();
}

async function refreshFSStatus() {
  const s = await fetch('/api/fs/state').then(r => r.json());
  document.getElementById('fs-rows').textContent    = s.rows.toLocaleString();
  document.getElementById('fs-cols').textContent    = s.cols;
  document.getElementById('fs-dropped').textContent = s.dropped;
  document.getElementById('fs-step').textContent    = s.step + ' / 4';
}

async function initFS() {
  const s = await apiPost('/api/fs/init');
  if (s.error) { alert(s.error); return; }
  document.getElementById('fs-rows').textContent    = s.rows.toLocaleString();
  document.getElementById('fs-cols').textContent    = s.cols;
  document.getElementById('fs-dropped').textContent = 0;
  document.getElementById('fs-step').textContent    = '0 / 4';

  for (let i = 1; i <= 4; i++) {
    const card = document.getElementById('fs-card-' + i);
    card.classList.remove('done');
    const btn = card.querySelector('.step-btn');
    btn.disabled = false;
    btn.textContent = 'Apply';
    if (i < 4) document.getElementById('fs-result-' + i).innerHTML = '';
  }

  document.getElementById('fs-final-card').style.display = 'none';
  loadManualChecklist();

  document.getElementById('fs-visuals').style.display = 'grid';
  await renderFSVisuals();
  
}

async function loadManualChecklist() {
  const data = await fetch('/api/fs/features').then(r => r.json());
  const box  = document.getElementById('fs-manual-checklist');
  box.innerHTML = data.features.map(f => `
    <label style="display:flex;align-items:center;gap:6px;font-size:13px;
      background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
      padding:5px 10px;cursor:pointer">
      <input type="checkbox" value="${f}"> ${f}
    </label>`).join('');
}

async function applyFS(n) {
  const btn = document.querySelector(`#fs-card-${n} .step-btn`);
  btn.textContent = 'Running...';
  btn.disabled = true;

  let data;
  if (n === 3) {
    const k = document.getElementById('fs-k-val').value || 15;
    data = await apiPost(`/api/fs/step/3?k=${k}`);
  } else if (n === 4) {
    const checked = [...document.querySelectorAll('#fs-manual-checklist input:checked')]
      .map(cb => cb.value);
    if (!checked.length) {
      alert('Please select at least one feature to drop');
      btn.textContent = 'Apply'; btn.disabled = false; return;
    }
    data = await apiPost('/api/fs/step/4', { cols: checked });
  } else {
    data = await apiPost(`/api/fs/step/${n}`);
  }

  if (data.error) { btn.textContent = 'Error'; alert(data.error); return; }

  renderFSResult(n, data);
  document.getElementById('fs-card-' + n).classList.add('done');
  btn.textContent = 'Done';
  await refreshFSStatus();

  if (n === 4) showFinalFeatures();
  else loadManualChecklist();
}

function renderFSResult(n, data) {
  const el = document.getElementById('fs-result-' + n);
  const b  = data.before, a = data.after;

  let html = `<div class="ba-grid">
    <div class="ba-box before">
      <div class="ba-label">Before</div>
      <div class="ba-stat">${b.rows.toLocaleString()} rows | ${b.cols} cols</div>
    </div>
    <div class="ba-arrow">→</div>
    <div class="ba-box after">
      <div class="ba-label">After</div>
      <div class="ba-stat">${a.rows.toLocaleString()} rows | ${a.cols} cols
        <span style="color:#A32D2D;font-size:11px;margin-left:6px">
          ${b.cols - a.cols > 0 ? '-' + (b.cols - a.cols) + ' cols' : 'no change'}
        </span>
      </div>
    </div>
  </div><div class="detail-panel">`;

  const d = data.detail;

  if (n === 1) {
    html += `<div class="detail-title">Threshold: ${d.threshold} — Dropped ${d.dropped.length} features</div>`;
    if (d.pairs.length) {
      html += d.pairs.map(p =>
        `<div class="detail-row">
          <span class="detail-tag tag-red">${p.col}</span>
          <span class="detail-val">correlated with <strong>${p.correlated_with}</strong> → r = ${p.value}</span>
        </div>`).join('');
    } else {
      html += `<div class="detail-row"><span class="detail-val">No highly correlated pairs found — all features kept</span></div>`;
    }
  }

  if (n === 2) {
    html += `<div class="detail-title">Top 10 most important features</div>`;
    const top10f = d.features.slice(0, 10);
    const top10i = d.importances.slice(0, 10);
    const maxImp = Math.max(...top10i);
    html += top10f.map((f, i) => {
      const pct = ((top10i[i] / maxImp) * 100).toFixed(0);
      return `<div style="margin-bottom:6px">
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:2px">
          <span>${f}</span><span>${top10i[i]}</span>
        </div>
        <div style="background:#e2e8f0;border-radius:4px;height:6px">
          <div style="background:#185FA5;width:${pct}%;height:6px;border-radius:4px"></div>
        </div>
      </div>`;
    }).join('');
  }

  if (n === 3) {
    html += `<div class="detail-title">Selected top ${d.k} features by f_classif score</div>`;
    html += `<div class="detail-row">` +
      d.selected.map(f => `<span class="detail-tag tag-blue">${f}</span>`).join('') +
    `</div>`;
    if (d.dropped.length) {
      html += `<div class="detail-title" style="margin-top:8px">Dropped (${d.dropped.length})</div>`;
      html += `<div class="detail-row">` +
        d.dropped.map(f => `<span class="detail-tag tag-red">${f}</span>`).join('') +
      `</div>`;
    }
  }

  if (n === 4) {
    html += `<div class="detail-title">Manually dropped</div>`;
    html += d.dropped.length
      ? d.dropped.map(f => `<span class="detail-tag tag-red">${f}</span>`).join(' ')
      : `<span class="detail-val">Nothing dropped</span>`;
    html += `<div class="detail-title" style="margin-top:8px">Remaining features (${d.remaining.length - 1})</div>`;
    html += `<div class="detail-row">` +
      d.remaining.filter(f => f !== 'readmitted')
        .map(f => `<span class="detail-tag tag-blue">${f}</span>`).join('') +
    `</div>`;
  }

  html += '</div>';
  el.innerHTML = html;
  el.style.display = 'block';
}

async function showFinalFeatures() {
  const data = await fetch('/api/fs/features').then(r => r.json());
  const card = document.getElementById('fs-final-card');
  const tags = document.getElementById('fs-final-tags');
  tags.innerHTML = `<p style="font-size:13px;color:#888;margin-bottom:10px">
    ${data.features.length} features selected for model training</p>` +
    data.features.map(f =>
      `<span class="detail-tag tag-blue" style="display:inline-block;margin:3px">${f}</span>`
    ).join('');
  card.style.display = 'block';
}

async function renderFSVisuals() {
  const featData = await fetch('/api/fs/features').then(r => r.json());
  const corrData = await fetch('/api/fs/correlation').then(r => r.json());
  const impData  = await fetch('/api/fs/importance').then(r => r.json());

  renderCorrHeatmap(corrData);
  renderImportanceChart(impData);
}

function renderCorrHeatmap(d) {
  const canvas = document.getElementById('fs-corr-canvas');
  if (!canvas) return;
  if (window._fsCorr) { window._fsCorr.destroy(); }

  const n   = d.columns.length;
  const pts = [];
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      pts.push({ x: j, y: i, v: d.matrix[i][j] });

  window._fsCorr = new Chart(canvas, {
    type: 'scatter',
    data: {
      datasets: [{
        data: pts.map(p => ({ x: p.x, y: p.y })),
        backgroundColor: pts.map(p => {
          const v = p.v;
          if (v >= 0.85) return '#A32D2D';
          if (v >= 0.6)  return '#E24B4A';
          if (v >= 0.4)  return '#EF9F27';
          if (v >= 0.2)  return '#378ADD';
          return '#D3D1C7';
        }),
        pointRadius: pts.map(p => Math.abs(p.v) * 16 + 4),
        pointHoverRadius: 18
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: c => {
              const p = pts[c.dataIndex];
              const warn = p.v >= 0.85 ? ' ⚠ HIGH' : '';
              return `${d.columns[p.y]} × ${d.columns[p.x]}: ${p.v.toFixed(2)}${warn}`;
            }
          }
        }
      },
      scales: {
        x: {
          min: -0.5, max: n - 0.5,
          ticks: { callback: i => d.columns[Math.round(i)] || '', font: { size: 9 } },
          grid: { display: false }
        },
        y: {
          min: -0.5, max: n - 0.5,
          ticks: { callback: i => d.columns[Math.round(i)] || '', font: { size: 9 } },
          grid: { display: false }
        }
      }
    }
  });
}

function renderImportanceChart(d) {
  const canvas = document.getElementById('fs-imp-canvas');
  if (!canvas) return;
  if (window._fsImp) { window._fsImp.destroy(); }

  const top15f = d.features.slice(0, 15);
  const top15i = d.importances.slice(0, 15);

  window._fsImp = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: top15f,
      datasets: [{
        label: 'Importance score',
        data: top15i,
        backgroundColor: top15i.map((v, i) =>
          i < 3 ? '#185FA5' : i < 8 ? '#378ADD' : '#85B7EB'
        ),
        borderRadius: 4,
        borderWidth: 0
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false },
             ticks: { font: { size: 11 } } },
        y: { grid: { display: false },
             ticks: { font: { size: 11 } } }
      }
    }
  });
}