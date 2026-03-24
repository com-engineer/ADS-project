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
# ── Run App ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)