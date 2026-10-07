# ECLIPSE: Mathematical & Architectural Methodology
**System: ECLIPSE — Adaptive Multi-Alpha / Execution-Aware Portfolio**
**Track: Bitget AI Base Camp Hackathon S2 — Track 1: Alpha Factory**

---

## 1. Mathematical Specifications of the Three Alpha Engines

### 1.1 PARALLAX: Price-Discovery / Information-Handoff Alpha
PARALLAX tracks the unobservable true latent log fair price $x_t$ across the market triad using a discrete state-space Kalman filter:

$$\begin{aligned}
x_t &= x_{t-1} + w_t, \quad w_t \sim \mathcal{N}(0, Q) \\
y_{i,t} &= x_t + v_{i,t}, \quad v_{i,t} \sim \mathcal{N}(0, R_{i,t})
\end{aligned}$$

where observations $y_{\text{spot}, t}, y_{\text{perp}, t}$ are fused via inverse-variance weighting. When the underlying cash equity market is closed ($t \notin [09:30, 16:00]$ ET), measurement noise variance $R_{\text{spot}, t}$ is inflated dynamically:

$$R_{\text{spot}, t} = R_0 \cdot \left(1 + \lambda \sqrt{\Delta t_{\text{ref}}}\right)$$

where $\Delta t_{\text{ref}}$ is the reference age in elapsed hours.

Causal lead-lag contribution is evaluated by computing lagged cross-correlations between spot and perpetual innovations:

$$\mathcal{L}_t = \text{Corr}(r_{\text{perp}, t-1}, r_{\text{spot}, t}) - \text{Corr}(r_{\text{spot}, t-1}, r_{\text{perp}, t})$$

A signal is emitted only if:
1. Observed price is outside the Kalman uncertainty corridor ($\|y_{\text{spot}} - x_t\| > 1.96 \sigma_t$).
2. Leadership metric satisfies $\|\mathcal{L}_t\| \ge 0.10$.
3. Expected convergence exceeds round-trip transaction costs plus the uncertainty buffer.

---

### 1.2 SHOCKWAVE: Cross-Asset Residual / Dislocation Alpha
SHOCKWAVE models rToken returns as a dynamic multi-factor regression:

$$r_{\text{rtoken}, t} = \beta_{\text{perp}, t} r_{\text{perp}, t} + \beta_{\text{btc}, t} r_{\text{btc}, t} + \beta_{\text{eth}, t} r_{\text{eth}, t} + \epsilon_t$$

Parameters $\boldsymbol{\beta}_t$ are estimated via rolling Ridge regression over a 72-hour historical window.

The idiosyncratic residual $\epsilon_t$ is tested for Ornstein-Uhlenbeck mean-reversion stationarity:

$$\epsilon_t = \phi \epsilon_{t-1} + \eta_t$$

If $0 < \phi < 1$, the half-life of mean reversion is calculated:

$$t_{1/2} = -\frac{\ln(2)}{\ln(\phi)}$$

If $t_{1/2} > 48$ hours or $\phi \ge 1$, the residual is non-stationary and the signal is suppressed. If a company-specific fundamental event (earnings, SEC 8-K) is detected, the Event Firewall activates and rejects fading the move.

---

### 1.3 CARRY: Same-Underlying Basis & Funding Alpha
CARRY isolates funding yield and basis convergence under strict contract multiplier hedging:

$$\text{Basis}_t = \ln\left(\frac{P_{\text{perp}, t}}{P_{\text{rtoken}, t}}\right)$$

Required perpetual hedge ratio:

$$N_{\text{contracts}} = \frac{N_{\text{shares}}}{M_{\text{contract}}} = \frac{N_{\text{shares}}}{0.01} = 100 \cdot N_{\text{shares}}$$

Expected Net Carry:

$$\mathbb{E}[\text{NetCarry}] = \mathbb{E}[\text{Funding}_{48\text{h}}] + \mathbb{E}[\text{BasisConvergence}] - \text{Fees}_{\text{roundtrip}} - \text{Slippage} - \text{DivAdjustment}$$

If impending dividend obligations or fees exceed gross yield, the Corporate Action Firewall suppresses entry.

---

## 2. Statistical Credibility & Multiple-Testing Adjustments

### 2.1 Deflated Sharpe Ratio (DSR)
Following Bailey & López de Prado (2014), the benchmark Sharpe ratio under $N$ tested trials is:

$$\text{SR}^* \approx \sqrt{V} \left( (1 - \gamma) \Phi^{-1}\left(1 - \frac{1}{N}\right) + \gamma \Phi^{-1}\left(1 - \frac{1}{Ne}\right) \right)$$

where $\gamma \approx 0.5772$ is the Euler-Mascheroni constant and $V$ is the variance of tested Sharpes. DSR computes the probability that the observed Sharpe exceeds $\text{SR}^*$ under non-normal returns.

### 2.2 Probability of Backtest Overfitting (PBO)
Combinatorial Purged Cross-Validation (CSCV) partitions the $T \times N$ strategy performance matrix into combinations of training and testing subsets, quantifying the empirical probability that the In-Sample optimal strategy achieves below-median Out-of-Sample rank.
