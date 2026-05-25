---
status: accepted
date: 2026-05-24
---

# PyPI Alpha distribution

## Status

Accepted.

## Context

Docguard is ready for Alpha source distribution from the repository. External projects need a low-friction install path without cloning the repository. The README already shows `pip install docguard`, but PyPI metadata, release verification, CI, and wheel smoke checks were not yet in place.

Release planning lives in `docs/release-readiness.md` per ADR 0007. Distribution decisions are hard to reverse once a package name and first public version are published.

## Decision

1. **Target PyPI Alpha `docguard==0.1.0`** with `Development Status :: 3 - Alpha`. Keep the package and CLI name `docguard`.
2. **Use a self-contained README for PyPI** with GitHub absolute links for deeper docs. Do not bundle `docs/` into the wheel.
3. **Standardize on uv-first workflows** for documentation, local verification, CI, and wheel smoke. Keep pip-compatible PyPI artifacts and document pip as a secondary install path.
4. **Automate verification in CI** (pytest, docguard self-check, build, twine check, wheel smoke). **Publish manually** via a `workflow_dispatch` GitHub Actions workflow using PyPI Trusted Publishing.
5. **Apply a light Alpha compatibility contract.** Configuration keys, diagnostic JSON fields, and rule defaults may change, but breaking changes must appear in `CHANGELOG.md`. Exit codes and existing diagnostic meanings should be preserved where practical.
6. **Implement the documentation language guard as a repository release gate test**, not as a new docguard product diagnostic.

Alternatives rejected:

- bundle full documentation in the wheel instead of a PyPI-safe README
- automatic publish on every git tag before the first Alpha release process is proven
- Stable-level compatibility freeze at first PyPI upload
- rename the package to avoid confusion with unrelated `docguard-cli` on PyPI

## Consequences

- External users can install with `uv add docguard` or `pip install docguard`.
- Contributors develop with `uv pip install -e ".[dev]"` and `uv run pytest`.
- Release notes live in `CHANGELOG.md`; distribution milestones stay in `docs/release-readiness.md`.
- First PyPI upload requires operator setup of PyPI Trusted Publishing outside the repository.
- Stable readiness remains a separate milestone with explicit compatibility commitments.

Distribution name `docguard` was superseded by **`docguard-structure`**; see [docs/adr/0013-pypi-distribution-name-docguard-structure.md](0013-pypi-distribution-name-docguard-structure.md).
