# docguard

CLI-first Markdown structure checker for repositories.

Docguard helps teams keep documentation from growing too large, becoming unreachable from index files, or drifting away from expected document types such as ADRs.

## Quick start

```bash
pip install docguard
docguard docs/
docguard docs/ --summary
docguard docs/ --verbose
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

| Code | Check |
|------|-------|
| `DG-SIZE001` | Document too long |
| `DG-SIZE002` | Section too long |
| `DG-FORMAT001` | Missing required heading |
| `DG-FORMAT003` | Missing front matter |
| `DG-ORG003` | Unreachable from index |

You can scan from the CLI, emit JSON for CI, override severity per rule, define typed documents such as ADRs, and run the same checks through pytest.

See [docs/usage.md](docs/usage.md) for the full capability list, configuration, exit codes, and self-test instructions.

## Documentation in this repository

- [docs/usage.md](docs/usage.md) — capabilities, configuration, and self-test
- [CONTEXT.md](CONTEXT.md) — domain glossary
- [docs/adr/0001-cli-first-docguard.md](docs/adr/0001-cli-first-docguard.md)
- [docs/adr/0002-structured-diagnostics-and-strict-config.md](docs/adr/0002-structured-diagnostics-and-strict-config.md)
- [docs/adr/0003-organization-link-rules.md](docs/adr/0003-organization-link-rules.md)

## Roadmap

### Phase 2

- `DG-ORG001` orphan document
- `DG-ORG002` missing outgoing links

### Phase 3

- `DG-SPLIT001` possible mixed document roles
- `DG-FORMAT002` unexpected heading order

Phase 3 rules will ship as warnings or experimental diagnostics first.
