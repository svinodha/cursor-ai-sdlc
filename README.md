# Cursor AI SDLC Pipeline

Automated Software Development Life Cycle (SDLC) pipeline driven by the **Cursor SDK** (Python). Given a **Jira Story ID**, an **Orchestrator Agent** fetches the story, spawns specialized sub-agents for each stage, and ends with a **Pull Request**.

## Overview

```
Input: Jira Story ID
            │
            ▼
   Orchestrator Agent  (Cursor SDK, local)
            │
            ├─► 1. Requirement Analysis   → requirement-analysis.md
            ├─► 2. Architecture           → architecture.md
            ├─► 3. Design                 → design.md
            ├─► 4. Design Review          → design-review.md
            ├─► 5. Implementation Plan    → implementation-plan.md
            ├─► 6. Implementation         → implementation.md
            ├─► 7. Code Review            → code-review.md
            ├─► 8. Verification           → verification.md
            └─► 9. PR Creation            → pr-creation.md
            │
            ▼
   Output: Pull Request
```

## Prerequisites

- Python 3.10+
- Jira access to `https://jiraeu.epam.com` (project `EPMCDMETST`)
- Cursor API key ([Dashboard → Integrations](https://cursor.com/dashboard/integrations))

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

Fill secrets in local `.env` (never paste tokens into chat).

Required `.env` values:

| Variable | Purpose |
|----------|---------|
| `JIRA_BASE_URL` | `https://jiraeu.epam.com` |
| `JIRA_PROJECT_KEY` | `EPMCDMETST` |
| `JIRA_AUTH_TYPE` | `bearer` (EPAM PAT) or `basic` (email + token) |
| `JIRA_EMAIL` | Required only for `basic` |
| `JIRA_API_TOKEN` | Jira PAT / API token (**secret**) |
| `CURSOR_API_KEY` | Cursor SDK key (**secret**) |
| `CURSOR_MODEL` | Default `composer-2.5` |
| `GITHUB_TOKEN` | GitHub PAT for `gh` push/PR (**secret**; `repo` scope) |

`.env` is gitignored. Do not commit secrets.

## Usage

Fetch a story only (validates Jira auth, writes snapshot Markdown):

```bash
python -m sdlc_pipeline EPMCDMETST-123 --fetch-only
# or numeric id within the project:
python -m sdlc_pipeline 123 --fetch-only
```

Run the full orchestrator (spawns sub-agents in order):

```bash
python -m sdlc_pipeline EPMCDMETST-123
```

Run the first N stages while iterating:

```bash
python -m sdlc_pipeline EPMCDMETST-123 --stop-after 1
```

## Orchestrator Agent

Entry point of the pipeline (`src/sdlc_pipeline/orchestrator.py`).

- Accepts a **Jira Story ID**
- Fetches story details via Jira REST (`/rest/api/2/issue/{key}`)
- Writes `outputs/<STORY-KEY>/jira-story.md`
- Creates a local Cursor agent with nine named sub-agents (`AgentDefinition`)
- Spawns each sub-agent in sequence and expects a `.md` artifact per stage

## Sub-Agents

| # | Sub-Agent | Output |
|---|-----------|--------|
| 1 | Requirement Analysis | `requirement-analysis.md` |
| 2 | Architecture | `architecture.md` |
| 3 | Design | `design.md` |
| 4 | Design Review | `design-review.md` |
| 5 | Implementation Plan | `implementation-plan.md` |
| 6 | Implementation | `implementation.md` |
| 7 | Code Review | `code-review.md` |
| 8 | Verification | `verification.md` |
| 9 | PR Creation | `pr-creation.md` |

## Output layout

Each Jira story gets a workspace folder named after the story id. **All** stage Markdown outputs and **all** implemented application code go inside it:

```
outputs/
  <jira-story-id>/
    jira-story.md
    pipeline-state.json
    requirement-analysis.md
    architecture.md
    design.md
    design-review.md
    implementation-plan.md
    implementation.md
    code-review.md
    verification.md
    pr-creation.md
    src/                 # application code for this story
      ...
```

## Project layout

```
src/sdlc_pipeline/
  __main__.py      # CLI
  config.py        # .env loading (no secret logging)
  jira_client.py   # Jira REST client
  stages.py        # Stage + sub-agent definitions
  orchestrator.py  # Cursor SDK orchestrator
.env               # local only (gitignored)
```

## Status

Orchestrator + Jira integration implemented. Sub-agents are registered and invoked sequentially by the orchestrator; deepen each stage’s prompts/tools as needed.
