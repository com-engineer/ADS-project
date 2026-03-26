import pandas as pd

def load_data(path="data/diabetes.csv", sample_size=20000):
    df = pd.read_csv(path)
    df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
    df.replace("?", None, inplace=True)
    return df