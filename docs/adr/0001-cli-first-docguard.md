---
status: accepted
date: 2026-05-23
---

# CLI-first docguard identity

## Status

Accepted.

## Context

Docguard needs a primary user entry point that works outside pytest-based workflows. Many repositories use mixed tooling, and a CLI keeps the checker usable from pre-commit hooks, Makefiles, and non-Python CI jobs.

## Decision

Docguard is distributed as a Python package named `docguard` with a primary CLI entry point. Pytest integration is provided as a thin adapter via `pytest --docguard`, not as the main product identity.

## Consequences

README, installation docs, and user onboarding should emphasize `docguard docs/` first. The pytest plugin must reuse the same core runner as the CLI.
