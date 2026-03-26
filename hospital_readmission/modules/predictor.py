import numpy as np
import pandas as pd
from modules.model import _model_state, MODELS
from modules.preprocessor import _pipeline as _prep_pipeline

_prediction_history = []

AGE_RISK_MAP = {0:1, 1:1, 2:2, 3:2, 4:3, 5:4, 6:5, 7:5, 8:4, 9:3}
GLUCOSE_MAP  = {"None":0, "Norm":1, ">200":2, ">300":3}
RACE_MAP     = {"Caucasian":0, "AfricanAmerican":1,
                "Hispanic":2, "Asian":3, "Other":4}
GENDER_MAP   = {"Female":0, "Male":1}

NUMERIC_COLS = [
    "time_in_hospital", "num_lab_procedures", "num_procedures",
    "num_medications", "number_outpatient", "number_emergency",
    "number_inpatient", "number_diagnoses"
]


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
        # ── Step 1: Extract raw inputs using CORRECT key names ──────────
        age    = int(float(input_data.get("age", 5)))
        inpat  = float(input_data.get("number_inpatient",  0))
        outpat = float(input_data.get("number_outpatient", 0))
        emerg  = float(input_data.get("number_emergency",  0))
        diag1  = float(input_data.get("diag_1", 0))
        diag2  = float(input_data.get("diag_2", 0))
        diag3  = float(input_data.get("diag_3", 0))

        # glucose comes as raw string from JS e.g. "None", ">200", ">300"
        glucose_raw  = input_data.get("max_glu_serum_raw", "None")
        glucose_risk = GLUCOSE_MAP.get(str(glucose_raw), 0)

        # ── Step 2: Calculate all engineered features ───────────────────
        total_visits     = inpat + outpat + emerg
        age_risk         = AGE_RISK_MAP.get(age, 3)
        is_high_utilizer = 1 if total_visits > 3 else 0
        diagnosis_count  = sum(
            1 for d in [diag1, diag2, diag3] if d > 0
        )

        # inject into input_data before building row
        input_data["total_visits"]     = total_visits
        input_data["age_risk"]         = age_risk
        input_data["glucose_risk"]     = glucose_risk
        input_data["is_high_utilizer"] = is_high_utilizer
        input_data["diagnosis_count"]  = diagnosis_count
        input_data["max_glu_serum"]    = glucose_risk

        # ── Step 3: Apply the SAME scaler used in preprocessing ─────────
        scaler = _prep_pipeline.get("scaler")
        if scaler is not None:
            try:
                scaler_cols = list(scaler.feature_names_in_) \
                    if hasattr(scaler, 'feature_names_in_') \
                    else NUMERIC_COLS

                full_temp = pd.DataFrame(
                    [[float(input_data.get(c, 0)) for c in scaler_cols]],
                    columns=scaler_cols
                )
                scaled_vals = scaler.transform(full_temp)[0]
                for i, col in enumerate(scaler_cols):
                    if col in features:
                        input_data[col] = float(scaled_vals[i])

                print(f"DEBUG scaler applied to: {scaler_cols}")
            except Exception as scale_err:
                print(f"WARNING scaler failed: {scale_err} — using raw values")

        # ── Step 4: Build row in exact same feature order as training ────
        row = pd.DataFrame([{
            f: float(input_data.get(f, 0)) for f in features
        }])

        print(f"DEBUG engineered → "
              f"total_visits={total_visits}, age_risk={age_risk}, "
              f"glucose_risk={glucose_risk}, "
              f"is_high_utilizer={is_high_utilizer}, "
              f"diagnosis_count={diagnosis_count}")

        # ── Step 5: Predict ─────────────────────────────────────────────
        prob = float(clf.predict_proba(row)[0][1]) \
               if hasattr(clf, "predict_proba") else None
        pred = int(clf.predict(row)[0])

        score      = prob if prob is not None else float(pred)
        risk_level = "High Risk"   if score > 0.7  \
                else "Medium Risk" if score > 0.5 \
                else "Low Risk"

        result = {
            "prediction":  pred,
            "probability": round(prob * 100, 1)
                           if prob is not None else None,
            "risk_level":  risk_level,
            "model_used":  MODELS[model_key]["name"],
            "engineered": {
                "total_visits":     int(total_visits),
                "age_risk":         age_risk,
                "glucose_risk":     glucose_risk,
                "is_high_utilizer": is_high_utilizer,
                "diagnosis_count":  diagnosis_count
            },
            "input": input_data
        }
        _prediction_history.append(result)
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def get_prediction_history():
    return list(reversed(_prediction_history))