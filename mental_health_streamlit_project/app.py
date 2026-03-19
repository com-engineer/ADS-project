import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, confusion_matrix

st.set_page_config(layout="wide")

# ---------- NAVBAR ----------
menu = ["Upload", "EDA", "Visualization", "Preprocessing", "Model Training", "Evaluation", "Prediction"]
choice = st.tabs(menu)

# ---------- UPLOAD ----------
with choice[0]:
    st.header("Upload Dataset")
    file = st.file_uploader("Upload CSV", type=["csv"])

    if file:
        df = pd.read_csv(file)
        st.session_state["df"] = df
        st.write(df.head())

# ---------- EDA ----------
with choice[1]:
    if "df" in st.session_state:
        df = st.session_state["df"]

        st.header("Exploratory Data Analysis")

        st.subheader("Basic Info")
        st.write(df.shape)
        st.write(df.dtypes)

        st.subheader("Statistical Measures")

        if st.checkbox("Mean"):
            st.write(df.mean(numeric_only=True))

        if st.checkbox("Median"):
            st.write(df.median(numeric_only=True))

        if st.checkbox("Mode"):
            st.write(df.mode().iloc[0])

        if st.checkbox("Standard Deviation"):
            st.write(df.std(numeric_only=True))

        if st.checkbox("Variance"):
            st.write(df.var(numeric_only=True))

        if st.checkbox("Skewness"):
            st.write(df.skew(numeric_only=True))

# ---------- VISUALIZATION ----------
with choice[2]:
    if "df" in st.session_state:
        df = st.session_state["df"]

        st.header("Visualization")

        plot = st.selectbox("Select Plot",
                            ["Histogram", "Scatter", "Boxplot", "Heatmap"])

        cols = df.columns

        if plot == "Histogram":
            col = st.selectbox("Select Column", cols)
            fig, ax = plt.subplots()
            sns.histplot(df[col], ax=ax)
            st.pyplot(fig)

        elif plot == "Scatter":
            x = st.selectbox("X Axis", cols)
            y = st.selectbox("Y Axis", cols)
            fig, ax = plt.subplots()
            sns.scatterplot(x=df[x], y=df[y], ax=ax)
            st.pyplot(fig)

        elif plot == "Boxplot":
            col = st.selectbox("Select Column", cols)
            fig, ax = plt.subplots()
            sns.boxplot(x=df[col], ax=ax)
            st.pyplot(fig)

        elif plot == "Heatmap":
            fig, ax = plt.subplots()
            sns.heatmap(df.corr(numeric_only=True), annot=True, ax=ax)
            st.pyplot(fig)

# ---------- PREPROCESSING ----------
with choice[3]:
    if "df" in st.session_state:
        df = st.session_state["df"].copy()

        st.header("Preprocessing")

        if st.checkbox("Remove Duplicate Rows"):
            df = df.drop_duplicates()

        if st.checkbox("Handle Missing Values (Fill Mean)"):
            df = df.fillna(df.mean(numeric_only=True))

        if st.checkbox("Drop ID Columns"):
            for col in df.columns:
                if "id" in col.lower():
                    df = df.drop(col, axis=1)

        if st.checkbox("Encode Categorical Columns"):
            df = pd.get_dummies(df, drop_first=True)

        st.session_state["processed"] = df
        st.write(df.head())

# ---------- MODEL TRAINING ----------
with choice[4]:
    if "processed" in st.session_state:

        df = st.session_state["processed"]

        st.header("Model Training")

        target = st.selectbox("Select Target Variable", df.columns)

        X = df.drop(target, axis=1)
        y = df[target]

        model_type = st.selectbox("Select Model",
                                 ["Linear Regression", "Random Forest", "Logistic Regression"])

        test_size = st.slider("Test Size", 0.1, 0.5, 0.2)

        if st.button("Train Model"):

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)

            if model_type == "Linear Regression":
                model = LinearRegression()

            elif model_type == "Random Forest":
                model = RandomForestRegressor()

            else:
                model = LogisticRegression(max_iter=1000)

            # Training progress
            progress = st.progress(0)

            for i in range(100):
                progress.progress(i + 1)

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            st.session_state["model"] = model
            st.session_state["X_test"] = X_test
            st.session_state["y_test"] = y_test
            st.session_state["y_pred"] = y_pred

            st.success("Model Trained Successfully")

# ---------- EVALUATION ----------
with choice[5]:
    if "model" in st.session_state:

        y_test = st.session_state["y_test"]
        y_pred = st.session_state["y_pred"]

        st.header("Model Evaluation")

        st.write("R2 Score:", r2_score(y_test, y_pred))
        st.write("MSE:", mean_squared_error(y_test, y_pred))

        # Plot
        fig, ax = plt.subplots()
        ax.scatter(y_test, y_pred)
        ax.set_xlabel("Actual")
        ax.set_ylabel("Predicted")
        st.pyplot(fig)

# ---------- PREDICTION ----------
with choice[6]:
    if "model" in st.session_state:

        st.header("Predict New Data")

        df = st.session_state["processed"]
        model = st.session_state["model"]

        input_data = []

        for col in df.columns[:-1]:
            val = st.number_input(f"Enter {col}", value=0.0)
            input_data.append(val)

        if st.button("Predict"):
            prediction = model.predict([input_data])

            st.success(f"Predicted Output: {prediction[0]}")