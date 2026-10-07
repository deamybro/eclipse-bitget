"""
app/pages/1_Parallax.py - PARALLAX Price-Discovery & Latent Fair Value Deep-Dive.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="PARALLAX // Price-Discovery Alpha", page_icon="🌒", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #F3F4F6; }
    .metric-box { background: #0A0C10; border: 1px solid rgba(0, 242, 254, 0.2); border-radius: 12px; padding: 16px; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🌒 PARALLAX // Latent Fair-Value & Lead-Lag Engine")
st.markdown("Identifies price-discovery leadership and temporarily late representations across the triad.")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Information Leader", "Perpetual (NVDAUSDT)", delta="Lead Score: +0.42")
with c2:
    st.metric("Latent Fair Value Spread", "-12.4 bps", delta="Laggard Opportunity")
with c3:
    st.metric("Uncertainty Corridor Width", "±7.8 bps", delta="90% Conformal Band")
with c4:
    st.metric("Gate Status", "FULL_RISK", delta="34% Allocation")

st.write("")

# Synthetic visual reproduction of Kalman spread on NVDA
dates = pd.date_range("2026-08-19", periods=120, freq="1h")
np.random.seed(42)
fair_price = np.cumsum(np.random.normal(0, 0.5, 120)) + 220.0
spot_price = fair_price - np.random.normal(0.4, 0.3, 120)
perp_price = fair_price + np.random.normal(0.1, 0.2, 120)

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=fair_price + 0.8, mode="lines", line=dict(width=0), showlegend=False))
fig.add_trace(go.Scatter(
    x=dates, y=fair_price - 0.8, mode="lines", line=dict(width=0),
    fill="tonexty", fillcolor="rgba(0, 242, 254, 0.08)", name="Kalman Uncertainty Band"
))
fig.add_trace(go.Scatter(x=dates, y=fair_price, mode="lines", line=dict(color="#00F2FE", width=2, dash="dash"), name="Latent Fair Value"))
fig.add_trace(go.Scatter(x=dates, y=spot_price, mode="lines", line=dict(color="#00E676", width=2), name="rToken Spot (RNVDAUSDT)"))
fig.add_trace(go.Scatter(x=dates, y=perp_price, mode="lines", line=dict(color="#C084FC", width=1.5), name="Perpetual (NVDAUSDT)"))

fig.update_layout(
    title="State-Space Kalman Filter: Latent Log Fair Price vs Observed Triad",
    paper_bgcolor="#000000",
    plot_bgcolor="#0A0C10",
    height=420,
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickprefix="$"),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)
