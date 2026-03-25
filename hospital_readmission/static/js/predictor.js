let _bestModelKey = null;
let _allFeatures  = [];

const ENGINEERED = [
  'total_visits', 'age_risk', 'glucose_risk',
  'is_high_utilizer', 'diagnosis_count'
];

const AGE_RISK_MAP = {0:1,1:1,2:2,3:2,4:3,5:4,6:5,7:5,8:4,9:3};

const GLUCOSE_MAP = {
  "None": 0, "Norm": 1, ">200": 2, ">300": 3
};

const RACE_MAP = {
  "Caucasian": 0, "AfricanAmerican": 1,
  "Hispanic": 2, "Asian": 3, "Other": 4
};

const GENDER_MAP = { "Female": 0, "Male": 1 };

async function loadPredictionPhase() {
  const best = await fetch('/api/predict/best').then(r => r.json());
  if (best.error) {
    document.getElementById('pred-model-info').innerHTML =
      `<div class="insight">${best.error} — complete Model Training first</div>`;
    return;
  }

  _bestModelKey = best.model_key;

  document.getElementById('pred-model-info').innerHTML = `
    <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap">
      <div>
        <span style="font-size:16px;font-weight:600;color:#185FA5">
          ${best.model_name}
        </span>
        <span style="font-size:12px;color:#888;margin-left:8px">
          (best performing model)
        </span>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <div class="stat-item" style="padding:8px 14px">
          <div class="lbl">Accuracy</div>
          <div class="val">${(best.accuracy*100).toFixed(1)}%</div>
        </div>
        <div class="stat-item" style="padding:8px 14px">
          <div class="lbl">F1 Score</div>
          <div class="val">${best.f1}</div>
        </div>
        <div class="stat-item" style="padding:8px 14px">
          <div class="lbl">ROC-AUC</div>
          <div class="val">${best.roc_auc || '—'}</div>
        </div>
      </div>
      <select id="pred-model-override"
        style="padding:7px 12px;border:1px solid #dde3ea;
               border-radius:8px;font-size:13px">
      </select>
    </div>`;

  await loadModelOverrideDropdown();

  const featData = await fetch('/api/predict/features').then(r => r.json());
  if (featData.error) return;
  _allFeatures = featData.features;
}

async function loadModelOverrideDropdown() {
  const models = await fetch('/api/eval/models').then(r => r.json());
  const sel    = document.getElementById('pred-model-override');
  if (!sel) return;
  sel.innerHTML = models.map(m =>
    `<option value="${m.key}" ${m.key===_bestModelKey?'selected':''}>
      Use: ${m.name}
    </option>`).join('');
}

/* ── Gather only the raw meaningful inputs ── */
function gatherInputs() {
  const age    = parseInt(document.getElementById('inp-age').value)    || 5;
  const inpat  = parseFloat(document.getElementById('inp-inpat').value)  || 0;
  const outpat = parseFloat(document.getElementById('inp-outpat').value) || 0;
  const emerg  = parseFloat(document.getElementById('inp-emerg').value)  || 0;

  const diag1  = parseFloat(document.getElementById('inp-diag1').value) || 0;
  const diag2  = parseFloat(document.getElementById('inp-diag2').value) || 0;
  const diag3  = parseFloat(document.getElementById('inp-diag3').value) || 0;

  const glucose = document.getElementById('inp-glucose').value;
  const race    = document.getElementById('inp-race').value;
  const gender  = document.getElementById('inp-gender').value;

  return {
    // direct features
    age:                  age,
    time_in_hospital:     parseFloat(document.getElementById('inp-time').value)  || 4,
    num_medications:      parseFloat(document.getElementById('inp-meds').value)  || 15,
    num_lab_procedures:   parseFloat(document.getElementById('inp-lab').value)   || 40,
    num_procedures:       parseFloat(document.getElementById('inp-proc').value)  || 1,
    number_diagnoses:     parseFloat(document.getElementById('inp-numdiag').value) || 7,
    number_inpatient:     inpat,
    number_outpatient:    outpat,
    number_emergency:     emerg,
    diag_1:               diag1,
    diag_2:               diag2,
    diag_3:               diag3,
    race:                 RACE_MAP[race]   ?? 0,
    gender:               GENDER_MAP[gender] ?? 0,
    max_glu_serum:        GLUCOSE_MAP[glucose] ?? 0
  };
}

async function runPrediction() {
  const btn = event.target;
  btn.textContent = 'Predicting...';
  btn.disabled = true;

  const sel      = document.getElementById('pred-model-override');
  const modelKey = sel ? sel.value : _bestModelKey;
  const inputs   = gatherInputs();

  const result = await fetch('/api/predict/run', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ model_key: modelKey, inputs })
  }).then(r => r.json());

  btn.textContent = 'Predict readmission risk';
  btn.disabled    = false;

  if (result.error) { alert(result.error); return; }

  renderPredictionResult(result);
  await loadPredictionHistory();
}

function renderPredictionResult(r) {
  const riskClass = r.risk_level === 'High Risk'   ? 'high'
                  : r.risk_level === 'Medium Risk'  ? 'medium'
                  : 'low';

  const prob = r.probability !== null
    ? r.probability
    : (r.prediction === 1 ? 100 : 0);

  const desc = r.risk_level === 'High Risk'
    ? 'High probability of readmission within 30 days. Recommend enhanced post-discharge care and immediate follow-up.'
    : r.risk_level === 'Medium Risk'
    ? 'Moderate readmission risk. Consider scheduling a follow-up appointment within 2 weeks of discharge.'
    : 'Low readmission risk. Standard discharge procedure is appropriate.';

  const engHtml = r.engineered ? `
    <div style="margin-top:16px;padding-top:14px;border-top:1px solid #e2e8f0">
      <div style="font-size:11px;font-weight:600;color:#888;
                  text-transform:uppercase;letter-spacing:0.4px;margin-bottom:10px">
        Auto-calculated from your inputs
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        ${Object.entries(r.engineered).map(([k,v]) => `
          <div class="stat-item" style="padding:8px 14px;min-width:120px">
            <div class="lbl">${k.replace(/_/g,' ')}</div>
            <div class="val" style="font-size:18px">${v}</div>
          </div>`).join('')}
      </div>
    </div>` : '';

  document.getElementById('pred-result-content').innerHTML = `
    <div class="risk-box ${riskClass}">
      <div>
        <div class="risk-label">${r.risk_level}</div>
        <div style="font-size:12px;margin-top:4px;opacity:0.8">
          Predicted by ${r.model_used}
        </div>
      </div>
      <div class="risk-prob">${prob !== null ? prob.toFixed(1)+'%' : '—'}</div>
      <div class="risk-desc">${desc}</div>
    </div>
    <div style="margin-bottom:6px;font-size:13px;color:#555">
      Readmission probability
    </div>
    <div class="prob-bar-wrap">
      <div class="prob-bar" style="width:${prob}%;
        background:${riskClass==='high'?'#E24B4A':
                    riskClass==='medium'?'#EF9F27':'#639922'}">
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;
                font-size:11px;color:#aaa;margin-top:2px">
      <span>0% (No risk)</span>
      <span>50%</span>
      <span>100% (Certain)</span>
    </div>
    ${engHtml}`;

  document.getElementById('pred-result').style.display = 'block';
}

async function loadPredictionHistory() {
  const history = await fetch('/api/predict/history').then(r => r.json());
  if (!history.length) return;

  const tbody = document.getElementById('pred-history-body');
  tbody.innerHTML = history.map((r, i) => {
    const rc = r.risk_level==='High Risk'  ? '#A32D2D'
             : r.risk_level==='Medium Risk' ? '#854F0B' : '#3B6D11';
    const rb = r.risk_level==='High Risk'  ? '#FCEBEB'
             : r.risk_level==='Medium Risk' ? '#FAEEDA' : '#EAF3DE';
    return `<tr>
      <td>${history.length - i}</td>
      <td><span style="background:${rb};color:${rc};padding:2px 10px;
           border-radius:20px;font-size:12px">${r.risk_level}</span></td>
      <td>${r.probability!==null ? r.probability.toFixed(1)+'%' : '—'}</td>
      <td>${r.prediction===1 ? 'Readmitted' : 'Not readmitted'}</td>
      <td>${r.model_used}</td>
    </tr>`;
  }).join('');

  document.getElementById('pred-history-card').style.display = 'block';
}