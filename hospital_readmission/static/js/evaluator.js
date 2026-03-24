async function loadEvalModels() {
  const models = await fetch('/api/eval/models').then(r => r.json());
  const sel = document.getElementById('eval-model-select');
  sel.innerHTML = models.length
    ? models.map(m =>
        `<option value="${m.key}">${m.name}</option>`
      ).join('')
    : '<option value="">No models trained yet</option>';
}

async function runEvaluation() {
  const key = document.getElementById('eval-model-select').value;
  if (!key) { alert('No model selected'); return; }

  const btn = event.target;
  btn.textContent = 'Evaluating...';
  btn.disabled = true;

  const d = await fetch(`/api/eval/${key}`).then(r => r.json());
  if (d.error) {
    alert(d.error);
    btn.textContent = 'Evaluate';
    btn.disabled = false;
    return;
  }

  renderMetricCards(d.metrics);
  renderConfusionMatrix(d.confusion_matrix);
  renderROCCurve(d.roc_curve);
  renderClassReport(d.classification_report);
  renderOverfit(d.overfit);
  if (d.feature_importance.length) renderFeatureImportance(d.feature_importance);
  else document.getElementById('feat-imp-card').style.display = 'none';

  document.getElementById('eval-results').style.display = 'block';
  btn.textContent = 'Evaluate';
  btn.disabled = false;
}

function renderMetricCards(m) {
  document.getElementById('ev-acc').textContent    = (m.accuracy * 100).toFixed(1) + '%';
  document.getElementById('ev-f1').textContent     = m.f1;
  document.getElementById('ev-auc').textContent    = m.roc_auc || '—';
  document.getElementById('ev-recall').textContent = m.recall;
}

function renderConfusionMatrix(cm) {
  const total = cm.tn + cm.fp + cm.fn + cm.tp;
  const cells = [
    { label: 'True Negative',  val: cm.tn, bg: '#EAF3DE', color: '#3B6D11',
      desc: 'Correctly predicted NOT readmitted' },
    { label: 'False Positive', val: cm.fp, bg: '#FAEEDA', color: '#854F0B',
      desc: 'Predicted readmitted — actually not' },
    { label: 'False Negative', val: cm.fn, bg: '#FCEBEB', color: '#A32D2D',
      desc: 'Predicted not readmitted — actually was' },
    { label: 'True Positive',  val: cm.tp, bg: '#E6F1FB', color: '#185FA5',
      desc: 'Correctly predicted readmitted' }
  ];

  document.getElementById('cm-grid').innerHTML = cells.map(c => `
    <div style="background:${c.bg};border-radius:8px;padding:14px;text-align:center">
      <div style="font-size:11px;font-weight:600;color:${c.color};
                  text-transform:uppercase;margin-bottom:6px">${c.label}</div>
      <div style="font-size:28px;font-weight:700;color:${c.color}">${c.val.toLocaleString()}</div>
      <div style="font-size:11px;color:${c.color};opacity:0.8;margin-top:4px">
        ${((c.val / total) * 100).toFixed(1)}%
      </div>
      <div style="font-size:10px;color:${c.color};opacity:0.7;margin-top:4px">
        ${c.desc}
      </div>
    </div>`).join('');

  document.getElementById('cm-legend').innerHTML =
    `Total predictions: <strong>${total.toLocaleString()}</strong> &nbsp;|&nbsp;
     Correct: <strong>${(cm.tn + cm.tp).toLocaleString()}</strong> &nbsp;|&nbsp;
     Wrong: <strong>${(cm.fp + cm.fn).toLocaleString()}</strong>`;
}

function renderROCCurve(roc) {
  if (window._rocChart) window._rocChart.destroy();
  if (!roc.fpr.length) return;

  window._rocChart = new Chart(document.getElementById('roc-canvas'), {
    type: 'line',
    data: {
      labels: roc.fpr,
      datasets: [
        {
          label: 'ROC Curve',
          data: roc.tpr,
          borderColor: '#185FA5',
          backgroundColor: 'rgba(24,95,165,0.08)',
          borderWidth: 2,
          pointRadius: 0,
          fill: true,
          tension: 0.3
        },
        {
          label: 'Random classifier',
          data: roc.fpr,
          borderColor: '#D3D1C7',
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { title: { display: true, text: 'False Positive Rate', font:{size:11} },
             ticks: { font: { size: 10 } }, min: 0, max: 1 },
        y: { title: { display: true, text: 'True Positive Rate', font:{size:11} },
             ticks: { font: { size: 10 } }, min: 0, max: 1 }
      }
    }
  });

  document.getElementById('roc-auc-label').textContent =
    `AUC = ${roc.auc}  (closer to 1.0 = better)`;
}

function renderClassReport(report) {
  const tbody = document.getElementById('clf-report-body');
  const rows  = [
    { label: 'Not readmitted (0)', ...report.not_readmitted },
    { label: 'Readmitted (1)',     ...report.readmitted }
  ];
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><strong>${r.label}</strong></td>
      <td>${r.precision}</td>
      <td>${r.recall}</td>
      <td>${r.f1}</td>
      <td>${r.support.toLocaleString()}</td>
    </tr>`).join('');
}

function renderOverfit(ov) {
  const color  = ov.status === 'Good fit'      ? '#3B6D11'
               : ov.status === 'Slight overfit' ? '#854F0B'
               : '#A32D2D';
  const bg     = ov.status === 'Good fit'      ? '#EAF3DE'
               : ov.status === 'Slight overfit' ? '#FAEEDA'
               : '#FCEBEB';

  document.getElementById('overfit-display').innerHTML = `
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
      <div class="stat-item">
        <div class="lbl">Train accuracy</div>
        <div class="val">${(ov.train_acc * 100).toFixed(1)}%</div>
      </div>
      <div style="font-size:20px;color:#aaa">→</div>
      <div class="stat-item">
        <div class="lbl">Test accuracy</div>
        <div class="val">${(ov.test_acc * 100).toFixed(1)}%</div>
      </div>
      <div style="font-size:20px;color:#aaa">→</div>
      <div class="stat-item">
        <div class="lbl">Gap</div>
        <div class="val">${(ov.gap * 100).toFixed(1)}%</div>
      </div>
      <div style="background:${bg};color:${color};padding:8px 18px;
           border-radius:20px;font-size:13px;font-weight:600">
        ${ov.status}
      </div>
    </div>
    <div style="font-size:12px;color:#888;margin-top:10px">
      Gap > 10% = Overfitting &nbsp;|&nbsp;
      Gap 5–10% = Slight overfit &nbsp;|&nbsp;
      Gap &lt; 5% = Good fit
    </div>`;
}

function renderFeatureImportance(importance) {
  if (window._impChart) window._impChart.destroy();

  const labels = importance.map(i => i.feature);
  const values = importance.map(i => i.importance);
  const maxVal = Math.max(...values);

  window._impChart = new Chart(document.getElementById('feat-imp-canvas'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Importance',
        data: values,
        backgroundColor: values.map((v, i) =>
          i === 0 ? '#0C447C' : i < 3 ? '#185FA5' :
          i < 7  ? '#378ADD' : '#85B7EB'
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