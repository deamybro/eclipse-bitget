# ECLIPSE: System Blockers & Data Constraints Log

This document tracks all real-world constraints, missing API endpoints, unavailable permissions, and historical data limitations discovered during Phase 0 audit and live operations.

| Blocker ID | Domain | Description | Impact | Defensible Mitigation / Status |
|---|---|---|---|---|
| BLK-001 | Orderbook Depth Access | Level 2 / Level 3 full historical orderbook depth requires proprietary institutional whitelist access on Bitget. | Cannot calculate tick-level historical micro-slippage from raw book replay. | Calibrated bar-turnover square-root impact model (`MODELLED CAPACITY`) with stress testing grid (1.0x to 2.0x). |
| BLK-002 | Bitget Qwen API Key | Official Hackathon Qwen 3.8 Max subsidy key provided and integrated. | Live qualitative event classification is operational. | **RESOLVED & VERIFIED**: HTTP 200 via `https://hackathon.bitgetops.com/v1` (`model: qwen3.8-max`). Audited in `data/raw/audit_qwen.json`. |
| BLK-003 | Historical Collateral Schedules | Pre-2024 piecewise UTA haircut change logs are not published as a public historical time-series API. | Cannot apply backward-in-time dynamic tier changes without lookahead bias. | Use verified current published UTA schedule for forward capital efficiency and mark historical backtest without collateral tilt as baseline. |
| BLK-004 | Native Equity 1-Minute Live Stream | Direct real-time SIP consolidated tape requires direct NASDAQ/NYSE redistribution licenses. | Live cross-market arbitrage requires delayed or proxy native feed. | Use synchronized daily & hourly native bars from verified historical archives, tracking `reference_age_seconds` and session closed flags. |
