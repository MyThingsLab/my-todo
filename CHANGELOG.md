# Changelog

## [Unreleased]
### Added/Changed
- implemented plan/sources/render/prioritize/curator/cli; 23 tests green (ruff+pytest, incl GITHUB_ACTIONS=true); dogfooded org roll-up over live org issues
- Mechanical migration to mythings.testing: local FakeGh/FakeSearch became fake_gh/fake_search wiring over the shared FakeGh; the empty-tree make_target_repo stays local by design (first run must create TODO.md in a fileless repo).
