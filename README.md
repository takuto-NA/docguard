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
| `DG-FORMAT002` | Unexpected heading order (opt-in) |
| `DG-FORMAT003` | Missing front matter |
| `DG-SPLIT001` | Possible mixed document roles (opt-in) |
| `DG-ORG001` | Orphan document (opt-in) |
| `DG-ORG002` | Missing outgoing links on hub (opt-in) |
| `DG-ORG003` | Unreachable from index |

### Organization link checks (Phase 2)

Phase 2 adds two **opt-in** link-structure checks on top of the existing reachability rule (`DG-ORG003`). Both default to `warning`, so they surface issues without failing CI unless you raise severity to `error`.

See [Organization link rules (Phase 2)](docs/organization-rules.md) for examples, configuration, and how these checks differ from reachability.

| Code | Check | Default |
|------|-------|---------|
| `DG-ORG001` | Orphan document — no incoming links from other in-scope Markdown | opt-in, `warning` |
| `DG-ORG002` | Hub dead end — hub document with no outgoing links to in-scope Markdown | opt-in, `warning` |
| `DG-ORG003` | Unreachable from index | when `require_index_reachability = true`, `error` |

### Structure checks (Phase 3)

Phase 3 adds two **opt-in** structure checks inside each document. Both default to `warning`.

With Phase 3 enabled you can:

- warn when an **untyped** document mixes multiple document purposes in its level-2 headings (`DG-SPLIT001`)
- warn when a heading **skips a level** (for example H2 then H4) (`DG-FORMAT002`)
- run the same checks from the CLI, JSON output, or `pytest --docguard`
- raise either rule to `error` severity when you want CI to fail

See [Structure rules (Phase 3)](docs/structure-rules.md) for role families, examples, and configuration.

| Code | Check | Default |
|------|-------|---------|
| `DG-SPLIT001` | Mixed document roles — untyped document with level-2 headings matching multiple role families | opt-in, `warning` |
| `DG-FORMAT002` | Unexpected heading order — heading level skip (for example H2 then H4) | opt-in, `warning` |

You can scan from the CLI, emit JSON for CI, override severity per rule, define typed documents such as ADRs, run the same checks through pytest, and scan UTF-8 Markdown with Japanese or other non-ASCII content.

See [docs/usage.md](docs/usage.md#what-you-can-do-today) for the phased capability summary, full configuration, exit codes, and self-test instructions. Maintainers of this repository should also read [docs/dogfood.md](docs/dogfood.md#what-you-can-rely-on-in-this-repository) for the document budget gate.

## Documentation in this repository

- [docs/usage.md](docs/usage.md) — capabilities, configuration, and entry point
- [docs/organization-rules.md](docs/organization-rules.md) — Phase 2 organization link rules
- [docs/structure-rules.md](docs/structure-rules.md) — Phase 3 structure rules
- [docs/dogfood.md](docs/dogfood.md) — self-test, readiness, and document budget gate
- [CONTEXT.md](CONTEXT.md) — domain glossary
- [docs/adr/0001-cli-first-docguard.md](docs/adr/0001-cli-first-docguard.md)
- [docs/adr/0002-structured-diagnostics-and-strict-config.md](docs/adr/0002-structured-diagnostics-and-strict-config.md)
- [docs/adr/0003-organization-link-rules.md](docs/adr/0003-organization-link-rules.md)
- [docs/adr/0004-utf-8-markdown-encoding.md](docs/adr/0004-utf-8-markdown-encoding.md)
- [docs/adr/0005-phase3-structure-diagnostics.md](docs/adr/0005-phase3-structure-diagnostics.md)
- [docs/adr/0006-document-budget-dogfood-gate.md](docs/adr/0006-document-budget-dogfood-gate.md)

## Roadmap

Phase 3 structure diagnostics (`DG-SPLIT001`, `DG-FORMAT002`) are implemented. Document budget dogfood gate is documented in [docs/dogfood.md](docs/dogfood.md).
