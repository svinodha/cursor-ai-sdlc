"""CLI entrypoint for the SDLC orchestrator."""

from __future__ import annotations

import argparse
import sys

from sdlc_pipeline.config import load_settings
from sdlc_pipeline.orchestrator import Orchestrator
from sdlc_pipeline.pipeline_state import load_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdlc-orchestrator",
        description=(
            "Run the Cursor SDLC orchestrator for a Jira story ID "
            "(project EPMCDMETST by default)."
        ),
    )
    parser.add_argument(
        "story_id",
        help="Jira story key or numeric id (e.g. EPMCDMETST-123 or 123)",
    )
    parser.add_argument(
        "--fetch-only",
        action="store_true",
        help="Fetch the Jira story and write jira-story.md without spawning agents",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show pipeline checkpoint status for the story and exit",
    )
    parser.add_argument(
        "--stop-after",
        type=int,
        choices=range(1, 10),
        metavar="N",
        help="Run through stage N only",
    )
    parser.add_argument(
        "--from-stage",
        type=int,
        default=1,
        choices=range(1, 10),
        metavar="N",
        help="Force re-run from stage N (marks N..9 pending)",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Ignore checkpoints and restart the full pipeline from stage 1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    orchestrator = Orchestrator(settings)

    try:
        if args.fetch_only:
            story, out_dir = orchestrator.prepare_story(args.story_id)
            print(f"Fetched {story.key}: {story.summary}")
            print(f"Wrote {(out_dir / 'jira-story.md').as_posix()}")
            return 0

        if args.status:
            _story, out_dir, state = orchestrator.load_pipeline_state(args.story_id)
            print("\n".join(state.summary_lines(out_dir)))
            return 0

        if args.restart and args.from_stage != 1:
            print("error: use either --restart or --from-stage, not both", file=sys.stderr)
            return 1

        out_dir = orchestrator.run(
            args.story_id,
            stop_after=args.stop_after,
            from_stage=args.from_stage,
            restart=args.restart,
        )
        state = load_state(out_dir, out_dir.name)
        print(f"Pipeline artifacts: {out_dir.as_posix()}")
        print(f"Pipeline status: {state.status}")
        return 0
    except (ValueError, LookupError, PermissionError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    except RuntimeError as err:
        print(f"error: {err}", file=sys.stderr)
        print("hint: re-run the same command to resume from the last checkpoint", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
