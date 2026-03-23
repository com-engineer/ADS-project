import pandas as pd
import numpy as np
from scipy import stats


def get_overview(df):
    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "missing_cells": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum())
    }


def get_missing(df):
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    result = []
    for col, count in missing.items():
        result.append({
            "column": col,
            "missing_count": int(count),
            "missing_pct": round(count / len(df) * 100, 2)
        })
    return result


def get_column_distribution(df, column):
    if column not in df.columns:
        return {"error": f"Column '{column}' not found"}

    col = df[column].dropna()

    if col.dtype == object or col.nunique() < 15:
        counts = col.value_counts().head(10)
        return {
            "type": "categorical",
            "labels": list(counts.index.astype(str)),
            "values": [int(v) for v in counts.values]
        }
    else:
        counts, edges = np.histogram(col, bins=15)
        labels = [f"{edges[i]:.1f}-{edges[i+1]:.1f}" for i in range(len(edges) - 1)]
        return {
            "type": "numeric",
            "labels": labels,
            "values": [int(v) for v in counts]
        }


def get_statistics(df, column):
    if column not in df.columns:
        return {"error": f"Column '{column}' not found"}

    col = df[column].dropna()

    if col.dtype == object:
        return {"error": f"'{column}' is categorical — select a numeric column"}

    return {
        "mean":   round(float(col.mean()), 4),
        "median": round(float(col.median()), 4),
        "std":    round(float(col.std()), 4),
        "min":    round(float(col.min()), 4),
        "max":    round(float(col.max()), 4),
        "q1":     round(float(col.quantile(0.25)), 4),
        "q3":     round(float(col.quantile(0.75)), 4),
        "skew":   round(float(stats.skew(col)), 4),
        "kurt":   round(float(stats.kurtosis(col)), 4)
    }


def get_correlation(df):
    numeric_df = df.select_dtypes(include=np.number)
    corr = numeric_df.corr().round(3)
    return {
        "columns": list(corr.columns),
        "matrix": corr.values.tolist()
    }


def get_target_distribution(df, target_col="readmitted"):
    if target_col not in df.columns:
        return {"labels": [], "values": []}
    counts = df[target_col].value_counts()
    return {
        "labels": list(counts.index.astype(str)),
        "values": [int(v) for v in counts.values]
    }


def get_bivariate(df, x_col, y_col):
    if x_col not in df.columns or y_col not in df.columns:
        return {"error": "One or both columns not found"}

    try:
        groups = df.groupby(x_col)[y_col]
        if df[y_col].dtype == object:
            mode_val = df[y_col].mode()[0]
            result = groups.apply(lambda g: round((g == mode_val).mean(), 4))
        else:
            result = groups.mean().round(4)

        return {
            "labels": [str(i) for i in result.index],
            "values": [round(float(v), 4) for v in result.values]
        }
    except Exception as e:
        return {"error": str(e)}