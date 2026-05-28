# Organization link rules (Phase 2)

Phase 2 adds two opt-in organization checks. They use the same document link graph as reachability but answer different questions.

| Question | Diagnostic | When it runs |
|----------|------------|--------------|
| Can anyone reach this file from an index? | `DG-ORG003` | `require_index_reachability = true` |
| Does any other in-scope document link to this file? | `DG-ORG001` | `require_orphan_detection = true` |
| Does this hub document link onward to other in-scope files? | `DG-ORG002` | `require_hub_outgoing_links = true` |

Orphan and unreachable are not the same. A linked cluster that is not connected to any index file can be unreachable without being an orphan. See [CONTEXT.md](../CONTEXT.md) for the glossary and example dialogue.

## Detect orphan documents (`DG-ORG001`)

What it finds: in-scope Markdown files that no other in-scope Markdown file links to.

Typical fix: add a relative Markdown link to the orphan from another document, or from an index file.

Example: if `README.md` links only to `docs/design.md` and `docs/orphan.md` has zero incoming links, docguard reports `DG-ORG001` on `docs/orphan.md`.

Enable:

```toml
[tool.docguard]
index_files = ["README.md"]
require_orphan_detection = true
```

Index files listed in `index_files` are never flagged as orphans, even when they have zero incoming links.

## Detect hub dead ends (`DG-ORG002`)

What it finds: hub documents that do not link onward to any other in-scope Markdown file.

Hub documents are paths in `index_files` plus any path matching optional `hub_globs`. Leaf documents are not checked for outgoing links.

Typical fix: add relative Markdown links from the hub to the documents it should introduce.

Example: if `README.md` has no outgoing links to in-scope Markdown, docguard reports `DG-ORG002` on `README.md`. A leaf such as `docs/design.md` is never an `DG-ORG002` target.

Enable:

```toml
[tool.docguard]
index_files = ["README.md"]
require_hub_outgoing_links = true
hub_globs = ["docs/index-*.md"]   # optional; extra hub paths
```

When `require_hub_outgoing_links = true` but no hub documents are in the scanned scope, docguard reports no diagnostics.

## Enable both rules

Both rules are opt-in and default to `warning`:

```toml
[tool.docguard]
index_files = ["README.md"]
require_orphan_detection = true
require_hub_outgoing_links = true
hub_globs = []

[tool.docguard.severity]
DG-ORG001 = "warning"
DG-ORG002 = "warning"
```

Set either code to `"error"` to fail CI on that diagnostic.

Full specification: [docs/adr/0003-organization-link-rules.md](adr/0003-organization-link-rules.md).

## Run Phase 2 checks

Phase 2 diagnostics use the same entry points as other rules:

```bash
docguard                       # warnings print on stdout; exit 0 unless severity is error
docguard --verbose             # summary plus non-error diagnostics
docguard --format json         # machine-readable output for CI
pytest --docguard              # one pytest item per Markdown file
```

Example output for `DG-ORG001` as a warning:

```text
FAILED docs/orphan.md::docguard

DG-ORG001 orphan document
  docs/orphan.md has no incoming links from other in-scope Markdown documents.

Why this matters:
  Documents with no incoming links from other in-scope documents are likely to be missed during review.

Link to this document from another in-scope Markdown document.
```

This repository keeps both Phase 2 flags off in its default `pyproject.toml`. Enable them in a project `pyproject.toml` when these checks are needed.

See also: [docs/usage.md](usage.md), [docs/dogfood.md](dogfood.md).
