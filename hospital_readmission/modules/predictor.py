import numpy as np
import pandas as pd
from modules.model import _model_state, MODELS

_prediction_history = []

def get_best_model_info():
    results = _model_state["results"]
    if not results:
        return {"error": "No models trained yet"}
    best_key = max(
        results,
        key=lambda k: results[k]["roc_auc"] or results[k]["accuracy"]
    )
    r = results[best_key]
    return {
        "model_key":  best_key,
        "model_name": r["model_name"],
        "accuracy":   r["accuracy"],
        "f1":         r["f1"],
        "roc_auc":    r["roc_auc"]
    }

def get_input_features():
    features = _model_state["feature_names"]
    if not features:
        return {"error": "Train models first"}
    return {"features": features}

def predict(model_key, input_data):
    if model_key not in _model_state["trained_models"]:
        return {"error": f"Model '{model_key}' not trained"}

    clf      = _model_state["trained_models"][model_key]
    features = _model_state["feature_names"]

    try:
        # ── Extract raw inputs ──────────────────────────────────────────
        age    = float(input_data.get("age", 5))
        inpat  = float(input_data.get("number_inpatient", 0))
        outpat = float(input_data.get("number_outpatient", 0))
        emerg  = float(input_data.get("number_emergency", 0))
        diag1  = float(input_data.get("diag_1", 0))
        diag2  = float(input_data.get("diag_2", 0))
        diag3  = float(input_data.get("diag_3", 0))

        # ── Auto-calculate engineered features ──────────────────────────
        AGE_RISK = {0:1, 1:1, 2:2, 3:2, 4:3, 5:4, 6:5, 7:5, 8:4, 9:3}

        total_visits = inpat + outpat + emerg

        input_data["total_visits"]     = total_visits
        input_data["age_risk"]         = AGE_RISK.get(int(age), 3)
        input_data["glucose_risk"]     = float(input_data.get("glucose_risk", 0))
        input_data["is_high_utilizer"] = 1 if total_visits > 3 else 0
        input_data["diagnosis_count"]  = sum(
            1 for d in [diag1, diag2, diag3] if d > 0
        )

        # ── Build feature row in exact training order ───────────────────
        row = pd.DataFrame([{
            f: float(input_data.get(f, 0)) for f in features
        }])

        # ── Predict ─────────────────────────────────────────────────────
        prob = float(clf.predict_proba(row)[0][1]) \
               if hasattr(clf, "predict_proba") else None
        pred = int(clf.predict(row)[0])

        # ── Risk level based on probability ─────────────────────────────
        score = prob if prob is not None else float(pred)
        risk_level = "High Risk"   if score > 0.6  \
                else "Medium Risk" if score > 0.35 \
                else "Low Risk"

        result = {
            "prediction":  pred,
            "probability": round(prob * 100, 1) if prob is not None else None,
            "risk_level":  risk_level,
            "model_used":  MODELS[model_key]["name"],
            "engineered": {
                "total_visits":     input_data["total_visits"],
                "age_risk":         input_data["age_risk"],
                "glucose_risk":     input_data["glucose_risk"],
                "is_high_utilizer": input_data["is_high_utilizer"],
                "diagnosis_count":  input_data["diagnosis_count"]
            },
            "input": input_data
        }
        _prediction_history.append(result)
        return result

    except Exception as e:
        return {"error": str(e)}
    
def get_prediction_history():
    return list(reversed(_prediction_history))