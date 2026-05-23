---
status: accepted
date: 2026-05-23
---

# Organization link rules for Phase 2

## Status

Accepted.

## Context

Phase 1.5 introduced a document graph with incoming links, outgoing links, and index reachability. Phase 2 adds organization diagnostics that use that graph without duplicating `DG-ORG003` unreachable-from-index behavior.

Teams need distinct signals for:

- documents that nothing links to
- hub documents that do not link onward to other in-scope Markdown files

## Decision

Phase 2 adds two opt-in organization rules:

| Code | Name | Definition |
|------|------|------------|
| `DG-ORG001` | orphan document | A scanned document with zero incoming Markdown links from other in-scope documents |
| `DG-ORG002` | missing outgoing links | A hub document with zero outgoing Markdown links to other in-scope documents |

Rules and semantics:

1. **Orphan vs unreachable remain distinct.** A document can be unreachable from index without being an orphan when it belongs to a linked cluster that is not connected to any configured index file.
2. **Index files are excluded from orphan detection.** Paths listed in `index_files` are never flagged as orphans even when they have zero incoming links.
3. **Hub documents are the only ORG002 targets.** Hub documents are paths listed in `index_files` plus any path matching optional `hub_globs`. Leaf documents are not checked for outgoing links.
4. **Both rules are opt-in.** Configuration keys are `require_orphan_detection` and `require_hub_outgoing_links`, both defaulting to `false`.
5. **Initial severity is warning.** Both diagnostics default to `warning` so teams can adopt Phase 2 without immediately failing CI.
6. **Independent from reachability.** `require_index_reachability` and `DG-ORG003` remain separate from ORG001 and ORG002.

Configuration shape:

```toml
[tool.docguard]
index_files = ["README.md"]
require_orphan_detection = false
require_hub_outgoing_links = false
hub_globs = []

[tool.docguard.severity]
DG-ORG001 = "warning"
DG-ORG002 = "warning"
```

## Consequences

- Phase 2 Execute wires graph helpers into rule functions in `src/docguard/rules/__init__.py`, extends configuration parsing, and adds runner integration.
- Documentation and tests preserve the orphan/unreachable example dialogue in `CONTEXT.md`.
- Dogfood impact was measured before enabling either rule in this repository's default configuration; both flags remain off by default.
