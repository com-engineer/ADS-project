import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

def train_model(df):

    st.subheader("Model Training")

    target = st.selectbox("Select Target Variable", df.columns)

    X = df.drop(target, axis=1)
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LinearRegression()

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    st.success("Model trained successfully")

    return model, X_test, y_test, y_pred