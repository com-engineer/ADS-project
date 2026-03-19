import streamlit as st
import pandas as pd


# Function to upload dataset
def load_dataset():

    uploaded_file = st.file_uploader("Upload your dataset (CSV)", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        return df

    return None


# Function to preview dataset
def show_preview(df):

    st.subheader("Dataset Preview")
    st.dataframe(df.head())


# Function to show dataset shape
def show_shape(df):

    st.subheader("Dataset Shape")

    rows, cols = df.shape

    st.write("Number of Rows:", rows)
    st.write("Number of Columns:", cols)


# Function to show dataset info
def show_info(df):

    st.subheader("Dataset Information")

    buffer = df.dtypes
    st.write(buffer)


# Function to show statistical summary
def show_statistics(df):

    st.subheader("Statistical Summary")

    st.write(df.describe())