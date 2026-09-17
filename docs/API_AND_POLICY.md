# AgentOps Control Tower — API and Policy Reference

This document is the API and governance reference for the currently implemented local project.

## API Base URLs

| Service | Base URL | Purpose |
|---|---|---|
| FastAPI Control Tower backend | `http://127.0.0.1:8000` | Company/operator APIs |
| Google ADK API | `http://127.0.0.1:8001` | Finance Agent execution |
| Company frontend | `http://localhost:5173` | Operator UI |
| User frontend | `http://localhost:5174` | User Finance Agent UI |

## FastAPI Endpoints

The current FastAPI application registers audit, approvals, approval-action, and refund routers.

### `GET /`

Purpose:

Returns the application running message.

Response:

```json
{
  "message": "AgentOps Control Tower is running"
}
```

### `GET /approvals/pending`

Purpose:

Return approval requests whose current status is `pending`.

Response shape:

```json
[
  {
    "id": 30,
    "customer_id": 102,
    "order_id": 1002,
    "amount": 10000,
    "reason": "customer requested a refund",
    "status": "pending"
  }
]
```

The endpoint filters by `status == "pending"` and orders results by approval ID descending.

### `POST /approvals/{approval_id}/approved`

Purpose:

Approve a pending approval request.

Example:

```http
POST /approvals/30/approved
```

Current behavior:

```text
pending approval
    -> status becomes approved
    -> refund is executed
    -> response includes the refund result
```

A request that is not found or is no longer pending returns an error response.

### `POST /approvals/{approval_id}/rejected`

Purpose:

Reject a pending approval request.

Example:

```http
POST /approvals/30/rejected
```

Current behavior:

```text
pending approval
    -> status becomes rejected
    -> no refund execution
```

The current implementation only accepts `approved` or `rejected` as the decision value passed to the approval tool.

### `GET /audit/logs`

Purpose:

Return audit records ordered newest-first.

Response shape:

```json
[
  {
    "id": 1,
    "customer_id": 101,
    "order_id": 1001,
    "refund_amount": 5000,
    "decision": "ALLOW",
    "reason": "Policy: Refund meets automatic approval policy | Risk: LOW (score 30)"
  }
]
```

The audit endpoint returns:

```text
id
customer_id
order_id
refund_amount
decision
reason
```

### `POST /refunds/request`

Purpose:

Company-side refund-request endpoint.

The current company frontend calls this route with its refund data:

```text
POST /refunds/request
```

The exact request-body schema is intentionally not reproduced here because the current `app/api/refunds.py` source file was not among the repository files available for this documentation review. The route itself is registered by the FastAPI application and called by the existing company frontend.

## Google ADK Endpoint

### `POST /run`

The active Finance Agent is exposed through the Google ADK API.

Base URL:

```text
http://127.0.0.1:8001
```

The current user frontend sends:

```json
{
  "appName": "finance_agent",
  "userId": "user-1",
  "sessionId": "<session id>",
  "newMessage": {
    "role": "user",
    "parts": [
      {
        "text": "I want a refund of ₹5,000 for customer 101, order 1001."
      }
    ]
  },
  "streaming": false
}
```

The current frontend checks the HTTP response and parses the returned JSON event list.

The active ADK application is:

```text
finance_agent
```

Verify it with:

```powershell
uv run python -c "import requests; r=requests.get('http://127.0.0.1:8001/list-apps'); print(r.status_code); print(r.text)"
```

Expected:

```text
200
["finance_agent"]
```

## Refund Policy

The currently verified project policy contains these documented blocking/approval rules.

### Automatic approval

A request can receive `ALLOW` when it satisfies the automatic refund policy.

Verified example:

```text
Refund: ₹4,000
Order:  ₹5,000
Decision: ALLOW
Reason: Refund meets automatic approval policy
```

### Human approval

A request can receive `HUMAN_APPROVAL` when it is above the automatic threshold but does not violate the blocking rules.

Verified example:

```text
Refund: ₹10,000
Order:  ₹15,000
Decision: HUMAN_APPROVAL
Reason: Refund requires human approval
```

### Blocking rules

The current documented blocking rules are:

- Refund amount exceeds ₹20,000.
- Refund amount exceeds the order amount.

Verified examples:

```text
Refund: ₹25,000
Order:  ₹30,000
Decision: BLOCK
Reason: Refund amount exceeds ₹20,000 limit
```

and:

```text
Refund: ₹6,000
Order:  ₹5,000
Decision: BLOCK
Reason: Refund amount exceeds order amount
```

## Risk Engine

The Control Tower consumes a risk result containing:

```text
risk_score
risk_level
risk_factors
```

Verified risk levels in the current tests/runtime are:

```text
LOW
HIGH
```

The project context also describes `MEDIUM` as a supported decision-driving risk state, because the Control Tower contains explicit `MEDIUM` handling. The complete risk scoring source was not included in the files available for this review, so the full scoring formula and all thresholds are intentionally not documented as complete.

### Verified risk examples

#### Low risk

```text
risk_score: 0
risk_level: LOW
risk_factors: []
```

#### Low risk with refund-ratio factor

```text
risk_score: 30
risk_level: LOW

risk_factors:
- Refund is 50% or more of order value
```

#### High risk

```text
risk_score: 100
risk_level: HIGH

risk_factors:
- High refund amount
- Refund is 50% or more of order value
- Refund exceeds ₹20,000
```

## Decision Precedence

The Control Tower combines the policy result and risk result.

The implemented precedence is:

```text
1. Start with policy_decision

2. If risk_level == HIGH
      -> BLOCK

3. Else if risk_level == MEDIUM
      and policy_decision == ALLOW
      -> HUMAN_APPROVAL

4. Otherwise
      -> retain policy_decision
```

This logic is implemented in `app/control_tower/control_tower.py`.

## Verified Scenarios

| Refund | Order | Verified decision | Verified risk |
|---:|---:|---|---|
| ₹5,000 | ₹5,000 | `ALLOW` | `LOW` |
| ₹10,000 | ₹25,000 | `HUMAN_APPROVAL` | `LOW` |
| ₹25,000 | ₹25,000 | `BLOCK` | `HIGH` |
| ₹6,000 | ₹5,000 | `BLOCK` | policy block |

The automated Control Tower tests independently verify the `ALLOW`, `HUMAN_APPROVAL`, and `BLOCK` execution paths.

## Approval Workflow

When the final decision is `HUMAN_APPROVAL`:

```text
Control Tower
     |
     v
ApprovalRequest(status="pending")
     |
     v
Company frontend
     |
     +------> approve
     |           |
     |           v
     |       Refund execution
     |
     +------> reject
                 |
                 v
           No refund execution
```

Approval records contain:

```text
id
customer_id
order_id
amount
reason
status
```

Supported approval statuses observed in the implementation:

```text
pending
approved
rejected
```

An approval can only be updated while it is pending.

## Refund Execution

The refund tool writes:

```text
Refund(
    customer_id,
    order_id,
    amount,
    status="processed",
    reason
)
```

A successful refund response contains:

```json
{
  "success": true,
  "refund_id": 1,
  "customer_id": 101,
  "order_id": 1001,
  "amount": 5000.0,
  "status": "processed",
  "reason": "Wrong product"
}
```

There is no real payment gateway integration. The current implementation records the refund in SQLite.

## Audit Logging

Every Control Tower decision attempts to create an `AuditLog` containing:

```text
customer_id
order_id
refund_amount
decision
reason
```

The stored reason includes the policy reason and risk level/score.

The audit endpoint exposes these fields through:

```http
GET /audit/logs
```

One current limitation is that an audit persistence exception is rolled back and not propagated by the Control Tower. Therefore audit persistence failure can currently be invisible to the immediate decision caller.

## Database Model Reference

Current tables:

```text
customers
orders
refunds
approval_requests
audit_logs
```

Foreign-key relationships:

```text
customers
  |
  +--> orders
  +--> refunds
  +--> approval_requests
  +--> audit_logs

orders
  |
  +--> refunds
  +--> approval_requests
  +--> audit_logs
```

## Policy and Risk Documentation Gap

The complete `policy_engine.py` and `risk_engine.py` source implementations were not included in the repository files available for this documentation review.

Accordingly:

- the rules explicitly documented above are the rules supported by the available project context and verified scenarios;
- the full automatic-approval threshold logic is not presented as a complete specification;
- the full risk scoring formula and all score thresholds are not presented as complete;
- no additional policy or risk rules are inferred.

For a complete rule-by-rule reference, update this document after the current `app/policy/policy_engine.py` and `app/risk_engine/risk_engine.py` source files are included in the documentation review.
