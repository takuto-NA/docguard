# Release readiness

This page records distribution milestones for docguard. It is separate from [docs/dogfood.md](dogfood.md), which covers self-application impact tables, self-test commands, and readiness checklists for this repository's own documentation. See [docs/adr/0007-document-responsibility-drift-guard.md](adr/0007-document-responsibility-drift-guard.md) for why release planning lives here.

## Distribution roadmap

Docguard is ready for Alpha source distribution from the repository and for PyPI Alpha publication after manual approval. See [docs/adr/0008-pypi-alpha-distribution.md](adr/0008-pypi-alpha-distribution.md) for distribution decisions.

### 1. Alpha source distribution

- [x] Keep `Development Status :: 3 - Alpha`.
- [x] Support repository installation and source checkouts.
- [x] Require the self-test commands in [docs/dogfood.md](dogfood.md#self-test-in-this-repository) to pass before sharing a release tag.

### 2. PyPI Alpha readiness

Resolved decisions:

- PyPI users rely on a self-contained README with GitHub absolute links; docs are not bundled in the wheel.
- Documentation and release verification standardize on uv-first workflows; pip remains supported.
- Publish is manual via GitHub Actions `workflow_dispatch` with PyPI Trusted Publishing.

Checklist:

- [x] ADR 0008 accepted.
- [x] Release notes in `CHANGELOG.md` for `0.1.0`.
- [x] CI runs full pytest, docguard self-check, build, twine check, and wheel smoke on Python 3.11–3.13.
- [x] Repository prose style guard for user-facing pages through docguard core (`tests/test_release_readiness.py`).
- [x] Wheel smoke test installs the built wheel and runs `docguard --help` plus installed pytest plugin discovery.
- [x] Manual publish workflow configured for PyPI Trusted Publishing.

Operator prerequisites before first upload:

- Create the PyPI project `docguard`.
- Configure PyPI Trusted Publishing for this GitHub repository and the `pypi` GitHub environment.
- Run CI green, then trigger the publish workflow manually.

Optional before first production upload:

- TestPyPI dry-run.

### 3. Stable readiness

- Freeze or explicitly version configuration keys and diagnostic JSON fields.
- Document compatibility expectations for rule defaults and exit codes.
- Keep dogfood gates green without raising document budgets or copying detailed reference content into README.

Do not present the project as a stable package until the Stable readiness items are complete.

See also: [docs/dogfood.md](dogfood.md), [docs/usage.md](usage.md).
