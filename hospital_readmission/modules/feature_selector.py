import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from modules.feature_engineer import get_fe_df

_fs_pipeline = {
    "current": None,
    "step": 0,
    "selected_features": [],
    "dropped_features": []
}

def init_fs():
    df = get_fe_df().copy()
    if df is None:
        return {"error": "Run Feature Engineering first"}
    _fs_pipeline["current"] = df
    _fs_pipeline["step"] = 0
    _fs_pipeline["selected_features"] = []
    _fs_pipeline["dropped_features"] = []
    return get_fs_state()

def get_fs_state():
    df = _fs_pipeline["current"]
    if df is None:
        return {"step": 0, "rows": 0, "cols": 0, "dropped": 0}
    return {
        "step": _fs_pipeline["step"],
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "dropped": len(_fs_pipeline["dropped_features"])
    }

def _snap(df):
    return {"rows": int(df.shape[0]), "cols": int(df.shape[1])}

def fs_step1_correlation_filter(threshold=0.85):
    df = _fs_pipeline["current"].copy()
    before = _snap(df)

    numeric = df.select_dtypes(include=np.number)
    if "readmitted" in numeric.columns:
        numeric = numeric.drop(columns=["readmitted"])

    corr_matrix = numeric.corr().abs()
    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )
    to_drop = [col for col in upper.columns if any(upper[col] > threshold)]

    # build pairs for display
    pairs = []
    for col in to_drop:
        correlated_with = upper.index[upper[col] > threshold].tolist()
        for other in correlated_with:
            pairs.append({
                "col": col,
                "correlated_with": other,
                "value": round(float(upper.loc[other, col]), 3)
            })

    if to_drop:
        df.drop(columns=to_drop, inplace=True)

    _fs_pipeline["current"] = df
    _fs_pipeline["dropped_features"].extend(to_drop)
    _fs_pipeline["step"] = max(_fs_pipeline["step"], 1)

    return {
        "step": 1,
        "title": "Correlation filter",
        "before": before,
        "after": _snap(df),
        "detail": {
            "threshold": threshold,
            "dropped": to_drop if to_drop else [],
            "pairs": pairs,
            "kept": int(df.shape[1])
        }
    }

def fs_step2_importance_ranking():
    df = _fs_pipeline["current"].copy()
    before = _snap(df)

    if "readmitted" not in df.columns:
        return {"error": "Target column missing"}

    X = df.drop(columns=["readmitted"]).select_dtypes(include=np.number)
    y = df["readmitted"]

    rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(X, y)

    importances = pd.Series(rf.feature_importances_, index=X.columns)
    importances = importances.sort_values(ascending=False)

    _fs_pipeline["step"] = max(_fs_pipeline["step"], 2)

    return {
        "step": 2,
        "title": "Feature importance ranking",
        "before": before,
        "after": _snap(df),
        "detail": {
            "features": list(importances.index),
            "importances": [round(float(v), 4) for v in importances.values],
            "top5": list(importances.head(5).index)
        }
    }

def fs_step3_select_k_best(k=15):
    df = _fs_pipeline["current"].copy()
    before = _snap(df)

    if "readmitted" not in df.columns:
        return {"error": "Target column missing"}

    X = df.drop(columns=["readmitted"]).select_dtypes(include=np.number)
    y = df["readmitted"]

    k = min(k, X.shape[1])
    selector = SelectKBest(score_func=f_classif, k=k)
    selector.fit(X, y)

    scores = pd.Series(selector.scores_, index=X.columns)
    scores = scores.sort_values(ascending=False)

    selected = list(X.columns[selector.get_support()])
    dropped  = [c for c in X.columns if c not in selected]

    keep_cols = selected + ["readmitted"]
    df = df[keep_cols]

    _fs_pipeline["current"] = df
    _fs_pipeline["dropped_features"].extend(dropped)
    _fs_pipeline["step"] = max(_fs_pipeline["step"], 3)

    return {
        "step": 3,
        "title": f"SelectKBest (top {k} features)",
        "before": before,
        "after": _snap(df),
        "detail": {
            "k": k,
            "selected": selected,
            "dropped": dropped,
            "scores": {col: round(float(scores[col]), 2)
                      for col in scores.index[:10]}
        }
    }

def fs_step4_manual_drop(cols_to_drop):
    df = _fs_pipeline["current"].copy()
    before = _snap(df)

    existing = [c for c in cols_to_drop if c in df.columns and c != "readmitted"]
    if existing:
        df.drop(columns=existing, inplace=True)

    _fs_pipeline["current"] = df
    _fs_pipeline["dropped_features"].extend(existing)
    _fs_pipeline["step"] = max(_fs_pipeline["step"], 4)

    return {
        "step": 4,
        "title": "Manual feature drop",
        "before": before,
        "after": _snap(df),
        "detail": {
            "dropped": existing,
            "remaining": list(df.columns)
        }
    }

def get_fs_df():
    return _fs_pipeline["current"]

def get_final_features():
    df = _fs_pipeline["current"]
    if df is None:
        return []
    return [c for c in df.columns if c != "readmitted"]