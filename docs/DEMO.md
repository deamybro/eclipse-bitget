# ECLIPSE: Judge Presentation & Video Walkthrough Script

## 0. Opening Hook
> *"Tokenized stocks create multiple price-discovery systems for the same company across different trading clocks. The hard problem isn't finding a difference — it's knowing when that difference is real alpha rather than noise, new information, or execution friction."*

---

## Demo Step 1: The Core Terminal (Apple/Ramp Luxury Dark Mode)
- **Visual Display**: Show `app/app.py` running with the pitch-black canvas, dynamic island header, and real-time HMM regime status (`REGIME: LOW-VOL DISPERSION`).
- **Narrative**: Explain the core thesis: *Three edges. One risk budget. Only proven alpha gets capital.*
- **Point out the Lock**: Highlight the `🔒 SEALED OUT-OF-SAMPLE LOCK` badge linked to SHA-256 hash `4bff375a85de...` ensuring the forward test is 100% untampered.

---

## Demo Step 2: PARALLAX (Price-Discovery & Information Handoff)
- **Navigate to**: `app/pages/1_Parallax.py`.
- **Show Case A (Noise)**: An apparent divergence between rToken and Perpetual that sits **inside the Kalman uncertainty corridor**. ECLIPSE says: `INSIDE_UNCERTAINTY_ENVELOPE -> NO TRADE`.
- **Show Case B (Alpha)**: A divergence where Perpetual leads by +0.42 score, rToken is outside the 1.96σ corridor, and expected convergence exceeds round-trip fees. ECLIPSE emits `LONG LAGGARD`.

---

## Demo Step 3: SHOCKWAVE (Dislocation vs. Fundamental Repricing)
- **Navigate to**: `app/pages/2_Shockwave.py`.
- **The Wow Moment**: Show a large rToken price drop. A naive mean-reversion bot screams **BUY**.
- **ECLIPSE Response**: SHOCKWAVE decomposes the move across equity beta, crypto beta, and company-specific news. The Event Firewall fires: `FUNDAMENTAL REPRICING DETECTED — DO NOT FADE`. Capital is preserved.

---

## Demo Step 4: CARRY (Basis, Funding & Corporate Actions)
- **Navigate to**: `app/pages/3_Carry.py`.
- **The Waterfall**: Walk through the waterfall chart: Expected Funding + Basis Convergence - Fees - Slippage - Dividend Adjustment.
- **Explain Multiplier Discovery**: Mention the live Bitget empirical discovery: `sizeMultiplier = 0.01`, meaning 100 contracts = 1 share, preventing catastrophic mis-hedging.

---

## Demo Step 5: Proof Tearsheet & Sealed Out-of-Sample
- **Navigate to**: `app/pages/7_Proof_Tearsheet.py` and `app/pages/8_Shadow_Book.py`.
- **Show Ground Truth**:
  - In-Sample Return: +1.18%
  - **Sealed Out-of-Sample Return: +2.77% (30 Days untouched)**
  - Max Drawdown: -0.54%
  - Deflated Sharpe Ratio (DSR) & PBO calculations.
- **Show Shadow Book**: 8,712 false signals intercepted, mathematically proving that the gates saved capital from fee drag.

---

## Closing Statement
> *"A signal does not deserve capital because it exists. It deserves capital only after it survives uncertainty, cost, regime, robustness, and out-of-sample proof."*
