import pandas as pd
import numpy as np
from modules.preprocessor import get_processed_df, _pipeline

AGE_RISK = {
    0: 1, 1: 1, 2: 2, 3: 2, 4: 3,
    5: 4, 6: 5, 7: 5, 8: 4, 9: 3
}

_fe_pipeline = {
    "current": None,
    "step": 0
}

def init_fe():
    df = get_processed_df().copy()
    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = 0

def get_fe_state():
    df = _fe_pipeline["current"]
    if df is None:
        return {"step": 0, "rows": 0, "cols": 0, "new_features": 0}
    return {
        "step": _fe_pipeline["step"],
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "new_features": _fe_pipeline["step"]
    }

def _snap(df):
    return {"rows": int(df.shape[0]), "cols": int(df.shape[1])}

def fe_step1_total_visits():
    df = _fe_pipeline["current"].copy()
    before = _snap(df)
    cols = ["number_outpatient","number_emergency","number_inpatient"]
    existing = [c for c in cols if c in df.columns]
    df["total_visits"] = df[existing].sum(axis=1)
    sample = df["total_visits"].value_counts().head(5)
    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 1)
    return {
        "step": 1, "title": "Total visits",
        "before": before, "after": _snap(df),
        "detail": {
            "new_col": "total_visits",
            "formula": "number_outpatient + number_emergency + number_inpatient",
            "min": round(float(df["total_visits"].min()), 2),
            "max": round(float(df["total_visits"].max()), 2),
            "mean": round(float(df["total_visits"].mean()), 2),
            "sample": {str(k): int(v) for k, v in sample.items()}
        }
    }

def fe_step2_age_risk():
    df = _fe_pipeline["current"].copy()
    before = _snap(df)
    if "age" in df.columns:
        df["age_risk"] = df["age"].map(AGE_RISK).fillna(3).astype(int)
    sample = df["age_risk"].value_counts().to_dict() if "age_risk" in df.columns else {}
    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 2)
    return {
        "step": 2, "title": "Age risk score",
        "before": before, "after": _snap(df),
        "detail": {
            "new_col": "age_risk",
            "mapping": "Age group → risk (1=low … 5=high)",
            "distribution": {str(k): int(v) for k, v in sample.items()}
        }
    }

def fe_step3_glucose_risk():
    df = _fe_pipeline["current"].copy()
    before = _snap(df)
    col = "max_glu_serum" if "max_glu_serum" in df.columns else None
    if col:
        mapping = {">300": 3, ">200": 2, "Norm": 1, "None": 0}
        df["glucose_risk"] = df[col].astype(str).map(mapping).fillna(0).astype(int)
    else:
        df["glucose_risk"] = 0
    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 3)
    dist = df["glucose_risk"].value_counts().to_dict()
    return {
        "step": 3, "title": "Glucose risk score",
        "before": before, "after": _snap(df),
        "detail": {
            "new_col": "glucose_risk",
            "mapping": {"None/missing": 0, "Normal": 1, ">200": 2, ">300": 3},
            "distribution": {str(k): int(v) for k, v in dist.items()}
        }
    }

def fe_step4_high_utilizer():
    df = _fe_pipeline["current"].copy()
    before = _snap(df)
    col = "total_visits" if "total_visits" in df.columns else None
    threshold = 3
    if col:
        df["is_high_utilizer"] = (df[col] > threshold).astype(int)
    else:
        df["is_high_utilizer"] = 0
    dist = df["is_high_utilizer"].value_counts().to_dict()
    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 4)
    return {
        "step": 4, "title": "High utilizer flag",
        "before": before, "after": _snap(df),
        "detail": {
            "new_col": "is_high_utilizer",
            "rule": f"total_visits > {threshold} → 1 else 0",
            "distribution": {str(k): int(v) for k, v in dist.items()}
        }
    }

def fe_step5_diagnosis_count():
    df = _fe_pipeline["current"].copy()
    before = _snap(df)
    diag_cols = [c for c in ["diag_1","diag_2","diag_3"] if c in df.columns]
    if diag_cols:
        df["diagnosis_count"] = df[diag_cols].notna().sum(axis=1)
    else:
        df["diagnosis_count"] = 0
    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 5)
    dist = df["diagnosis_count"].value_counts().to_dict()
    return {
        "step": 5, "title": "Diagnosis count",
        "before": before, "after": _snap(df),
        "detail": {
            "new_col": "diagnosis_count",
            "formula": "count of non-null values across diag_1, diag_2, diag_3",
            "distribution": {str(k): int(v) for k, v in dist.items()}
        }
    }

def fe_step6_drop_low_value():
    df = _fe_pipeline["current"].copy()
    before = _snap(df)
    to_drop = []
    for col in df.columns:
        if df[col].nunique() <= 1:
            to_drop.append(col)
    low_var = []
    for col in df.select_dtypes(include=np.number).columns:
        if df[col].std() < 0.01:
            low_var.append(col)
    to_drop = list(set(to_drop + low_var))
    if to_drop:
        df.drop(columns=to_drop, inplace=True)
    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 6)
    return {
        "step": 6, "title": "Drop low-value columns",
        "before": before, "after": _snap(df),
        "detail": {
            "dropped": to_drop if to_drop else ["None — all columns retained"],
            "reason": "Columns with zero/near-zero variance add noise without signal"
        }
    }

def get_fe_df():
    return _fe_pipeline["current"]

def get_feature_list():
    df = _fe_pipeline["current"]
    if df is None:
        return []
    return list(df.columns)