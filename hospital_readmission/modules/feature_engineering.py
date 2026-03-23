import pandas as pd
import numpy as np
from modules.preprocessor import get_processed_df

# ── Global state ──────────────────────────────────────────────────────────
_fe_pipeline = {
    "current": None,
    "step": 0
}


def init_fe_pipeline():
    df = get_processed_df().copy()
    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = 0


def _snapshot(df):
    result = {"rows": int(df.shape[0]), "cols": int(df.shape[1])}
    if "readmitted" in df.columns:
        vc = df["readmitted"].value_counts()
        result["target"] = {str(k): int(v) for k, v in vc.items()}
    return result


# ── Step 1: Create new features ──────────────────────────────────────────
def step1_create_features():
    df = _fe_pipeline["current"].copy()
    before = _snapshot(df)
    created = []

    # Total visits
    if all(col in df.columns for col in [
        "number_outpatient", "number_emergency", "number_inpatient"
    ]):
        df["total_visits"] = (
            df["number_outpatient"] +
            df["number_emergency"] +
            df["number_inpatient"]
        )
        created.append("total_visits")

    # Medication intensity (binned)
    if "num_medications" in df.columns:
        df["med_intensity"] = pd.cut(
            df["num_medications"],
            bins=[-1, 10, 20, 50],
            labels=[0, 1, 2]
        ).astype(int)
        created.append("med_intensity")

    # High admission flag
    if "time_in_hospital" in df.columns:
        df["long_stay"] = (df["time_in_hospital"] > df["time_in_hospital"].mean()).astype(int)
        created.append("long_stay")

    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 1)

    return {
        "step": 1,
        "title": "Create new features",
        "before": before,
        "after": _snapshot(df),
        "detail": {
            "created_features": created
        }
    }


# ── Step 2: Binning / transformation ─────────────────────────────────────
def step2_binning():
    df = _fe_pipeline["current"].copy()
    before = _snapshot(df)
    transformed = []

    # Binning number of diagnoses
    if "number_diagnoses" in df.columns:
        df["diag_group"] = pd.cut(
            df["number_diagnoses"],
            bins=[-1, 3, 6, 20],
            labels=[0, 1, 2]
        ).astype(int)
        transformed.append("diag_group")

    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 2)

    return {
        "step": 2,
        "title": "Binning features",
        "before": before,
        "after": _snapshot(df),
        "detail": {
            "transformed": transformed
        }
    }


# ── Step 3: Remove highly correlated features ────────────────────────────
def step3_remove_correlation():
    df = _fe_pipeline["current"].copy()
    before = _snapshot(df)

    corr = df.corr(numeric_only=True).abs()

    upper = corr.where(
        np.triu(np.ones(corr.shape), k=1).astype(bool)
    )

    to_drop = [col for col in upper.columns if any(upper[col] > 0.9)]

    df.drop(columns=to_drop, inplace=True)

    _fe_pipeline["current"] = df
    _fe_pipeline["step"] = max(_fe_pipeline["step"], 3)

    return {
        "step": 3,
        "title": "Remove highly correlated features",
        "before": before,
        "after": _snapshot(df),
        "detail": {
            "dropped": to_drop,
            "threshold": "0.9"
        }
    }


# ── Step 4: Final feature set (X, y split info only) ──────────────────────
def step4_prepare_xy():
    df = _fe_pipeline["current"].copy()
    before = _snapshot(df)

    if "readmitted" not in df.columns:
        return {"error": "Target column not found"}

    X = df.drop(columns=["readmitted"])
    y = df["readmitted"]

    _fe_pipeline["step"] = max(_fe_pipeline["step"], 4)

    return {
        "step": 4,
        "title": "Prepare feature matrix",
        "before": before,
        "after": {
            "X_shape": [int(X.shape[0]), int(X.shape[1])],
            "y_shape": int(y.shape[0])
        },
        "detail": {
            "feature_columns": list(X.columns)
        }
    }


# ── Helpers ──────────────────────────────────────────────────────────────
def get_fe_df():
    return _fe_pipeline["current"]


def get_fe_state():
    df = _fe_pipeline["current"]
    return {
        "step": _fe_pipeline["step"],
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "missing": int(df.isnull().sum().sum())
    }