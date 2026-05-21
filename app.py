import streamlit as st
import plotly.graph_objects as go
import time as time_module
from datetime import datetime
from engine import SQLCopilot

st.set_page_config(
    page_title="GothamQuery",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;0,700;1,300&family=Bebas+Neue&display=swap');

:root {
  --bg:       #0d1117;
  --bg1:      #161b22;
  --bg2:      #1c2230;
  --bg3:      #21293a;
  --border:   #2d3748;
  --border2:  #3a4a5c;
  --text:     #e2e8f0;
  --text-dim: #94a3b8;
  --text-xs:  #4a5568;
  --accent:   #ff4500;
  --accent2:  #ff6b35;
  --green:    #48bb78;
  --yellow:   #f6e05e;
  --blue:     #63b3ed;
}

html, body, [class*="css"] {
  font-family: 'JetBrains Mono', monospace;
  background: var(--bg);
  color: var(--text);
}
.stApp { background: var(--bg); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* ── Topbar ── */
.gq-topbar {
  background: var(--bg1);
  border-bottom: 2px solid var(--accent);
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 52px;
}
.gq-logo {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.5rem;
  letter-spacing: 0.08em;
  color: #f0f0f0;
  margin-right: 36px;
  flex-shrink: 0;
}
.gq-logo em { color: var(--accent); font-style: normal; }
.gq-topbar-pills { display: flex; gap: 6px; flex: 1; }
.gq-pill {
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-dim);
  padding: 4px 12px;
  border: 1px solid var(--border);
  background: var(--bg2);
}
.gq-pill.live { border-color: var(--green); color: var(--green); font-weight: 700; }
.gq-pill.live::before { content: '● '; font-size: 0.5rem; vertical-align: middle; }
.gq-topbar-right {
  font-size: 0.65rem;
  color: var(--text-dim);
  letter-spacing: 0.06em;
  text-align: right;
  line-height: 1.9;
}

/* ── Sidebar sections ── */
.gq-sidebar-section {
  border-bottom: 1px solid var(--border);
  padding: 16px 18px;
}
.gq-sidebar-title {
  font-size: 0.6rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-xs);
  margin-bottom: 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
.gq-metric-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 10px;
}
.gq-metric-label { font-size: 0.7rem; color: var(--text-dim); }
.gq-metric-val { font-size: 0.95rem; font-weight: 700; color: var(--text); }
.gq-metric-val.green { color: var(--green); }
.gq-metric-val.accent { color: var(--accent); }
.gq-metric-val.blue { color: var(--blue); }
.gq-metric-val.yellow { color: var(--yellow); }

.gq-bar-track { height: 3px; background: var(--bg3); margin-bottom: 12px; position: relative; border-radius: 1px; }
.gq-bar-fill { height: 100%; background: var(--accent); position: absolute; top:0; left:0; border-radius: 1px; }
.gq-bar-fill.green { background: var(--green); }

/* schema */
.gq-schema-col {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.68rem;
}
.gq-schema-col:last-child { border-bottom: none; }
.gq-schema-name { color: var(--text); }
.gq-schema-type { color: var(--blue); opacity: 0.8; }

/* history */
.gq-history-item { padding: 8px 0; border-bottom: 1px solid var(--border); }
.gq-history-item:last-child { border-bottom: none; }
.gq-history-q {
  font-size: 0.68rem;
  color: var(--text);
  line-height: 1.5;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gq-history-meta { font-size: 0.6rem; color: var(--text-dim); }
.gq-history-meta .ok { color: var(--green); font-weight: 700; }
.gq-history-meta .err { color: var(--accent); font-weight: 700; }

/* caps tags */
.gq-cap-tag {
  font-size: 0.62rem;
  border: 1px solid var(--border2);
  padding: 3px 9px;
  color: var(--text-dim);
  background: var(--bg2);
}

/* ── Input area ── */
.stTextInput > div > div > input {
  background: var(--bg2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 0 !important;
  color: var(--text) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 1rem !important;
  padding: 12px 16px !important;
  caret-color: var(--accent) !important;
  transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(255,69,0,0.12) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text-xs) !important; }
.stTextInput label { display: none !important; }

/* ── Chip buttons ── */
.gq-chip-btn > div > button {
  background: var(--bg2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 0 !important;
  color: var(--text) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.72rem !important;
  font-weight: 400 !important;
  padding: 6px 12px !important;
  line-height: 1.5 !important;
  min-height: 0 !important;
  height: auto !important;
  transition: all 0.12s !important;
  white-space: normal !important;
  text-align: left !important;
}
.gq-chip-btn > div > button:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  background: rgba(255,69,0,0.07) !important;
}

/* ── Section labels ── */
.gq-section-label {
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--text-xs);
  padding: 8px 0 6px 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.gq-section-label span { color: var(--text-dim); font-size: 0.58rem; }

/* ── Result header ── */
.gq-result-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 0;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--border);
}
.gq-badge {
  font-size: 0.65rem;
  letter-spacing: 0.12em;
  padding: 3px 10px;
  border: 1px solid;
  font-weight: 700;
}
.gq-badge.ok  { border-color: var(--green); color: var(--green); background: rgba(72,187,120,0.08); }
.gq-badge.err { border-color: var(--accent); color: var(--accent); background: rgba(255,69,0,0.08); }
.gq-rmeta { font-size: 0.65rem; color: var(--text-dim); }
.gq-rmeta b { color: var(--text); font-weight: 500; }

/* ── Panel chrome ── */
.gq-panel-header {
  font-size: 0.62rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-dim);
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-bottom: none;
  background: var(--bg2);
  display: flex;
  justify-content: space-between;
}
.gq-panel-header span:last-child { color: var(--text-xs); font-size: 0.58rem; }

/* ── Code block ── */
.stCodeBlock pre {
  border-radius: 0 !important;
  background: #0a0f17 !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  font-size: 0.8rem !important;
  margin: 0 !important;
  padding: 14px !important;
}
.stCodeBlock { margin: 0 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] > div {
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 !important;
}
[data-testid="stDataFrame"] iframe {
  border-radius: 0 !important;
}

/* ── Alert ── */
.stAlert {
  border-radius: 0 !important;
  background: rgba(255,69,0,0.07) !important;
  border: 1px solid rgba(255,69,0,0.4) !important;
  border-left: 3px solid var(--accent) !important;
  font-size: 0.75rem !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Console label ── */
.gq-console-wrap {
  background: var(--bg1);
  border-bottom: 1px solid var(--border);
  padding: 12px 20px 8px 20px;
}
.gq-console-label {
  font-size: 0.62rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin-bottom: 8px;
}
.gq-console-label em { color: var(--accent); font-style: normal; font-weight: 700; }

/* ── Empty state ── */
.gq-empty {
  margin-top: 80px;
  text-align: center;
}
.gq-empty-icon { font-size: 2.5rem; color: var(--border2); margin-bottom: 18px; }
.gq-empty-msg { font-size: 0.78rem; color: var(--text-dim); letter-spacing: 0.1em; }
.gq-empty-sub { font-size: 0.65rem; color: var(--text-xs); margin-top: 10px; letter-spacing: 0.04em; line-height: 2; }

/* ── Chips area bg ── */
.gq-chips-wrap {
  background: var(--bg1);
  border-bottom: 1px solid var(--border);
  padding: 8px 20px 12px 20px;
}
.gq-chips-label {
  font-size: 0.58rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-xs);
  margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "selected_example" not in st.session_state:
    st.session_state.selected_example = ""
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

copilot = SQLCopilot()

SCHEMA_COLS = [
    ("Unique Key",    "BIGINT"),
    ("Created Date",  "TIMESTAMP"),
    ("Agency",        "VARCHAR"),
    ("Problem (...)", "VARCHAR"),
    ("Descriptor",    "VARCHAR"),
    ("Incident Zip",  "BIGINT"),
    ("Status",        "VARCHAR"),
    ("Borough",       "VARCHAR"),
    ("Latitude",      "DOUBLE"),
    ("Longitude",     "DOUBLE"),
]

EXAMPLES = [
    "Which borough had the most complaints?",
    "Show daily count for March 2026.",
    "Agencies with over 500 complaints?",
    "Complaints with no zip code?",
    "Rank agencies by volume with RANK().",
    "What % of complaints are NYPD?",
    "Count complaints on weekends.",
    "Avg daily complaints via CTE.",
]

CAPS = ["GROUP BY", "HAVING", "Window Fn", "CTE", "Subquery",
        "Self-JOIN", "Date Math", "NULL check", "CASE/WHEN", "LIKE"]

# ── Topbar ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="gq-topbar">
  <div class="gq-logo">Gotham<em>Query</em></div>
  <div class="gq-topbar-pills">
    <div class="gq-pill live">connected</div>
    <div class="gq-pill">nyc_311</div>
    <div class="gq-pill">duckdb 0.10</div>
    <div class="gq-pill">groq · llama-3.3-70b</div>
    <div class="gq-pill">534,134 rows</div>
  </div>
  <div class="gq-topbar-right">
    EXEC ACCURACY&nbsp;<strong style="color:#ff4500">93%</strong>&nbsp;·&nbsp;15 QUERY TYPES<br>
    {datetime.now().strftime("%Y-%m-%d&nbsp;&nbsp;%H:%M")} EDT
  </div>
</div>
""", unsafe_allow_html=True)

# ── Two-column layout ─────────────────────────────────────────────────────────
sidebar_col, main_col = st.columns([1, 4], gap="small")

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with sidebar_col:
    st.markdown(f"""
    <div class="gq-sidebar-section">
      <div class="gq-sidebar-title">System Metrics</div>
      <div class="gq-metric-row">
        <span class="gq-metric-label">eval accuracy</span>
        <span class="gq-metric-val accent">93%</span>
      </div>
      <div class="gq-bar-track"><div class="gq-bar-fill" style="width:93%"></div></div>
      <div class="gq-metric-row">
        <span class="gq-metric-label">avg latency</span>
        <span class="gq-metric-val green">~1.2s</span>
      </div>
      <div class="gq-bar-track"><div class="gq-bar-fill green" style="width:38%"></div></div>
      <div class="gq-metric-row">
        <span class="gq-metric-label">query types</span>
        <span class="gq-metric-val blue">15+</span>
      </div>
      <div class="gq-metric-row">
        <span class="gq-metric-label">golden dataset</span>
        <span class="gq-metric-val yellow">15 cases</span>
      </div>
      <div class="gq-metric-row">
        <span class="gq-metric-label">session queries</span>
        <span class="gq-metric-val">{st.session_state.query_count}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    schema_html = '<div class="gq-sidebar-section"><div class="gq-sidebar-title">Schema · nyc_311</div>'
    for name, typ in SCHEMA_COLS:
        schema_html += f'<div class="gq-schema-col"><span class="gq-schema-name">{name}</span><span class="gq-schema-type">{typ}</span></div>'
    schema_html += '</div>'
    st.markdown(schema_html, unsafe_allow_html=True)

    hist_html = '<div class="gq-sidebar-section"><div class="gq-sidebar-title">Query History</div>'
    if not st.session_state.history:
        hist_html += '<div style="font-size:0.68rem;color:var(--text-xs);padding:4px 0">No queries yet this session.</div>'
    else:
        for h in reversed(st.session_state.history[-8:]):
            sc = "ok" if h["ok"] else "err"
            st = "OK" if h["ok"] else "ERR"
            hist_html += f"""
            <div class="gq-history-item">
              <div class="gq-history-q">{h['question'][:44]}{'…' if len(h['question'])>44 else ''}</div>
              <div class="gq-history-meta">
                <span class="{sc}">{st}</span>&nbsp;·&nbsp;{h['rows']:,} rows&nbsp;·&nbsp;{h['latency']:.2f}s&nbsp;·&nbsp;{h['ts']}
              </div>
            </div>"""
    hist_html += '</div>'
    # Note: reusing 'st' variable name for status text above — need to re-import
    import streamlit as _st
    _st.markdown(hist_html, unsafe_allow_html=True)

    caps_html = '<div class="gq-sidebar-section"><div class="gq-sidebar-title">Supported Patterns</div><div style="display:flex;flex-wrap:wrap;gap:5px">'
    for c in CAPS:
        caps_html += f'<div class="gq-cap-tag">{c}</div>'
    caps_html += '</div></div>'
    _st.markdown(caps_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
with main_col:

    # Console label
    st.markdown("""
    <div class="gq-console-wrap">
      <div class="gq-console-label"><em>$</em>&nbsp;&nbsp;Natural Language Query</div>
    </div>
    """, unsafe_allow_html=True)

    query = st.text_input(
        label="nl",
        label_visibility="collapsed",
        value=st.session_state.selected_example,
        placeholder="e.g.  Which borough had the most noise complaints in March 2026?",
        key="query_input"
    )

    # Chips
    st.markdown('<div class="gq-chips-wrap"><div class="gq-chips-label">Quick examples</div>',
                unsafe_allow_html=True)
    chip_cols = st.columns(len(EXAMPLES))
    for i, ex in enumerate(EXAMPLES):
        with chip_cols[i]:
            st.markdown('<div class="gq-chip-btn">', unsafe_allow_html=True)
            if st.button(ex, key=f"chip_{i}"):
                st.session_state.selected_example = ex
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Results
    st.markdown('<div style="padding:16px 20px 24px 20px">',
                unsafe_allow_html=True)

    if query:
        t0 = time_module.time()
        with st.spinner("Generating SQL…"):
            sql = copilot.generate_query(query)
        t_gen = time_module.time() - t0

        t1 = time_module.time()
        df, error = copilot.execute_query(sql)
        t_exec = time_module.time() - t1
        total_t = t_gen + t_exec

        rows = len(df) if df is not None else 0
        st.session_state.history.append({
            "question": query, "ok": error is None,
            "rows": rows, "latency": total_t,
            "ts": datetime.now().strftime("%H:%M:%S"), "sql": sql,
        })
        st.session_state.query_count += 1

        # Result header
        if error:
            badge = '<span class="gq-badge err">✕ ERROR</span>'
            meta = f'<span class="gq-rmeta">gen <b>{t_gen:.2f}s</b> · exec <b>—</b></span>'
        else:
            badge = '<span class="gq-badge ok">✓ OK</span>'
            ncols = len(df.columns) if df is not None else 0
            meta = f'<span class="gq-rmeta"><b>{rows:,}</b> rows · <b>{ncols}</b> cols · latency <b>{total_t:.2f}s</b> · gen <b>{t_gen:.2f}s</b> · exec <b>{t_exec:.2f}s</b></span>'

        st.markdown(f"""
        <div class="gq-result-header">
          {badge} {meta}
          <span class="gq-rmeta" style="margin-left:auto;color:var(--text-xs)">
            query #{st.session_state.query_count}
          </span>
        </div>
        """, unsafe_allow_html=True)

        # SQL + Data panels
        sql_col, data_col = st.columns([1, 1], gap="small")

        with sql_col:
            st.markdown("""
            <div class="gq-panel-header">
              <span>Generated SQL</span>
              <span>DuckDB Dialect</span>
            </div>
            """, unsafe_allow_html=True)
            st.code(sql, language="sql")

        with data_col:
            st.markdown("""
            <div class="gq-panel-header">
              <span>Result Set</span>
              <span>first 200 rows</span>
            </div>
            """, unsafe_allow_html=True)
            if error:
                st.error(f"{error}")
            elif df is not None and df.empty:
                st.markdown('<div style="font-size:0.75rem;color:var(--text-dim);padding:14px 0;border:1px solid var(--border);border-top:none;padding:14px">Query ran — 0 rows returned. Check filter values (Borough must be uppercase: MANHATTAN, BROOKLYN…)</div>', unsafe_allow_html=True)
            elif df is not None:
                st.dataframe(df.head(200), use_container_width=True,
                             height=240, hide_index=False)

        # Chart
        if df is not None and not df.empty and len(df.columns) >= 2:
            num_cols = df.select_dtypes(include='number').columns.tolist()
            cat_cols = df.select_dtypes(exclude='number').columns.tolist()
            date_cols = [c for c in df.columns
                         if any(k in str(c).lower() for k in ('date', 'day', 'time', 'month'))]

            chart_theme = dict(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,17,23,0.6)",
                font=dict(family="JetBrains Mono, monospace",
                          color="#94a3b8", size=11),
                xaxis=dict(gridcolor="#2d3748", linecolor="#2d3748",
                           tickcolor="#2d3748", tickfont=dict(color="#94a3b8", size=10), zeroline=False),
                yaxis=dict(gridcolor="#2d3748", linecolor="#2d3748",
                           tickcolor="#2d3748", tickfont=dict(color="#94a3b8", size=10), zeroline=False),
                margin=dict(l=56, r=20, t=36, b=52),
                legend=dict(font=dict(color="#94a3b8", size=10),
                            bgcolor="rgba(0,0,0,0)"),
            )

            fig = None
            chart_type = ""

            if date_cols and num_cols:
                chart_type = "Time Series"
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df[date_cols[0]], y=df[num_cols[0]],
                    mode='lines', name=num_cols[0],
                    line=dict(color="#ff4500", width=2),
                    fill='tozeroy', fillcolor="rgba(255,69,0,0.06)"
                ))
                fig.update_layout(**chart_theme, height=260,
                                  title=dict(text=f"{num_cols[0]} over time",
                                             font=dict(color="#94a3b8", size=11), x=0.01))

            elif cat_cols and num_cols:
                df_plot = df[[cat_cols[0], num_cols[0]]].dropna().head(
                    20).sort_values(num_cols[0])
                if len(df_plot) <= 6:
                    chart_type = "Donut"
                    fig = go.Figure(go.Pie(
                        labels=df_plot[cat_cols[0]],
                        values=df_plot[num_cols[0]],
                        hole=0.55,
                        marker=dict(
                            colors=["#ff4500", "#ff6b35", "#e84393",
                                    "#63b3ed", "#48bb78", "#f6e05e"],
                            line=dict(color="#0d1117", width=3)
                        ),
                        textfont=dict(family="JetBrains Mono",
                                      size=11, color="#e2e8f0"),
                        textinfo="label+percent",
                    ))
                    fig.update_layout(**chart_theme, height=300,
                                      title=dict(text=f"{num_cols[0]} by {cat_cols[0]}",
                                                 font=dict(color="#94a3b8", size=11), x=0.01))
                else:
                    chart_type = "Horizontal Bar"
                    fig = go.Figure(go.Bar(
                        x=df_plot[num_cols[0]], y=df_plot[cat_cols[0]],
                        orientation='h',
                        marker=dict(
                            color=df_plot[num_cols[0]],
                            colorscale=[[0, "#1c2230"], [
                                0.4, "#7b2d00"], [1, "#ff4500"]],
                            line=dict(width=0),
                        ),
                        text=df_plot[num_cols[0]].apply(lambda v: f"{v:,.0f}"),
                        textposition="outside",
                        textfont=dict(color="#94a3b8", size=10),
                    ))
                    fig.update_layout(**chart_theme, height=max(240, len(df_plot)*32),
                                      title=dict(text=f"{num_cols[0]} by {cat_cols[0]}",
                                                 font=dict(color="#94a3b8", size=11), x=0.01))
                    fig.update_yaxes(tickfont=dict(size=11, color="#e2e8f0"))

            elif len(num_cols) >= 2:
                chart_type = "Scatter"
                fig = go.Figure(go.Scatter(
                    x=df[num_cols[0]], y=df[num_cols[1]],
                    mode='lines+markers',
                    line=dict(color="#ff4500", width=1.5),
                    marker=dict(size=4, color="#ff4500"),
                ))
                fig.update_layout(**chart_theme, height=260,
                                  title=dict(text=f"{num_cols[1]} vs {num_cols[0]}",
                                             font=dict(color="#94a3b8", size=11), x=0.01))

            if fig:
                st.markdown(f"""
                <div class="gq-panel-header" style="margin-top:14px">
                  <span>Visualization</span>
                  <span>{chart_type.upper()} · auto-detected</span>
                </div>
                """, unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})

    else:
        st.markdown("""
        <div class="gq-empty">
          <div class="gq-empty-icon">⬡</div>
          <div class="gq-empty-msg">Type a question or select an example above</div>
          <div class="gq-empty-sub">
            GROUP BY &nbsp;·&nbsp; HAVING &nbsp;·&nbsp; CTEs &nbsp;·&nbsp;
            Window Functions &nbsp;·&nbsp; Self-JOINs<br>
            Date Math &nbsp;·&nbsp; NULL Handling &nbsp;·&nbsp; CASE/WHEN &nbsp;·&nbsp; LIKE/ILIKE
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
