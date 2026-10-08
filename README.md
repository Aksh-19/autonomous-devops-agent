# Autonomous DevOps Remediator Agent 🤖

This repository contains my submission for the **CentrAlign AI Engineering Intern Assignment**.

I have built a prototype of an **Autonomous AI Task Worker** focused on a highly valuable enterprise use-case: **L1 DevOps Auto-Remediation**. 

Instead of building a broad, mocked-out browser system, I adhered to the scope guidelines (*"A narrow prototype that genuinely works is better than a broad system where most functionality is mocked"*) and built a system that autonomously interacts with simulated internal REST APIs to diagnose server issues, fix them, and log tickets.

## 🚀 How to Run (Setup Instructions)

**Prerequisites:** Python 3.10+, and a free Google Gemini API Key.

1. Clone the repository:
   ```bash
   git clone https://github.com/Aksh-19/autonomous-devops-agent.git
   cd autonomous-devops-agent
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Export your LLM API Key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```
5. Run the Agent:
   ```bash
   python agent.py
   ```

---

## 🧠 Architecture Explanation
The system operates on a pure Python **ReAct (Reason + Act)** loop that interacts with `mock_system.py`, which acts as the stateful "Company Server".

1. **Understand & Plan:** The LLM receives the prompt and the JSON schemas of available tools. It checks active alerts.
2. **Context & Memory:** Before acting, the agent uses `search_company_runbooks` to read the company policy for the degraded service.
3. **Execute & Human-in-the-Loop:** If the runbook requires human approval for a critical action (like a restart), the agent automatically halts and uses `request_human_approval` to ask the operator in the terminal.
4. **Observe & Adapt:** The output is fed back to the LLM. If an action fails, the error string is fed back, allowing the agent to adapt and retry.
5. **Verify & Complete:** The system prompt strictly requires the agent to verify its actions by checking service health *after* a restart, ensuring it actually accomplished the goal before generating a Jira ticket.

---

## 🛠️ Important Technical & Design Decisions
* **Custom Orchestration Loop:** I intentionally avoided heavy frameworks like LangChain or AutoGen. Writing the `while` loop manually provides complete control over execution flow and demonstrates first-principles understanding of how an LLM interacts with tools.
* **Human-in-the-Loop (HITL) Safety:** True enterprise autonomy requires safety rails. The agent comprehends English policies from the runbook and intelligently pauses execution to request Y/N approval from a human before executing critical infrastructure changes.
* **Automatic Rate Limit Recovery:** Free-tier LLM APIs aggressively rate-limit. I engineered the agent to catch `429 Quota Exceeded` exceptions, gracefully sleep, and seamlessly resume execution without crashing.
* **UX / Readability:** To make the terminal output readable for human operators, I used the `rich` Python library to clearly separate the AI's internal thoughts (blue panels) from actual system execution results (magenta JSON panels).

---

## ⚠️ Known Limitations
1. **API Rate Limits:** Running on a free Gemini key means the agent is artificially slow. If multiple tools are needed rapidly, it will pause for 60 seconds.
2. **Single-Threaded Execution:** The agent executes tools sequentially. In a production environment, we would want parallel tool execution (e.g., querying logs from 3 services at once).

---

## 🔮 What I Would Build Next (Given More Time)
1. **Vector-Database Context Memory:** Before making decisions, I would have the agent query a local ChromaDB containing "Past Incident Reports". This would allow the agent to learn that "Alert XYZ usually means we should restart the cache, not the database."
2. **Human-in-the-Loop (HITL) Approvals:** For highly sensitive actions (e.g., `drop_database` or `restart_production_cluster`), I would implement a tool that pauses the loop and sends a Slack/CLI prompt to a human manager for a simple "Y/N" approval before proceeding.

---

## 📋 Assumptions Made
* I assumed the user wants the agent to handle the entire lifecycle (Investigate -> Remediate -> Verify -> Document) autonomously.
* I assumed the mock environment accurately reflects standard JSON API responses in a typical enterprise.

---

## 🧩 Components Used
* **Model:** Google `gemini-3.5-flash` (via `google-generativeai` SDK). Chosen because flash models are exceptionally fast and reliable at JSON-based tool calling.
* **Framework:** Pure Python (No AI agent frameworks used to demonstrate raw engineering control).
* **Mock Environment:** Hand-written Python state machine (`mock_system.py`).
