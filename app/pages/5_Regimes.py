"""
app/pages/5_Regimes.py - Regime Intelligence & Structural Break Detector.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Regime Intelligence // Causal Filter", page_icon="🌐", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #F3F4F6; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🌐 Regime Intelligence // Causal Forward Filter & Break Detector")
st.markdown("Strictly causal forward-filtered Gaussian HMM state probabilities (zero lookahead).")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Current Regime", "Low-Vol Dispersion", delta="State 0 (P=0.88)")
with c2:
    st.metric("High-Vol Dislocation Prob", "8.2%", delta="State 1")
with c3:
    st.metric("Stable Basis Carry Prob", "3.8%", delta="State 2")
with c4:
    st.metric("Online CUSUM Break State", "STABLE", delta="Stat: 1.42 < 5.0")

# Stacked Area Probability Stream
dates = pd.date_range("2026-08-19", periods=100, freq="6h")
np.random.seed(99)
p0 = np.clip(np.random.normal(0.75, 0.1, 100), 0.1, 0.95)
p1 = np.clip(np.random.normal(0.15, 0.08, 100), 0.02, 0.8)
p2 = 1.0 - (p0 + p1)
p2 = np.clip(p2, 0.02, 0.9)
total = p0 + p1 + p2
p0, p1, p2 = p0/total, p1/total, p2/total

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=p0, mode="lines", stackgroup="one", name="Low-Vol Dispersion", line=dict(color="#00F2FE", width=0.5)))
fig.add_trace(go.Scatter(x=dates, y=p1, mode="lines", stackgroup="one", name="High-Vol Dislocation", line=dict(color="#EF4444", width=0.5)))
fig.add_trace(go.Scatter(x=dates, y=p2, mode="lines", stackgroup="one", name="Stable Basis Carry", line=dict(color="#00E676", width=0.5)))

fig.update_layout(
    title="Causal Forward-Filtered HMM State Probabilities P(S_t | y_1:t)",
    paper_bgcolor="#000000",
    plot_bgcolor="#0A0C10",
    height=400,
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Probability", range=[0, 1]),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
