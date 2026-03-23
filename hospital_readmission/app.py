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
from modules.feature_engineering import (
    init_fe_pipeline,
    step1_create_features,
    step2_binning,
    step3_remove_correlation,
    step4_prepare_xy,
    get_fe_state
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

# Initialize Feature Engineering (must call after preprocessing)
@app.route("/api/feature/init", methods=["POST"])
def fe_init():
    init_fe_pipeline()
    return jsonify({"status": "Feature Engineering Initialized"})

# Get state
@app.route("/api/feature/state")
def fe_state():
    return jsonify(get_fe_state())

# Step 1: Create features
@app.route("/api/feature/step/1", methods=["POST"])
def fe_s1():
    return jsonify(step1_create_features())

# Step 2: Binning
@app.route("/api/feature/step/2", methods=["POST"])
def fe_s2():
    return jsonify(step2_binning())

# Step 3: Remove correlation
@app.route("/api/feature/step/3", methods=["POST"])
def fe_s3():
    return jsonify(step3_remove_correlation())

# Step 4: Prepare X, y
@app.route("/api/feature/step/4", methods=["POST"])
def fe_s4():
    return jsonify(step4_prepare_xy())

# ── Run App ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)