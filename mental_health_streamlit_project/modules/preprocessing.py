import streamlit as st
import pandas as pd

def preprocess_data(df):

    st.subheader("Preprocessing")

    if st.checkbox("Remove ID columns"):

        for col in df.columns:
            if "id" in col.lower():
                df = df.drop(col, axis=1)

    if st.checkbox("Convert categorical variables"):

        df = pd.get_dummies(df, drop_first=True)

    return df