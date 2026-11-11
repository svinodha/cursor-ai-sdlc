"""Persist pipeline progress so runs can resume after mid-pipeline failures."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from sdlc_pipeline.stages import STAGES, Stage

STATE_FILENAME = "pipeline-state.json"
StageStatus = Literal["pending", "running", "completed", "failed"]
PipelineStatus = Literal["pending", "running", "failed", "completed"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class StageState:
    number: int
    agent_name: str
    title: str
    output_file: str
    status: StageStatus = "pending"
    run_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None

    @classmethod
    def from_stage(cls, stage: Stage) -> StageState:
        return cls(
            number=stage.number,
            agent_name=stage.agent_name,
            title=stage.title,
            output_file=stage.output_file,
        )


@dataclass
class PipelineState:
    story_key: str
    status: PipelineStatus = "pending"
    agent_id: str | None = None
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    last_error: str | None = None
    stages: dict[str, StageState] = field(default_factory=dict)

    @classmethod
    def new(cls, story_key: str) -> PipelineState:
        return cls(
            story_key=story_key,
            stages={stage.agent_name: StageState.from_stage(stage) for stage in STAGES},
        )

    @property
    def path_hint(self) -> str:
        return STATE_FILENAME

    def touch(self) -> None:
        self.updated_at = _utc_now()

    def get_stage(self, agent_name: str) -> StageState:
        if agent_name not in self.stages:
            raise KeyError(f"Unknown stage in pipeline state: {agent_name}")
        return self.stages[agent_name]

    def mark_running(self, stage: Stage, *, agent_id: str | None = None) -> None:
        entry = self.get_stage(stage.agent_name)
        entry.status = "running"
        entry.started_at = _utc_now()
        entry.completed_at = None
        entry.error = None
        entry.run_id = None
        self.status = "running"
        self.last_error = None
        if agent_id:
            self.agent_id = agent_id
        self.touch()

    def mark_completed(self, stage: Stage, *, run_id: str | None = None) -> None:
        entry = self.get_stage(stage.agent_name)
        entry.status = "completed"
        entry.run_id = run_id
        entry.completed_at = _utc_now()
        entry.error = None
        self.touch()
        if all(item.status == "completed" for item in self.stages.values()):
            self.status = "completed"

    def mark_failed(self, stage: Stage, error: str, *, run_id: str | None = None) -> None:
        entry = self.get_stage(stage.agent_name)
        entry.status = "failed"
        entry.run_id = run_id
        entry.error = error
        entry.completed_at = _utc_now()
        self.status = "failed"
        self.last_error = error
        self.touch()

    def reset(self, *, from_stage: int = 1) -> None:
        for entry in self.stages.values():
            if entry.number >= from_stage:
                entry.status = "pending"
                entry.run_id = None
                entry.started_at = None
                entry.completed_at = None
                entry.error = None
        self.status = "pending"
        self.last_error = None
        self.touch()

    def is_stage_done(self, stage: Stage, out_dir: Path) -> bool:
        entry = self.get_stage(stage.agent_name)
        artifact = out_dir / stage.output_file
        return (
            entry.status == "completed"
            and artifact.is_file()
            and artifact.stat().st_size > 0
        )

    def pending_stages(
        self,
        out_dir: Path,
        *,
        stop_after: int | None = None,
        from_stage: int = 1,
    ) -> tuple[Stage, ...]:
        selected: list[Stage] = []
        for stage in STAGES:
            if stage.number < from_stage:
                continue
            if stop_after is not None and stage.number > stop_after:
                continue
            if self.is_stage_done(stage, out_dir):
                continue
            selected.append(stage)
        return tuple(selected)

    def summary_lines(self, out_dir: Path) -> list[str]:
        lines = [
            f"story={self.story_key}",
            f"status={self.status}",
            f"agent_id={self.agent_id or '-'}",
            f"updated_at={self.updated_at}",
        ]
        if self.last_error:
            lines.append(f"last_error={self.last_error}")
        for stage in STAGES:
            entry = self.get_stage(stage.agent_name)
            artifact = out_dir / stage.output_file
            artifact_flag = "artifact=yes" if artifact.is_file() else "artifact=no"
            lines.append(
                f"  {stage.number}. {stage.agent_name}: {entry.status} ({artifact_flag})"
            )
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "story_key": self.story_key,
            "status": self.status,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_error": self.last_error,
            "stages": {name: asdict(stage) for name, stage in self.stages.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineState:
        stages: dict[str, StageState] = {}
        raw_stages = data.get("stages") or {}
        for stage in STAGES:
            raw = raw_stages.get(stage.agent_name) or {}
            stages[stage.agent_name] = StageState(
                number=int(raw.get("number", stage.number)),
                agent_name=stage.agent_name,
                title=str(raw.get("title", stage.title)),
                output_file=str(raw.get("output_file", stage.output_file)),
                status=raw.get("status", "pending"),  # type: ignore[arg-type]
                run_id=raw.get("run_id"),
                started_at=raw.get("started_at"),
                completed_at=raw.get("completed_at"),
                error=raw.get("error"),
            )
        return cls(
            story_key=str(data.get("story_key", "")),
            status=data.get("status", "pending"),  # type: ignore[arg-type]
            agent_id=data.get("agent_id"),
            created_at=str(data.get("created_at") or _utc_now()),
            updated_at=str(data.get("updated_at") or _utc_now()),
            last_error=data.get("last_error"),
            stages=stages,
        )


def state_path(out_dir: Path) -> Path:
    return out_dir / STATE_FILENAME


def load_state(out_dir: Path, story_key: str) -> PipelineState:
    path = state_path(out_dir)
    if not path.is_file():
        return PipelineState.new(story_key)
    data = json.loads(path.read_text(encoding="utf-8"))
    state = PipelineState.from_dict(data)
    if not state.story_key:
        state.story_key = story_key
    # Ensure newly added stages appear if the pipeline definition grows.
    for stage in STAGES:
        if stage.agent_name not in state.stages:
            state.stages[stage.agent_name] = StageState.from_stage(stage)
    return state


def save_state(out_dir: Path, state: PipelineState) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    state.touch()
    path = state_path(out_dir)
    path.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path
