"""SDLC pipeline stage definitions loaded from agents/*.md instruction files."""

from __future__ import annotations

from dataclasses import dataclass

from sdlc_pipeline.agent_instructions import load_stage_agents


@dataclass(frozen=True)
class Stage:
    number: int
    agent_name: str
    title: str
    output_file: str
    description: str
    prompt: str
    model: str = "inherit"
    instructions_path: str = ""


def _load_stages() -> tuple[Stage, ...]:
    stages: list[Stage] = []
    for agent in load_stage_agents():
        assert agent.number is not None
        stages.append(
            Stage(
                number=agent.number,
                agent_name=agent.name,
                title=agent.title or agent.name,
                output_file=agent.output_file,
                description=agent.description,
                prompt=agent.prompt,
                model=agent.model,
                instructions_path=str(agent.path),
            )
        )
    return tuple(stages)


STAGES: tuple[Stage, ...] = _load_stages()


def stage_by_name(name: str) -> Stage:
    for stage in STAGES:
        if stage.agent_name == name:
            return stage
    raise KeyError(f"Unknown stage agent: {name}")
