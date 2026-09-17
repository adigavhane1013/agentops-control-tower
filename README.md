# AgentOps Control Tower

AgentOps Control Tower is a personal AI Engineer project that demonstrates a governed refund workflow built around a Google ADK Finance Agent.

The Finance Agent handles the user's refund request and uses tools to retrieve customer/order data and submit the request to the Control Tower. The Control Tower remains the authority for the deterministic refund decision and returns one of three outcomes: `ALLOW`, `HUMAN_APPROVAL`, or `BLOCK`.

## Purpose

The project demonstrates a clear separation between:

- **LLM-driven request handling** — understanding the request and selecting the available tools.
- **Deterministic governance** — policy and risk evaluation before refund execution.
- **Human oversight** — approval or rejection when the request requires review.
- **Auditability** — recording the final decision in SQLite.

## Key Features

- Google ADK Finance Agent using Gemini `gemini-3.5-flash-lite`.
- Customer and order lookup before refund evaluation.
- Deterministic policy and risk evaluation.
- `ALLOW`, `HUMAN_APPROVAL`, and `BLOCK` decisions.
- Refund execution through a controlled tool path.
- Human approval/rejection workflow.
- SQLite persistence for refunds, approvals, and audit logs.
- Separate company and user-facing React frontends.
- Isolated pytest database for automated tests.

## High-Level Architecture

```text
User
  |
  v
User Frontend (:5174)
  |
  v
Google ADK API (:8001)
  |
  v
Finance Agent
  |
  +--> get_customer_order
  |
  +--> evaluate_refund_request
             |
             v
      AgentOps Control Tower
        |             |
        v             v
   Policy Engine   Risk Engine
        \             /
         \           /
          v         v
       ALLOW / HUMAN_APPROVAL / BLOCK
             |
       +-----+------+
       |            |
       v            v
  Refund        Human Review
  Execution     Approve / Reject
       |            |
       +-----+------+
             |
             v
          SQLite
```

The separate company frontend communicates with the FastAPI backend on `http://127.0.0.1:8000` for approvals, refunds, and audit data.

For the detailed implementation, see:

- [Architecture](docs/ARCHITECTURE.md)
- [API and Policy Reference](docs/API_AND_POLICY.md)

## Tech Stack

| Area | Technology |
|---|---|
| Language | Python 3.12 |
| Agent framework | Google Agent Development Kit (ADK) |
| Model | Gemini `gemini-3.5-flash-lite` |
| API backend | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite |
| Testing | pytest |
| Python/package runner | uv |
| Frontend | React + Vite |
| Company frontend HTTP client | Axios |
| User frontend HTTP client | Fetch API |

## Finance Agent and Control Tower

The active Finance Agent is defined in `app/finance_agent/agent.py`.

It has two tools:

- `get_customer_order` — retrieves the customer's database record and associated order.
- `evaluate_refund_request` — sends the refund request to the Control Tower.

The agent is explicitly instructed not to make, override, approve, or execute refund decisions itself. The Control Tower performs the policy/risk evaluation and controls the next action.

## Demo Workflow

A typical request follows:

```text
1. User submits refund request
2. Finance Agent retrieves customer/order information
3. Control Tower evaluates policy + risk
4. Final decision:
      ALLOW            -> refund is processed
      HUMAN_APPROVAL   -> company operator reviews it
      BLOCK            -> refund is not executed
5. Decision is written to the audit log
```

The user frontend displays the three decision states with dedicated decision cards.

## Project Structure

```text
AgentOps_Control_Tower/
├── app/
│   ├── api/
│   ├── control_tower/
│   ├── database/
│   ├── finance_agent/
│   ├── policy/
│   ├── risk_engine/
│   └── tools/
├── frontend/
├── user_frontend/
├── conftest.py
├── pyproject.toml
├── uv.lock
├── test.py
├── PROJECT CONTEXT.MD
└── README.md
```

## Setup and Run

### Prerequisites

- Python 3.12
- `uv`
- Node.js and npm
- Gemini credentials configured in the local environment

### Install Python dependencies

From the project root:

```powershell
uv sync
```

### Configure local environment

Create a local `.env` file with the Google credentials required by the current ADK/GenAI setup.

Do not commit `.env`.

### Start the FastAPI backend

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

### Start the Google ADK Finance Agent

On the current Windows development setup:

```powershell
$env:PYTHONPATH="C:\path\to\AgentOps_Control_Tower"
uv run adk api_server app/finance_agent --port 8001 --allow_origins http://localhost:5174 --auto_create_session
```

Replace the example path with the local project path.

ADK API:

```text
http://127.0.0.1:8001
```

Verify the active agent:

```powershell
uv run python -c "import requests; r=requests.get('http://127.0.0.1:8001/list-apps'); print(r.status_code); print(r.text)"
```

Expected:

```text
200
["finance_agent"]
```

### Start the company frontend

From `frontend/`, start the existing React development server on:

```text
http://localhost:5173
```

### Start the user frontend

From `user_frontend/`:

```powershell
npm install
npm run dev -- --port 5174
```

Open:

```text
http://localhost:5174
```

## Testing

Run the automated suite:

```powershell
uv run pytest -q
```

Verified result:

```text
18 passed
```

Pytest uses the isolated temporary database configured in `conftest.py`, so automated tests do not populate the real `agentops.db`.

Manual runtime testing has also covered the `ALLOW`, `HUMAN_APPROVAL`, and `BLOCK` paths, including the company-side approve/reject workflow.

## Current Limitations

This is a local portfolio project, not a production financial system.

Current limitations include:

- SQLite is used for local persistence.
- No authentication or authorization layer is implemented in the current FastAPI application.
- Refund execution is represented by writing a processed refund record to SQLite; there is no real payment gateway.
- The policy/risk logic is intentionally small and project-specific.
- The system currently contains one active Finance Agent.
- No cloud deployment or production secret-management system is configured.
- The current API and database setup is intended for local development.

For the detailed technical behavior, API contract, policy rules, and known documentation gaps, see:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/API_AND_POLICY.md](docs/API_AND_POLICY.md)
