import numpy as np
import pandas as pd
import time
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, roc_auc_score, confusion_matrix, roc_curve
)
from modules.feature_selector import get_fs_df

_model_state = {
    "X_train": None, "X_test": None,
    "y_train": None, "y_test": None,
    "feature_names": [],
    "trained_models": {},
    "results": {},
    "split_ratio": 0.2
}

MODELS = {
    "logistic_regression": {
        "name": "Logistic Regression",
        "cls": LogisticRegression,
        "params": {"max_iter": 1000, "random_state": 42}
    },
    "decision_tree": {
        "name": "Decision Tree",
        "cls": DecisionTreeClassifier,
        "params": {"random_state": 42, "max_depth": 10}
    },
    "random_forest": {
        "name": "Random Forest",
        "cls": RandomForestClassifier,
        "params": {"n_estimators": 100, "random_state": 42, "n_jobs": -1}
    }
}

try:
    from xgboost import XGBClassifier
    MODELS["xgboost"] = {
        "name": "XGBoost",
        "cls": XGBClassifier,
        "params": {
            "n_estimators": 100, "random_state": 42,
            "eval_metric": "logloss", "verbosity": 0
        }
    }
except ImportError:
    pass


def split_data(test_size=0.2):
    df = get_fs_df()
    if df is None:
        return {"error": "Run Feature Selection first"}

    if "readmitted" not in df.columns:
        return {"error": "Target column not found"}

    X = df.drop(columns=["readmitted"]).select_dtypes(include=np.number)
    y = df["readmitted"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    _model_state["X_train"]       = X_train
    _model_state["X_test"]        = X_test
    _model_state["y_train"]       = y_train
    _model_state["y_test"]        = y_test
    _model_state["feature_names"] = list(X.columns)
    _model_state["split_ratio"]   = test_size

    train_dist = y_train.value_counts().to_dict()
    test_dist  = y_test.value_counts().to_dict()

    return {
        "status": "success",
        "total_rows":   int(len(X)),
        "train_rows":   int(len(X_train)),
        "test_rows":    int(len(X_test)),
        "features":     int(X.shape[1]),
        "train_dist":   {str(k): int(v) for k, v in train_dist.items()},
        "test_dist":    {str(k): int(v) for k, v in test_dist.items()},
        "feature_names": list(X.columns)
    }


def train_model(model_key):
    if _model_state["X_train"] is None:
        return {"error": "Split data first"}

    if model_key not in MODELS:
        return {"error": f"Unknown model: {model_key}"}

    X_train = _model_state["X_train"]
    X_test  = _model_state["X_test"]
    y_train = _model_state["y_train"]
    y_test  = _model_state["y_test"]

    model_info = MODELS[model_key]
    clf = model_info["cls"](**model_info["params"])

    start = time.time()
    clf.fit(X_train, y_train)
    train_time = round(time.time() - start, 2)

    y_pred       = clf.predict(X_test)
    y_pred_proba = clf.predict_proba(X_test)[:, 1] \
                   if hasattr(clf, "predict_proba") else None

    acc       = round(float(accuracy_score(y_test, y_pred)), 4)
    f1        = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)
    precision = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
    recall    = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)
    roc_auc   = round(float(roc_auc_score(y_test, y_pred_proba)), 4) \
                if y_pred_proba is not None else None

    train_acc = round(float(accuracy_score(y_train, clf.predict(X_train))), 4)

    cm = confusion_matrix(y_test, y_pred).tolist()

    fpr, tpr, roc_thresh = [], [], []
    if y_pred_proba is not None:
        fpr_arr, tpr_arr, _ = roc_curve(y_test, y_pred_proba)
        fpr = [round(float(v), 4) for v in fpr_arr[::5]]
        tpr = [round(float(v), 4) for v in tpr_arr[::5]]

    result = {
        "model_key":  model_key,
        "model_name": model_info["name"],
        "train_time": train_time,
        "train_acc":  train_acc,
        "accuracy":   acc,
        "f1":         f1,
        "precision":  precision,
        "recall":     recall,
        "roc_auc":    roc_auc,
        "confusion_matrix": cm,
        "roc_curve":  {"fpr": fpr, "tpr": tpr}
    }

    _model_state["trained_models"][model_key] = clf
    _model_state["results"][model_key]        = result
    return result


def get_all_results():
    return list(_model_state["results"].values())


def get_best_model():
    if not _model_state["results"]:
        return None
    return max(
        _model_state["results"].values(),
        key=lambda r: r["roc_auc"] or r["accuracy"]
    )


def get_model_state():
    return {
        "split_done":    _model_state["X_train"] is not None,
        "models_trained": list(_model_state["trained_models"].keys()),
        "results_count": len(_model_state["results"])
    }