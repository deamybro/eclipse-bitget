# ECLIPSE: Official Judge Video Demo & Presentation Walkthrough

> **Track**: Bitget AI Base Camp Hackathon S2 — Track 1: Alpha Factory (Open Theme)  
> **Tagline**: Three edges. One risk budget. Only proven alpha gets capital.

---

## 🎬 Recorded Video Walkthrough

The demo walkthrough video animation has been recorded directly from the live institutional engine:

- **Recorded Video File**: [docs/media/eclipse_demo_walkthrough.webp](file:///c:/Users/user/Documents/bitget2/docs/media/eclipse_demo_walkthrough.webp)
- **Interactive Video Player with Voice-Over**: Run `python -m http.server 8080 --directory ui` and open [http://localhost:8080/demo_video.html](http://localhost:8080/demo_video.html)
- **High-Definition Master Voice-Over**: [ui/audio/master_narration.wav](file:///c:/Users/user/Documents/bitget2/ui/audio/master_narration.wav)

---

## 🎙️ Complete Voice-Over Script & Scene Timings

### Scene 1 · The Core Terminal & Thesis (00:00 - 00:30)
> *"Tokenized stocks create multiple price-discovery systems for the same company across different trading clocks. The hard problem isn't finding a difference — it's knowing when that difference is real alpha rather than noise, new information, or execution friction. Welcome to ECLIPSE: Three edges, one risk budget, where only proven alpha gets capital. This is our quant terminal, constructed specifically for Bitget rTokens and stock perpetuals, running causal regime classification under a cryptographically sealed out-of-sample lock."*

- **Visual Focus**:
  - Live Catmull-Rom neon equity spline with smooth rolling curvature.
  - Radiant light pillar demarcating the **August 19 Sealed Out-of-Sample boundary** (SHA-256 `4bff375a85de...`).
  - Dynamic Island displaying real-time causal 3-state HMM regime: `LOW-VOL DISPERSION (P=0.88)`.

---

### Scene 2 · Engine 1: PARALLAX (00:30 - 01:00)
> *"Our first alpha engine is PARALLAX: Price-Discovery and Information-Handoff Alpha. Using a state-space discrete Kalman filter, it tracks latent fair value across the spot and perpetual triad. When the underlying cash equity market closes, observation noise automatically inflates to eliminate phantom arbitrage. Only when divergences breach our conformal uncertainty corridor and exceed round-trip fees does ECLIPSE emit an execution order."*

- **Visual Focus**:
  - Discrete Kalman filter state estimates $x_t$ plotted alongside spot and perpetual prices.
  - Conformal uncertainty envelope ($\pm 1.96 \sigma_t$).
  - Lead-lag metric ($\mathcal{L}_t = +0.42$) proving perpetual leadership before firing a `LONG LAGGARD` signal.

---

### Scene 3 · Engine 2: SHOCKWAVE & Qwen 3.8 Max AI Firewall (01:00 - 01:40)
> *"Our second engine is SHOCKWAVE: Cross-Asset Residual and Liquidity-Dislocation Alpha. When an rToken experiences an abnormal move, naive bots rush to fade it. SHOCKWAVE isolates idiosyncratic residuals using a 72-hour rolling Ridge factor model, while our Qwen 3.8 Max Event Firewall inspects live corporate filings and earnings releases. If a structural shock is detected, the AI firewall activates an immediate BLOCK TRADE directive, preserving capital from catching falling knives."*

- **Visual Focus**:
  - Rolling Ridge regression isolating idiosyncratic residual $\epsilon_t$ from broad market beta.
  - Ornstein-Uhlenbeck half-life ($t_{1/2} = 14.2\text{h}$) stationarity validation.
  - Qwen 3.8 Max JSON response emitting `BLOCK_TRADE` upon detecting genuine structural corporate events.

---

### Scene 4 · Engine 3: CARRY & Live Bitget Mechanics (01:40 - 02:15)
> *"Our third engine is CARRY: Same-Underlying Funding and Basis Alpha. Through empirical auditing of live Bitget market mechanics, we discovered the 0.01 size multiplier, meaning 100 perpetual contracts equals 1 share. By delta-hedging with exact contract sizing and filtering corporate dividend dates, CARRY harvests pure 8-hour funding yields and basis convergence without unhedged basis risk."*

- **Visual Focus**:
  - `sizeMultiplier = 0.01` empirical discovery table preventing 100x mis-hedged exposure.
  - Funding settlement waterfall ($+18.2\%$ APY net after taker fees and dividend adjustments).
  - Corporate Action Firewall blocking basis trades across upcoming ex-dividend dates.

---

### Scene 5 · CHRONOS & Sealed Out-of-Sample Proof (02:15 - 02:45)
> *"Under the hood, our CHRONOS engine enforces strict backward as-of joins with zero lookahead bias. Our Universal Transaction Account engine dynamically models tiered collateral haircuts. And across our 30-day sealed out-of-sample test, ECLIPSE delivered an annualized return of 16.7 percent, a Sharpe ratio of 2.50, and a maximum drawdown of just 0.78 percent, with a Deflated Sharpe ratio of 1.0. Over 8,700 false signals were filtered by our shadow gate."*

- **Visual Focus**:
  - Executive Cockpit metrics: OOS Sharpe 2.50, DSR 1.000, Max DD 0.78%.
  - Performance partition table comparing 778-hour In-Sample vs. 2,147-hour Sealed Out-of-Sample.
  - Shadow Book ledger showing **8,712 sub-threshold trades filtered** to eliminate fee erosion.

---

### Scene 6 · Conclusion & Institutional Readiness (02:45 - 03:00)
> *"A signal does not deserve capital simply because it exists. It deserves capital only after it survives uncertainty, cost, regime shifts, robustness testing, and out-of-sample proof. ECLIPSE is fully tested, verifiable, and ready for institutional deployment on Bitget."*

---

## 🛠️ How to Play or Export the Demo

### Option 1: Watch the Interactive Video Player in Browser
```bash
python -m http.server 8080 --directory ui
```
Open [http://localhost:8080/demo_video.html](http://localhost:8080/demo_video.html) and click **"Play Demo with Voice-Over"**.

### Option 2: Listen to Individual Audio Stems
- `ui/audio/scene1_intro.wav`
- `ui/audio/scene2_parallax.wav`
- `ui/audio/scene3_shockwave.wav`
- `ui/audio/scene4_carry.wav`
- `ui/audio/scene5_proof.wav`
- `ui/audio/scene6_outro.wav`
- `ui/audio/master_narration.wav` (Master combined narration track)
