import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from engine import SQLCopilot

st.set_page_config(
    page_title="GothamQuery",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Syne:wght@400;600;700;800&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
    background-color: #0a0a0a;
    color: #e8e8e8;
}
.stApp { background-color: #0a0a0a; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem 3rem; max-width: 1400px; }

/* ── Hero header ── */
.gq-hero {
    border-bottom: 1px solid #2a2a2a;
    padding-bottom: 2rem;
    margin-bottom: 2.5rem;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
}
.gq-wordmark {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 3rem;
    letter-spacing: -0.03em;
    color: #f0f0f0;
    line-height: 1;
    margin: 0;
}
.gq-wordmark span { color: #ff4b2b; }
.gq-tagline {
    font-size: 0.72rem;
    color: #555;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    line-height: 1.6;
    text-align: right;
}

/* ── Stats bar ── */
.gq-stats {
    display: flex;
    gap: 0;
    margin-bottom: 2.5rem;
    border: 1px solid #1e1e1e;
}
.gq-stat {
    flex: 1;
    padding: 1.2rem 1.5rem;
    border-right: 1px solid #1e1e1e;
    position: relative;
}
.gq-stat:last-child { border-right: none; }
.gq-stat-label {
    font-size: 0.65rem;
    color: #444;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.gq-stat-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #f0f0f0;
    line-height: 1;
}
.gq-stat-value.accent { color: #ff4b2b; }

/* ── Input area ── */
.gq-input-label {
    font-size: 0.65rem;
    color: #555;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.stTextInput > div > div > input {
    background-color: #111 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 0 !important;
    color: #f0f0f0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.95rem !important;
    padding: 0.9rem 1.2rem !important;
    caret-color: #ff4b2b;
    transition: border-color 0.2s;
}
.stTextInput > div > div > input:focus {
    border-color: #ff4b2b !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder { color: #333 !important; }

/* ── Example chips ── */
.gq-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 2rem;
    margin-top: 0.75rem;
}
.gq-chip {
    background: #111;
    border: 1px solid #222;
    color: #666;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    padding: 0.35rem 0.8rem;
    cursor: pointer;
    transition: all 0.15s;
    letter-spacing: 0.02em;
}
.gq-chip:hover { border-color: #ff4b2b; color: #ff4b2b; background: #140800; }

/* ── Section labels ── */
.gq-section-label {
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #333;
    border-bottom: 1px solid #1a1a1a;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

/* ── SQL code block ── */
.stCodeBlock, pre {
    border-radius: 0 !important;
    border: 1px solid #1e1e1e !important;
    background-color: #0e0e0e !important;
}

/* ── Dataframe ── */
.stDataFrame { border: 1px solid #1e1e1e; }
[data-testid="stDataFrame"] { border-radius: 0; }

/* ── Buttons ── */
.stButton > button {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 0 !important;
    color: #555 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    padding: 0.4rem 0.9rem !important;
    transition: all 0.15s !important;
    letter-spacing: 0.03em;
}
.stButton > button:hover {
    border-color: #ff4b2b !important;
    color: #ff4b2b !important;
    background: #140800 !important;
}

/* ── Error / warning ── */
.stAlert { border-radius: 0 !important; border-left: 3px solid #ff4b2b !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #ff4b2b !important; }

/* ── Divider ── */
hr { border-color: #1a1a1a !important; }

/* ── Result panel ── */
.gq-result-panel {
    border: 1px solid #1e1e1e;
    padding: 1.5rem;
    background: #0d0d0d;
}
</style>
""", unsafe_allow_html=True)

copilot = SQLCopilot()

st.markdown("""
<div class="gq-hero">
  <div>
    <p class="gq-wordmark">Gotham<span>Query</span></p>
  </div>
  <div class="gq-tagline">
    NL → SQL · NYC 311 · ~534k records<br>
    DuckDB · Groq · Llama 3.3 70B
  </div>
</div>
""", unsafe_allow_html=True)

# Stats bar
st.markdown("""
<div class="gq-stats">
  <div class="gq-stat">
    <div class="gq-stat-label">Eval Accuracy</div>
    <div class="gq-stat-value accent">93%</div>
  </div>
  <div class="gq-stat">
    <div class="gq-stat-label">Avg Latency</div>
    <div class="gq-stat-value">~1.2s</div>
  </div>
  <div class="gq-stat">
    <div class="gq-stat-label">Query Types</div>
    <div class="gq-stat-value">15+</div>
  </div>
  <div class="gq-stat">
    <div class="gq-stat-label">Dataset</div>
    <div class="gq-stat-value">NYC 311</div>
  </div>
  <div class="gq-stat">
    <div class="gq-stat-label">Date Range</div>
    <div class="gq-stat-value">Mar–Apr 2026</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Example chips
examples = [
    "Which borough had the most complaints?",
    "Show the daily trend for March 2026.",
    "Agencies with over 500 complaints?",
    "How many complaints have no zip code?",
    "Rank agencies by volume using RANK().",
    "What % of complaints are NYPD?",
    "Complaints created on weekends?",
    "Average daily complaints via CTE.",
]

st.markdown('<div class="gq-input-label">Try an example</div>',
            unsafe_allow_html=True)

cols = st.columns(len(examples))
selected = None
for i, ex in enumerate(examples):
    if cols[i].button(ex, key=f"ex_{i}"):
        selected = ex

# Query input
st.markdown('<div class="gq-input-label" style="margin-top:1.5rem;">Your question</div>',
            unsafe_allow_html=True)
query = st.text_input(
    label="query",
    label_visibility="collapsed",
    value=selected or "",
    placeholder="e.g.  Which borough had the most noise complaints in March 2026?",
    key="query_input"
)

# Results
if query:
    with st.spinner(""):
        sql = copilot.generate_query(query)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([5, 7], gap="large")

    with left:
        st.markdown(
            '<div class="gq-section-label">Generated SQL</div>', unsafe_allow_html=True)
        st.code(sql, language="sql")

    with right:
        df, error = copilot.execute_query(sql)

        if error:
            st.markdown('<div class="gq-section-label">Error</div>',
                        unsafe_allow_html=True)
            st.error(f"{error}")
            st.caption(
                "Try rephrasing — e.g. use 'NYPD' not 'police', 'MANHATTAN' not 'manhattan'.")

        elif df is not None and df.empty:
            st.markdown('<div class="gq-section-label">Result</div>',
                        unsafe_allow_html=True)
            st.warning("Query executed — no matching rows found.")

        else:
            st.markdown('<div class="gq-section-label">Result</div>',
                        unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, height=220)

            # Auto-chart
            if df is not None and len(df.columns) >= 2:
                num_cols = df.select_dtypes(include='number').columns.tolist()
                cat_cols = df.select_dtypes(exclude='number').columns.tolist()
                date_cols = [c for c in df.columns if 'date' in str(
                    c).lower() or 'day' in str(c).lower()]

                st.markdown(
                    '<div class="gq-section-label" style="margin-top:1.2rem;">Visualization</div>', unsafe_allow_html=True)

                plot_config = {"displayModeBar": False}
                chart_theme = dict(
                    paper_bgcolor="#0d0d0d",
                    plot_bgcolor="#0d0d0d",
                    font=dict(family="DM Mono, monospace",
                              color="#666", size=11),
                    xaxis=dict(gridcolor="#1a1a1a",
                               linecolor="#222", tickcolor="#222"),
                    yaxis=dict(gridcolor="#1a1a1a",
                               linecolor="#222", tickcolor="#222"),
                    margin=dict(l=40, r=20, t=30, b=40),
                )

                if date_cols and num_cols:
                    # Time series — line chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df[date_cols[0]], y=df[num_cols[0]],
                        mode='lines',
                        line=dict(color="#ff4b2b", width=1.5),
                        fill='tozeroy',
                        fillcolor="rgba(255,75,43,0.06)"
                    ))
                    fig.update_layout(**chart_theme, height=240)
                    st.plotly_chart(
                        fig, use_container_width=True, config=plot_config)

                elif cat_cols and num_cols:
                    # Bar chart — horizontal for readability
                    df_plot = df.head(15).sort_values(num_cols[0])
                    fig = go.Figure(go.Bar(
                        x=df_plot[num_cols[0]],
                        y=df_plot[cat_cols[0]],
                        orientation='h',
                        marker_color="#ff4b2b",
                        marker_line_width=0,
                    ))
                    fig.update_layout(
                        **chart_theme, height=max(200, len(df_plot) * 30))
                    st.plotly_chart(
                        fig, use_container_width=True, config=plot_config)

                elif len(num_cols) >= 2:
                    fig = go.Figure(go.Scatter(
                        x=df[num_cols[0]], y=df[num_cols[1]],
                        mode='lines+markers',
                        line=dict(color="#ff4b2b", width=1.5),
                        marker=dict(size=3, color="#ff4b2b")
                    ))
                    fig.update_layout(**chart_theme, height=240)
                    st.plotly_chart(
                        fig, use_container_width=True, config=plot_config)
