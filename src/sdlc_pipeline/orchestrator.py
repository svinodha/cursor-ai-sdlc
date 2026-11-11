"""Orchestrator agent: Jira story in → spawn SDLC sub-agents → PR out."""

from __future__ import annotations

import sys
from pathlib import Path

from cursor_sdk import Agent, AgentDefinition, AgentOptions, CursorAgentError, LocalAgentOptions

from sdlc_pipeline.agent_instructions import load_agent_instructions
from sdlc_pipeline.config import Settings
from sdlc_pipeline.jira_client import JiraClient, JiraStory
from sdlc_pipeline.pipeline_state import PipelineState, load_state, save_state
from sdlc_pipeline.stages import STAGES, Stage


class Orchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.jira = JiraClient(settings)
        self._orchestrator_instructions = load_agent_instructions("orchestrator")

    def prepare_story(self, story_id: str) -> tuple[JiraStory, Path]:
        """Create/reuse outputs/<JIRA-KEY>/ as the exclusive story workspace."""
        story = self.jira.fetch_story(story_id)
        story_dir = self.settings.outputs_dir / story.key
        story_dir.mkdir(parents=True, exist_ok=True)
        # Optional code root hint; agents may add more structure as needed.
        (story_dir / "src").mkdir(exist_ok=True)
        story_path = story_dir / "jira-story.md"
        story_path.write_text(story.to_markdown(), encoding="utf-8")
        return story, story_dir

    def load_pipeline_state(self, story_id: str) -> tuple[JiraStory, Path, PipelineState]:
        story, out_dir = self.prepare_story(story_id)
        state = load_state(out_dir, story.key)
        return story, out_dir, state

    def _subagents(self) -> dict[str, AgentDefinition]:
        return {
            stage.agent_name: AgentDefinition(
                description=stage.description,
                prompt=stage.prompt,
                model=stage.model,
            )
            for stage in STAGES
        }

    def _agent_options(self) -> AgentOptions:
        return AgentOptions(
            model=self.settings.cursor_model,
            api_key=self.settings.cursor_api_key,
            local=LocalAgentOptions(
                cwd=str(self.settings.workspace_dir),
                # Load project rules (.cursor/rules) and skills (.cursor/skills).
                setting_sources=["project"],
            ),
            agents=self._subagents(),
        )

    def _orchestrator_system_prompt(
        self,
        story: JiraStory,
        out_dir: Path,
        state: PipelineState,
        pending: tuple[Stage, ...],
    ) -> str:
        stage_lines = "\n".join(
            f"{stage.number}. Spawn `{stage.agent_name}` → write `{(out_dir / stage.output_file).as_posix()}`"
            for stage in STAGES
        )
        completed = [
            f"- {stage.number}. `{stage.agent_name}` → `{(out_dir / stage.output_file).as_posix()}`"
            for stage in STAGES
            if state.is_stage_done(stage, out_dir)
        ]
        completed_block = "\n".join(completed) if completed else "- _(none yet)_"
        pending_block = (
            "\n".join(f"- {stage.number}. `{stage.agent_name}`" for stage in pending)
            if pending
            else "- _(none — pipeline complete)_"
        )
        return (
            f"{self._orchestrator_instructions.prompt}\n\n"
            "## Run context\n\n"
            f"- Story key: {story.key}\n"
            f"- Story URL: {story.url}\n"
            f"- Story workspace (Jira-ID folder): `{out_dir.as_posix()}`\n"
            f"- Story snapshot: `{(out_dir / 'jira-story.md').as_posix()}`\n"
            f"- Suggested code root: `{(out_dir / 'src').as_posix()}`\n"
            f"- Pipeline state file: `{(out_dir / 'pipeline-state.json').as_posix()}`\n\n"
            "## Hard constraint\n\n"
            f"- Put **all** stage Markdown outputs and **all** implemented application code "
            f"inside `{out_dir.as_posix()}`.\n"
            "- Do not change the pipeline framework (`src/sdlc_pipeline/`, `agents/`, `.cursor/`).\n\n"
            f"## Concrete output paths\n\n{stage_lines}\n\n"
            f"## Already completed (do not redo)\n\n{completed_block}\n\n"
            f"## Remaining stages for this run\n\n{pending_block}\n"
        )

    def _stage_prompt(self, stage: Stage, story: JiraStory, out_dir: Path) -> str:
        prior = [s for s in STAGES if s.number < stage.number]
        prior_paths = "\n".join(
            f"- `{(out_dir / s.output_file).as_posix()}`" for s in prior
        ) or "- _(none — this is the first stage)_"
        output_path = (out_dir / stage.output_file).as_posix()
        implementation_note = ""
        if stage.agent_name == "implementation":
            implementation_note = (
                f"\nImplement **all application code** under `{out_dir.as_posix()}` "
                f"(prefer `{(out_dir / 'src').as_posix()}`). "
                "Do not modify the pipeline framework.\n"
            )
        return (
            f"Run SDLC stage {stage.number}/9: {stage.title}.\n\n"
            f"Spawn the `{stage.agent_name}` sub-agent. "
            f"Its instructions live in `{stage.instructions_path}`.\n"
            f"Jira story: {story.key} ({story.url})\n"
            f"Story workspace: `{out_dir.as_posix()}`\n"
            f"Story snapshot: `{(out_dir / 'jira-story.md').as_posix()}`\n"
            f"Prior stage outputs:\n{prior_paths}\n"
            f"{implementation_note}\n"
            f"Required deliverable: write Markdown to `{output_path}`.\n"
            "After the sub-agent finishes, confirm the file exists and briefly summarize it."
        )

    def _open_agent(self, state: PipelineState):
        options = self._agent_options()
        if state.agent_id:
            try:
                print(f"[orchestrator] resuming agent {state.agent_id}", flush=True)
                return Agent.resume(state.agent_id, options)
            except Exception as err:  # noqa: BLE001 - fall back to a fresh agent
                print(
                    f"[orchestrator] resume failed ({err}); creating a new agent",
                    file=sys.stderr,
                    flush=True,
                )
        return Agent.create(options)

    def run(
        self,
        story_id: str,
        *,
        stop_after: int | None = None,
        from_stage: int = 1,
        restart: bool = False,
    ) -> Path:
        self.settings.require_cursor()
        story, out_dir = self.prepare_story(story_id)
        state = load_state(out_dir, story.key)

        if restart:
            state = PipelineState.new(story.key)
            print("[orchestrator] restarting pipeline from stage 1", flush=True)
        elif from_stage > 1:
            state.reset(from_stage=from_stage)
            print(f"[orchestrator] forcing re-run from stage {from_stage}", flush=True)

        pending = state.pending_stages(
            out_dir, stop_after=stop_after, from_stage=from_stage
        )
        save_state(out_dir, state)

        if not pending:
            state.status = "completed"
            save_state(out_dir, state)
            print("[orchestrator] nothing to do — all requested stages already completed", flush=True)
            return out_dir

        skipped = [
            stage
            for stage in STAGES
            if stage.number >= from_stage
            and (stop_after is None or stage.number <= stop_after)
            and state.is_stage_done(stage, out_dir)
        ]
        for stage in skipped:
            print(
                f"[orchestrator] skip completed stage {stage.number}/9 {stage.title}",
                flush=True,
            )

        try:
            with self._open_agent(state) as agent:
                state.agent_id = agent.agent_id
                save_state(out_dir, state)

                bootstrap = agent.send(
                    self._orchestrator_system_prompt(story, out_dir, state, pending)
                    + "\nAcknowledge the remaining pipeline plan. Do not start stages yet."
                )
                bootstrap_result = bootstrap.wait()
                if bootstrap_result.status == "error":
                    state.status = "failed"
                    state.last_error = f"Orchestrator bootstrap failed (run_id={bootstrap_result.id})."
                    save_state(out_dir, state)
                    raise RuntimeError(state.last_error)

                for stage in pending:
                    print(
                        f"[orchestrator] stage {stage.number}/9 {stage.title} "
                        f"(agent={agent.agent_id})",
                        flush=True,
                    )
                    state.mark_running(stage, agent_id=agent.agent_id)
                    save_state(out_dir, state)

                    run = agent.send(self._stage_prompt(stage, story, out_dir))
                    print(f"[orchestrator] run_id={run.id}", flush=True)
                    result = run.wait()
                    expected = out_dir / stage.output_file

                    if result.status == "error":
                        error = (
                            f"Stage {stage.number} ({stage.agent_name}) failed "
                            f"(run_id={result.id})."
                        )
                        state.mark_failed(stage, error, run_id=result.id)
                        save_state(out_dir, state)
                        raise RuntimeError(error)

                    if not expected.is_file() or expected.stat().st_size == 0:
                        error = (
                            f"Stage {stage.number} ({stage.agent_name}) finished but "
                            f"missing output: {expected}"
                        )
                        state.mark_failed(stage, error, run_id=result.id)
                        save_state(out_dir, state)
                        raise RuntimeError(error)

                    state.mark_completed(stage, run_id=result.id)
                    save_state(out_dir, state)
                    print(
                        f"[orchestrator] checkpointed stage {stage.number}: {expected.name}",
                        flush=True,
                    )
        except CursorAgentError as err:
            state.status = "failed"
            state.last_error = (
                f"Cursor agent startup failed (retryable={err.is_retryable}): {err}"
            )
            save_state(out_dir, state)
            raise RuntimeError(state.last_error) from err
        except Exception:
            # Stage-level failures already checkpointed; persist any unexpected break.
            if state.status != "failed":
                state.status = "failed"
                state.last_error = "Pipeline interrupted before completion."
                save_state(out_dir, state)
            raise

        return out_dir
