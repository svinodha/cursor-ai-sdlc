---
name: sdlc-orchestrate
description: Runs the SDLC orchestrator loop—spawn stage sub-agents in order, point them at prior Markdown artifacts, and confirm outputs. Use when orchestrating the pipeline or spawning requirement-analysis through pr-creation sub-agents.
---

# SDLC orchestrate

## When to use

Use for the parent orchestrator agent only.

## Workflow

1. Read run context (story key, story workspace `outputs/<JIRA-KEY>/`, completed vs remaining stages).
2. For the requested stage, spawn the **named** sub-agent (do not do the stage work yourself).
3. Pass paths to `jira-story.md` and prior stage `.md` files inside the story workspace.
4. Require stage Markdown outputs **and** (for implementation) all code to stay inside that folder.
5. After the sub-agent returns, confirm the artifact exists and is non-empty; summarize briefly.

## Resume

- Skip stages listed as already completed.
- Continue from the first remaining stage.

## Do not

- Skip ahead or merge multiple stages into one spawn
- Print secrets or `.env` values
