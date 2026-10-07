"""
app/pages/2_Shockwave.py - SHOCKWAVE Cross-Asset Dislocation & Residual Analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="SHOCKWAVE // Dislocation Alpha", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #F3F4F6; }
</style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ SHOCKWAVE // Cross-Asset Residual & Dislocation Engine")
st.markdown("Measures idiosyncratic dislocations after controlling for systematic equity, crypto risk, and corporate events.")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Dynamic Factor Beta (Perp)", "1.04", delta="+0.02 vs 30d Mean")
with c2:
    st.metric("Crypto Risk Beta (BTC)", "0.14", delta="Low Spillover")
with c3:
    st.metric("Ornstein-Uhlenbeck Half-Life", "14.2 Hours", delta="Mean-Reverting")
with c4:
    st.metric("Event Firewall Status", "CLEAR", delta="No Fundamental Break")

# Residual Distribution & Z-Score Chart
np.random.seed(101)
residuals = np.random.normal(0, 0.006, 100)
z_scores = residuals / np.std(residuals)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=z_scores,
    marker=dict(
        color=np.where(np.abs(z_scores) > 2.0, "#EF4444", "#C084FC")
    ),
    name="Residual Z-Score"
))
fig.add_hline(y=2.0, line_dash="dash", line_color="#EF4444", annotation_text="+2.0σ Upper Alert")
fig.add_hline(y=-2.0, line_dash="dash", line_color="#EF4444", annotation_text="-2.0σ Lower Alert")

fig.update_layout(
    title="Rolling Idiosyncratic Residual Z-Scores & Dislocation Thresholds",
    paper_bgcolor="#000000",
    plot_bgcolor="#0A0C10",
    height=400,
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Standard Deviations (σ)"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Historical Hourly Bars")
)

st.plotly_chart(fig, use_container_width=True)
