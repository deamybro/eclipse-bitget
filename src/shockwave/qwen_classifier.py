"""
src/shockwave/qwen_classifier.py - Production Qwen 3.8 Max Event Classifier.
Utilizes the Bitget-sponsored Qwen endpoint (https://hackathon.bitgetops.com/v1)
to classify corporate news, earnings releases, and SEC filings for the SHOCKWAVE Event Firewall.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("eclipse.qwen")


class EventClassification(BaseModel):
    symbol: str
    is_fundamental_shock: bool = False
    event_type: str = "noise"
    sentiment: str = "neutral"
    confidence: float = 0.5
    firewall_action: str = "ALLOW_TRADE"  # "BLOCK_TRADE" or "ALLOW_TRADE"
    raw_response: Optional[str] = None


class QwenEventClassifier:
    """Production Qwen 3.8 Max qualitative event classifier for Bitget Hackathon S2."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0
    ):
        self.api_key = api_key or os.getenv("BITGET_QWEN_API_KEY", "joodwdgjXhQy4fBC")
        self.base_url = base_url or os.getenv("BITGET_QWEN_BASE_URL", "https://hackathon.bitgetops.com/v1")
        self.model = model or os.getenv("BITGET_QWEN_MODEL", "qwen3.8-max")
        self.timeout = timeout
        self._cache: Dict[str, EventClassification] = {}

    def classify_headline(self, symbol: str, headline: str) -> EventClassification:
        """
        Classifies a market headline into fundamental shock or noise.
        Strictly blocks mean-reversion when a genuine structural corporate shock occurs.
        """
        cache_key = f"{symbol}:{headline.strip().lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.api_key:
            return EventClassification(
                symbol=symbol,
                is_fundamental_shock=False,
                event_type="noise",
                confidence=0.5,
                firewall_action="ALLOW_TRADE"
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "You are an institutional financial event classifier for a multi-alpha quant portfolio. "
            "Analyze the headline for the given tokenized equity. "
            "Determine if this is a genuine structural fundamental shock (earnings surprise, fraud investigation, "
            "CEO resignation, acquisition, FDA rejection) that invalidates short-term statistical mean reversion, "
            "or routine noise/momentum where mean reversion is safe. "
            "Output strictly valid JSON with keys: "
            "'is_fundamental_shock' (boolean), 'event_type' (string), 'sentiment' (positive/negative/neutral), "
            "'confidence' (float between 0 and 1), 'firewall_action' ('BLOCK_TRADE' if is_fundamental_shock else 'ALLOW_TRADE')."
        )

        user_content = f"Symbol: {symbol}\nHeadline: {headline}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.0,
            "max_tokens": 150
        }

        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                res = client.post("/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                    
                    # Clean markdown codeblocks if returned
                    clean_content = content.strip()
                    if clean_content.startswith("```json"):
                        clean_content = clean_content[7:]
                    if clean_content.startswith("```"):
                        clean_content = clean_content[3:]
                    if clean_content.endswith("```"):
                        clean_content = clean_content[:-3]
                    clean_content = clean_content.strip()

                    parsed = json.loads(clean_content)
                    is_shock = bool(parsed.get("is_fundamental_shock", False))
                    action = "BLOCK_TRADE" if is_shock else "ALLOW_TRADE"

                    result = EventClassification(
                        symbol=symbol,
                        is_fundamental_shock=is_shock,
                        event_type=str(parsed.get("event_type", "unspecified")),
                        sentiment=str(parsed.get("sentiment", "neutral")),
                        confidence=float(parsed.get("confidence", 0.85)),
                        firewall_action=action,
                        raw_response=content
                    )
                    self._cache[cache_key] = result
                    return result
                else:
                    logger.warning(f"Qwen returned HTTP {res.status_code}: {res.text[:100]}")
        except Exception as e:
            logger.warning(f"Qwen classification failed with error: {e}")

        # Fallback to statistical default
        fallback = EventClassification(
            symbol=symbol,
            is_fundamental_shock=False,
            event_type="network_fallback",
            confidence=0.5,
            firewall_action="ALLOW_TRADE"
        )
        self._cache[cache_key] = fallback
        return fallback
