# preprocessing.py

import pandas as pd
import numpy as np


# 1️⃣ Load Dataset
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df


# 2️⃣ Basic Info
def dataset_info(df):
    info = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "missing_values": df.isnull().sum(),
        "duplicates": df.duplicated().sum()
    }
    return info


# 3️⃣ Handle Missing Values
def handle_missing_values(df):
    # Fill numeric columns with mean
    numeric_cols = df.select_dtypes(include=np.number).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    # Fill categorical columns with mode
    categorical_cols = df.select_dtypes(include='object').columns
    for col in categorical_cols:
        df[col] = df[col].fillna(df[col].mode()[0])

    return df


# 4️⃣ Remove Duplicates
def remove_duplicates(df):
    df = df.drop_duplicates()
    return df


# 5️⃣ Convert Data Types
def convert_datatypes(df):
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except:
            pass
    return df


# 6️⃣ Remove Outliers (IQR Method)
def remove_outliers(df, column):
    if column in df.select_dtypes(include=np.number).columns:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1

        df = df[(df[column] >= Q1 - 1.5 * IQR) &
                (df[column] <= Q3 + 1.5 * IQR)]
    return df


# 7️⃣ Full Preprocessing Pipeline
def preprocess_pipeline(df):
    df = handle_missing_values(df)
    df = remove_duplicates(df)
    df = convert_datatypes(df)
    return df