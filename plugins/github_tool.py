"""
title: GitHub
author: custom-fork
version: 1.0.0
description: GitHub API tool — set GITHUB_TOKEN in Valves (PAT). Not a Skill.
requirements: requests
"""

from typing import Optional
import requests


class Tools:
    class Valves:
        def __init__(self):
            self.GITHUB_TOKEN: str = ""
            self.GITHUB_API_BASE: str = "https://api.github.com"

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self) -> dict:
        h = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = (self.valves.GITHUB_TOKEN or "").strip()
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def github_whoami(self) -> str:
        """Return the authenticated GitHub user for the configured PAT."""
        if not self.valves.GITHUB_TOKEN:
            return "Error: set GITHUB_TOKEN in this tool Valves. Do not paste tokens in chat."
        r = requests.get(f"{self.valves.GITHUB_API_BASE}/user", headers=self._headers(), timeout=30)
        if r.status_code >= 400:
            return f"GitHub error {r.status_code}: {r.text[:500]}"
        u = r.json()
        return f"login={u.get('login')} name={u.get('name')} url={u.get('html_url')}"

    def github_list_repos(self, per_page: int = 10) -> str:
        """List repositories for the authenticated user."""
        if not self.valves.GITHUB_TOKEN:
            return "Error: set GITHUB_TOKEN in tool Valves."
        r = requests.get(
            f"{self.valves.GITHUB_API_BASE}/user/repos",
            headers=self._headers(),
            params={"per_page": max(1, min(per_page, 50)), "sort": "updated"},
            timeout=30,
        )
        if r.status_code >= 400:
            return f"GitHub error {r.status_code}: {r.text[:500]}"
        repos = r.json()
        lines = [f"- {x.get('full_name')} ({x.get('html_url')})" for x in repos]
        return "Repos:\n" + ("\n".join(lines) if lines else "(none)")

    def github_get_file(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> str:
        """Get a text file content from a repository."""
        if not self.valves.GITHUB_TOKEN:
            return "Error: set GITHUB_TOKEN in tool Valves."
        url = f"{self.valves.GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path.lstrip('/')}"
        params = {"ref": ref} if ref else None
        r = requests.get(url, headers=self._headers(), params=params, timeout=30)
        if r.status_code >= 400:
            return f"GitHub error {r.status_code}: {r.text[:500]}"
        data = r.json()
        if isinstance(data, list):
            return "Path is a directory. Items:\n" + "\n".join(f"- {i.get('path')}" for i in data[:50])
        import base64

        if data.get("encoding") == "base64" and data.get("content"):
            raw = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            if len(raw) > 15000:
                return raw[:15000] + "\n\n...[truncated]..."
            return raw
        return str(data)[:2000]

    def github_create_issue(self, owner: str, repo: str, title: str, body: str = "") -> str:
        """Create an issue on a repository."""
        if not self.valves.GITHUB_TOKEN:
            return "Error: set GITHUB_TOKEN in tool Valves."
        r = requests.post(
            f"{self.valves.GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
            headers=self._headers(),
            json={"title": title, "body": body or ""},
            timeout=30,
        )
        if r.status_code >= 400:
            return f"GitHub error {r.status_code}: {r.text[:500]}"
        issue = r.json()
        return f"Created issue #{issue.get('number')}: {issue.get('html_url')}"
