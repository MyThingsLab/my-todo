from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

# Shared fakes come from mythings.testing (plain imports; aliased fixture
# re-export + getfixturevalue wrapper per core docs/CONVENTIONS.md).
from mythings.testing import FakeGh as _FakeGh
from mythings.testing import clean_git_env as _shared_clean_git_env  # noqa: F401


@pytest.fixture(autouse=True)
def _clean_git_env(request: pytest.FixtureRequest) -> None:
    # Real git worktrees in every test; hook-launched pytest (pre-commit)
    # must not leak GIT_* into them.
    request.getfixturevalue("_shared_clean_git_env")


def git(repo: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(repo), *argv], check=True, capture_output=True, text=True)


def make_target_repo(tmp_path: Path) -> Path:
    # Deliberately an EMPTY tree (--allow-empty), not the shared make_git_repo:
    # my-todo's first run must create TODO.md in a repo with no files at all.
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


def fake_gh(issues: list[dict] | None = None) -> _FakeGh:
    return _FakeGh(
        {
            ("issue", "list"): json.dumps(issues or []),
            ("pr", "create"): "https://github.com/owner/name/pull/7\n",
        }
    )


def fake_search(results: list[dict]) -> _FakeGh:
    # Org mode's only gh call is `search issues`; anything else raises.
    return _FakeGh({("search", "issues"): json.dumps(results)})


def org_hit(repo: str, number: int, title: str, labels: tuple[str, ...] = ()) -> dict:
    return {
        "repository": {"name": repo},
        "number": number,
        "title": title,
        "url": f"https://github.com/MyThingsLab/{repo}/issues/{number}",
        "labels": [{"name": name} for name in labels],
    }
