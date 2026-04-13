# Elio POC User Manual

Welcome to the **Elio Agentic Data Center Operations Platform** (Proof of Concept). This manual provides an overview of the platform's features, how to navigate the dashboard, and how to utilize the agentic AI capabilities for data center monitoring and remediation.

---

## 1. Overview
Elio is an agentic AI platform designed to transform data center operations from reactive to autonomous. It monitors real-time telemetry, predicts potential failures, and uses a pipeline of specialized AI agents to reason about anomalies and execute remediation actions.

---

## 2. The Command Dashboard
The Command Dashboard is your central hub for monitoring the fleet's health.

### **2.1 Header: Fleet Status**
- **Connectivity Indicator**: Displays `🟢 Linked` when connected to the backend telemetry stream and `🔴 Offline` if the connection is lost.
- **System Metrics**:
  - **Fleet CPU**: Average utilization across all monitored racks.
  - **Memory**: Current memory headroom availability.
  - **Peak Thermal**: The highest temperature recorded in the fleet.
  - **Risk Score**: A real-time probability index of upcoming failures.

### **2.2 Real-time Telemetry (Rack A-12)**
- **Trend Chart**: Visualizes the live CPU usage (cyan) and temperature (amber) of the primary rack (A-12).
- **Fleet Integrity**: A vertical list showing the current thermal status of all 8 racks in the fabric. Color-coded progress bars indicate safety:
  - `Cyan`: Nominal (< 75°C)
  - `Amber`: Elevated (75°C - 85°C)
  - `Rose`: Critical (> 85°C)

---

## 3. Agentic Intelligence & Remediation
This section covers the "brains" of the platform—the autonomous agents.

### **3.1 Agent Reasoning Trace**
Located at the bottom left, this panel shows the live thought process of the AI agents. When a fault occurs, you can watch the agents communicate:
- **Prediction Agent**: Forecasts potential issues based on telemetry trends.
- **Monitoring Agent**: Detects immediate anomalies and spikes.
- **Decision Agent**: Evaluates the fault and determines the best course of action.
- **Action Agent**: Prepares and logs the specific remediation steps.

### **3.2 Remediation Queue**
When an agent determines that action is required, a **Work Order** is generated here.
- **Severity**: Critical (Immediate) or Elevated (Urgent).
- **Reasoning**: A human-readable explanation of why the agent chose this specific action.
- **SLA Countdown**: Shows the remaining time to execute the action before SLA breach.
- **Acknowledge**: Allows an operator to review and confirm the agent's autonomous decision.

---

## 4. Using the Simulation Tools
To demonstrate the platform's capabilities without real hardware, use the simulation controls in the header:

1.  **Simulate A-12 Thermal Fault**: Triggers a rapid temperature spike on Rack A-12. Watch the "Trend Chart" rise and the "Agent Reasoning Trace" begin analyzing the heat.
2.  **Simulate B-07 Fan Failure**: Simulates a cooling failure on Rack B-07. This will trigger a "Critical" work order in the Remediation Queue.
3.  **Clear All**: Resets all simulation data and clears the logs for a fresh demo run.

---

## 5. Deployment Information

### **Local Development**
- **Backend API**: `http://localhost:8000`
- **Frontend Dashboard**: `http://localhost:3000`

### **Vercel Cloud Deployment**
- **Production URL**: `https://[your-project-name].vercel.app`
- **Data Fetching**: The dashboard is configured to automatically switch to **High-Frequency Polling** if it cannot establish a permanent WebSocket connection in the cloud environment.

---

## 6. Support & Maintenance
The current POC uses an **In-Memory Store**. This means all logs and simulation data are wiped whenever the backend service is restarted. For persistent data, please consult the `docs/database.md` to configure the PostgreSQL/TimescaleDB integration.
