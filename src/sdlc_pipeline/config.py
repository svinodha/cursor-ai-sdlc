"""Load configuration from environment / .env. Never log secret values."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    jira_base_url: str
    jira_project_key: str
    jira_auth_type: str
    jira_email: str
    jira_api_token: str
    cursor_api_key: str
    cursor_model: str
    outputs_dir: Path
    workspace_dir: Path

    def require_jira(self) -> None:
        if not self.jira_api_token.strip():
            raise ValueError(
                "JIRA_API_TOKEN is missing. Set it in your local .env file."
            )
        if self.jira_auth_type == "basic" and not self.jira_email.strip():
            raise ValueError("JIRA_EMAIL is required when JIRA_AUTH_TYPE=basic.")

    def require_cursor(self) -> None:
        if not self.cursor_api_key.strip():
            raise ValueError(
                "CURSOR_API_KEY is missing. Set it in .env "
                "(Cursor Dashboard → Integrations / API Keys)."
            )


def load_settings(env_file: Path | None = None) -> Settings:
    load_dotenv(env_file or (REPO_ROOT / ".env"), override=False)

    auth_type = os.getenv("JIRA_AUTH_TYPE", "bearer").strip().lower()
    if auth_type not in {"bearer", "basic"}:
        raise ValueError("JIRA_AUTH_TYPE must be 'bearer' or 'basic'.")

    return Settings(
        jira_base_url=os.getenv("JIRA_BASE_URL", "https://jiraeu.epam.com").rstrip("/"),
        jira_project_key=os.getenv("JIRA_PROJECT_KEY", "EPMCDMETST").strip().upper(),
        jira_auth_type=auth_type,
        jira_email=os.getenv("JIRA_EMAIL", "").strip(),
        jira_api_token=os.getenv("JIRA_API_TOKEN", "").strip(),
        cursor_api_key=os.getenv("CURSOR_API_KEY", "").strip(),
        cursor_model=os.getenv("CURSOR_MODEL", "composer-2.5").strip(),
        outputs_dir=REPO_ROOT / "outputs",
        workspace_dir=REPO_ROOT,
    )
