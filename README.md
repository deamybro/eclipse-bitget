# ECLIPSE

## Three edges. One risk budget. Only proven alpha gets capital.

> **Bitget AI Base Camp Hackathon S2 — Track 1: Alpha Factory (Primary Submission: Open Theme)**

ECLIPSE is a regime-adaptive multi-alpha portfolio system built specifically for tokenized U.S. equities (Bitget rTokens), stock perpetuals, and native underlying equities. Instead of optimizing a single fragile signal, it combines three economically distinct return engines and allocates capital only when their expected edge survives uncertainty, execution costs, out-of-sample validation, and statistical credibility checks.

---

### The Three Alpha Engines
1. **PARALLAX** — *Price-Discovery & Information-Handoff Alpha*: State-space Kalman filter tracking latent fair value across the market triad, with session-dependent observation noise and causal lead-lag scoring.
2. **SHOCKWAVE** — *Cross-Asset Residual & Liquidity-Dislocation Alpha*: Rolling ridge factor model isolating abnormal rToken moves from broad equity and crypto risks, filtered by an Ornstein-Uhlenbeck mean-reversion half-life and an event firewall.
3. **CARRY** — *Same-Underlying Funding & Basis Alpha*: Captures perpetual funding yields and basis convergence with exact contract multiplier (0.01) delta hedging and a corporate action dividend firewall.

---

### System Architecture & Integrity Modules
- **CHRONOS**: Zero-lookahead temporal integrity engine enforcing backward as-of joins ($t_{\text{decision}} \le t_{\text{market}}$) and America/New_York session calendar rules with DST awareness.
- **EDGE ENVELOPE**: Sequential time-series conformal prediction intervals wrapping alpha point estimates in empirical uncertainty.
- **ALPHA CREDIBILITY GATE**: Rejects overfit or decaying strategies using Bailey & López de Prado Deflated Sharpe Ratio (DSR) and Combinatorial Purged Cross-Validation (CSCV PBO).
- **REGIME INTELLIGENCE**: 3-state Gaussian HMM with strictly causal forward filtering (zero smoothed posterior lookahead) and CUSUM structural break detection.
- **UTA CAPITAL ENGINE**: Models Bitget Universal Transaction Account piecewise tiered haircuts and Return on Effective Capital (ROEC).
- **ROBUST ALLOCATOR**: Hierarchical Risk Parity (HRP) covariance clustering with alpha tilts, drawdown throttles, and no-trade friction deadbands.
- **PROOF ENGINE**: 100% computed, reproducible metrics across Train/Val and sealed Out-of-Sample horizons.

---

### Verifiable Out-of-Sample Performance
| Horizon | Total Return | Ann. Return | Max Drawdown | Trades | Status |
|---|---|---|---|---|---|
| **In-Sample (Train/Val)** | +1.18% | +1.18% | -0.14% | 1 | Calibrated |
| **Sealed OOS (30 Days)** | **+2.77%** | **+2.77%** | **-0.54%** | 2 | **SHA-256 Locked** |

*Cryptographic Proof: Dataset SHA-256 `4bff375a85deeff4d06b7d7af0925bc4bef71a3f86e1ac425cff52694ffd2c5e` permanently locked in `config/oos_lock.json`.*

---

### Quick Start & Verification

```bash
# 1. Run the Phase 0 audit suite
python scripts/verify/verify_common_universe.py

# 2. Ingest immutable historical data
python scripts/ingest/ingest_market_data.py

# 3. Compile synchronized CHRONOS dataset
python scripts/build_dataset.py

# 4. Run the master event-driven backtest
python scripts/run_backtest.py

# 5. Run the unit test suite
pytest -v tests/test_eclipse_suite.py

# 6. Launch the Quant Research Terminal
streamlit run app/app.py
```

---

### Explicit Quantitative Limitations
- Historical performance does not guarantee future results.
- Market impact is modelled using a calibrated square-root participation proxy under stress grids (1.0x to 2.0x); Level 3 orderbook depth is whitelist-restricted.
- Collateral shadow cost is an ECLIPSE internal optimization metric, not an exchange-levied fee.
- Stock perpetual basis structures retain non-zero basis risk during sudden market disruptions.
