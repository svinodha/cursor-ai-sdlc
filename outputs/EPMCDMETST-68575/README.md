# EPMCDMETST-68575 — Manager Dashboard Leave Approval (demo)

Self-contained leave-approval feature slice for Jira story **EPMCDMETST-68575**.

## Demo auth (NOT production)

This demo identifies callers with `X-User-Id` and `X-Role` HTTP headers (and page defaults for the UI). **This is demo-only and not production-safe.** Production must replace header trust with real session/authentication.

Seeded actors:

| Actor | Id | Role |
|-------|-----|------|
| Manager | `mgr-1` | manager |
| Employee (history demo) | `emp-1` | employee |
| Teammate | `emp-2` | employee |

## Setup

From this story folder:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Ensure `src/` is on `PYTHONPATH` (the commands below set it).

## Run the demo app

```bash
cd outputs/EPMCDMETST-68575
set PYTHONPATH=src
python -m leave_approval.app
```

Open:

- Manager Dashboard: http://127.0.0.1:5055/manager
- Employee History: http://127.0.0.1:5055/employee/history

API examples (PowerShell):

```powershell
$headers = @{ "X-User-Id"="mgr-1"; "X-Role"="manager"; "Content-Type"="application/json" }
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:5055/api/leave-requests/lr-1001/approve -Headers $headers -Body '{"comment":"Approved — enjoy"}'
```

## Run tests

```bash
cd outputs/EPMCDMETST-68575
set PYTHONPATH=src
python -m pytest tests -v
```

## Scope notes

- Approve with optional comment, balance deduct, pending list + employee history.
- No reject / bulk / notifications.
- Insufficient balance **blocks** approval (`409 insufficient_balance`).
