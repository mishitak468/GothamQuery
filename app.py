import streamlit as st
import plotly.express as px
from engine import SQLCopilot

st.set_page_config(page_title="NYC Analytics Co-pilot", layout="wide")
copilot = SQLCopilot()

st.title("🏙️ NL-to-SQL Analytics Co-pilot")
st.markdown(
    "Query NYC 311 complaint data using plain English. *Built with DuckDB & Groq (Llama 3.3 70B).*")

with st.sidebar:
    st.header("Project Performance")
    st.metric("Avg. Latency", "~1.2s")
    st.metric("Test Set Accuracy", "80%+")
    st.info("Handles: GROUP BY, HAVING, JOINs, Window Functions, CTEs, Date Truncation, NULLs, CASE statements")
    st.markdown("---")
    st.markdown("**Dataset:** NYC 311 Service Requests")
    st.markdown("**Date range:** March–April 2026")
    st.markdown("**Rows:** ~534,000")

# Example queries that actually work with the 2026 data
examples = [
    "Which borough had the most complaints?",
    "Show the daily complaint trend for March 2026.",
    "Which agencies have more than 500 complaints?",
    "How many complaints are missing a zip code?",
    "Rank agencies by complaint volume using a window function.",
    "What percentage of complaints belong to the NYPD?",
    "How many complaints were created on weekends?",
]

st.markdown("**Try an example:**")
cols = st.columns(len(examples))
selected_example = None
for i, ex in enumerate(examples):
    if cols[i].button(ex, use_container_width=True):
        selected_example = ex

query = st.text_input(
    "Or type your own question:",
    value=selected_example or "",
    placeholder="e.g. Which borough had the most noise complaints?"
)

if query:
    with st.spinner("Generating SQL..."):
        sql = copilot.generate_query(query)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Generated SQL")
        st.code(sql, language="sql")

    with col2:
        df, error = copilot.execute_query(sql)
        if error:
            st.error(f"Execution Error: {error}")
            st.caption(
                "The model may have generated invalid SQL. Try rephrasing your question.")
        elif df is not None and df.empty:
            st.warning(
                "Query ran successfully but returned no results. Try adjusting your filters.")
        else:
            st.subheader("Data Result")
            st.dataframe(df, use_container_width=True)

            # Auto-Visualization: pick the right chart type
            if df is not None and len(df.columns) >= 2:
                num_cols = df.select_dtypes(include='number').columns.tolist()
                cat_cols = df.select_dtypes(exclude='number').columns.tolist()

                if cat_cols and num_cols:
                    # Bar chart: categorical x, numeric y
                    fig = px.bar(
                        df.head(20),
                        x=cat_cols[0],
                        y=num_cols[0],
                        title=f"{num_cols[0]} by {cat_cols[0]}",
                        color_discrete_sequence=["#636EFA"]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                elif len(num_cols) >= 2:
                    # Line chart for time series
                    fig = px.line(
                        df.head(200),
                        x=df.columns[0],
                        y=df.columns[1],
                        title="Trend over time"
                    )
                    st.plotly_chart(fig, use_container_width=True)
