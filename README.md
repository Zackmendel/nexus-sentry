# 🛡️ Nexus Sentry: The Autonomous AI Risk Guardian

> **Building Safe Agentic Commerce on X Layer.**  
> *Winner-bound entry for the X Layer Global Developer Challenge.*

![Nexus Sentry Dashboard Mockup](https://raw.githubusercontent.com/placeholder-images/nexus-sentry/main/dashboard.png)

## 💡 The "Why": Beyond Static UIs
In high-velocity DeFi, static user interfaces are insufficient. In **March 2026**, a major liquidity event on Aave resulted in a single user losing **$50M** due to a catastrophic slippage error that a traditional UI failed to block. 

As trading transitions from human-initiated to **Agent-led**, we need an autonomous reasoning layer that can analyze, deliberate, and intervene in real-time. **Nexus Sentry** is that layer—a proactive "Cyber-Guardian" that sits between the intent and the execution, ensuring that 0xFF-style losses never happen on X Layer.

---

## 🧠 Technical Architecture

| Component | Technology | Role |
| :--- | :--- | :--- |
| **The Brain** | Google Gemini 2.5 Flash | Real-time "Nexus Reasoning" and risk deliberation. |
| **The Network** | X Layer (ZK-EVM) | Ultra-low latency execution and cryptographically secure settlement. |
| **The Economy** | x402 Protocol | Native agent-to-developer micro-donations and protocol fees. |
| **The Data** | OKX DEX Aggregator | Real-time liquidity depth and price impact analysis. |
| **The Frontend** | React + Vite | High-fidelity "Cyber-Guardian" Dashboard. |

---

## 🤖 The Agentic Workflow
Nexus Sentry operates as an autonomous gatekeeper through a three-stage lifecycle:

1.  **Analyze**: Sentry fetches deep liquidity data from the **OKX Aggregator API** on X Layer, measuring precise price impact for any given trade size.
2.  **Reason**: The raw data is fed into the **Gemini 2.5 Flash** "Sentry-Core." It doesn't just check numbers; it *reasons* about the risk relative to historical events (like the Aave Incident).
3.  **Resolve**: 
    *   🟢 **PROCEED**: If the trade is safe, the dashboard unlocks the execution layer.
    *   🔴 **BLOCK**: If the trade is dangerous, Sentry prevents execution and generates a **Resolution Panel** offering split-trade strategies, DCA plans, and liquidity alerts.

---

## 💰 Integrated Economy: x402 Protocol
Nexus Sentry features the first-of-its-kind **x402 Protocol** integration. Users can support the continuous development of the guardian network via a "Buy Me a Coffee" flow that triggers a real EVM handshake.

*   **Handshake**: 402 Payment Required integration.
*   **Settlement**: Seamless $1.00 USDC transaction on X Layer.
*   **Reward**: Immediate "Nexus Guardian Status" granted upon on-chain verification.

---

## 🚀 Demo Guide

### 1. Trigger a "BLOCK" (High Risk)
*   Enter a massive trade amount (e.g., `50000 OKB`).
*   Click **SCAN**.
*   **Result**: The UI will turn a subtle "Danger Red," the execution button will be disabled, and the **Nexus Resolution Panel** will activate with recovery strategies.

### 2. Trigger a "PROCEED" (Safe Trade)
*   Enter a standard trade amount (e.g., `1.0 OKB`).
*   Click **SCAN**.
*   **Result**: The indicator will glow green, the "Protection Score" will be high, and the trade execution path will be unlocked.

---

## 🧾 Submission Details
*   **Project Name**: Nexus Sentry
*   **Target Network**: X Layer (Chain ID: 196)
*   **Submission Transaction Hash**: `0xf846ebfc7322ed1cd7195a6257e258378d9c6a973289f8c84dc3da07587dfbdf`

---

## 🔭 The Vision: Safe Agentic Commerce
The future of finance isn't just about speed; it's about **trust**. By combining the reasoning capabilities of Gemini AI with the low-cost, high-performance infrastructure of X Layer, we are enabling a world where machines can trade millions with AI-guaranteed safety. Nexus Sentry is the first step toward a future where "Slippage Loss" is a historical relic.

---

### 🛠️ Local Development

```bash
# 1. Start the Backend (X Layer Sentry Node)
cd xlayer
pip install "x402[fastapi]" "x402[evm]" fastapi uvicorn google-genai
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 2. Start the Frontend (Nexus Guardian UI)
cd nexus-sentry-ui
npm install
npm run dev -- --port 3000
```

*Built with ❤️ for the X Layer Global Developer Challenge.*
