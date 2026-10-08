# Autonomous DevOps Agent 🤖

This repository contains the prototype for the "Autonomous AI Task Worker" (CentrAlign AI Engineering Intern Assignment). 

## About The Project
This project implements an **L1 DevOps Remediator Agent**. Instead of simply answering questions, this agent acts autonomously to investigate server alerts, diagnose issues by reading logs, remediate them (e.g., restarting services), verify the fix, and automatically file incident reports in a simulated company environment.

### Scope & Architecture
As requested by the prompt, this is a **narrow prototype that genuinely works**. Rather than mocking a massive, unstructured web environment, the agent operates against a simulated local "Company API" (`mock_system.py`) that enforces strict constraints and requires the agent to reason through errors and verify its actions.

### Phases
* ✅ **Phase 1**: Mock Environment Setup (`mock_system.py` - Simulates Alerts, Logs, Services, and Tickets).
* ⏳ **Phase 2**: Tool Definitions.
* ⏳ **Phase 3**: Core Agent Loop.
* ⏳ **Phase 4**: Testing & Reliability Constraints.
* ⏳ **Phase 5**: Final Polish & Documentation.

*(More setup instructions and architecture details will be added as phases are completed).*
