from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _clean_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # pre-commit runs hooks with GIT_DIR/GIT_INDEX_FILE set; they leak into the
    # git subprocesses these tests spawn (and into isolation.Workspace) and break
    # worktree ops on the throwaway repo. Real my-todo runs aren't inside a hook.
    for var in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY"):
        monkeypatch.delenv(var, raising=False)


def git(repo: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(repo), *argv], check=True, capture_output=True, text=True)


def make_target_repo(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)
    repo = tmp_path / "work"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "Tester")
    git(repo, "commit", "-m", "init", "--allow-empty")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-u", "origin", "main")
    return repo


def issue(number: int, title: str, labels: tuple[str, ...] = ()) -> dict:
    return {
        "number": number,
        "title": title,
        "body": "",
        "labels": [{"name": name} for name in labels],
        "url": f"https://github.com/o/r/issues/{number}",
    }


class FakeGh:
    # Mocks the `gh` boundary for GitHub: serves `issue list` and `pr create`.
    def __init__(self, issues: list[dict] | None = None) -> None:
        self.issues = issues or []
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str]) -> str:
        self.calls.append(argv)
        if argv[:2] == ["issue", "list"]:
            return json.dumps(self.issues)
        if argv[:2] == ["pr", "create"]:
            return "https://github.com/owner/name/pull/7\n"
        raise AssertionError(f"unexpected gh call: {argv}")


class FakeSearch:
    # Mocks the `gh search issues` boundary for org mode.
    def __init__(self, results: list[dict]) -> None:
        self.results = results

    def __call__(self, argv: list[str]) -> str:
        assert argv[:2] == ["search", "issues"], argv
        return json.dumps(self.results)


def org_hit(repo: str, number: int, title: str, labels: tuple[str, ...] = ()) -> dict:
    return {
        "repository": {"name": repo},
        "number": number,
        "title": title,
        "url": f"https://github.com/MyThingsLab/{repo}/issues/{number}",
        "labels": [{"name": name} for name in labels],
    }
