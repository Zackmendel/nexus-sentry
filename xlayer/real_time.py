import hmac
import hashlib
import base64
import requests
import os
import json
from google import genai
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

# Setup Gemini AI
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("GEMINI_API_KEY not found!")
client = genai.Client(api_key=gemini_key)

# --- CONFIGURATION ---
API_KEY = os.getenv("OKX_API_KEY")
SECRET_KEY = os.getenv("OKX_SECRET_KEY")
PASSPHRASE = os.getenv("OKX_PASSPHRASE")
PROJECT_ID = os.getenv("OKX_PROJECT_ID")
BASE_URL = "https://www.okx.com"

def get_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z")

def generate_signature(timestamp, method, request_path, body=""):
    message = timestamp + method.upper() + request_path + body
    mac = hmac.new(bytes(SECRET_KEY, encoding='utf8'), bytes(message, encoding='utf8'), digestmod=hashlib.sha256)
    return base64.b64encode(mac.digest()).decode('utf-8')

def get_x_layer_quote(from_token, to_token, amount):
    method = "GET"
    request_path = f"/api/v6/dex/aggregator/quote?chainIndex=196&fromTokenAddress={from_token}&toTokenAddress={to_token}&amount={amount}"
    
    timestamp = get_timestamp()
    signature = generate_signature(timestamp, method, request_path)

    headers = {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "OK-PROJECT-ID": PROJECT_ID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(BASE_URL + request_path, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_agent_decision(quote_data):
    """Nexus Sentry autonomous risk analysis."""
    # Ensure we are passing numeric values
    impact = quote_data.get('priceImpactPercent', quote_data.get('priceImpact', '0'))
    
    prompt = f"""
    You are 'Nexus Sentry', the primary AI Risk Guardian for X Layer.
    Analyze this trade to prevent catastrophic slippage loss.

    DATA:
    - Expected Output: {quote_data.get('toTokenAmount')}
    - Price Impact: {impact}%
    - Network Fee: {quote_data.get('tradeFee')}

    CONTEXT: 
    In March 2026, a user lost $50M on Aave. Your mission is to ensure this never happens on X Layer.

    TASK:
    1. If Price Impact > 2%, set action to 'BLOCK'.
    2. Provide a 'thought_log' (array of 3 strings) describing your internal reasoning.
    3. Calculate a 'protection_score' (0-100).

    OUTPUT ONLY JSON:
    {{
      "action": "BLOCK" | "PROCEED",
      "reasoning": "human-readable explanation",
      "thought_log": ["step 1...", "step 2...", "step 3..."],
      "protection_score": integer,
      "warning_message": "urgent alert text",
      "recommendations": {{
        "split_tranche_size": float,
        "split_count": integer,
        "dca_hours": integer,
        "liquidity_threshold": float,
        "alternative_routes_found": boolean
      }}
    }}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={'response_mime_type': 'application/json'}
    )
    return json.loads(response.text)

NATIVE_OKB = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
USDC_X_LAYER = "0x74b7f16337b8972027f6196a17a631ac6de26d22"

def analyze_trade(amount: str):
    """
    Analyzes a trade amount. 
    Input amount is in decimal units (e.g., 1.5 for 1.5 OKB).
    Converts to WEI before calling OKX API.
    """
    try:
        # Convert decimal amount to WEI (18 decimals for OKB)
        amount_in_wei = str(int(float(amount) * 1e18))
    except ValueError:
        return {"error": f"Invalid amount format: {amount}"}

    print(f"Nexus Sentry: Fetching X Layer Liquidity Data for {amount} OKB ({amount_in_wei} WEI)...")
    result = get_x_layer_quote(NATIVE_OKB, USDC_X_LAYER, amount_in_wei)

    if result.get("code") == "0" and result.get("data"):
        quote = result["data"][0]
        print(f"Price Impact: {quote.get('priceImpactPercent', 'N/A')}%")
        
        print("\nNexus Sentry is deliberating...")
        decision = get_agent_decision(quote)
        return decision
    else:
        return {"error": str(result)}

if __name__ == "__main__":
    amount_in_wei = "1000000000000000000" # 1 OKB
    print(json.dumps(analyze_trade(amount_in_wei), indent=2))