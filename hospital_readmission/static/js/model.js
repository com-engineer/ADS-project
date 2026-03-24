let _trainedResults = [];

async function doSplit() {
  const testSize = parseFloat(document.getElementById('split-ratio').value);
  const btn = event.target;
  btn.textContent = 'Splitting...';
  btn.disabled = true;

  const d = await fetch('/api/model/split', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ test_size: testSize })
  }).then(r => r.json());

  if (d.error) { alert(d.error); btn.textContent='Split data'; btn.disabled=false; return; }

  document.getElementById('spl-total').textContent = d.total_rows.toLocaleString();
  document.getElementById('spl-train').textContent = d.train_rows.toLocaleString();
  document.getElementById('spl-test').textContent  = d.test_rows.toLocaleString();
  document.getElementById('spl-feats').textContent = d.features;

  document.getElementById('spl-train-dist').innerHTML =
    Object.entries(d.train_dist).map(([k, v]) =>
      `<div class="ba-row">
        <span>Class ${k} (${k==='1'?'readmitted':'not readmitted'})</span>
        <span><strong>${v.toLocaleString()}</strong></span>
      </div>`
    ).join('');

  document.getElementById('spl-test-dist').innerHTML =
    Object.entries(d.test_dist).map(([k, v]) =>
      `<div class="ba-row">
        <span>Class ${k} (${k==='1'?'readmitted':'not readmitted'})</span>
        <span><strong>${v.toLocaleString()}</strong></span>
      </div>`
    ).join('');

  document.getElementById('split-result').style.display = 'block';
  btn.textContent = 'Done';
  btn.style.background = '#639922';
  btn.style.borderColor = '#639922';
}

async function trainAllModels() {
  const checked = [...document.querySelectorAll('.model-check input:checked')]
    .map(cb => cb.value);

  if (!checked.length) { alert('Select at least one model'); return; }

  const btn = document.getElementById('train-btn');
  btn.disabled = true;
  btn.textContent = 'Training...';

  const progress = document.getElementById('training-progress');
  progress.innerHTML = checked.map(key => `
    <div class="train-row" id="tr-${key}">
      <div class="model-name">${modelLabel(key)}</div>
      <div class="train-status" id="ts-${key}">Waiting...</div>
    </div>`).join('');

  _trainedResults = [];

  for (const key of checked) {
    const row    = document.getElementById('tr-' + key);
    const status = document.getElementById('ts-' + key);
    row.classList.add('running');
    status.textContent = 'Training...';

    const result = await fetch(`/api/model/train/${key}`, {
      method: 'POST'
    }).then(r => r.json());

    if (result.error) {
      status.textContent = 'Error: ' + result.error;
      row.classList.remove('running');
      continue;
    }

    row.classList.remove('running');
    row.classList.add('done');
    status.innerHTML = `
      Acc: <strong>${(result.accuracy*100).toFixed(1)}%</strong> &nbsp;|&nbsp;
      F1: <strong>${result.f1}</strong> &nbsp;|&nbsp;
      ROC-AUC: <strong>${result.roc_auc || '—'}</strong> &nbsp;|&nbsp;
      Time: <strong>${result.train_time}s</strong>`;

    _trainedResults.push(result);
  }

  btn.textContent = 'All done';
  renderResultsTable(_trainedResults);
}

function modelLabel(key) {
  const map = {
    logistic_regression: 'Logistic Regression',
    decision_tree:       'Decision Tree',
    random_forest:       'Random Forest',
    xgboost:             'XGBoost'
  };
  return map[key] || key;
}

function renderResultsTable(results) {
  if (!results.length) return;

  const best = results.reduce((a, b) =>
    (b.roc_auc || b.accuracy) > (a.roc_auc || a.accuracy) ? b : a
  );

  const tbody = document.getElementById('results-tbody');
  tbody.innerHTML = results.map(r => {
    const isBest = r.model_key === best.model_key;
    return `<tr class="${isBest ? 'best-row' : ''}">
      <td>${r.model_name} ${isBest ? '🏆' : ''}</td>
      <td>${(r.train_acc*100).toFixed(1)}%</td>
      <td>${(r.accuracy*100).toFixed(1)}%</td>
      <td>${r.f1}</td>
      <td>${r.precision}</td>
      <td>${r.recall}</td>
      <td>${r.roc_auc || '—'}</td>
      <td>${r.train_time}s</td>
    </tr>`;
  }).join('');

  renderComparisonChart(results, best.model_key);
  document.getElementById('results-card').style.display = 'block';
}

function renderComparisonChart(results, bestKey) {
  if (window._resChart) window._resChart.destroy();

  const labels  = results.map(r => r.model_name);
  const acc     = results.map(r => parseFloat((r.accuracy*100).toFixed(1)));
  const f1      = results.map(r => parseFloat((r.f1*100).toFixed(1)));
  const rocauc  = results.map(r => r.roc_auc ? parseFloat((r.roc_auc*100).toFixed(1)) : 0);

  window._resChart = new Chart(
    document.getElementById('results-chart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Accuracy %',  data: acc,    backgroundColor: '#378ADD', borderRadius: 4, borderWidth: 0 },
        { label: 'F1 Score %',  data: f1,     backgroundColor: '#1D9E75', borderRadius: 4, borderWidth: 0 },
        { label: 'ROC-AUC %',   data: rocauc, backgroundColor: '#EF9F27', borderRadius: 4, borderWidth: 0 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { grid: { display: false } },
        y: { min: 0, max: 100,
             ticks: { callback: v => v + '%' } }
      }
    }
  });
}