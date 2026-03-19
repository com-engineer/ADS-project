import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def visualize_data(df):

    st.subheader("Visualization")

    plot_type = st.selectbox(
        "Select Plot Type",
        ["Histogram", "Scatter Plot", "Box Plot", "Correlation Heatmap"]
    )

    columns = df.columns.tolist()

    if plot_type == "Histogram":

        feature = st.selectbox("Select Feature", columns)

        fig, ax = plt.subplots()
        sns.histplot(df[feature], ax=ax)

        st.pyplot(fig)

    elif plot_type == "Scatter Plot":

        x = st.selectbox("X Axis", columns)
        y = st.selectbox("Y Axis", columns)

        fig, ax = plt.subplots()
        sns.scatterplot(x=df[x], y=df[y], ax=ax)

        st.pyplot(fig)

    elif plot_type == "Box Plot":

        feature = st.selectbox("Select Feature", columns)

        fig, ax = plt.subplots()
        sns.boxplot(x=df[feature], ax=ax)

        st.pyplot(fig)

    elif plot_type == "Correlation Heatmap":

        fig, ax = plt.subplots()
        corr = df.corr(numeric_only=True)

        sns.heatmap(corr, annot=True, ax=ax)

        st.pyplot(fig)