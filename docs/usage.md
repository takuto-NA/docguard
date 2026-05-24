# docguard usage

Docguard is a CLI-first Markdown structure checker for repositories. It helps teams keep documentation from growing too large, becoming unreachable from index files, or drifting away from expected document types such as ADRs.

Docguard is intentionally different from markdownlint or Prettier. Those tools focus on formatting. Docguard focuses on document structure and repository health.

## Install

From PyPI with [uv](https://docs.astral.sh/uv/):

```bash
uv add docguard
uv run docguard docs/ --summary
```

Equivalent with pip:

```bash
pip install docguard
docguard docs/ --summary
```

For development in this repository, see [README.md](../README.md#development).

## What you can do today

Docguard treats Markdown as a maintainable repository asset, not just prose files. Run the same checks from the CLI, JSON output, or pytest.

| Phase | What you can check | Diagnostics | Typical default |
|-------|-------------------|-------------|-----------------|
| Core | Document and section size; typed document shape; index reachability | `DG-SIZE001`, `DG-SIZE002`, `DG-FORMAT001`, `DG-FORMAT003`, `DG-ORG003` | on when configured |
| Phase 2 | Link structure between files: orphans and hub dead ends | `DG-ORG001`, `DG-ORG002` | opt-in, `warning` |
| Phase 3 | Structure inside each file: mixed roles and heading level skips | `DG-SPLIT001`, `DG-FORMAT002` | opt-in, `warning` |

All nine diagnostics share the same entry points:

```bash
docguard docs/ --summary
docguard docs/ --format json
pytest --docguard
pytest --docguard-only
```

Phase 2 details: [docs/organization-rules.md](organization-rules.md). Phase 3 details: [docs/structure-rules.md](structure-rules.md). UTF-8 and Japanese content: [Unicode and UTF-8 support](#unicode-and-utf-8-support) below.

This repository dogfoods docguard with a fixed **400-line document budget**; see [docs/dogfood.md](dogfood.md#what-you-can-rely-on-in-this-repository).

## Scan Markdown from the CLI

```bash
docguard docs/ --summary            # recommended for local use
docguard docs/                      # silent when no diagnostics (CI-friendly default)
docguard docs/ --quiet              # silent on success, including warnings
docguard README.md docs/            # explicit paths override configured paths
docguard docs/ --format json        # machine-readable output for CI
docguard docs/ --verbose            # success summary or non-error diagnostics
```

If `pyproject.toml` contains `[tool.docguard]`, docguard uses that configuration. Otherwise it scans `docs/` with size limits and a built-in ADR document type for `adr/*.md`.

## Output modes

| Mode | Success output (human) | When to use |
|------|------------------------|-------------|
| default | silent if no diagnostics; **warnings print** if present | CI when warnings should surface |
| `--quiet` | silent on success, **including warnings** | CI or scripts that want exit-code-only success |
| `--summary` | one summary line if **no diagnostics** | local daily check |
| `--verbose` | summary + non-error diagnostics | warning triage |
| `--format json` | JSON payload always | machine-readable CI |

`--summary` prints a one-line success summary only when there are no diagnostics. If warnings are present, use `--verbose` to review them. `--quiet` cannot be combined with `--summary` or `--verbose`. `--format json` ignores `--quiet`.

## Enforce nine diagnostics

| Code | What it checks |
|------|----------------|
| `DG-SIZE001` | Whole document exceeds the line limit |
| `DG-SIZE002` | A heading section exceeds the line limit |
| `DG-FORMAT001` | A typed document is missing a required heading |
| `DG-FORMAT002` | A heading skips one or more levels (opt-in) |
| `DG-FORMAT003` | A typed document is missing YAML front matter or a required key |
| `DG-SPLIT001` | An untyped document may mix multiple document role families (opt-in) |
| `DG-ORG001` | Orphan document: zero incoming links from other in-scope Markdown files (opt-in) |
| `DG-ORG002` | Missing outgoing links: hub document with zero outgoing links to in-scope Markdown files (opt-in) |
| `DG-ORG003` | A document is not reachable from configured index files |

Each diagnostic includes a human-readable message, why-it-matters text, and an optional suggested next action such as a split target.

## Define typed documents

Use `document_types` in `pyproject.toml` to attach rules to glob patterns. ADRs are the primary example:

- required headings such as `Status`, `Context`, `Decision`, and `Consequences`
- required YAML front matter keys such as `status` and `date`
- per-type line limits that override global defaults

A document may match at most one `document_types` entry. Overlapping globs are rejected as a configuration error.

## Require index reachability

When `require_index_reachability = true`, docguard builds a document link graph and flags documents that cannot be reached from any configured `index_files` entry inside the scanned scope.

This catches documentation that exists in the repository but is easy to miss during review because nothing links to it.

## Detailed rule guides

| Topic | Document |
|-------|----------|
| Phase 2 organization link rules | [docs/organization-rules.md](organization-rules.md) |
| Phase 3 structure rules | [docs/structure-rules.md](structure-rules.md) |
| Dogfood, readiness, and self-test | [docs/dogfood.md](dogfood.md) |

## Run the same checks through pytest

```bash
pytest --docguard          # normal tests plus one docguard item per Markdown file
pytest --docguard-only     # docguard checks only, without normal Python tests
```

Each Markdown document becomes one pytest item named like `docs/architecture.md::docguard`.

## Use predictable CI exit codes

| Code | Meaning |
|------|---------|
| `0` | No error-severity diagnostics |
| `1` | One or more error-severity diagnostics |
| `2` | Invalid `[tool.docguard]` configuration or a Markdown file that is not valid UTF-8 |

Warnings do not fail a run. Exit code `2` failures are pre-diagnostic: invalid configuration is rejected before scanning, and non-UTF-8 Markdown files fail during discovery with a clear message instead of a traceback.

Severity can be overridden per diagnostic code:

```toml
[tool.docguard.severity]
DG-SIZE001 = "warning"
```

Supported values are `error`, `warning`, and `experimental`. Only `error` fails a run.

## Unicode and UTF-8 support

Docguard officially supports UTF-8 Markdown. Teams can use Japanese or other non-ASCII content in documents, configuration, and file paths without hitting tracebacks.

See [docs/adr/0004-utf-8-markdown-encoding.md](adr/0004-utf-8-markdown-encoding.md) for the encoding contract.

### What you can do

| Capability | Example |
|------------|---------|
| Scan Japanese Markdown | `## 概要`, body text, and paths such as `docs/設計.md` |
| Use Japanese in configuration | `required_headings = ["概要", "背景"]` |
| Import docguard as a library | `from docguard.runner import run_docguard_from_paths` |
| Fail safely on non-UTF-8 input | Shift_JIS files exit with code `2` instead of a traceback |
| Preserve CJK in JSON output | Diagnostic messages keep characters such as `概要` |
| Read UTF-8 with BOM | BOM is stripped automatically through `utf-8-sig` |
| Get useful split suggestions for CJK headings | `## 概要` / `## 背景` → `section-3.md`, `section-6.md` |

All entry points share the same behavior:

- CLI: `docguard docs/`
- pytest: `pytest --docguard`
- library: `run_docguard_from_paths()`

### Encoding rules

- Markdown files must be UTF-8. Files without a BOM are preferred; UTF-8 with BOM is also accepted.
- Non-UTF-8 files such as Shift_JIS fail with exit code `2` and do not produce a traceback.
- Diagnostic messages stay in English.
- Document paths, heading names, and configuration values may contain Unicode characters.

Example with Japanese required headings:

```toml
[[tool.docguard.document_types]]
name = "guide"
glob = "docs/guide/*.md"
required_headings = ["概要", "背景"]
```

Example scan:

```bash
docguard README.md docs/ --summary
docguard docs/ --format json
docguard docs/ --quiet
pytest --docguard
```

Example split suggestion for a Japanese document:

```text
Suggested split:
  - docs/notes/section-3.md
  - docs/notes/section-6.md
```

Non-ASCII headings use `section-{line_number}` when a Latin slug cannot be generated.

### Not supported yet

- Automatic detection of Shift_JIS or other legacy encodings
- Localized diagnostic messages (English only; Unicode content in paths and headings is fine)

Automated coverage lives in `tests/test_unicode_support.py`.

## Phase 1.5 UX and reliability

These improvements are part of the current release even though the CLI surface looks the same:

- `--summary` prints checked document count and diagnostic count on success when there are no diagnostics
- `--verbose` prints checked document count and any non-error diagnostics
- `--quiet` suppresses human output on success, including warnings; errors still print
- `--docguard-only` runs only docguard items in pytest
- document title headings (`# ...`) are not treated as section-size targets when lower-level headings exist
- missing, out-of-project, or non-Markdown explicit CLI paths exit with code `2` without a traceback
- non-UTF-8 Markdown files exit with code `2` without a traceback
- invalid severity values and invalid reachability configuration are rejected before scanning
- JSON output includes `checked_document_count`
- `--verbose` cannot be used with `--format json`
- `--quiet` cannot be used with `--summary` or `--verbose`
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
require_orphan_detection = false
require_hub_outgoing_links = false
require_mixed_role_detection = false
require_heading_order_check = false
hub_globs = []

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
- orphan detection runs only when `require_orphan_detection = true`; index files in scope are excluded
- hub outgoing-link checks run only when `require_hub_outgoing_links = true`; hub documents are `index_files` plus optional `hub_globs`
- when `require_hub_outgoing_links = true` but no hub documents are in scope, docguard reports no diagnostics
- mixed-role detection runs only when `require_mixed_role_detection = true`; typed documents are excluded
- heading order checks run only when `require_heading_order_check = true`
- `experimental_rules_enabled = true` is reserved for future opt-in rules and currently has no effect

When documentation exceeds the configured budget, split files instead of raising `max_document_lines`. See [docs/dogfood.md](dogfood.md) and [docs/adr/0006-document-budget-dogfood-gate.md](adr/0006-document-budget-dogfood-gate.md).

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
