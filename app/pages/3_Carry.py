"""
app/pages/3_Carry.py - CARRY Multi-Leg Funding & Basis Convergence.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="CARRY // Basis & Funding Alpha", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #F3F4F6; }
</style>
""", unsafe_allow_html=True)

st.markdown("## ⚖️ CARRY // Same-Underlying Funding & Basis Engine")
st.markdown("Harvests spot-perp funding premiums and basis convergence under strict contract multiplier hedging.")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Annualized Funding Rate", "+2.94%", delta="8h Settlement")
with c2:
    st.metric("Log Basis ln(P_perp / P_spot)", "+16.8 bps", delta="Perp Premium")
with c3:
    st.metric("Round-Trip Friction", "-6.4 bps", delta="Fees + Impact")
with c4:
    st.metric("Expected Net Carry", "+18.2% APY", delta="Dividend Firewall: PASS")

# Waterfall Net Carry Breakdown
fig = go.Figure(go.Waterfall(
    name="Carry Decomposition",
    orientation="v",
    measure=["relative", "relative", "relative", "relative", "total"],
    x=["Expected Funding", "Basis Convergence", "Exchange Fees", "Modelled Slippage", "Net Expected Carry"],
    textposition="outside",
    text=["+14.2 bps", "+12.0 bps", "-4.0 bps", "-2.4 bps", "+19.8 bps"],
    y=[14.2, 12.0, -4.0, -2.4, 19.8],
    connector=dict(line=dict(color="rgba(255,255,255,0.2)")),
    decreasing=dict(marker=dict(color="#EF4444")),
    increasing=dict(marker=dict(color="#00E676")),
    totals=dict(marker=dict(color="#00F2FE"))
))

fig.update_layout(
    title="Net Expected Carry Waterfall (Basis Points per 48h Window)",
    paper_bgcolor="#000000",
    plot_bgcolor="#0A0C10",
    height=420,
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Basis Points (bps)")
)

st.plotly_chart(fig, use_container_width=True)
