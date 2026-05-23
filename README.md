# docguard

CLI-first Markdown structure checker for repositories.

Docguard helps teams keep documentation from growing too large, becoming unreachable from index files, or drifting away from expected document types such as ADRs.

## Quick start

```bash
pip install docguard
docguard docs/
pytest --docguard
```

For development:

```bash
pip install -e ".[dev]"
python -m pytest
```

## What this tool checks

The MVP checks document size, section size, required headings, YAML front matter, and index reachability.

See [docs/usage.md](docs/usage.md) for the full capability list, configuration, diagnostics, and self-test instructions.

## Documentation in this repository

- [docs/usage.md](docs/usage.md) — capabilities, configuration, and self-test
- [CONTEXT.md](CONTEXT.md) — domain glossary
- [docs/adr/0001-cli-first-docguard.md](docs/adr/0001-cli-first-docguard.md)
- [docs/adr/0002-structured-diagnostics-and-strict-config.md](docs/adr/0002-structured-diagnostics-and-strict-config.md)

## Roadmap

### Phase 2

- `DG-ORG001` orphan document
- `DG-ORG002` missing outgoing links

### Phase 3

- `DG-SPLIT001` possible mixed document roles
- `DG-FORMAT002` unexpected heading order

Phase 3 rules will ship as warnings or experimental diagnostics first.
