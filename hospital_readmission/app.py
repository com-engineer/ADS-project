from flask import Flask, jsonify, render_template, request
from modules.data_loader import load_data
from modules.eda import (
    get_overview, get_missing, get_column_distribution,
    get_statistics, get_correlation, get_target_distribution,
    get_bivariate
)
from modules.preprocessor import (
    init_pipeline,
    step1_drop_columns, step2_fix_missing,
    step3_encode_target, step4_remove_duplicates,
    step5_encode_features, step6_scale_features,
    step7_handle_imbalance, get_pipeline_state
)

# ⭐ NEW: Feature Engineering imports
from modules.feature_engineer import (
    init_fe, get_fe_state, get_feature_list,
    fe_step1_total_visits, fe_step2_age_risk,
    fe_step3_glucose_risk, fe_step4_high_utilizer,
    fe_step5_diagnosis_count, fe_step6_drop_low_value
)

# ⭐ NEW: Feature selection imports
from modules.feature_selector import (
    init_fs, get_fs_state, get_final_features,
    fs_step1_correlation_filter, fs_step2_importance_ranking,
    fs_step3_select_k_best, fs_step4_manual_drop, get_fs_df
)

from modules.model import (
    split_data, train_model,
    get_all_results, get_best_model, get_model_state
)

from modules.evaluator import get_available_models, evaluate_model
app = Flask(__name__)

# Load dataset
df = load_data(path="data/diabetes.csv")
init_pipeline(df)

# ── Root ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── EDA ─────────────────────────────────────────────────────────────────
@app.route("/api/overview")
def overview():
    return jsonify(get_overview(df))

@app.route("/api/columns")
def columns():
    return jsonify({"columns": list(df.columns)})

@app.route("/api/missing")
def missing():
    return jsonify(get_missing(df))

@app.route("/api/distribution/<column>")
def distribution(column):
    return jsonify(get_column_distribution(df, column))

@app.route("/api/statistics/<column>")
def statistics(column):
    return jsonify(get_statistics(df, column))

@app.route("/api/correlation")
def correlation():
    return jsonify(get_correlation(df))

@app.route("/api/target")
def target():
    return jsonify(get_target_distribution(df))

@app.route("/api/bivariate")
def bivariate():
    x = request.args.get("x")
    y = request.args.get("y")
    return jsonify(get_bivariate(df, x, y))

# ── Preprocessing ───────────────────────────────────────────────────────
@app.route("/api/preprocess/state")
def preprocess_state():
    return jsonify(get_pipeline_state())

@app.route("/api/preprocess/reset", methods=["POST"])
def preprocess_reset():
    init_pipeline(df)
    return jsonify({"status": "reset"})

@app.route("/api/preprocess/step/1", methods=["POST"])
def ps1():
    return jsonify(step1_drop_columns())

@app.route("/api/preprocess/step/2", methods=["POST"])
def ps2():
    return jsonify(step2_fix_missing())

@app.route("/api/preprocess/step/3", methods=["POST"])
def ps3():
    return jsonify(step3_encode_target())

@app.route("/api/preprocess/step/4", methods=["POST"])
def ps4():
    return jsonify(step4_remove_duplicates())

@app.route("/api/preprocess/step/5", methods=["POST"])
def ps5():
    return jsonify(step5_encode_features())

@app.route("/api/preprocess/step/6", methods=["POST"])
def ps6():
    return jsonify(step6_scale_features())

@app.route("/api/preprocess/step/7", methods=["POST"])
def ps7():
    return jsonify(step7_handle_imbalance())

# ── Feature Engineering ────────────────────────────────────────────────

# Feature Engineering
@app.route("/api/fe/init", methods=["POST"])
def fe_init():
    init_fe()
    return jsonify(get_fe_state())

@app.route("/api/fe/state")
def fe_state():
    return jsonify(get_fe_state())

@app.route("/api/fe/features")
def fe_features():
    return jsonify({"features": get_feature_list()})

@app.route("/api/fe/step/1", methods=["POST"])
def fe1(): return jsonify(fe_step1_total_visits())

@app.route("/api/fe/step/2", methods=["POST"])
def fe2(): return jsonify(fe_step2_age_risk())

@app.route("/api/fe/step/3", methods=["POST"])
def fe3(): return jsonify(fe_step3_glucose_risk())

@app.route("/api/fe/step/4", methods=["POST"])
def fe4(): return jsonify(fe_step4_high_utilizer())

@app.route("/api/fe/step/5", methods=["POST"])
def fe5(): return jsonify(fe_step5_diagnosis_count())

@app.route("/api/fe/step/6", methods=["POST"])
def fe6(): return jsonify(fe_step6_drop_low_value())

# Feature Selection
@app.route("/api/fs/init", methods=["POST"])
def fs_init():
    return jsonify(init_fs())

@app.route("/api/fs/state")
def fs_state():
    return jsonify(get_fs_state())

@app.route("/api/fs/features")
def fs_features():
    return jsonify({"features": get_final_features()})

@app.route("/api/fs/step/1", methods=["POST"])
def fss1(): return jsonify(fs_step1_correlation_filter())

@app.route("/api/fs/correlation")
def fs_correlation():
    from modules.feature_selector import get_fs_df
    import numpy as np
    df = get_fs_df()
    if df is None:
        return jsonify({"columns": [], "matrix": []})
    numeric = df.select_dtypes(include=np.number)
    if "readmitted" in numeric.columns:
        numeric = numeric.drop(columns=["readmitted"])
    corr = numeric.corr().round(3)
    return jsonify({
        "columns": list(corr.columns),
        "matrix": corr.values.tolist()
    })

@app.route("/api/fs/importance")
def fs_importance():
    from modules.feature_selector import get_fs_df
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np
    df = get_fs_df()
    if df is None or "readmitted" not in df.columns:
        return jsonify({"features": [], "importances": []})
    X = df.drop(columns=["readmitted"]).select_dtypes(include=np.number)
    y = df["readmitted"]
    rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    import pandas as pd
    imp = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    return jsonify({
        "features": list(imp.index),
        "importances": [round(float(v), 4) for v in imp.values]
    })

@app.route("/api/fs/step/2", methods=["POST"])
def fss2(): return jsonify(fs_step2_importance_ranking())

@app.route("/api/fs/step/3", methods=["POST"])
def fss3():
    k = int(request.args.get("k", 15))
    return jsonify(fs_step3_select_k_best(k))

@app.route("/api/fs/step/4", methods=["POST"])
def fss4():
    cols = request.json.get("cols", [])
    return jsonify(fs_step4_manual_drop(cols))

# Model Training
@app.route("/api/model/state")
def model_state():
    return jsonify(get_model_state())

@app.route("/api/model/split", methods=["POST"])
def model_split():
    test_size = float(request.json.get("test_size", 0.2))
    return jsonify(split_data(test_size))

@app.route("/api/model/train/<model_key>", methods=["POST"])
def model_train(model_key):
    return jsonify(train_model(model_key))

@app.route("/api/model/results")
def model_results():
    return jsonify(get_all_results())

@app.route("/api/model/best")
def model_best():
    return jsonify(get_best_model())


# Evaluation
@app.route("/api/eval/models")
def eval_models():
    return jsonify(get_available_models())

@app.route("/api/eval/<model_key>")
def eval_model(model_key):
    return jsonify(evaluate_model(model_key))

# ── Run App ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)