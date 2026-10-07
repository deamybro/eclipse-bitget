# ECLIPSE: Explicit Quantitative Limitations

In strict adherence to the **No-Fake-Numbers** mandate, ECLIPSE explicitly documents the following technical and market limitations:

1. **Modelled Market Impact**:
   - Because historical Level-3 tick-by-tick orderbook archives require proprietary institutional VIP whitelisting on Bitget, execution slippage is estimated using a calibrated square-root participation model:
     $$\text{Impact} = \alpha \cdot \sigma_{\text{bar}} \cdot \sqrt{\frac{\text{Order Notional}}{\text{Bar Turnover}}}$$
   - Performance has been verified under a conservative cost stress grid up to 2.0x base friction.

2. **Collateral Shadow Cost**:
   - The Collateral Shadow Cost metric is ECLIPSE's internal mathematical optimization concept reflecting the opportunity cost of consuming scarce margin under piecewise haircut schedules. It is **not** an exchange-billed fee.

3. **No Liquidation Attribution**:
   - SHOCKWAVE detects statistically abnormal factor residuals and tests for mean-reversion stationarity. It does not claim to identify specific forced liquidations or order flow intent.

4. **Basis Risk in Delta-Neutral Structures**:
   - While CARRY hedges directional equity beta using verified contract multipliers ($M = 0.01$), the spread retains basis risk during extreme market decoupling or exchange maintenance windows.

5. **Historical Collateral Schedule Segregation**:
   - Historical backtests use baseline un-tilted cash accounting to prevent lookahead bias regarding historical tier adjustments, reserving the UTA capital engine for live capital sizing and forward scenario analysis.
