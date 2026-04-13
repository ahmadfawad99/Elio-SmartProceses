"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Activity,
  ArrowUpRight,
  Bot,
  Gauge,
  Radar,
  ShieldAlert,
  Snowflake,
  Zap,
} from "lucide-react";

// --- Types ---

interface Reading {
  rack_id: string;
  cpu_usage: number;
  cpu_temp: number;
  power_kw: number;
  fan_rpm: number;
  ups_load: number;
  is_anomaly: boolean;
  fault_type: string | null;
  timestamp: string;
}

interface AgentEvent {
  agent: string;
  status: "running" | "complete";
  step: number;
  message: string;
  reasoning?: string;
  correlation_id: string;
  severity?: string;
}

interface WorkOrder {
  id: string;
  rack_id: string;
  severity: string;
  failure_type: string;
  action_type: string;
  priority: string;
  assigned_to: string;
  sla_hours: number;
  anomaly_score: number;
  time_to_failure_minutes: number;
  reasoning: string;
  created_at: string;
  correlation_id: string;
}

// --- Helpers ---

function toneClasses(tone: string) {
  switch (tone) {
    case "emerald":
      return "from-emerald-400/25 to-emerald-500/5 text-emerald-100";
    case "amber":
      return "from-amber-400/25 to-amber-500/5 text-amber-100";
    case "rose":
      return "from-rose-400/25 to-rose-500/5 text-rose-100";
    default:
      return "from-cyan-400/25 to-sky-500/5 text-cyan-100";
  }
}

function buildPath(values: number[], width: number, height: number, minVal: number = 0, maxVal: number = 100) {
  if (values.length < 2) return "";
  const range = Math.max(maxVal - minVal, 1);

  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - minVal) / range) * height;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

// --- Components ---

function MetricCard({ label, value, change, detail, tone }: any) {
  return (
    <div className={`rounded-[28px] border border-white/10 bg-gradient-to-br ${toneClasses(tone)} p-5`}>
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-200/80">{label}</p>
        <ArrowUpRight className="h-4 w-4 text-white/75" />
      </div>
      <p className="mt-5 text-4xl font-semibold tracking-[-0.05em] text-white">
        {value}
      </p>
      <p className="mt-2 text-sm text-white/80">{change}</p>
      <p className="mt-4 text-sm leading-6 text-slate-300">{detail}</p>
    </div>
  );
}

export default function Home() {
  const [readings, setReadings] = useState<Reading[]>([]);
  const [history, setHistory] = useState<Record<string, Reading[]>>({});
  const [agentLogs, setAgentLogs] = useState<AgentEvent[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket("ws://localhost:8000/demo/ws");

      ws.current.onopen = () => {
        setConnected(true);
        console.log("Connected to Elio Backend");
      };

      ws.current.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "initial_state") {
          setReadings(msg.data.readings);
          setHistory(msg.data.history);
        } else if (msg.type === "metrics_update") {
          setReadings(msg.data);
          setHistory(prev => {
            const next = { ...prev };
            msg.data.forEach((r: Reading) => {
              const h = [...(next[r.rack_id] || []), r];
              next[r.rack_id] = h.slice(-30);
            });
            return next;
          });
        } else if (msg.type === "agent_event") {
          setAgentLogs(prev => [msg.data, ...prev].slice(0, 10));
        } else if (msg.type === "work_order") {
          setWorkOrders(prev => [msg.data, ...prev].slice(0, 5));
        }
      };

      ws.current.onclose = () => {
        setConnected(false);
        console.log("Disconnected. Reconnecting...");
        setTimeout(connect, 2000);
      };
    };

    connect();
    return () => ws.current?.close();
  }, []);

  const simulateFault = async (rack_id: string, type: string) => {
    try {
      await fetch(`http://localhost:8000/demo/simulate-fault?rack_id=${rack_id}&fault_type=${type}`, {
        method: "POST",
      });
    } catch (err) {
      console.error("Fault simulation failed", err);
    }
  };

  const clearFaults = async () => {
    await fetch("http://localhost:8000/demo/clear-faults", { method: "POST" });
    setAgentLogs([]);
    setWorkOrders([]);
  };

  // Aggregated view for metrics
  const latestA12 = readings.find(r => r.rack_id === "A-12") || readings[0];
  const avgCpu = Math.round(readings.reduce((acc, r) => acc + r.cpu_usage, 0) / (readings.length || 1));
  const avgMem = 65; // Fixed for demo
  const maxTemp = Math.round(Math.max(...readings.map(r => r.cpu_temp), 0));
  const latestRisk = workOrders[0]?.anomaly_score || 0.12;

  const summaryMetrics = [
    { label: "Fleet CPU", value: `${avgCpu}%`, change: "Live", detail: "Avg utilization across east fabric", tone: "cyan" },
    { label: "Memory", value: "68%", change: "Stable", detail: "Healthy headroom on all hot nodes", tone: "emerald" },
    { label: "Peak Thermal", value: `${maxTemp}C`, change: latestA12?.cpu_temp > 80 ? "Critical" : "Nominal", detail: `Highest temp recorded on Rack ${readings.find(r => r.cpu_temp === maxTemp)?.rack_id || 'N/A'}`, tone: maxTemp > 80 ? "rose" : "amber" },
    { label: "Risk Score", value: latestRisk.toFixed(2), change: latestRisk > 0.6 ? "Elevated" : "Low", detail: "Real-time failure probability index", tone: latestRisk > 0.6 ? "rose" : "cyan" },
  ];

  const mainRackHistory = history["A-12"] || [];
  const chartWidth = 520;
  const chartHeight = 210;

  return (
    <main className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,#16314d_0%,#07111f_38%,#030712_100%)] text-white font-sans">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(120deg,rgba(56,189,248,0.10),transparent_30%,transparent_70%,rgba(244,63,94,0.08))]" />
      
      <div className="relative mx-auto flex max-w-7xl flex-col gap-6 px-5 py-8 md:px-8 xl:px-10">
        
        {/* Header Section */}
        <section className="overflow-hidden rounded-[36px] border border-white/10 bg-[linear-gradient(135deg,rgba(15,23,42,0.96),rgba(15,23,42,0.72))] p-6 shadow-[0_30px_120px_rgba(2,132,199,0.16)] backdrop-blur-xl md:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-4xl">
              <p className="text-xs uppercase tracking-[0.38em] text-cyan-300/75">
                AVAR Data Center Command • {connected ? "🟢 Linked" : "🔴 Offline"}
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-white md:text-5xl">
                Agentic Intelligence for DC Operations.
              </h1>
              <div className="mt-6 flex flex-wrap gap-3">
                 <button 
                  onClick={() => simulateFault("A-12", "temp_spike")}
                  className="rounded-full bg-rose-500/20 border border-rose-500/40 px-5 py-2 text-sm font-medium text-rose-200 transition hover:bg-rose-500/30"
                >
                  Simulate A-12 Thermal Fault
                </button>
                <button 
                  onClick={() => simulateFault("B-07", "fan_failure")}
                  className="rounded-full bg-amber-500/20 border border-amber-500/40 px-5 py-2 text-sm font-medium text-amber-200 transition hover:bg-amber-500/30"
                >
                  Simulate B-07 Fan Failure
                </button>
                <button 
                  onClick={clearFaults}
                  className="rounded-full bg-white/5 border border-white/10 px-5 py-2 text-sm font-medium text-slate-300 transition hover:bg-white/10"
                >
                  Clear All
                </button>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 xl:w-[320px] xl:grid-cols-1">
              <div className="rounded-[24px] border border-emerald-400/15 bg-emerald-500/10 p-4">
                <div className="flex items-center gap-3 text-emerald-50">
                  <Snowflake className="h-5 w-5" />
                  <span className="text-sm font-medium">Autonomous Mode Active</span>
                </div>
              </div>
              <div className="rounded-[24px] border border-cyan-400/15 bg-cyan-500/10 p-4">
                <div className="flex items-center gap-3 text-cyan-50">
                  <Activity className="h-5 w-5" />
                  <span className="text-sm font-medium">20ms Telemetry Pipeline</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {summaryMetrics.map((metric) => (
              <MetricCard key={metric.label} {...metric} />
            ))}
          </div>
        </section>

        {/* Charts Section */}
        <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
          {/* Trend Chart */}
          <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Real-time Telemetry</p>
                <h3 className="mt-2 text-xl font-semibold text-white">Rack A-12 Signal Window</h3>
              </div>
              <div className="flex gap-3 text-xs">
                <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-cyan-300" /> CPU</span>
                <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-amber-300" /> Temp</span>
              </div>
            </div>
            <div className="mt-6 overflow-hidden rounded-[24px] border border-white/5 bg-white/5 p-4 relative">
              <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="h-[240px] w-full">
                <path d={buildPath(mainRackHistory.map(r => r.cpu_usage), chartWidth, chartHeight)} fill="none" stroke="#67e8f9" strokeWidth="3" />
                <path d={buildPath(mainRackHistory.map(r => r.cpu_temp), chartWidth, chartHeight, 0, 110)} fill="none" stroke="#fde68a" strokeWidth="3" />
              </svg>
            </div>
          </div>

          {/* Rack Status List */}
          <div className="rounded-[28px] border border-white/10 bg-black/20 p-5">
             <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-white">Fleet Integrity</h3>
                <span className="text-xs text-slate-500 uppercase">8 Racks Active</span>
             </div>
             <div className="mt-6 flex flex-col gap-3">
                {readings.map(r => (
                  <div key={r.rack_id} className="grid grid-cols-[60px_1fr_40px] items-center gap-4 group">
                    <span className="text-sm font-mono text-slate-400">{r.rack_id}</span>
                    <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-500 ${r.cpu_temp > 85 ? 'bg-rose-500' : r.cpu_temp > 75 ? 'bg-amber-500' : 'bg-cyan-500'}`}
                        style={{ width: `${(r.cpu_temp / 105) * 100}%` }}
                      />
                    </div>
                    <span className={`text-xs font-medium text-right ${r.cpu_temp > 80 ? 'text-rose-300' : 'text-slate-300'}`}>{Math.round(r.cpu_temp)}°</span>
                  </div>
                ))}
             </div>
          </div>
        </section>

        {/* Intelligence Section */}
        <section className="grid gap-6 xl:grid-cols-[1fr_1.5fr]">
          
          {/* Agent reasoning panel */}
          <div className="rounded-[32px] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
             <div className="flex items-center justify-between border-b border-white/5 pb-4 mb-6">
                <h2 className="text-xl font-semibold flex items-center gap-3">
                  <Bot className="h-5 w-5 text-cyan-400" />
                  Agent Reasoning Trace
                </h2>
                <div className="animate-pulse flex items-center gap-2 text-[10px] text-cyan-300 uppercase tracking-widest">
                  <span className="h-1 w-1 bg-cyan-300 rounded-full" /> Live Process
                </div>
             </div>
             
             <div className="flex flex-col gap-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                {agentLogs.length === 0 && (
                  <div className="py-12 text-center text-slate-500 italic text-sm">
                    No active agent processes. Simulation standing by...
                  </div>
                )}
                {agentLogs.map((log, i) => (
                  <div key={i} className={`p-4 rounded-2xl border ${log.status === 'running' ? 'border-cyan-500/30 bg-cyan-500/5 animate-pulse' : 'border-white/10 bg-white/5'} transition-all`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold uppercase tracking-tighter text-cyan-400">{log.agent}</span>
                      <span className="text-[10px] text-slate-500">#{log.correlation_id}</span>
                    </div>
                    <p className="text-sm text-white font-medium mb-1">{log.message}</p>
                    {log.reasoning && (
                      <p className="text-xs text-slate-400 leading-relaxed italic border-t border-white/5 mt-3 pt-3">
                        {log.reasoning}
                      </p>
                    )}
                  </div>
                ))}
             </div>
          </div>

          {/* Work Order / Action Panel */}
          <div className="rounded-[32px] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
             <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold flex items-center gap-3">
                  <Zap className="h-5 w-5 text-amber-400" />
                  Remediation Queue
                </h2>
             </div>

             <div className="grid gap-4">
                {workOrders.length === 0 && (
                  <div className="rounded-2xl border border-dashed border-white/10 p-12 text-center text-slate-500">
                    SLA monitoring active. No critical work orders pending.
                  </div>
                )}
                {workOrders.map(wo => (
                  <div key={wo.id} className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/10 to-transparent p-6 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <ShieldAlert size={80} />
                    </div>
                    
                    <div className="flex flex-col md:flex-row justify-between gap-6 relative">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-4">
                          <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest ${wo.severity === 'critical' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`}>
                            {wo.severity}
                          </span>
                          <span className="text-xs font-mono text-slate-500">ID: {wo.id}</span>
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">
                          {wo.action_type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')} on {wo.rack_id}
                        </h3>
                        <p className="text-sm text-slate-400 max-w-md">{wo.reasoning}</p>
                      </div>

                      <div className="grid grid-cols-2 gap-4 md:w-[240px]">
                        <div className="bg-white/5 rounded-2xl p-3 border border-white/10">
                          <p className="text-[10px] uppercase text-slate-500 mb-1">Assigned</p>
                          <p className="text-xs font-bold text-white">{wo.assigned_to}</p>
                        </div>
                        <div className="bg-white/5 rounded-2xl p-3 border border-white/10">
                          <p className="text-[10px] uppercase text-slate-500 mb-1">SLA</p>
                          <p className="text-xs font-bold text-emerald-400">{wo.sla_hours}h Remaining</p>
                        </div>
                        <div className="bg-white/5 rounded-2xl p-3 border border-white/10 col-span-2">
                           <button className="w-full py-2 bg-white text-black rounded-xl text-xs font-bold transition hover:bg-slate-200">
                            Acknowledge Action
                           </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
             </div>
          </div>
        </section>

      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
      `}</style>
    </main>
  );
}
