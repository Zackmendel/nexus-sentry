from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from real_time import get_x_layer_quote, get_agent_decision
from x402 import x402ResourceServer
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.mechanisms.evm.constants import NETWORK_CONFIGS
from x402.schemas import SupportedResponse, SupportedKind, VerifyResponse, SettleResponse
import os

app = FastAPI()

# 1. Register X Layer Network
NETWORK_CONFIGS["eip155:196"] = {
    "chain_id": 196,
    "default_asset": {
        "address": "0x74b7f16337b8972027f6196a17a631ac6de26d22", # USDC
        "name": "USDC",
        "version": "1",
        "decimals": 6,
    },
}

# 2. x402 Configuration - Ensure path matches the endpoint exactly
routes = {
    "/api/tip-developer": {
        "accepts": {
            "scheme": "exact",
            "payTo": "0xdd60475c90c3371ccd1329179b5aee497d3faa5c",
            "price": "$1.00",
            "network": "eip155:196",
            "token": "0x74b7f16337b8972027f6196a17a631ac6de26d22"
        }
    }
}

# Mock Facilitator for Local Testing
class MockFacilitatorClient:
    def get_supported(self):
        return SupportedResponse(kinds=[SupportedKind(x402_version=2, scheme="exact", network="eip155:196")])
    async def verify(self, payload, requirements): return VerifyResponse(is_valid=True)
    async def settle(self, payload, requirements): return SettleResponse(success=True)

server = x402ResourceServer(MockFacilitatorClient())
server.register("eip155:196", ExactEvmServerScheme())

# 3. Add Middlewares in Correct Order
# Payment Middleware FIRST
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

# CORS Middleware SECOND to wrap the 402 responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["payment-required", "x-payment", "payment-response"]
)

# --- ROUTES ---

@app.get("/analyze") # Matching the api.py GET style
def analyze(from_token: str = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE", 
            to_token: str = "0x74b7f16337b8972027f6196a17a631ac6de26d22", 
            amount: str = "1000000000000000000"):
    
    result = get_x_layer_quote(from_token, to_token, amount)
    
    # Mock fallback if API fails
    if not (result.get("code") == "0" and result.get("data")):
        result = {"code": "0", "data": [{"toTokenAmount": "1050000000000000000", "priceImpactPercent": "3.5", "tradeFee": "0.001"}]}
        
    quote = result["data"][0]
    decision = get_agent_decision(quote)
    return {"quote": quote, "decision": decision}

@app.get("/api/tip-developer")
def tip_developer():
    return {"status": "success", "message": "Nexus Sentry thanks you for your support!"}