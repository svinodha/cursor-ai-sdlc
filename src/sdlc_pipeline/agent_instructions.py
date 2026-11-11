"""Load agent instruction Markdown files from the agents/ directory."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sdlc_pipeline.config import REPO_ROOT

AGENTS_DIR = REPO_ROOT / "agents"
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


@dataclass(frozen=True)
class AgentInstructions:
    name: str
    path: Path
    description: str
    body: str
    title: str = ""
    number: int | None = None
    output_file: str = ""
    model: str = "inherit"

    @property
    def prompt(self) -> str:
        return self.body.strip()


def _parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw.strip()

    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta, match.group(2).strip()


def load_agent_instructions(name: str, *, agents_dir: Path | None = None) -> AgentInstructions:
    directory = agents_dir or AGENTS_DIR
    path = directory / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Missing agent instructions file: {path}")

    meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    number_raw = meta.get("number", "").strip()
    return AgentInstructions(
        name=meta.get("name", name),
        path=path,
        description=meta.get("description", ""),
        body=body,
        title=meta.get("title", ""),
        number=int(number_raw) if number_raw.isdigit() else None,
        output_file=meta.get("output_file", ""),
        model=meta.get("model", "inherit") or "inherit",
    )


def load_stage_agents(*, agents_dir: Path | None = None) -> tuple[AgentInstructions, ...]:
    directory = agents_dir or AGENTS_DIR
    agents: list[AgentInstructions] = []
    for path in sorted(directory.glob("*.md")):
        if path.stem == "orchestrator":
            continue
        agent = load_agent_instructions(path.stem, agents_dir=directory)
        if agent.number is None:
            raise ValueError(f"Stage agent '{path.name}' is missing numeric 'number' frontmatter.")
        if not agent.output_file:
            raise ValueError(f"Stage agent '{path.name}' is missing 'output_file' frontmatter.")
        agents.append(agent)
    agents.sort(key=lambda item: item.number or 0)
    return tuple(agents)
