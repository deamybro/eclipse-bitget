"""
app/pages/6_UTA_Capital.py - Bitget Universal Transaction Account (UTA) Capital Economics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.uta.effective_capital import UTACapitalEngine

st.set_page_config(page_title="UTA Capital Engine // Haircut Economics", page_icon="🏦", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #F3F4F6; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🏦 UTA Capital Engine // Effective Collateral & Haircuts")
st.markdown("Models Bitget-specific piecewise collateral schedules, marginal capital efficiency, and internal shadow costs.")

uta = UTACapitalEngine()

notionals = np.linspace(10_000, 3_000_000, 100)
effective_vals = [uta.compute_effective_collateral(n) for n in notionals]
marginal_effs = [uta.compute_marginal_efficiency(n) * 100.0 for n in notionals]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Portfolio Nominal Notional", "$100,000", delta="Tier 1 Boundary")
with c2:
    st.metric("Effective Collateral Value", "$90,000", delta="90.0% Haircut Efficiency")
with c3:
    st.metric("Marginal Efficiency", "80.0%", delta="Next $1k Consumes 20% Haircut")
with c4:
    st.metric("Internal Shadow Cost", "4.2 bps", delta="Opportunity Cost of Capital")

fig = go.Figure()
fig.add_trace(go.Scatter(x=notionals, y=effective_vals, mode="lines", name="Effective Collateral ($)", line=dict(color="#00E676", width=2.5)))
fig.add_trace(go.Scatter(x=notionals, y=notionals, mode="lines", name="Nominal Value (1:1)", line=dict(color="rgba(255,255,255,0.3)", dash="dash")))

fig.update_layout(
    title="Piecewise Tiered Collateral Valuation Curve",
    paper_bgcolor="#000000",
    plot_bgcolor="#0A0C10",
    height=400,
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Nominal Position Notional ($)", tickprefix="$"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Effective Collateral Credit ($)", tickprefix="$")
)

st.plotly_chart(fig, use_container_width=True)
