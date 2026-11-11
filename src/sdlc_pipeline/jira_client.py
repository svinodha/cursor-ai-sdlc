"""Jira REST client. Credentials come from Settings; never logged."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import requests

from sdlc_pipeline.config import Settings


@dataclass(frozen=True)
class JiraStory:
    key: str
    summary: str
    issue_type: str
    status: str
    description: str
    acceptance_criteria: str
    labels: tuple[str, ...]
    components: tuple[str, ...]
    assignee: str
    reporter: str
    url: str
    raw_fields: dict[str, Any]

    def to_markdown(self) -> str:
        labels = ", ".join(self.labels) if self.labels else "_none_"
        components = ", ".join(self.components) if self.components else "_none_"
        return "\n".join(
            [
                f"# Jira Story: {self.key}",
                "",
                f"- **URL:** {self.url}",
                f"- **Type:** {self.issue_type}",
                f"- **Status:** {self.status}",
                f"- **Summary:** {self.summary}",
                f"- **Assignee:** {self.assignee or '_unassigned_'}",
                f"- **Reporter:** {self.reporter or '_unknown_'}",
                f"- **Labels:** {labels}",
                f"- **Components:** {components}",
                "",
                "## Description",
                "",
                self.description or "_No description provided._",
                "",
                "## Acceptance Criteria",
                "",
                self.acceptance_criteria or "_No acceptance criteria field found._",
                "",
            ]
        )


class JiraClient:
    def __init__(self, settings: Settings) -> None:
        settings.require_jira()
        self._settings = settings
        self._session = requests.Session()
        self._session.headers.update(self._auth_headers())
        self._session.headers["Accept"] = "application/json"

    def _auth_headers(self) -> dict[str, str]:
        token = self._settings.jira_api_token
        if self._settings.jira_auth_type == "basic":
            raw = f"{self._settings.jira_email}:{token}".encode()
            return {"Authorization": f"Basic {base64.b64encode(raw).decode()}"}
        return {"Authorization": f"Bearer {token}"}

    def normalize_story_id(self, story_id: str) -> str:
        value = story_id.strip().upper()
        if not value:
            raise ValueError("Jira story ID is required.")
        if "-" not in value:
            value = f"{self._settings.jira_project_key}-{value}"
        project = value.split("-", 1)[0]
        if project != self._settings.jira_project_key:
            raise ValueError(
                f"Story {value} is outside project {self._settings.jira_project_key}."
            )
        return value

    def fetch_story(self, story_id: str) -> JiraStory:
        key = self.normalize_story_id(story_id)
        url = f"{self._settings.jira_base_url}/rest/api/2/issue/{key}"
        # Fetch default fields (includes custom fields so acceptance criteria can be detected).
        response = self._session.get(url, timeout=60)
        if response.status_code == 404:
            raise LookupError(f"Jira issue not found: {key}")
        if response.status_code in {401, 403}:
            raise PermissionError(
                "Jira authentication failed. Check JIRA_API_TOKEN / JIRA_AUTH_TYPE "
                "(and JIRA_EMAIL for basic)."
            )
        response.raise_for_status()
        payload = response.json()
        fields = payload.get("fields") or {}

        def _user_name(user: Any) -> str:
            if not isinstance(user, dict):
                return ""
            return str(
                user.get("displayName")
                or user.get("emailAddress")
                or user.get("name")
                or ""
            )

        def _adf_or_text(value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, str):
                return value.strip()
            if isinstance(value, dict):
                # ADF / structured docs — keep a readable fallback
                return str(value)
            return str(value)

        acceptance = ""
        for field_key, field_value in fields.items():
            lowered = field_key.lower()
            if "acceptance" in lowered:
                acceptance = _adf_or_text(field_value)
                break

        components = tuple(
            str(c.get("name", ""))
            for c in (fields.get("components") or [])
            if isinstance(c, dict) and c.get("name")
        )
        labels = tuple(str(label) for label in (fields.get("labels") or []))
        status = fields.get("status") or {}
        issue_type = fields.get("issuetype") or {}

        return JiraStory(
            key=payload.get("key") or key,
            summary=str(fields.get("summary") or ""),
            issue_type=str(issue_type.get("name") or ""),
            status=str(status.get("name") or ""),
            description=_adf_or_text(fields.get("description")),
            acceptance_criteria=acceptance,
            labels=labels,
            components=components,
            assignee=_user_name(fields.get("assignee")),
            reporter=_user_name(fields.get("reporter")),
            url=f"{self._settings.jira_base_url}/browse/{key}",
            raw_fields=fields,
        )
