#!/usr/bin/env python3
"""Fetch allowlisted public commit metadata. A failed refresh leaves the snapshot intact."""
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from build import ROOT, activity_markdown


def fetch_json(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "signal-foundry-profile", "X-GitHub-Api-Version": "2022-11-28"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = Request("https://api.github.com" + path, headers=headers)
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def collect(repositories, fetch=fetch_json):
    entries = []
    for repository in repositories:
        if not re.fullmatch(r"JONNY-ME/[A-Za-z0-9_.-]+", repository):
            raise ValueError("Only explicitly named JONNY-ME repositories are supported")
        metadata = fetch(f"/repos/{repository}")
        if metadata.get("private") is not False:
            raise ValueError(f"{repository} must be public")
        try:
            commits = fetch(f"/repos/{repository}/commits?per_page=1")
        except HTTPError as error:
            if error.code == 409 and metadata.get("size") == 0:
                continue  # An empty public repository has no commits to show.
            raise
        if not commits:
            continue
        commit = commits[0]
        title = " ".join(commit["commit"]["message"].splitlines()[0].split())
        title = title if len(title) <= 100 else title[:97] + "…"
        entries.append({
            "repository": repository, "sha": commit["sha"],
            "date": commit["commit"]["committer"]["date"], "title": title,
        })
    entries.sort(key=lambda item: (item["date"], item["repository"]), reverse=True)
    result = {"entries": entries}
    activity_markdown(result, repositories)  # Validate everything before any write.
    return result


def refresh(root=ROOT, fetch=fetch_json):
    profile = json.loads((root / "profile.json").read_text())
    snapshot = collect(profile["activity_repositories"], fetch)
    path = root / "data/activity.json"
    content = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text() == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(content)
    temporary.replace(path)
    return True


if __name__ == "__main__":
    try:
        print("Activity snapshot updated." if refresh() else "No public activity changes.")
    except Exception as error:
        print(f"Refresh failed; existing snapshot retained: {error}", file=sys.stderr)
        sys.exit(1)
