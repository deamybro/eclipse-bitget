"""
app/app.py - ECLIPSE Quantitative Alpha Terminal.
Bespoke Apple/Ramp luxury dark mode interface.
Displays 100% computed, real, verifiable metrics from Phase 0-13 pipeline runs.
"""

import streamlit as st
import streamlit.components.v1 as components

# Page Configuration
st.set_page_config(
    page_title="ECLIPSE // Quantitative Alpha Factory",
    page_icon="🌘",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Eliminate Streamlit borders, nested scrollbars, and header lag
st.markdown("""
<style>
    header[data-testid="stHeader"], footer, #MainMenu { 
        display: none !important; 
        height: 0px !important;
    }
    .block-container { 
        padding: 0 !important; 
        margin: 0 !important; 
        max-width: 100% !important; 
    }
    .stApp { 
        background-color: #000000 !important; 
        overflow: hidden !important; 
    }
    iframe { 
        width: 100vw !important; 
        height: 100vh !important; 
        border: none !important; 
        display: block !important; 
    }
</style>
""", unsafe_allow_html=True)

# Full-bleed unified luxury interface without nested scrollbar traps
components.iframe("http://localhost:3000", height=1000, scrolling=True)
