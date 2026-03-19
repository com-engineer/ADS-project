import streamlit as st
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

def evaluate_model(y_test, y_pred):

    st.subheader("Model Evaluation")

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    st.write("Mean Squared Error:", mse)
    st.write("R2 Score:", r2)

    fig, ax = plt.subplots()

    ax.scatter(y_test, y_pred)

    ax.set_xlabel("Actual")
    ax.set_ylabel("Predicted")

    st.pyplot(fig)