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

| Code | Check |
|------|-------|
| `DG-SIZE001` | Document too long |
| `DG-SIZE002` | Section too long |
| `DG-FORMAT001` | Missing required heading |
| `DG-FORMAT003` | Missing front matter |
| `DG-ORG001` | Orphan document (opt-in) |
| `DG-ORG002` | Missing outgoing links on hub (opt-in) |
| `DG-ORG003` | Unreachable from index |

### Organization link checks (Phase 2)

Phase 2 adds two **opt-in** link-structure checks on top of the existing reachability rule (`DG-ORG003`). Both default to `warning`, so they surface issues without failing CI unless you raise severity to `error`.

See [Organization link rules (Phase 2)](docs/usage.md#organization-link-rules-phase-2) in [docs/usage.md](docs/usage.md) for examples, configuration, and how these checks differ from reachability.

| Code | Check | Default |
|------|-------|---------|
| `DG-ORG001` | Orphan document — no incoming links from other in-scope Markdown | opt-in, `warning` |
| `DG-ORG002` | Hub dead end — hub document with no outgoing links to in-scope Markdown | opt-in, `warning` |
| `DG-ORG003` | Unreachable from index | when `require_index_reachability = true`, `error` |

You can scan from the CLI, emit JSON for CI, override severity per rule, define typed documents such as ADRs, run the same checks through pytest, and scan UTF-8 Markdown with Japanese or other non-ASCII content.

See [docs/usage.md](docs/usage.md) for the full capability list, UTF-8 support, configuration, exit codes, and self-test instructions.

## Documentation in this repository

- [docs/usage.md](docs/usage.md) — capabilities, configuration, and self-test
- [CONTEXT.md](CONTEXT.md) — domain glossary
- [docs/adr/0001-cli-first-docguard.md](docs/adr/0001-cli-first-docguard.md)
- [docs/adr/0002-structured-diagnostics-and-strict-config.md](docs/adr/0002-structured-diagnostics-and-strict-config.md)
- [docs/adr/0003-organization-link-rules.md](docs/adr/0003-organization-link-rules.md)
- [docs/adr/0004-utf-8-markdown-encoding.md](docs/adr/0004-utf-8-markdown-encoding.md)

## Roadmap

### Phase 3

- `DG-SPLIT001` possible mixed document roles
- `DG-FORMAT002` unexpected heading order

Phase 3 rules will ship as warnings or experimental diagnostics first.
