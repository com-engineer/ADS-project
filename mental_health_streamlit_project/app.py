import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

st.set_page_config(layout="wide")

# ---------- TITLE ----------
st.title("AI-Based Digital Wellbeing Decision Support System")

# ---------- NAVBAR ----------
tabs = st.tabs(["Data Overview", "EDA", "Visualization", "Model", "Prediction"])

df = None

# ---------- LOAD DATA ----------
file = st.file_uploader("Upload Dataset", type=["csv"])

if file:
    df = pd.read_csv(file)

    # Drop ID columns
    df = df.drop(columns=[col for col in df.columns if "id" in col.lower()], errors='ignore')

    # Handle missing values
    df = df.fillna(df.mean(numeric_only=True))

    # Encode categorical columns
    df = pd.get_dummies(df, drop_first=True)

# ---------- TAB 1: DATA OVERVIEW ----------
with tabs[0]:
    if df is not None:
        st.subheader("Dataset Preview")
        st.write(df.head())
        st.write("Shape:", df.shape)

# ---------- TAB 2: EDA ----------
with tabs[1]:
    if df is not None:
        st.subheader("Statistical Analysis")

        st.write("Mean")
        st.write(df.mean())

        st.write("Median")
        st.write(df.median())

        st.write("Standard Deviation")
        st.write(df.std())

        st.write("Skewness")
        st.write(df.skew())

# ---------- TAB 3: VISUALIZATION ----------
with tabs[2]:
    if df is not None:
        st.subheader("Visualization")

        cols = df.columns

        plot_type = st.selectbox("Select Plot", ["Histogram", "Scatter", "Heatmap"])

        if plot_type == "Histogram":
            col = st.selectbox("Column", cols)
            fig, ax = plt.subplots()
            sns.histplot(df[col], ax=ax)
            st.pyplot(fig)

        elif plot_type == "Scatter":
            x = st.selectbox("X-axis", cols)
            y = st.selectbox("Y-axis", cols)
            fig, ax = plt.subplots()
            sns.scatterplot(x=df[x], y=df[y], ax=ax)
            st.pyplot(fig)

        elif plot_type == "Heatmap":
            fig, ax = plt.subplots()
            sns.heatmap(df.corr(), annot=True, ax=ax)
            st.pyplot(fig)

# ---------- TAB 4: MODEL ----------
with tabs[3]:
    if df is not None:
        st.subheader("Model Training")

        target = "Happiness_Index(1-10)" if "Happiness_Index(1-10)" in df.columns else df.columns[-1]
        st.write(f"Target Variable: {target}")

        X = df.drop(target, axis=1)
        y = df[target]

        # Train/Test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        model = LinearRegression()

        # -------- TRAIN BUTTON --------
        if st.button("Train Model"):
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            # Save everything
            st.session_state["model"] = model
            st.session_state["features"] = X.columns
            st.session_state["y_test"] = y_test
            st.session_state["y_pred"] = y_pred

            st.success("Model Trained Successfully")

        # -------- AFTER TRAINING --------
        if "y_pred" in st.session_state:

            y_test = st.session_state["y_test"]
            y_pred = st.session_state["y_pred"]

            st.subheader("Model Performance Metrics")

            r2 = r2_score(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(y_test - y_pred))

            # Accuracy (approx for regression)
            accuracy = 100 - (mae * 10)

            st.write(f"R² Score: {round(r2,3)}")
            st.write(f"MSE: {round(mse,3)}")
            st.write(f"RMSE: {round(rmse,3)}")
            st.write(f"MAE: {round(mae,3)}")
            st.write(f"Accuracy (approx): {round(accuracy,2)} %")

            # -------- GRAPH SELECT --------
            st.subheader("Evaluation Graphs")

            graph_type = st.selectbox(
                "Select Graph",
                ["Actual vs Predicted", "Residual Plot", "Error Distribution", "Line Plot"]
            )

            # -------- GRAPHS --------
            if graph_type == "Actual vs Predicted":
                fig, ax = plt.subplots()
                ax.scatter(y_test, y_pred)
                ax.set_xlabel("Actual")
                ax.set_ylabel("Predicted")
                ax.set_title("Actual vs Predicted")
                st.pyplot(fig)

            elif graph_type == "Residual Plot":
                residuals = y_test - y_pred
                fig, ax = plt.subplots()
                ax.scatter(y_pred, residuals)
                ax.axhline(0)
                ax.set_xlabel("Predicted")
                ax.set_ylabel("Residuals")
                ax.set_title("Residual Plot")
                st.pyplot(fig)

            elif graph_type == "Error Distribution":
                errors = y_test - y_pred
                fig, ax = plt.subplots()
                sns.histplot(errors, kde=True, ax=ax)
                ax.set_title("Error Distribution")
                st.pyplot(fig)

            elif graph_type == "Line Plot":
                fig, ax = plt.subplots()
                ax.plot(list(y_test.values), label="Actual")
                ax.plot(list(y_pred), label="Predicted")
                ax.legend()
                ax.set_title("Actual vs Predicted Line Plot")
                st.pyplot(fig)
# ---------- TAB 5: PREDICTION ----------
with tabs[4]:
    if "model" in st.session_state:

        st.subheader("Predict Mental Wellbeing")

        model = st.session_state["model"]
        features = st.session_state["features"]

        input_dict = {}

        for feature in features:
            input_dict[feature] = st.number_input(f"Enter {feature}", value=0.0)

        if st.button("Predict"):

            input_df = pd.DataFrame([input_dict])
            prediction = model.predict(input_df)[0]

            # ---------- FIX REALISM ----------
            prediction = max(1, min(10, prediction))  # Clip
            prediction = round(prediction, 2)

            # ---------- RISK CLASSIFICATION ----------
            if prediction <= 3.5:
                risk = "HIGH 🔴"
            elif prediction <= 6.5:
                risk = "MODERATE 🟡"
            else:
                risk = "LOW 🟢"

            st.success(f"Happiness Score: {prediction}")
            st.warning(f"Risk Level: {risk}")

            # ---------- RECOMMENDATIONS ----------
            st.subheader("Recommendations")

            suggestions = []

            if "Daily_Screen_Time" in input_dict and input_dict["Daily_Screen_Time"] > 6:
                suggestions.append("Reduce screen time")

            if "Sleep_Quality" in input_dict and input_dict["Sleep_Quality"] < 5:
                suggestions.append("Improve sleep quality")

            if "Exercise_Frequency" in input_dict and input_dict["Exercise_Frequency"] < 2:
                suggestions.append("Increase physical activity")

            if "Stress_Level" in input_dict and input_dict["Stress_Level"] > 7:
                suggestions.append("Try stress management techniques")

            if suggestions:
                for s in suggestions:
                    st.write("•", s)
            else:
                st.write("✔ Lifestyle looks good. Keep it up!")