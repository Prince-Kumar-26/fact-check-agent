"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [claim, setClaim] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [supportText, setSupportText] = useState("");
  const [opposeText, setOpposeText] = useState("");
  const [supportRebuttal, setSupportRebuttal] = useState("");
  const [opposeRebuttal, setOpposeRebuttal] = useState("");
  const [verdict, setVerdict] = useState<{ verdict: string; confidence: number; summary: string } | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      interval = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedTime(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);
  
  const handleFactCheck = async () => {
    if (!claim.trim()) return;
    
    setIsLoading(true);
    setElapsedTime(0);
    setStatus("Connecting to Fact Check Engine...");
    setSupportText("");
    setOpposeText("");
    setSupportRebuttal("");
    setOpposeRebuttal("");
    setVerdict(null);

    // Use NEXT_PUBLIC_BACKEND_URL if available (for Vercel/Render deployment), fallback to localhost
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || `http://${window.location.hostname}:8000`;
    const backendUrl = `${baseUrl.replace(/\/$/, '')}/api/factcheck/stream`;
    
    const response = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim }),
    });

    if (!response.body) {
      setIsLoading(false);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      // Split by \n\n or \r\n\r\n
      const lines = buffer.split(/\r?\n\r?\n/);
      buffer = lines.pop() || "";
      
      for (const line of lines) {
        if (line.includes("event: ")) {
          const eventTypeMatch = line.match(/event:\s*(.*)/);
          const dataMatch = line.match(/data:\s*(.*)/);
          
          if (eventTypeMatch && dataMatch) {
            const eventType = eventTypeMatch[1];
            const data = JSON.parse(dataMatch[1]);
            
            if (eventType === "status") {
              setStatus(data.message);
            } else if (eventType === "token") {
              if (data.node === "support_agent" || data.node === "oppose_agent") {
                setStatus("Agents are presenting their initial cases...");
              } else if (data.node === "support_rebuttal" || data.node === "oppose_rebuttal") {
                setStatus("Cross-examination and rebuttals in progress...");
              }
              
              if (data.node === "support_agent") {
                setSupportText(prev => prev + data.token);
              } else if (data.node === "oppose_agent") {
                setOpposeText(prev => prev + data.token);
              } else if (data.node === "support_rebuttal") {
                setSupportRebuttal(prev => prev + data.token);
              } else if (data.node === "oppose_rebuttal") {
                setOpposeRebuttal(prev => prev + data.token);
              }
            } else if (eventType === "verdict") {
              setVerdict(data);
              setStatus("");
              setIsLoading(false);
            } else if (eventType === "done") {
              setStatus("");
              setIsLoading(false);
            } else if (eventType === "error") {
              setStatus(`Error: ${data.reason}`);
              setIsLoading(false);
            }
          }
        }
      }
    }
  };

  return (
    <main className="max-w-6xl mx-auto p-8">
      <div className="text-center mb-12">
        <div className="w-20 h-20 bg-[#e0e5ec] rounded-full flex items-center justify-center mx-auto mb-6 neumorphic-panel">
          <span className="text-4xl">⚖️</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-800 mb-2">Fact Check Engine V2</h1>
        <p className="text-gray-500 font-medium">Powered by Next.js, Server-Sent Events, & Playwright</p>
      </div>
      <section className="guide-section neumorphic-panel mb-12">
        <h2 className="section-title text-center font-bold text-2xl mb-6">How it Works</h2>
        <div className="guide-grid grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="neumorphic-inset guide-step p-4 text-center rounded-2xl">
            <div className="step-number font-bold text-xl mb-2 text-blue-500">1</div>
            <h4 className="font-semibold mb-2">Submit a Claim</h4>
            <p className="text-gray-500 text-sm">Enter any factual statement. The system extracts atomic sub-claims.</p>
          </div>
          <div className="neumorphic-inset guide-step p-4 text-center rounded-2xl">
            <div className="step-number font-bold text-xl mb-2 text-blue-500">2</div>
            <h4 className="font-semibold mb-2">Dual Retrieval</h4>
            <p className="text-gray-500 text-sm">We search the live web for evidence to both PROVE and DISPROVE the claim.</p>
          </div>
          <div className="neumorphic-inset guide-step p-4 text-center rounded-2xl">
            <div className="step-number font-bold text-xl mb-2 text-blue-500">3</div>
            <h4 className="font-semibold mb-2">Agent Debate</h4>
            <p className="text-gray-500 text-sm">A Support Agent and Oppose Agent build their cases and cross-examine.</p>
          </div>
          <div className="neumorphic-inset guide-step p-4 text-center rounded-2xl">
            <div className="step-number font-bold text-xl mb-2 text-blue-500">4</div>
            <h4 className="font-semibold mb-2">Final Verdict</h4>
            <p className="text-gray-500 text-sm">An impartial AI Judge weighs the evidence and issues a definitive verdict.</p>
          </div>
        </div>

        <div className="topic-boundaries mt-8 text-center">
          <h3 className="mb-4 font-semibold text-lg">Supported Topics</h3>
          <div className="badges-container flex flex-wrap justify-center gap-4">
            <span className="neumorphic-badge px-4 py-2 rounded-full text-sm font-medium">🧬 Science</span>
            <span className="neumorphic-badge px-4 py-2 rounded-full text-sm font-medium">🏥 Health & Medicine</span>
            <span className="neumorphic-badge px-4 py-2 rounded-full text-sm font-medium">📰 Public Domain Facts</span>
            <span className="neumorphic-badge px-4 py-2 rounded-full text-sm font-medium">🌍 Current Events</span>
          </div>
          <p className="mt-4 text-gray-500 text-sm">Note: Political opinions and subjective claims are blocked by guardrails.</p>
        </div>

        <div className="quick-prompts mt-8 text-center">
          <h4 className="mb-4 text-gray-500 font-medium">Try a sample claim:</h4>
          <div className="badges-container flex flex-wrap justify-center gap-4">
            <button className="neumorphic-btn px-4 py-2 rounded-full text-sm" onClick={() => setClaim("mRNA vaccines alter human DNA")}>mRNA vaccines alter human DNA</button>
            <button className="neumorphic-btn px-4 py-2 rounded-full text-sm" onClick={() => setClaim("The Earth is flat")}>The Earth is flat</button>
            <button className="neumorphic-btn px-4 py-2 rounded-full text-sm" onClick={() => setClaim("Water boils at 100 degrees Celsius")}>Water boils at 100 degrees Celsius</button>
          </div>
        </div>
      </section>

      <div className="flex justify-center mb-12">
        <div className="flex gap-4 w-full max-w-2xl">
          <input
            type="text"
            className="flex-1 px-6 py-4 rounded-full neumorphic-input text-lg"
            placeholder="Enter a claim to verify..."
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleFactCheck()}
            disabled={isLoading}
          />
          <button 
            className="px-8 py-4 rounded-full neumorphic-btn font-semibold text-lg"
            onClick={handleFactCheck}
            disabled={isLoading}
          >
            {isLoading ? "Analyzing..." : "Verify"}
          </button>
        </div>
      </div>

      {status && (
        <div className="text-center mb-8">
          <div className="text-blue-600 font-semibold animate-pulse mb-2">
            {status}
          </div>
          {isLoading && (
            <div className="max-w-md mx-auto mt-4">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{elapsedTime}s elapsed</span>
                <span>Est: 45s</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-1000" 
                  style={{ width: `${Math.min((elapsedTime / 45) * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      )}

      {verdict && (
        <div className="neumorphic-panel text-center mb-8">
          <h2 className="text-2xl font-bold mb-4">Final Verdict</h2>
          <div className="inline-block p-6 neumorphic-inset mb-6">
            <span className={`text-4xl font-bold ${
              verdict.verdict.includes('True') ? 'text-green-600' :
              verdict.verdict.includes('False') ? 'text-red-600' :
              'text-orange-500'
            }`}>
              {verdict.verdict}
            </span>
            <span className="block mt-2 text-gray-500">
              Confidence: {Math.round(verdict.confidence)}%
            </span>
          </div>
          <p className="text-lg max-w-3xl mx-auto">{verdict.summary}</p>
        </div>
      )}

      {(supportText || opposeText) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="neumorphic-panel flex flex-col gap-4">
            <h2 className="text-xl font-bold text-green-600 text-center">Support Agent</h2>
            <div className="neumorphic-inset h-64 overflow-y-auto whitespace-pre-wrap text-sm p-4">
              {supportText}
            </div>
            {supportRebuttal && (
              <>
                <h4 className="font-semibold text-center mt-2">Rebuttal</h4>
                <div className="neumorphic-inset h-48 overflow-y-auto whitespace-pre-wrap text-sm p-4 text-gray-700">
                  {supportRebuttal}
                </div>
              </>
            )}
          </div>
          <div className="neumorphic-panel flex flex-col gap-4">
            <h2 className="text-xl font-bold text-red-500 text-center">Oppose Agent</h2>
            <div className="neumorphic-inset h-64 overflow-y-auto whitespace-pre-wrap text-sm p-4">
              {opposeText}
            </div>
            {opposeRebuttal && (
              <>
                <h4 className="font-semibold text-center mt-2">Rebuttal</h4>
                <div className="neumorphic-inset h-48 overflow-y-auto whitespace-pre-wrap text-sm p-4 text-gray-700">
                  {opposeRebuttal}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {(verdict || supportText) && (
        <div className="ai-disclaimer mt-12 text-gray-500 text-sm text-center max-w-3xl mx-auto">
          <p>⚠️ <strong>Disclaimer:</strong> This is an experimental AI-based fact-check engine. It can make mistakes or hallucinate evidence. Always verify critical information independently.</p>
        </div>
      )}
      
      <footer className="mt-16 text-center text-gray-400 text-sm pb-8">
        <p>&copy; 2026 Fact Check Debate Engine. Built with LangGraph, Next.js, and Neumorphism.</p>
      </footer>
    </main>
  );
}
