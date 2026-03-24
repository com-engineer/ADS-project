import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_curve, roc_auc_score,
    precision_score, recall_score,
    f1_score, accuracy_score
)
from modules.model import _model_state, MODELS

def get_available_models():
    return [
        {"key": k, "name": MODELS[k]["name"]}
        for k in _model_state["trained_models"]
    ]

def evaluate_model(model_key):
    if model_key not in _model_state["trained_models"]:
        return {"error": f"Model '{model_key}' not trained yet"}

    clf     = _model_state["trained_models"][model_key]
    X_test  = _model_state["X_test"]
    y_test  = _model_state["y_test"]
    X_train = _model_state["X_train"]
    y_train = _model_state["y_train"]
    features = _model_state["feature_names"]

    y_pred       = clf.predict(X_test)
    y_pred_proba = clf.predict_proba(X_test)[:, 1] \
                   if hasattr(clf, "predict_proba") else None

    # ── Confusion matrix ──
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    # ── Classification report ──
    report = classification_report(
        y_test, y_pred,
        target_names=["Not readmitted", "Readmitted"],
        output_dict=True
    )

    # ── ROC curve ──
    fpr_arr, tpr_arr, _ = roc_curve(y_test, y_pred_proba) \
        if y_pred_proba is not None else ([], [], [])
    auc = round(float(roc_auc_score(y_test, y_pred_proba)), 4) \
          if y_pred_proba is not None else None

    step = max(1, len(fpr_arr) // 60)
    fpr = [round(float(v), 4) for v in fpr_arr[::step]]
    tpr = [round(float(v), 4) for v in tpr_arr[::step]]

    # ── Feature importance ──
    importance = []
    if hasattr(clf, "feature_importances_"):
        imp = pd.Series(clf.feature_importances_, index=features)
        imp = imp.sort_values(ascending=False).head(15)
        importance = [
            {"feature": f, "importance": round(float(v), 4)}
            for f, v in imp.items()
        ]
    elif hasattr(clf, "coef_"):
        imp = pd.Series(np.abs(clf.coef_[0]), index=features)
        imp = imp.sort_values(ascending=False).head(15)
        importance = [
            {"feature": f, "importance": round(float(v), 4)}
            for f, v in imp.items()
        ]

    # ── Overfitting check ──
    train_acc = round(float(accuracy_score(y_train, clf.predict(X_train))), 4)
    test_acc  = round(float(accuracy_score(y_test, y_pred)), 4)
    overfit_gap = round(float(train_acc - test_acc), 4)

    return {
        "model_key":  model_key,
        "model_name": MODELS[model_key]["name"],
        "confusion_matrix": {
            "tn": int(tn), "fp": int(fp),
            "fn": int(fn), "tp": int(tp)
        },
        "metrics": {
            "accuracy":  round(float(accuracy_score(y_test, y_pred)), 4),
            "f1":        round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall":    round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "roc_auc":   auc,
            "train_acc": train_acc,
            "test_acc":  test_acc,
            "overfit_gap": overfit_gap
        },
        "classification_report": {
            "not_readmitted": {
                "precision": round(report["Not readmitted"]["precision"], 4),
                "recall":    round(report["Not readmitted"]["recall"], 4),
                "f1":        round(report["Not readmitted"]["f1-score"], 4),
                "support":   int(report["Not readmitted"]["support"])
            },
            "readmitted": {
                "precision": round(report["Readmitted"]["precision"], 4),
                "recall":    round(report["Readmitted"]["recall"], 4),
                "f1":        round(report["Readmitted"]["f1-score"], 4),
                "support":   int(report["Readmitted"]["support"])
            }
        },
        "roc_curve": {"fpr": fpr, "tpr": tpr, "auc": auc},
        "feature_importance": importance,
        "overfit": {
            "train_acc":    train_acc,
            "test_acc":     test_acc,
            "gap":          overfit_gap,
            "status": "Overfitting" if overfit_gap > 0.1
                      else "Slight overfit" if overfit_gap > 0.05
                      else "Good fit"
        }
    }