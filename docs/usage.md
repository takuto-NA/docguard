## What you can do

Docguard treats Markdown as a maintainable repository asset, not just prose files.

With the current MVP you can:

- scan Markdown files or directories from the CLI
- enforce document and section size limits in CI
- require headings and YAML front matter for typed documents such as ADRs
- require documents to be reachable from configured index files
- get human-readable diagnostics with why-it-matters text and suggested next actions
- emit the same diagnostics as JSON for automation
- run the same checks through `pytest --docguard`

Docguard is intentionally different from markdownlint or Prettier. Those tools focus on formatting. Docguard focuses on document structure and repository health.

## CLI usage

Scan a directory with zero-config defaults:

```bash
docguard docs/
```

Scan explicit paths:

```bash
docguard README.md docs/
```

Emit JSON for CI or automation:

```bash
docguard README.md docs/ --format json
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | No error-severity diagnostics |
| `1` | One or more error-severity diagnostics |
| `2` | Invalid `[tool.docguard]` configuration |

Warnings do not fail a run. Configuration errors fail before document scanning begins.

## Pytest usage

Run docguard through pytest in CI:

```bash
pytest --docguard
```

Each Markdown document in the configured scope becomes one pytest item named like `docs/architecture.md::docguard`.

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
- a document may match at most one `document_types` entry
- index reachability is checked only when `require_index_reachability = true`

## MVP diagnostics

| Code | Meaning |
|------|---------|
| `DG-SIZE001` | Document too long |
| `DG-SIZE002` | Section too long |
| `DG-FORMAT001` | Missing required heading |
| `DG-FORMAT003` | Missing front matter |
| `DG-ORG003` | Unreachable from index |

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

## Self-test in this repository

This repository uses docguard on its own documentation.

Configured scope in `pyproject.toml`:

- `README.md`
- `CONTEXT.md`
- `docs/usage.md`
- `docs/adr/*.md`

Configured checks:

- all scoped documents must be reachable from `README.md`
- ADRs must include `Status`, `Context`, `Decision`, and `Consequences`
- ADRs must include YAML front matter keys `status` and `date`

Run the self-check manually:

```bash
docguard README.md CONTEXT.md docs/
docguard README.md CONTEXT.md docs/ --format json
pytest --docguard
python -m pytest
```

Automated self-check tests live in `tests/test_dogfood.py`.
