import React, { useState, useEffect } from 'react';
import { ShieldAlert, ShieldCheck, Activity, Terminal, AlertTriangle, Zap, PieChart, Calendar, Search, Globe, ShieldQuestion, Coffee, CheckCircle } from 'lucide-react';
import { x402Client, wrapFetchWithPayment } from '@x402/fetch';
import { ExactEvmScheme } from '@x402/evm';

// x402 Payment Initialization
const getEVMClient = () => {
  const client = new x402Client();
  
  // Real Signer that uses the browser wallet (window.ethereum)
  const walletSigner = {
    get address() {
      return window.ethereum?.selectedAddress || '0x0000000000000000000000000000000000000000';
    },
    signTypedData: async (args) => {
      if (!window.ethereum) throw new Error('No wallet extension found');
      // Ensure we have an account connected
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      const from = accounts[0];
      
      // The x402 SDK expects signTypedData to match the EIP-712 standard
      return await window.ethereum.request({
        method: 'eth_signTypedData_v4',
        params: [from, JSON.stringify(args)]
      });
    }
  };

  client.register('eip155:196', new ExactEvmScheme(walletSigner));
  return client;
};

const x402Fetch = wrapFetchWithPayment(window.fetch, getEVMClient());

export default function App() {
  const [amount, setAmount] = useState('1.0');
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [isTipped, setIsTipped] = useState(false);
  const [isTipping, setIsTipping] = useState(false);
  const [tipError, setTipError] = useState(null);
  const [showSupporterBadge, setShowSupporterBadge] = useState(false);

  const handleScan = async () => {
    setIsScanning(true);
    setResult(null);

    try {
      // Use the correct amount in basic units for the API
      const weiAmount = (parseFloat(amount) * 1e18).toString();
      const response = await fetch(`http://localhost:8000/analyze?amount=${weiAmount}`);
      const data = await response.json();
      setResult(data.decision ? { ...data.decision, reasoning: data.decision.thought_log[0], thought_log: data.decision.thought_log } : data);
    } catch (error) {
      console.error(error);
      setResult({ error: 'Failed to reach Nexus Sentry API' });
    } finally {
      setIsScanning(false);
    }
  };

  const handleTip = async () => {
    setIsTipping(true);
    setTipError(null);
    try {
      if (!window.ethereum) {
        throw new Error('Please install OKX Wallet or MetaMask to continue.');
      }
      
      const response = await x402Fetch('http://localhost:8000/api/tip-developer');
      const data = await response.json();
      
      if (data.status === 'success') {
        setIsTipped(true);
        setShowSupporterBadge(true);
        // Play success sound or visual effect logic could go here
      }
    } catch (error) {
      console.error('Payment failed deeper error:', error);
      // If it's a Failed to create payment payload error, try to extract the original cause
      const msg = error.message || 'Payment flow interrupted.';
      setTipError(msg);
    } finally {
      setIsTipping(false);
    }
  };

  const isBlocked = result?.action === 'BLOCK';
  const bgColor = isBlocked ? 'bg-red-950/40' : 'bg-slate-950';

  return (
    <div className={`min-h-screen ${bgColor} text-slate-100 transition-colors duration-500 font-sans p-6`}>
      <header className="flex items-center justify-between border-b border-sky-500/30 pb-4 mb-8">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-8 h-8 text-sky-400" />
          <h1 className="text-3xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-sky-600">
            NEXUS SENTRY
          </h1>
        </div>
        <div className="flex items-center gap-2 text-sm px-4 py-2 bg-slate-900 border border-slate-700 rounded-full shadow-inner">
          <Activity className="w-4 h-4 text-orange-500 animate-pulse" />
          <span className="text-slate-400">System Online</span>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: Terminal & Logs */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900/80 border border-slate-700 rounded-lg p-4 shadow-xl">
            <h2 className="text-lg font-semibold text-sky-400 flex items-center gap-2 mb-4 uppercase tracking-wide">
              <Terminal className="w-5 h-5" /> Thought Log
            </h2>
            <div className="bg-black/60 rounded p-4 h-64 overflow-y-auto terminal-scroll font-mono text-sm">
              <div className="text-sky-500/50 mb-2">{'>'} Initializing Guardian Protocol...</div>
              {result && result.thought_log ? (
                result.thought_log.map((log, idx) => (
                  <div key={idx} className="text-green-400 mb-2 leading-relaxed animate-fade-in" style={{ animationDelay: `${idx * 0.2}s` }}>
                    {'>'} {log}
                  </div>
                ))
              ) : (
                <div className="text-slate-600 italic">Waiting for scan data...</div>
              )}
            </div>
          </div>

          <div className="bg-orange-950/20 border border-orange-500/30 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-orange-400 flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4" /> Benchmark Info
            </h3>
            <p className="text-xs text-orange-200/70">
              Benchmarked against March 2026 Aave Liquidity Event.
            </p>
          </div>
        </div>

        {/* Right Column: Interaction & Output */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/80 border border-slate-700 rounded-lg p-6 shadow-xl relative overflow-hidden">
            {isScanning && (
              <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center">
                <div className="w-16 h-16 border-4 border-sky-500/30 border-t-sky-400 rounded-full animate-spin mb-4"></div>
                <h3 className="text-xl font-bold tracking-widest text-sky-400 animate-pulse uppercase">
                  Nexus Sentry Deliberating
                </h3>
              </div>
            )}
            
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              Trade Parameters
            </h2>
            
            <div className="space-y-4 mb-8">
              <div>
                <label className="block text-sm text-slate-400 mb-2 uppercase tracking-tighter">Amount (OKB)</label>
                <div className="flex gap-4 items-center">
                  <div className="relative flex-1">
                    <input
                      type="number"
                      step="0.1"
                      min="0.01"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="w-full bg-black/60 border-2 border-slate-700/50 rounded-lg px-4 py-3 text-sky-100 focus:outline-none focus:border-sky-500/80 font-mono text-lg transition-all"
                      placeholder="e.g. 1.0"
                    />
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 text-sky-500/50 font-bold select-none">OKB</div>
                  </div>
                  <button
                    onClick={handleScan}
                    disabled={isScanning}
                    className="group relative bg-sky-600 hover:bg-sky-500 text-white font-black py-4 px-10 rounded-lg shadow-[0_0_20px_rgba(14,165,233,0.3)] transition-all disabled:opacity-50 overflow-hidden"
                  >
                    <span className="relative z-10 tracking-widest">SCAN</span>
                    <div className="absolute inset-x-0 bottom-0 h-1 bg-sky-400 transform scale-x-0 group-hover:scale-x-100 transition-transform origin-left"></div>
                  </button>
                </div>
              </div>
            </div>

            {/* Results Section */}
            {result && !result.error && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-slate-800">
                <div className="flex flex-col items-center justify-center">
                  <h3 className="text-sm text-slate-400 mb-4 uppercase tracking-widest">Protection Score</h3>
                  <div className="relative w-40 h-40">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="45" fill="none" stroke="#1e293b" strokeWidth="8" />
                      <circle 
                        cx="50" cy="50" r="45" 
                        fill="none" 
                        stroke={result.protection_score > 80 ? "#10b981" : result.protection_score > 50 ? "#f59e0b" : "#ef4444"} 
                        strokeWidth="8" 
                        strokeDasharray={`${(result.protection_score / 100) * 283} 283`}
                        className="transition-all duration-1000 ease-out"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center flex-col">
                      <span className="text-4xl font-black">{result.protection_score}</span>
                      <span className="text-xs text-slate-400">/100</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col justify-center space-y-4">
                  {result.warning_message && (
                    <div className="bg-orange-950/40 border border-orange-500 text-orange-400 px-4 py-3 rounded-lg flex items-start gap-3 shadow-[0_0_10px_rgba(249,115,22,0.2)]">
                      <AlertTriangle className="w-6 h-6 flex-shrink-0 mt-0.5" />
                      <div>
                        <strong className="block text-sm uppercase mb-1">Nexus Alert</strong>
                        <span className="text-sm">{result.warning_message}</span>
                      </div>
                    </div>
                  )}

                  <div className="bg-black/30 p-4 rounded border border-slate-700">
                    <div className="text-sm text-slate-400 mb-1">Sentry Action</div>
                    <div className={`text-2xl font-black tracking-widest ${isBlocked ? 'text-red-500' : 'text-green-400'}`}>
                      {result.action}
                    </div>
                    {result.reasoning && (
                      <div className="text-sm mt-2 text-slate-300 italic">
                        "{result.reasoning}"
                      </div>
                    )}
                  </div>

                  <button
                    disabled={isBlocked}
                    className={`w-full py-3 rounded font-bold uppercase tracking-wider transition-all ${
                      isBlocked 
                        ? 'bg-slate-800 text-slate-500 cursor-not-allowed' 
                        : 'bg-green-600 hover:bg-green-500 text-white shadow-[0_0_15px_rgba(34,197,94,0.3)]'
                    }`}
                  >
                    {isBlocked ? 'Execution Blocked' : 'Execute Trade'}
                  </button>
                </div>
              </div>
            )}
            {result?.error && (
              <div className="mt-6 text-red-400 bg-red-950/30 p-4 rounded border border-red-500/30">
                Error: {result.error}
              </div>
            )}
          </div>
        </div>

        {/* Far Right Column: Proactive Guardian Resolution Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className={`bg-slate-900/80 border ${isBlocked ? 'border-sky-500/50' : 'border-slate-800'} rounded-lg p-5 shadow-2xl transition-all duration-500 ${!isBlocked && 'opacity-40 grayscale pointer-events-none'}`}>
            <h2 className={`text-lg font-bold flex items-center gap-2 mb-6 uppercase tracking-widest ${isBlocked ? 'text-sky-400' : 'text-slate-500'}`}>
              <ShieldQuestion className="w-5 h-5 text-sky-400" />
              Nexus Resolution Panel
            </h2>

            {!isBlocked ? (
              <div className="flex flex-col items-center justify-center h-full py-20 text-center">
                <ShieldCheck className="w-12 h-12 text-slate-700 mb-4 opacity-20" />
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-tighter">
                  No recommendations needed for safe execution.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Split Trade Strategy */}
                <div className="bg-slate-800/40 border border-slate-700 p-4 rounded-lg hover:border-sky-500/50 transition-colors group">
                  <div className="flex items-start gap-3 mb-3">
                    <PieChart className="w-5 h-5 text-sky-400 mt-1" />
                    <div>
                      <h4 className="text-sm font-bold text-sky-100 uppercase mb-1">Split Trade Strategy</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Divide this total into <span className="text-sky-400 font-bold">{result?.recommendations?.split_count || 10}</span> smaller tranches of <span className="text-sky-400 font-bold">{(amount / (result?.recommendations?.split_count || 10)).toFixed(2)} OKB</span> to reduce price impact under 1%.
                      </p>
                    </div>
                  </div>
                  <button className="w-full bg-sky-900/30 hover:bg-sky-600 border border-sky-500/30 text-sky-400 hover:text-white text-[10px] font-black py-2 rounded uppercase tracking-widest transition-all">
                    Generate Split Plan
                  </button>
                </div>

                {/* Automated DCA Plan */}
                <div className="bg-slate-800/40 border border-slate-700 p-4 rounded-lg hover:border-orange-500/50 transition-colors group">
                  <div className="flex items-start gap-3 mb-3">
                    <Calendar className="w-5 h-5 text-orange-400 mt-1" />
                    <div>
                      <h4 className="text-sm font-bold text-orange-100 uppercase mb-1">Automated DCA Plan</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Set up an autonomous DCA agent to buy <span className="text-orange-400 font-bold">{(amount / (result?.recommendations?.dca_hours || 24)).toFixed(2)} OKB</span> hourly over the next <span className="text-orange-400 font-bold">{result?.recommendations?.dca_hours || 24} hours</span>.
                      </p>
                    </div>
                  </div>
                  <button className="w-full bg-orange-950/20 hover:bg-orange-600 border border-orange-500/30 text-orange-400 hover:text-white text-[10px] font-black py-2 rounded uppercase tracking-widest transition-all">
                    Deploy DCA Agent
                  </button>
                </div>

                {/* Liquidity Threshold Alert */}
                <div className="bg-slate-800/40 border border-slate-700 p-4 rounded-lg hover:border-sky-500/50 transition-colors group">
                  <div className="flex items-start gap-3 mb-3">
                    <Search className="w-5 h-5 text-sky-400 mt-1" />
                    <div>
                      <h4 className="text-sm font-bold text-sky-100 uppercase mb-1">Liquidity Alert</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Create an alert for when depth for <span className="text-sky-400 font-bold">{amount} OKB</span> on X Layer drops below <span className="text-sky-400 font-bold">{result?.recommendations?.liquidity_threshold || 2.5}%</span> price impact.
                      </p>
                    </div>
                  </div>
                  <button className="w-full bg-sky-900/30 hover:bg-sky-600 border border-sky-500/30 text-sky-400 hover:text-white text-[10px] font-black py-2 rounded uppercase tracking-widest transition-all">
                    Set Liquidity Alert
                  </button>
                </div>

                {/* Alternative Router Re-scan */}
                <div className="bg-slate-800/40 border border-slate-700 p-4 rounded-lg hover:border-green-500/50 transition-colors group">
                  <div className="flex items-start gap-3 mb-3">
                    <Globe className="w-5 h-5 text-green-400 mt-1" />
                    <div>
                      <h4 className="text-sm font-bold text-green-100 uppercase mb-1">Router Re-scan</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Search deeper for alternative X Layer liquidity pools and DEX aggregators.
                      </p>
                    </div>
                  </div>
                  <button className="w-full bg-green-950/20 hover:bg-green-600 border border-green-500/30 text-green-400 hover:text-white text-[10px] font-black py-2 rounded uppercase tracking-widest transition-all">
                    Re-scan All Routes
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Buy Me a Coffee / Support Button */}
      <div className="fixed bottom-8 right-8 flex flex-col items-end gap-3 z-50">
        {tipError && (
          <div className="bg-red-950/40 border border-red-500/50 text-red-200 px-4 py-2 rounded-lg flex items-center gap-2 animate-bounce shadow-lg backdrop-blur-md">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            <span className="text-xs font-bold uppercase tracking-wider">{tipError}</span>
          </div>
        )}
        {isTipped && (
          <div className="bg-emerald-900/80 border border-emerald-400 text-emerald-100 px-6 py-3 rounded-lg flex items-center gap-3 animate-bounce shadow-[0_0_30px_rgba(16,185,129,0.4)] backdrop-blur-md">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <div className="flex flex-col">
              <span className="text-sm font-black uppercase tracking-widest">Nexus Guardian Status Achieved!</span>
              <span className="text-[10px] text-emerald-300/80 opacity-80 uppercase tracking-tighter">Handshake Protocol: Finalized on X Layer</span>
            </div>
          </div>
        )}
        
        <button
          onClick={handleTip}
          disabled={isTipping}
          className="group relative flex items-center gap-3 bg-amber-600/20 hover:bg-amber-500 border-2 border-amber-500/50 text-amber-500 hover:text-white px-6 py-3 rounded-full font-black uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(245,158,11,0.2)] hover:shadow-[0_0_30px_rgba(245,158,11,0.5)] overflow-hidden"
        >
          <div className={`absolute inset-0 bg-gradient-to-r from-amber-600 to-amber-400 opacity-0 group-hover:opacity-100 transition-opacity`}></div>
          <Coffee className={`w-5 h-5 relative z-10 ${isTipping ? 'animate-spin' : 'group-hover:scale-110 transition-transform'}`} />
          <span className="relative z-10">{isTipped ? 'SUPPORT CONFIRMED' : 'Support Nexus Sentry'}</span>
        </button>
      </div>
    </div>
  );
}
