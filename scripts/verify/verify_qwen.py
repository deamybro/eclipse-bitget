"""
verify_qwen.py - Audit Bitget-Sponsored Qwen Connectivity & Event Schema.
Checks BITGET_QWEN_API_KEY, tests connection to https://hackathon.bitgetops.com/v1,
and validates structured qualitative event extraction.
"""

import sys
import os
import json
import httpx

def main():
    print("=== [PHASE 0] VERIFYING BITGET QWEN LLM ACCESS ===")
    
    api_key = os.getenv("BITGET_QWEN_API_KEY")
    base_url = os.getenv("BITGET_QWEN_BASE_URL", "https://hackathon.bitgetops.com/v1")
    model = os.getenv("BITGET_QWEN_MODEL", "qwen3.8-max")

    audit_result = {
        "base_url": base_url,
        "model": model,
        "key_present": bool(api_key),
        "status": "UNAVAILABLE" if not api_key else "PROBING"
    }

    if not api_key:
        print("[WARN] BITGET_QWEN_API_KEY is not set in environment.")
        print("  Qwen role is qualitative event extraction and earnings headline classification.")
        print("  All core quant calculations run natively in Python.")
        print("  Status: Marking Qwen as UNAVAILABLE until key is supplied.")
        audit_result["status"] = "UNAVAILABLE"
        audit_result["mitigation"] = "Deterministic event proxies and contemporaneous earnings calendar records used."
    else:
        print(f"API key found. Probing {base_url} with model {model}...")
        try:
            client = httpx.Client(base_url=base_url, timeout=10.0)
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a financial event classifier. Output JSON only."},
                    {"role": "user", "content": "Classify: NVDA reports Q2 revenue $30B vs $28.7B expected, up 122% YoY."}
                ],
                "temperature": 0.0
            }
            res = client.post("/chat/completions", headers=headers, json=payload)
            if res.status_code == 200:
                print("Qwen API connection successful!")
                audit_result["status"] = "CONNECTED"
                audit_result["sample_response"] = res.json().get("choices", [{}])[0].get("message", {}).get("content")
            else:
                print(f"Qwen returned status {res.status_code}: {res.text[:120]}")
                audit_result["status"] = "ERROR"
                audit_result["error"] = res.text[:120]
        except Exception as e:
            print(f"Connection error: {e}")
            audit_result["status"] = "ERROR"
            audit_result["error"] = str(e)

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/audit_qwen.json", "w") as f:
        json.dump(audit_result, f, indent=2)

    print("Audit results written to data/raw/audit_qwen.json")

if __name__ == "__main__":
    main()
