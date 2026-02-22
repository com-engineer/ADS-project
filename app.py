import streamlit as st
import pandas as pd

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

st.title("🛒 E-Commerce Customer Behavior Dashboard")

# Load Dataset
@st.cache_data
def load_data():
    df = pd.read_csv("ecommerce_customer_behavior_dataset_v2.csv")
    return df

df = load_data()

st.subheader("Dataset Preview")
st.dataframe(df.head())

st.write("Dataset Shape:", df.shape)

st.write(df.describe())
# code2+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

st.sidebar.header("📊 Statistical Analysis")

numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns

selected_column = st.sidebar.selectbox(
    "Select Numerical Column",
    numeric_columns
)

operation = st.sidebar.selectbox(
    "Select Operation",
    ["Mean", "Median", "Standard Deviation", "Variance", "Min", "Max"]
)

if selected_column:
    if operation == "Mean":
        result = df[selected_column].mean()
    elif operation == "Median":
        result = df[selected_column].median()
    elif operation == "Standard Deviation":
        result = df[selected_column].std()
    elif operation == "Variance":
        result = df[selected_column].var()
    elif operation == "Min":
        result = df[selected_column].min()
    elif operation == "Max":
        result = df[selected_column].max()

    st.subheader("📌 Result")
    st.metric(label=f"{operation} of {selected_column}", value=round(result, 2))

    # code3+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    import plotly.express as px

st.sidebar.header("📈 Visualization")

graph_type = st.sidebar.selectbox(
    "Select Graph Type",
    ["Histogram", "Box Plot", "Bar Chart"]
)

st.subheader("📊 Visualization")

if graph_type == "Histogram":
    fig = px.histogram(df, x=selected_column)
    st.plotly_chart(fig, use_container_width=True)

elif graph_type == "Box Plot":
    fig = px.box(df, y=selected_column)
    st.plotly_chart(fig, use_container_width=True)

elif graph_type == "Bar Chart":
    categorical_columns = df.select_dtypes(include=['object']).columns
    category = st.sidebar.selectbox("Select Category", categorical_columns)
    fig = px.bar(df, x=category, y=selected_column)
    st.plotly_chart(fig, use_container_width=True)

    # code4 Add Correlation Heatmap+++++++++++++++++++++++++++++++++++++++++++++
    st.subheader("🔥 Correlation Heatmap")

corr = df[numeric_columns].corr()
fig = px.imshow(corr, text_auto=True)
st.plotly_chart(fig, use_container_width=True)

# code5 Add Customer Segmentation (Bonus ML)++++++++++++++++++++++++++++
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.subheader("👥 Customer Segmentation")

features = df[numeric_columns]

scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

kmeans = KMeans(n_clusters=3, random_state=42)
df['Cluster'] = kmeans.fit_predict(scaled_features)

fig = px.scatter(
    df,
    x=numeric_columns[0],
    y=numeric_columns[1],
    color="Cluster"
)

st.plotly_chart(fig, use_container_width=True)

# code6 Add KPI section+++++++++++++++++++++++++++++++++++++++=
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Customers", len(df))
col2.metric("Average Purchase", round(df[numeric_columns[0]].mean(),2))
col3.metric("Max Purchase", round(df[numeric_columns[0]].max(),2))


# code7 Add Insights Section++++++++++++++++++++++++++++++++++++
st.subheader("💡 Insights")

st.write("1. Identify high spending customers.")
st.write("2. Observe category trends.")
st.write("3. Analyze correlation between variables.")


# code8 preprocessing++++++++++++++++++++++++++++++++++++++++++++++
import preprocessing as pp

st.title("E-Commerce Customer Behavior Dashboard")

# Load dataset
df = pp.load_data("ecommerce_customer_behavior_dataset_v2.csv")

# Show raw info
st.subheader("Raw Dataset Info")
info = pp.dataset_info(df)
st.write("Shape:", info["shape"])
st.write("Missing Values:", info["missing_values"])
st.write("Duplicate Rows:", info["duplicates"])

# Preprocess dataset
df = pp.preprocess_pipeline(df)

st.success("Data Preprocessing Completed Successfully ✅")

# Show cleaned dataset
st.subheader("Cleaned Dataset Preview")
st.dataframe(df.head())