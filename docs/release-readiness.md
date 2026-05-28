# Release readiness

This page records distribution milestones for docguard. It is separate from [docs/dogfood.md](dogfood.md), which covers self-application impact tables, self-test commands, and readiness checklists for this repository's own documentation. See [docs/adr/0007-document-responsibility-drift-guard.md](adr/0007-document-responsibility-drift-guard.md) for why release planning lives here.

## Distribution roadmap

Docguard is published on PyPI as `docguard-structure` 0.2.0 (Alpha). The next Alpha release is 0.3.0 for strict baseline adoption. This page records distribution milestones and operator history. See [docs/adr/0008-pypi-alpha-distribution.md](adr/0008-pypi-alpha-distribution.md) for distribution decisions and [docs/adr/0013-pypi-distribution-name-docguard-structure.md](adr/0013-pypi-distribution-name-docguard-structure.md) for the PyPI distribution name.

### 1. Alpha source distribution

- [x] Keep `Development Status :: 3 - Alpha`.
- [x] Support repository installation and source checkouts.
- [x] Require the self-test commands in [docs/dogfood.md](dogfood.md#self-test-in-this-repository) to pass before sharing a release tag.

### 2. PyPI Alpha readiness

Resolved decisions:

- PyPI distribution name is `docguard-structure` (CLI and import remain `docguard`).
- PyPI users rely on a self-contained README with GitHub absolute links; docs are not bundled in the wheel.
- Documentation and release verification standardize on uv-first workflows; pip remains supported.
- Publish is manual via GitHub Actions `workflow_dispatch` with PyPI Trusted Publishing.
- TestPyPI dry-run uses [`.github/workflows/publish-testpypi.yml`](../.github/workflows/publish-testpypi.yml) before production upload (optional; skipped for `0.2.0`).

Checklist:

- [x] ADR 0008 accepted.
- [x] ADR 0013 accepted (distribution name).
- [x] Release notes in `CHANGELOG.md` for `0.2.0`.
- [x] CI runs full pytest, docguard self-check, build, twine check, and wheel smoke on Python 3.11–3.13.
- [x] Repository prose style guard for user-facing pages through docguard core (`tests/test_release_readiness.py`).
- [x] Wheel smoke test installs the built wheel and runs `docguard --help` plus installed pytest plugin discovery.
- [x] Manual publish workflow configured for PyPI Trusted Publishing (`publish.yml`).
- [x] TestPyPI publish workflow configured (`publish-testpypi.yml`).

Operator prerequisites before first upload:

- [x] Configure production PyPI Trusted Publishing: `docguard-structure` / `publish.yml` / `pypi` environment.
- [ ] Configure TestPyPI Trusted Publishing: `docguard-structure` / `publish-testpypi.yml` / `testpypi` environment (deferred; skipped for `0.2.0`).
- [x] Create GitHub environment `pypi`.
- [ ] Create GitHub environment `testpypi` (deferred; skipped for `0.2.0`).
- [x] Run CI green on `main`, then trigger production publish workflow.
- [x] Verify `pip install docguard-structure` from production PyPI.
- [x] Tag `v0.2.0`, create GitHub Release.

TestPyPI install verification (optional, not run for `0.2.0`):

```bash
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "docguard-structure==0.2.0"
docguard --help
```

Production install verification: see [docs/usage.md](usage.md#from-pypi).

First production upload checklist (`0.2.0`):

- [x] TestPyPI skipped for first release (Trusted Publishing verified on production PyPI instead).
- [x] `v0.2.0` tag pushed and [GitHub Release](https://github.com/takuto-NA/docguard/releases/tag/v0.2.0) published.
- [x] Production publish workflow succeeded.
- [x] [pypi.org/project/docguard-structure/0.2.0](https://pypi.org/project/docguard-structure/0.2.0/) published.

### 3. Stable readiness

- Freeze or explicitly version configuration keys and diagnostic JSON fields.
- Document compatibility expectations for rule defaults and exit codes.
- Keep dogfood gates green without raising document budgets or copying detailed reference content into README.

Do not present the project as a stable package until the Stable readiness items are complete.

See also: [docs/dogfood.md](dogfood.md), [docs/usage.md](usage.md).
