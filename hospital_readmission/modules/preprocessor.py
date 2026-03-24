import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ── Global state: pipeline stages ──────────────────────────────────────────
_pipeline = {
    "original": None,   # raw loaded df
    "current":  None,   # df after latest applied step
    "step":     0,      # last completed step index (0 = none)
    "scaler":   None,
    "encoders": {}
}

NUMERIC_COLS = [
    "time_in_hospital", "num_lab_procedures", "num_procedures",
    "num_medications", "number_outpatient", "number_emergency",
    "number_inpatient", "number_diagnoses"
]

AGE_ORDER = [
    "[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)",
    "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"
]

COLS_TO_DROP = ["weight", "payer_code", "encounter_id", "patient_nbr"]

CAT_COLS = ["race", "gender", "medical_specialty",
            "diag_1", "diag_2", "diag_3", "change", "diabetesMed"]


def init_pipeline(df: pd.DataFrame):
    _pipeline["original"] = df.copy()
    _pipeline["current"]  = df.copy()
    _pipeline["step"]     = 0
    _pipeline["scaler"]   = None
    _pipeline["encoders"] = {}


def _snapshot(df):
    """Return quick shape + target balance for before/after cards."""
    result = {"rows": int(df.shape[0]), "cols": int(df.shape[1])}
    if "readmitted" in df.columns:
        vc = df["readmitted"].value_counts()
        result["target"] = {str(k): int(v) for k, v in vc.items()}
    return result


# ── Step 1 : Drop useless columns ──────────────────────────────────────────
def step1_drop_columns():
    df = _pipeline["current"].copy()
    before = _snapshot(df)

    existing = [c for c in COLS_TO_DROP if c in df.columns]
    df.drop(columns=existing, inplace=True)

    _pipeline["current"] = df
    _pipeline["step"] = max(_pipeline["step"], 1)

    return {
        "step": 1,
        "title": "Drop useless columns",
        "before": before,
        "after": _snapshot(df),
        "detail": {
            "dropped": existing,
            "reason": "High missing % or are identifiers with no predictive value"
        }
    }


# ── Step 2 : Handle missing values ─────────────────────────────────────────
def step2_fix_missing():
    df = _pipeline["current"].copy()
    before = _snapshot(df)
    filled = {}

    if "race" in df.columns:
        n = int(df["race"].isnull().sum())
        # df["race"].fillna(df["race"].mode()[0], inplace=True)
        df["race"] = df["race"].fillna(df["race"].mode()[0])
        filled["race"] = {"count": n, "strategy": "mode"}

    if "medical_specialty" in df.columns:
        n = int(df["medical_specialty"].isnull().sum())
        # df["medical_specialty"].fillna("Unknown", inplace=True)
        df["medical_specialty"] = df["medical_specialty"].fillna("Unknown")

        filled["medical_specialty"] = {"count": n, "strategy": "Unknown"}

    if "diag_1" in df.columns:
        n = int(df["diag_1"].isnull().sum())
        df.dropna(subset=["diag_1"], inplace=True)
        filled["diag_1"] = {"count": n, "strategy": "drop rows"}

    _pipeline["current"] = df.reset_index(drop=True)
    _pipeline["step"] = max(_pipeline["step"], 2)

    return {
        "step": 2,
        "title": "Handle missing values",
        "before": before,
        "after": _snapshot(df),
        "detail": {"filled": filled}
    }


# ── Step 3 : Encode target variable ────────────────────────────────────────
def step3_encode_target():
    df = _pipeline["current"].copy()
    before = _snapshot(df)

    if "readmitted" in df.columns:
        before_dist = df["readmitted"].value_counts().to_dict()
        df["readmitted"] = (df["readmitted"] == "<30").astype(int)
        after_dist = df["readmitted"].value_counts().to_dict()
    else:
        before_dist, after_dist = {}, {}

    _pipeline["current"] = df
    _pipeline["step"] = max(_pipeline["step"], 3)

    return {
        "step": 3,
        "title": "Encode target variable",
        "before": before,
        "after": _snapshot(df),
        "detail": {
            "before_dist": {str(k): int(v) for k, v in before_dist.items()},
            "after_dist":  {str(k): int(v) for k, v in after_dist.items()},
            "mapping": {"<30": 1, ">30": 0, "NO": 0}
        }
    }


# ── Step 4 : Remove duplicates ─────────────────────────────────────────────
def step4_remove_duplicates():
    df = _pipeline["current"].copy()
    before = _snapshot(df)
    rows_before = len(df)

    df.drop_duplicates(inplace=True)
    rows_after = len(df)

    _pipeline["current"] = df.reset_index(drop=True)
    _pipeline["step"] = max(_pipeline["step"], 4)

    return {
        "step": 4,
        "title": "Remove duplicate rows",
        "before": before,
        "after": _snapshot(df),
        "detail": {
            "removed": rows_before - rows_after,
            "remaining": rows_after
        }
    }


# ── Step 5 : Encode categorical features ───────────────────────────────────
def step5_encode_features():
    df = _pipeline["current"].copy()
    before = _snapshot(df)
    encoded = {}

    # Ordinal encode age
    if "age" in df.columns:
        age_map = {v: i for i, v in enumerate(AGE_ORDER)}
        df["age"] = df["age"].map(age_map).fillna(5).astype(int)
        encoded["age"] = "ordinal (0-9)"

    # Label encode remaining cat cols
    for col in CAT_COLS:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            _pipeline["encoders"][col] = le
            encoded[col] = f"label encoded ({df[col].nunique()} classes)"

    _pipeline["current"] = df
    _pipeline["step"] = max(_pipeline["step"], 5)

    return {
        "step": 5,
        "title": "Encode categorical features",
        "before": before,
        "after": _snapshot(df),
        "detail": {"encoded_columns": encoded}
    }


# ── Step 6 : Scale numeric features ────────────────────────────────────────
def step6_scale_features():
    df = _pipeline["current"].copy()
    before = _snapshot(df)

    existing = [c for c in NUMERIC_COLS if c in df.columns]
    stats_before = {c: round(float(df[c].mean()), 3) for c in existing}

    scaler = StandardScaler()
    df[existing] = scaler.fit_transform(df[existing])
    _pipeline["scaler"] = scaler

    stats_after = {c: round(float(df[c].mean()), 3) for c in existing}

    _pipeline["current"] = df
    _pipeline["step"] = max(_pipeline["step"], 6)

    return {
        "step": 6,
        "title": "Scale numeric features",
        "before": before,
        "after": _snapshot(df),
        "detail": {
            "scaled_columns": existing,
            "mean_before": stats_before,
            "mean_after": stats_after
        }
    }


# ── Step 7 : Handle class imbalance (undersample majority) ─────────────────
def step7_handle_imbalance():
    df = _pipeline["current"].copy()
    before = _snapshot(df)

    if "readmitted" not in df.columns:
        return {"error": "Target column not found"}

    vc = df["readmitted"].value_counts()
    before_dist = {str(k): int(v) for k, v in vc.items()}

    minority_count = int(vc.min())
    majority_class = int(vc.idxmax())
    minority_class = int(vc.idxmin())

    df_maj = df[df["readmitted"] == majority_class].sample(
        n=minority_count * 2, random_state=42
    )
    df_min = df[df["readmitted"] == minority_class]
    df = pd.concat([df_maj, df_min]).sample(frac=1, random_state=42).reset_index(drop=True)

    after_dist = {str(k): int(v) for k, v in df["readmitted"].value_counts().items()}

    _pipeline["current"] = df
    _pipeline["step"] = max(_pipeline["step"], 7)

    return {
        "step": 7,
        "title": "Handle class imbalance",
        "before": before,
        "after": _snapshot(df),
        "detail": {
            "strategy": "Undersample majority class (2:1 ratio)",
            "before_dist": before_dist,
            "after_dist": after_dist
        }
    }


def get_processed_df():
    return _pipeline["current"]


def get_pipeline_state():
    df = _pipeline["current"]
    return {
        "step": _pipeline["step"],
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "missing": int(df.isnull().sum().sum())
    }