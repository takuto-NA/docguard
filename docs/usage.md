# docguard usage

Docguard is a CLI-first Markdown structure checker for repositories. It helps teams keep documentation from growing too large, becoming unreachable from index files, or drifting away from expected document types such as ADRs.

Docguard is intentionally different from markdownlint or Prettier. Those tools focus on formatting. Docguard focuses on document structure and repository health.

## What you can do today

Docguard treats Markdown as a maintainable repository asset, not just prose files.

### Scan Markdown from the CLI

```bash
docguard docs/                      # zero-config: scan docs/ with gentle defaults
docguard README.md docs/            # explicit paths override configured paths
docguard docs/ --format json        # machine-readable output for CI
docguard docs/ --summary            # success summary: Checked N documents. Found M diagnostics.
docguard docs/ --verbose            # success summary or non-error diagnostics
```

If `pyproject.toml` contains `[tool.docguard]`, docguard uses that configuration. Otherwise it scans `docs/` with size limits and a built-in ADR document type for `adr/*.md`.

### Enforce five MVP diagnostics

| Code | What it checks |
|------|----------------|
| `DG-SIZE001` | Whole document exceeds the line limit |
| `DG-SIZE002` | A heading section exceeds the line limit |
| `DG-FORMAT001` | A typed document is missing a required heading |
| `DG-FORMAT003` | A typed document is missing YAML front matter or a required key |
| `DG-ORG003` | A document is not reachable from configured index files |

Each diagnostic includes a human-readable message, why-it-matters text, and an optional suggested next action such as a split target.

### Define typed documents

Use `document_types` in `pyproject.toml` to attach rules to glob patterns. ADRs are the primary example:

- required headings such as `Status`, `Context`, `Decision`, and `Consequences`
- required YAML front matter keys such as `status` and `date`
- per-type line limits that override global defaults

A document may match at most one `document_types` entry. Overlapping globs are rejected as a configuration error.

### Require index reachability

When `require_index_reachability = true`, docguard builds a document link graph and flags documents that cannot be reached from any configured `index_files` entry inside the scanned scope.

This catches documentation that exists in the repository but is easy to miss during review because nothing links to it.

### Run the same checks through pytest

```bash
pytest --docguard          # normal tests plus one docguard item per Markdown file
pytest --docguard-only     # docguard checks only, without normal Python tests
```

Each Markdown document becomes one pytest item named like `docs/architecture.md::docguard`.

### Use predictable CI exit codes

| Code | Meaning |
|------|---------|
| `0` | No error-severity diagnostics |
| `1` | One or more error-severity diagnostics |
| `2` | Invalid `[tool.docguard]` configuration |

Warnings do not fail a run. Configuration errors fail before document scanning begins.

Severity can be overridden per diagnostic code:

```toml
[tool.docguard.severity]
DG-SIZE001 = "warning"
```

Supported values are `error`, `warning`, and `experimental`. Only `error` fails a run.

## Phase 1.5 UX and reliability

These improvements are part of the current release even though the CLI surface looks the same:

- `--summary` prints checked document count and diagnostic count on success
- `--verbose` prints checked document count and any non-error diagnostics
- `--docguard-only` runs only docguard items in pytest
- document title headings (`# ...`) are not treated as section-size targets when lower-level headings exist
- missing, out-of-project, or non-Markdown explicit CLI paths exit with code `2` without a traceback
- invalid severity values and invalid reachability configuration are rejected before scanning
- JSON output includes `checked_document_count`
- `--verbose` cannot be used with `--format json`
- when both `--verbose` and `--summary` are provided, `--verbose` takes precedence

## Configuration

Configure docguard in `pyproject.toml`:

```toml
[tool.docguard]
paths = ["docs", "adr", "README.md"]
ignore_globs = ["docs/archive/**", "docs/generated/**"]
max_document_lines = 400
max_section_lines = 120
index_files = ["README.md", "docs/index.md"]
require_index_reachability = true

[[tool.docguard.document_types]]
name = "adr"
glob = "docs/adr/*.md"
required_headings = ["Status", "Context", "Decision", "Consequences"]
required_front_matter_keys = ["status", "date"]
max_document_lines = 160
max_section_lines = 60
```

Behavior notes:

- CLI paths override configured `paths`
- ignored files are excluded from diagnostics and reachability graphs
- index reachability is checked only when `require_index_reachability = true`
- missing or out-of-project CLI paths exit with code `2`
- explicit CLI paths must point to Markdown files or directories containing Markdown
- configured paths that do not exist yet are skipped silently
- when `require_index_reachability = true`, at least one configured `index_files` entry must be inside the scanned scope
- `experimental_rules_enabled = true` is reserved for future opt-in rules and currently has no effect

## Example output

```text
FAILED docs/architecture.md::docguard

DG-SIZE001 document too long
  docs/architecture.md has 812 lines.
  Limit: 400 lines.

Why this matters:
  Large Markdown files tend to mix overview, decisions, implementation details, and operations.

Suggested split:
  - docs/architecture/overview.md
  - docs/architecture/runtime-model.md
```

## Phase 2 specification (not yet implemented)

Phase 2 organization rules are specified in [docs/adr/0003-organization-link-rules.md](adr/0003-organization-link-rules.md).

| Code | What it will check |
|------|-------------------|
| `DG-ORG001` | Orphan document: zero incoming links from other in-scope Markdown files |
| `DG-ORG002` | Missing outgoing links: hub document with zero outgoing links to in-scope Markdown files |

Planned behavior:

- index files listed in `index_files` are excluded from orphan detection
- hub documents are `index_files` plus optional `hub_globs`
- leaf documents are not checked for outgoing links
- both rules default to `warning` and are opt-in via `require_orphan_detection` and `require_hub_outgoing_links`
- `DG-ORG003` unreachable-from-index remains independent

Readiness ships graph helper functions only. Diagnostics and configuration keys arrive in Phase 2 Execute.

## Dogfood impact for Phase 2 rules

If Phase 2 helpers were applied to this repository today:

| Document | Incoming | Outgoing | Orphan candidate | Hub outgoing violation |
|----------|----------|----------|------------------|------------------------|
| `README.md` | none | 5 links | no (index excluded) | no |
| `CONTEXT.md` | `README.md` | none | no | no (leaf) |
| `docs/usage.md` | `README.md` | `docs/adr/0003-organization-link-rules.md` | no | no (leaf) |
| `docs/adr/0001-cli-first-docguard.md` | `README.md` | none | no | no (leaf) |
| `docs/adr/0002-structured-diagnostics-and-strict-config.md` | `README.md` | none | no | no (leaf) |
| `docs/adr/0003-organization-link-rules.md` | `README.md`, `docs/usage.md` | none | no | no (leaf) |

Expected candidate counts: **0 orphan**, **0 hub outgoing violations**.

Automated gate: `tests/test_phase2_readiness.py`.

## Not implemented yet

| Phase | Planned diagnostics |
|-------|---------------------|
| Phase 2 | `DG-ORG001` orphan document, `DG-ORG002` missing outgoing links |
| Phase 3 | `DG-SPLIT001` possible mixed document roles, `DG-FORMAT002` unexpected heading order |

Phase 3 rules will ship as warnings or experimental diagnostics first.

## Self-test in this repository

This repository uses docguard on its own documentation.

Configured scope in `pyproject.toml`:

- `README.md`
- `CONTEXT.md`
- everything under `docs/`

Configured checks:

- all scoped documents must be reachable from `README.md`
- ADRs must include `Status`, `Context`, `Decision`, and `Consequences`
- ADRs must include YAML front matter keys `status` and `date`

Run the self-check manually:

```bash
docguard README.md CONTEXT.md docs/
docguard README.md CONTEXT.md docs/ --summary
docguard README.md CONTEXT.md docs/ --verbose
docguard README.md CONTEXT.md docs/ --format json
pytest --docguard
pytest --docguard-only
python -m pytest
```

Automated self-check tests live in `tests/test_dogfood.py`.

## Phase 2 Readiness Checklist

- [x] ADR 0003 accepted
- [x] `test_graph_phase2_contract.py` green
- [x] `test_phase2_readiness.py` green
- [x] `--verbose` shipped and tested
- [x] Dogfood impact table documented
- [ ] Phase 2 Execute plan approved
