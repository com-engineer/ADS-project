const charts = {};

function killChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

async function api(url) {
  const r = await fetch(url);
  return r.json();
}

/* ── Phase switching (top-level nav) ── */
function showPhase(phaseId, btn) {
  document.querySelectorAll('.phase').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.phase-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.sub-nav').forEach(n => n.style.display = 'none');

  document.getElementById(phaseId).classList.add('active');
  if (!btn.classList.contains('disabled')) btn.classList.add('active');

  const subnavMap = { 'phase-eda': 'subnav-eda', 'phase-preprocess': 'subnav-preprocess' };
  if (subnavMap[phaseId]) document.getElementById(subnavMap[phaseId]).style.display = 'flex';

  if (phaseId === 'phase-preprocess') refreshPipelineStatus();
}

/* ── Tab switching (within a phase) ── */
function showTab(id, btn) {
  const subnav = btn.closest('.sub-nav');
  const phaseId = 'phase-' + subnav.id.replace('subnav-', '');
  document.querySelectorAll('#' + phaseId + ' .section').forEach(s => s.classList.remove('active'));
  subnav.querySelectorAll('button').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
}

/* ── Populate all <select> elements with column names ── */
function populateSelects(columns) {
  ['uni-col', 'bi-x', 'bi-y', 'stats-col', 'tgt-col'].forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = '';
    columns.forEach(c => {
      const o = document.createElement('option');
      o.value = c; o.textContent = c; sel.appendChild(o);
    });
  });
}

/* ── Overview ── */
async function initOverview() {
  const [ov, tgt] = await Promise.all([api('/api/overview'), api('/api/target')]);
  document.getElementById('m-rows').textContent    = ov.rows.toLocaleString();
  document.getElementById('m-cols').textContent    = ov.cols;
  document.getElementById('m-missing').textContent = ov.missing_cells.toLocaleString();
  document.getElementById('m-dupes').textContent   = ov.duplicate_rows;

  killChart('targetChart');
  charts['targetChart'] = new Chart(document.getElementById('targetChart'), {
    type: 'bar',
    data: {
      labels: tgt.labels,
      datasets: [{ label: 'Count', data: tgt.values,
        backgroundColor: ['#378ADD', '#1D9E75', '#E24B4A'], borderRadius: 5, borderWidth: 0 }]
    },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false } },
        y: { ticks: { callback: v => v >= 1000 ? (v/1000).toFixed(0)+'k' : v } } } }
  });
}

/* ── Missing values table ── */
async function initMissing() {
  const miss = await api('/api/missing');
  const tbody = document.getElementById('missing-body');
  if (!miss.length) {
    tbody.innerHTML = '<tr><td colspan="4" style="color:#888;padding:20px">No missing values found.</td></tr>';
    return;
  }
  tbody.innerHTML = miss.map(m => {
    const pct = m.missing_pct;
    const cls    = pct > 50 ? 'badge-red' : pct > 20 ? 'badge-yellow' : 'badge-green';
    const action = pct > 50 ? 'Drop column' : pct > 20 ? 'Review / fill' : 'Fill with mode';
    return `<tr><td><strong>${m.column}</strong></td><td>${m.missing_count.toLocaleString()}</td>
      <td>${pct}%</td><td><span class="badge ${cls}">${action}</span></td></tr>`;
  }).join('');
}

/* ── Univariate ── */
async function renderUni() {
  const col  = document.getElementById('uni-col').value;
  const type = document.getElementById('uni-type').value;
  if (!col) return;
  const d = await api('/api/distribution/' + encodeURIComponent(col));
  killChart('uniChart');
  const colors = d.labels.map((_, i) => `hsl(${200 + i * 18}, 60%, 55%)`);
  charts['uniChart'] = new Chart(document.getElementById('uniChart'), {
    type: type === 'pie' ? 'pie' : 'bar',
    data: { labels: d.labels, datasets: [{ label: 'Count', data: d.values,
      backgroundColor: type === 'pie' ? colors : '#378ADD', borderRadius: 5, borderWidth: 0 }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: type === 'pie' } },
      scales: type === 'pie' ? {} : {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: { ticks: { callback: v => v >= 1000 ? (v/1000).toFixed(1)+'k' : v } } } }
  });
  const ins = document.getElementById('uni-insight');
  ins.textContent = `"${col}" — ${d.labels.length} unique values. Most frequent: "${d.labels[0]}" (${d.values[0].toLocaleString()} records).`;
  ins.style.display = 'block';
}

/* ── Bivariate ── */
async function renderBi() {
  const x = document.getElementById('bi-x').value;
  const y = document.getElementById('bi-y').value;
  if (!x || !y) return;
  const d = await api(`/api/bivariate?x=${encodeURIComponent(x)}&y=${encodeURIComponent(y)}`);
  if (d.error) { alert('Error: ' + d.error); return; }
  killChart('biChart');
  charts['biChart'] = new Chart(document.getElementById('biChart'), {
    type: 'bar',
    data: { labels: d.labels, datasets: [{ label: y, data: d.values,
      backgroundColor: '#1D9E75', borderRadius: 5, borderWidth: 0 }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false }, ticks: { font: { size: 11 } } }, y: {} } }
  });
}

/* ── Statistics ── */
async function renderStats() {
  const col = document.getElementById('stats-col').value;
  if (!col) return;
  const s = await api('/api/statistics/' + encodeURIComponent(col));
  const grid = document.getElementById('stat-grid');
  if (s.error) {
    grid.innerHTML = `<p style="color:#888;font-size:13px;grid-column:span 3">${s.error}</p>`;
    return;
  }
  const items = [['Mean',s.mean],['Median',s.median],['Std Dev',s.std],
    ['Min',s.min],['Max',s.max],['Q1 (25%)',s.q1],['Q3 (75%)',s.q3],
    ['Skewness',s.skew],['Kurtosis',s.kurt]];
  grid.innerHTML = items.map(([l, v], i) => {
    const cls = (i === 7 && Math.abs(v) > 1) ? 'val skew-warn' : 'val';
    return `<div class="stat-item"><div class="lbl">${l}</div><div class="${cls}">${v}</div></div>`;
  }).join('');
}

/* ── Correlation ── */
async function renderCorr() {
  const d = await api('/api/correlation');
  const n = d.columns.length;
  const pts = [];
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++)
      pts.push({ x: j, y: i, v: d.matrix[i][j] });
  killChart('corrChart');
  charts['corrChart'] = new Chart(document.getElementById('corrChart'), {
    type: 'scatter',
    data: { datasets: [{ data: pts.map(p => ({ x: p.x, y: p.y })),
      backgroundColor: pts.map(p => p.v>0.6?'#0C447C':p.v>0.4?'#185FA5':p.v>0.2?'#378ADD':p.v>0.1?'#85B7EB':'#D3D1C7'),
      pointRadius: pts.map(p => Math.abs(p.v)*20+5), pointHoverRadius: 22 }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false },
        tooltip: { callbacks: { label: c => {
          const p = pts[c.dataIndex];
          return `${d.columns[p.y]} × ${d.columns[p.x]}: ${p.v.toFixed(2)}`;
        }}}},
      scales: {
        x: { min: -0.5, max: n-0.5, ticks: { callback: i => d.columns[Math.round(i)]||'', font:{size:10} }, grid:{display:false} },
        y: { min: -0.5, max: n-0.5, ticks: { callback: i => d.columns[Math.round(i)]||'', font:{size:10} }, grid:{display:false} }
      }}
  });
}

/* ── Target analysis ── */
async function renderTarget() {
  const col = document.getElementById('tgt-col').value;
  if (!col) return;
  const d = await api(`/api/bivariate?x=${encodeURIComponent(col)}&y=readmitted`);
  if (d.error) { alert('Error: ' + d.error); return; }
  killChart('tgtChart');
  charts['tgtChart'] = new Chart(document.getElementById('tgtChart'), {
    type: 'bar',
    data: { labels: d.labels, datasets: [{ label: 'Avg readmission rate', data: d.values,
      backgroundColor: d.values.map(v => v>0.13?'#E24B4A':v>0.10?'#EF9F27':'#1D9E75'),
      borderRadius: 5, borderWidth: 0 }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid:{display:false}, ticks:{font:{size:11}} },
        y: { ticks: { callback: v => (v*100).toFixed(1)+'%' } } } }
  });
}

/* ── Bootstrap ── */
async function init() {
  const cols = await api('/api/columns');
  populateSelects(cols.columns);
  await initOverview();
  await initMissing();
  renderCorr();
}

document.addEventListener('DOMContentLoaded', init);