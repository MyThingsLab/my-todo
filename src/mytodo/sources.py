from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field

from mythings.github import Issue

# Same injectable-boundary pattern as mythings.github: the default shells out to
# `gh`, tests pass a fake so the subprocess is the only thing mocked.
Runner = Callable[[list[str]], str]


class GhError(RuntimeError):
    pass


def gh(argv: list[str]) -> str:
    proc = subprocess.run(["gh", *argv], capture_output=True, text=True)
    if proc.returncode != 0:
        raise GhError(f"gh {' '.join(argv)} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


@dataclass(frozen=True)
class TodoItem:
    title: str
    number: int
    url: str
    labels: list[str] = field(default_factory=list)
    repo: str | None = None  # set in org mode, None for a single-repo curation


def issues_to_items(issues: list[Issue], repo: str | None = None) -> list[TodoItem]:
    return [
        TodoItem(title=i.title, number=i.number, url=i.url, labels=list(i.labels), repo=repo)
        for i in issues
    ]


def search_org_open_issues(org: str, *, runner: Runner = gh, limit: int = 200) -> list[TodoItem]:
    raw = json.loads(
        runner(
            [
                "search",
                "issues",
                "--owner",
                org,
                "--state",
                "open",
                "--limit",
                str(limit),
                "--json",
                "repository,number,title,url,labels",
            ]
        )
    )
    items: list[TodoItem] = []
    for obj in raw:
        repo = (obj.get("repository") or {}).get("name")
        labels = [lbl["name"] for lbl in obj.get("labels", [])]
        items.append(
            TodoItem(
                title=obj["title"],
                number=obj["number"],
                url=obj.get("url", ""),
                labels=labels,
                repo=repo,
            )
        )
    return items
