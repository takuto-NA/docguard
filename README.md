# docguard

CLI-first Markdown structure checker for repositories.

Docguard helps teams keep documentation from growing too large, becoming unreachable from index files, or drifting away from expected document types such as ADRs.

## Quick start

With [uv](https://docs.astral.sh/uv/):

```bash
uv add docguard
uv run docguard docs/ --summary
uv run docguard docs/ --format json
uv run pytest --docguard
uv run pytest --docguard-only
```

Equivalent with pip:

```bash
pip install docguard
docguard docs/ --summary
pytest --docguard
```

## Configuration

Add a minimal configuration to `pyproject.toml`:

```toml
[tool.docguard]
paths = ["docs"]
index_files = ["README.md"]
max_document_lines = 400
max_section_lines = 120
```

Full configuration, diagnostics, and exit codes: [usage guide](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md#what-you-can-do-today). To adopt docguard in another repository, see [Use in another repository](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md#use-in-another-repository).

## What this tool checks

Docguard focuses on document structure and repository health, not Markdown formatting.

| Phase | What you can check | Diagnostics | Typical default |
|-------|-------------------|-------------|-----------------|
| Core | Document and section size; typed document shape; index reachability | `DG-SIZE001`, `DG-SIZE002`, `DG-FORMAT001`, `DG-FORMAT003`, `DG-ORG003` | on when configured |
| Phase 2 | Link structure between files: orphans and hub dead ends | `DG-ORG001`, `DG-ORG002` | opt-in, `warning` |
| Phase 3 | Structure inside each file: mixed roles and heading level skips | `DG-SPLIT001`, `DG-FORMAT002` | opt-in, `warning` |

Phase 2 details: [organization rules](https://github.com/takuto-NA/docguard/blob/main/docs/organization-rules.md). Phase 3 details: [structure rules](https://github.com/takuto-NA/docguard/blob/main/docs/structure-rules.md).

## Development

Requires Python 3.11+ and uv on PATH:

```bash
uv pip install -e ".[dev]"
uv run pytest
uv run docguard README.md CONTEXT.md docs/ --summary
```

## Documentation

- [Usage](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md)
- [Organization rules (Phase 2)](https://github.com/takuto-NA/docguard/blob/main/docs/organization-rules.md)
- [Structure rules (Phase 3)](https://github.com/takuto-NA/docguard/blob/main/docs/structure-rules.md)
- [Dogfood and self-test](https://github.com/takuto-NA/docguard/blob/main/docs/dogfood.md)
- [Release readiness](https://github.com/takuto-NA/docguard/blob/main/docs/release-readiness.md)
- [Domain glossary (CONTEXT.md)](https://github.com/takuto-NA/docguard/blob/main/CONTEXT.md)
- [Architecture decision records](https://github.com/takuto-NA/docguard/tree/main/docs/adr)

## Status

Alpha (`Development Status :: 3 - Alpha`). Configuration keys, diagnostic JSON fields, and rule defaults may change; breaking changes are recorded in [CHANGELOG.md](https://github.com/takuto-NA/docguard/blob/main/CHANGELOG.md). Exit codes and existing diagnostic meanings are preserved where practical.

Phase 3 structure diagnostics (`DG-SPLIT001`, `DG-FORMAT002`) are implemented. Release readiness is documented in [docs/release-readiness.md](https://github.com/takuto-NA/docguard/blob/main/docs/release-readiness.md).

## Repository navigation

Relative links for clone checkouts and docguard reachability checks:

- [docs/usage.md](docs/usage.md)
- [docs/organization-rules.md](docs/organization-rules.md)
- [docs/structure-rules.md](docs/structure-rules.md)
- [docs/dogfood.md](docs/dogfood.md)
- [docs/release-readiness.md](docs/release-readiness.md)
- [CONTEXT.md](CONTEXT.md)
- [docs/adr/0001-cli-first-docguard.md](docs/adr/0001-cli-first-docguard.md)
- [docs/adr/0002-structured-diagnostics-and-strict-config.md](docs/adr/0002-structured-diagnostics-and-strict-config.md)
- [docs/adr/0003-organization-link-rules.md](docs/adr/0003-organization-link-rules.md)
- [docs/adr/0004-utf-8-markdown-encoding.md](docs/adr/0004-utf-8-markdown-encoding.md)
- [docs/adr/0005-phase3-structure-diagnostics.md](docs/adr/0005-phase3-structure-diagnostics.md)
- [docs/adr/0006-document-budget-dogfood-gate.md](docs/adr/0006-document-budget-dogfood-gate.md)
- [docs/adr/0007-document-responsibility-drift-guard.md](docs/adr/0007-document-responsibility-drift-guard.md)
- [docs/adr/0008-pypi-alpha-distribution.md](docs/adr/0008-pypi-alpha-distribution.md)
