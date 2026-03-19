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

# ---------- LOAD DATA ----------
df = None
file = st.file_uploader("Upload Dataset", type=["csv"])

if file:
    df = pd.read_csv(file)
    df = df.drop(columns=[col for col in df.columns if "id" in col.lower()], errors='ignore')

    # Encode categorical
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

        target = st.selectbox("Select Target Variable", df.columns)

        X = df.drop(target, axis=1)
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        model = LinearRegression()

        if st.button("Train Model"):
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            st.session_state["model"] = model
            st.session_state["features"] = X.columns

            st.success("Model Trained")

            st.write("R2 Score:", r2_score(y_test, y_pred))
            st.write("MSE:", mean_squared_error(y_test, y_pred))

            fig, ax = plt.subplots()
            ax.scatter(y_test, y_pred)
            ax.set_xlabel("Actual")
            ax.set_ylabel("Predicted")
            st.pyplot(fig)

# ---------- TAB 5: PREDICTION ----------
with tabs[4]:
    if "model" in st.session_state:

        st.subheader("Predict Mental Wellbeing")

        model = st.session_state["model"]
        features = st.session_state["features"]

        input_data = []

        for feature in features:
            val = st.number_input(f"Enter {feature}", value=0.0)
            input_data.append(val)

        if st.button("Predict"):

            prediction = model.predict([input_data])[0]

            # Risk classification
            if prediction <= 3:
                risk = "HIGH 🔴"
            elif prediction <= 6:
                risk = "MODERATE 🟡"
            else:
                risk = "LOW 🟢"

            st.success(f"Happiness Score: {round(prediction,2)}")
            st.warning(f"Risk Level: {risk}")

            # Recommendations
            st.subheader("Recommendations")

            suggestions = []

            if input_data[1] > 6:
                suggestions.append("Reduce screen time")

            if input_data[2] < 5:
                suggestions.append("Improve sleep quality")

            if input_data[4] < 2:
                suggestions.append("Increase physical activity")

            for s in suggestions:
                st.write("•", s)