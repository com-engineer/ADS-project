import streamlit as st
import pandas as pd

from modules.visualization import visualize_data
from modules.preprocessing import preprocess_data
from modules.model_training import train_model
from modules.evaluation import evaluate_model

st.title("Applied Data Science Model Builder")

st.sidebar.title("Navigation")

menu = st.sidebar.selectbox(
    "Select Phase",
    [
        "Upload Dataset",
        "Data Understanding",
        "Visualization",
        "Preprocessing",
        "Model Training",
        "Model Evaluation"
    ]
)

# Upload dataset
if menu == "Upload Dataset":

    uploaded_file = st.file_uploader("Upload CSV Dataset", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state["data"] = df

        st.write("Dataset Uploaded Successfully")
        st.write(df.head())


# Data Understanding
elif menu == "Data Understanding":

    if "data" in st.session_state:

        df = st.session_state["data"]

        st.subheader("Dataset Preview")
        st.write(df.head())

        st.subheader("Shape")
        st.write(df.shape)

        st.subheader("Data Types")
        st.write(df.dtypes)

        st.subheader("Statistical Summary")
        st.write(df.describe())

    else:
        st.warning("Please upload dataset first")


# Visualization
elif menu == "Visualization":

    if "data" in st.session_state:
        df = st.session_state["data"]
        visualize_data(df)

    else:
        st.warning("Upload dataset first")


# Preprocessing
elif menu == "Preprocessing":

    if "data" in st.session_state:

        df = st.session_state["data"]
        processed_df = preprocess_data(df)

        st.session_state["processed_data"] = processed_df

        st.write("Processed Data")
        st.write(processed_df.head())

    else:
        st.warning("Upload dataset first")


# Model Training
elif menu == "Model Training":

    if "processed_data" in st.session_state:

        df = st.session_state["processed_data"]

        model, X_test, y_test, y_pred = train_model(df)

        st.session_state["model_results"] = (X_test, y_test, y_pred)

    else:
        st.warning("Run preprocessing first")


# Model Evaluation
elif menu == "Model Evaluation":

    if "model_results" in st.session_state:

        X_test, y_test, y_pred = st.session_state["model_results"]

        evaluate_model(y_test, y_pred)

    else:
        st.warning("Train model first")