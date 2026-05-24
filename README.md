# docguard

CLI-first Markdown structure checker for repositories.

Docguard helps teams keep documentation from growing too large, becoming unreachable from index files, or drifting away from expected document types such as ADRs.

## Quick start

```bash
pip install docguard
docguard docs/ --summary       # one-line success summary when clean
docguard docs/                 # warnings print if present; silent when clean
docguard docs/ --quiet         # silent on success, including warnings
docguard docs/ --verbose       # summary plus non-error diagnostics
docguard docs/ --format json   # machine-readable output for CI
pytest --docguard
pytest --docguard-only
```

For development:

```bash
pip install -e ".[dev]"
python -m pytest
```

## What this tool checks

Docguard focuses on document structure and repository health, not Markdown formatting.

| Phase | What you can check | Diagnostics | Typical default |
|-------|-------------------|-------------|-----------------|
| Core | Document and section size; typed document shape; index reachability | `DG-SIZE001`, `DG-SIZE002`, `DG-FORMAT001`, `DG-FORMAT003`, `DG-ORG003` | on when configured |
| Phase 2 | Link structure between files: orphans and hub dead ends | `DG-ORG001`, `DG-ORG002` | opt-in, `warning` |
| Phase 3 | Structure inside each file: mixed roles and heading level skips | `DG-SPLIT001`, `DG-FORMAT002` | opt-in, `warning` |

See [docs/usage.md](docs/usage.md#what-you-can-do-today) for the full diagnostic catalog, configuration, exit codes, and self-test instructions. Phase 2 details: [docs/organization-rules.md](docs/organization-rules.md). Phase 3 details: [docs/structure-rules.md](docs/structure-rules.md). Maintainers of this repository should also read [docs/dogfood.md](docs/dogfood.md#what-you-can-rely-on-in-this-repository) for the document budget gate.

## Documentation in this repository

- [docs/usage.md](docs/usage.md) — capabilities, configuration, and entry point
- [docs/organization-rules.md](docs/organization-rules.md) — Phase 2 organization link rules
- [docs/structure-rules.md](docs/structure-rules.md) — Phase 3 structure rules
- [docs/dogfood.md](docs/dogfood.md) — self-test, readiness, document budget gate, and document responsibility boundaries
- [CONTEXT.md](CONTEXT.md) — domain glossary
- [docs/adr/0001-cli-first-docguard.md](docs/adr/0001-cli-first-docguard.md)
- [docs/adr/0002-structured-diagnostics-and-strict-config.md](docs/adr/0002-structured-diagnostics-and-strict-config.md)
- [docs/adr/0003-organization-link-rules.md](docs/adr/0003-organization-link-rules.md)
- [docs/adr/0004-utf-8-markdown-encoding.md](docs/adr/0004-utf-8-markdown-encoding.md)
- [docs/adr/0005-phase3-structure-diagnostics.md](docs/adr/0005-phase3-structure-diagnostics.md)
- [docs/adr/0006-document-budget-dogfood-gate.md](docs/adr/0006-document-budget-dogfood-gate.md)

## Status

Phase 3 structure diagnostics (`DG-SPLIT001`, `DG-FORMAT002`) are implemented. Document budget dogfood gate is documented in [docs/dogfood.md](docs/dogfood.md).
