---
status: accepted
date: 2026-05-25
---

# PyPI distribution name docguard-structure

## Status

Accepted.

## Context

ADR 0008 planned the first PyPI Alpha release as package name `docguard` with CLI name `docguard`. PyPI rejected `docguard`, `repo-docguard`, and `markdown-docguard` as invalid or too similar to the existing [docguard-cli](https://pypi.org/project/docguard-cli/) project (Canonical-Driven Development tooling, unrelated to this repository).

Trusted Publishing for production PyPI was registered successfully as **`docguard-structure`**.

## Decision

1. **Publish to PyPI as `docguard-structure==0.2.0`** (first public upload).
2. **Keep the CLI command and Python import package as `docguard`.** Users run `pip install docguard-structure` then `docguard docs/ --summary`.
3. **Record the distribution name in release docs and install guides.** Do not rename the GitHub repository or tool brand.
4. **Supersede ADR 0008 item 1** (PyPI package name `docguard`) for distribution naming only. Other ADR 0008 decisions (Alpha status, uv-first docs, manual publish, README policy) remain in force.

Alternatives rejected:

- wait for PEP 541 name transfer for `docguard` (weeks of delay with no guarantee)
- rename the CLI to match the PyPI distribution name (breaks existing docs and `[tool.docguard]` configuration key)
- skip PyPI and rely on Git installs only

## Consequences

- Install commands use `uv add docguard-structure` and `pip install docguard-structure`.
- PyPI project URL: `https://pypi.org/project/docguard-structure/`
- Users searching for `docguard` on PyPI may find `docguard-cli`; README and usage docs must state the correct distribution name prominently.
- TestPyPI and production Trusted Publishing both target project name `docguard-structure`.

See also: [docs/adr/0008-pypi-alpha-distribution.md](0008-pypi-alpha-distribution.md), [docs/release-readiness.md](../release-readiness.md).
