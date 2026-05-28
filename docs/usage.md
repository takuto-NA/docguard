# docguard usage

Docguard is a CLI-first Markdown structure checker for repositories. It helps teams keep documentation from growing too large, becoming unreachable from index files, or drifting away from expected document types such as ADRs.

Docguard is intentionally different from markdownlint or Prettier. Those tools focus on formatting. Docguard focuses on document structure and repository health.

## Install

### From PyPI

```bash
uv add docguard-structure
uv run docguard --summary
```

Equivalent with pip:

```bash
pip install docguard-structure
docguard --summary
```

```bash
uvx --from docguard-structure docguard --summary
```

### Update an existing uv install

If the project already added docguard with `uv add docguard-structure`, upgrade the dependency and then run the strict baseline check:

```bash
uv add --upgrade docguard-structure
uv run docguard --summary
```

To pin the 0.3 series explicitly:

```bash
uv add "docguard-structure==0.3.0"
uv run docguard --summary
```

Docguard 0.3.0 is a breaking Alpha update. If the check exits with code `2`, first verify that `README.md` is in scope when index reachability is enabled, and move any looser settings such as severity downgrades or larger line limits into `[[tool.docguard.relaxations]]` with a reason.

### Install from Git

Add as a project dependency. Recommended:

```bash
uv add "docguard-structure @ git+https://github.com/takuto-NA/docguard.git"
uv run docguard --summary
```

Install into the active environment:

```bash
uv pip install "git+https://github.com/takuto-NA/docguard.git"
```

```bash
uvx --from "git+https://github.com/takuto-NA/docguard.git" docguard --summary
```

For development in this repository, see [README.md](../README.md#development).

## Use in another repository

Follow these steps when creating or adopting docguard in a separate project.

1. Install docguard — use [Install](#install). Add pytest when using the pytest plugin: `uv add --dev pytest`.
2. Add configuration — start from the [Configuration](#configuration) example. For Phase 2 opt-in checks, see [organization-rules.md](organization-rules.md).
3. Run checks locally — use [Scan Markdown from the CLI](#scan-markdown-from-the-cli) and [Run the same checks through pytest](#run-the-same-checks-through-pytest).
4. Add CI — use the GitHub Actions pattern under [Add docguard to CI](#add-docguard-to-ci). Exit codes are documented in [Use predictable CI exit codes](#use-predictable-ci-exit-codes).

## What you can do today

Docguard treats Markdown as a maintainable repository asset, not only prose files. Run the same checks from the CLI, JSON output, or pytest.

| Phase | What you can check | Diagnostics | Typical default |
|-------|-------------------|-------------|-----------------|
| Core | Document and section size; stub detection; typed document shape; index reachability; prose and documentation style | `DG-SIZE001`, `DG-SIZE002`, `DG-SIZE003`, `DG-FORMAT001`, `DG-FORMAT003`, `DG-ORG003`, `DG-STYLE001`, `DG-STYLE002`, `DG-STYLE003` | strict baseline, `error` |
| Phase 2 | Link structure between files: orphans and hub dead ends | `DG-ORG001`, `DG-ORG002` | opt-in, `warning` |
| Phase 3 | Structure inside each file: mixed roles and heading level skips | `DG-SPLIT001`, `DG-FORMAT002` | opt-in, `warning` |
| Duplicate guidance | Repeated commands, list guidance, or prose paragraphs across the scan scope; headings and paragraphs opt-in | `DG-SPLIT002` | strict baseline, `error` |

Entry points are shared across all diagnostics. See [Scan Markdown from the CLI](#scan-markdown-from-the-cli) and [Run the same checks through pytest](#run-the-same-checks-through-pytest).

Phase 2 details: [docs/organization-rules.md](organization-rules.md). Phase 3 details: [docs/structure-rules.md](structure-rules.md). Prose style details: [docs/prose-style-rules.md](prose-style-rules.md). Duplicate guidance details: [docs/structure-rules.md#detect-duplicate-guidance-dg-split002](structure-rules.md#detect-duplicate-guidance-dg-split002). UTF-8 and Japanese content: [Unicode and UTF-8 support](#unicode-and-utf-8-support).

This repository dogfoods docguard with a fixed 300-line document budget; see [docs/dogfood.md](dogfood.md#what-you-can-rely-on-in-this-repository).

## Scan Markdown from the CLI

```bash
docguard --summary                  # recommended for local use
docguard                            # silent when no diagnostics (CI-friendly default)
docguard --quiet                    # silent on success, including warnings
docguard README.md docs/            # explicit paths override configured paths
docguard --format json              # machine-readable output for CI
docguard --verbose                  # success summary or non-error diagnostics
```

If `pyproject.toml` has no `[tool.docguard]`, or the table is empty, docguard uses the strict baseline: scan `README.md`, `CONTEXT.md`, and `docs`; require reachability from `README.md`; enforce 300-line documents, 120-line sections, and a 20-line floor for untyped non-index documents.

Strict baseline at a glance:

- scope: `README.md`, `CONTEXT.md`, `docs`
- navigation: `README.md` is the index file and unreachable documents fail
- size: documents over 300 lines, sections over 120 lines, and untyped non-index documents under 20 lines fail
- enabled by default: duplicate guidance, prose style, ADR shape, ADR front matter
- still opt-in: orphan detection, hub outgoing-link checks, mixed-role detection, heading-level skips
- relaxation rule: looser settings require `[[tool.docguard.relaxations]]` with `parameter`, `value`, and `reason`

## Output modes

| Mode | Success output (human) | When to use |
|------|------------------------|-------------|
| default | silent if no diagnostics; **warnings print** if present | CI when warnings should surface |
| `--quiet` | silent on success, **including warnings** | CI or scripts that want exit-code-only success |
| `--summary` | summary and active policy if **no diagnostics** | local daily check |
| `--verbose` | summary + non-error diagnostics | warning triage |
| `--format json` | JSON payload always | machine-readable CI |

`--summary` prints a success summary and policy line only when there are no diagnostics. If warnings are present, use `--verbose` to review them. `--quiet` cannot be combined with `--summary` or `--verbose`. `--format json` ignores `--quiet`. `--verbose` cannot be used with `--format json`.

## Enforce diagnostics

| Code | What it checks |
|------|----------------|
| `DG-SIZE001` | Whole document exceeds the line limit |
| `DG-SIZE002` | A heading section exceeds the line limit |
| `DG-SIZE003` | An untyped non-index document is below the document floor |
| `DG-FORMAT001` | A typed document is missing a required heading |
| `DG-FORMAT002` | A heading skips one or more levels (opt-in) |
| `DG-FORMAT003` | A typed document is missing YAML front matter or a required key |
| `DG-SPLIT001` | An untyped document may mix multiple document role families (opt-in) |
| `DG-SPLIT002` | Repeated commands, list guidance, or prose paragraphs across the scan scope; headings and paragraphs opt-in |
| `DG-ORG001` | Orphan document: zero incoming links from other in-scope Markdown files (opt-in) |
| `DG-ORG002` | Missing outgoing links: hub document with zero outgoing links to in-scope Markdown files (opt-in) |
| `DG-ORG003` | A document is not reachable from configured index files |
| `DG-STYLE001` | Prose contains more strong emphasis pairs than `max_strong_emphasis_pairs` |
| `DG-STYLE002` | Prose matches a prohibited pronoun, slang, or parenthetical punctuation pattern |
| `DG-STYLE003` | Heading, prose, or table header matches a forbidden documentation expression |

Each diagnostic includes a human-readable message, why-it-matters text, and an optional suggested next action such as a split target.

## Detect prose style violations (always on)

Prose style checks run on every scan without an opt-in flag. `DG-STYLE001` limits strong emphasis pairs in body prose; default limit is `0`. `DG-STYLE002` flags built-in pronoun and slang patterns such as `you`, `easy`, or `just`, and parenthetical punctuation in body prose after masking Markdown syntax. Code fences, headings, tables, glossary term lines, example dialogue sections, and typed documents such as ADRs are excluded from `DG-STYLE001` and `DG-STYLE002`. `DG-STYLE003` flags forbidden documentation expressions in headings, body prose, and table header cells, including typed ADRs. All three run as strict-baseline `error`; details in [docs/prose-style-rules.md](prose-style-rules.md).

## Detect repeated prose paragraphs (opt-in)

Default duplicate guidance for `code_block` and `list_item` catches repeated commands and checklist bullets. It does not catch the same long narrative paragraph copy-pasted across multiple documents.

Add `paragraph` to `duplicate_guidance_kinds` to have docguard flag exact-copy body prose that appears in at least three in-scope documents and is at least 80 normalized characters long.

```toml
[tool.docguard]
require_duplicate_guidance_detection = true
duplicate_guidance_kinds = ["code_block", "list_item", "paragraph"]
```

Review duplicate guidance with `docguard --verbose` when downgraded during migration. Full kind matrix, thresholds, exclusions, and examples: [docs/structure-rules.md#detect-duplicate-guidance-dg-split002](structure-rules.md#detect-duplicate-guidance-dg-split002).

## Define typed documents

Use `document_types` in `pyproject.toml` to attach rules to glob patterns. ADRs are the primary example:

- required headings such as `Status`, `Context`, `Decision`, and `Consequences`
- required YAML front matter keys such as `status` and `date`
- per-type line limits that override global defaults

A document may match at most one `document_types` entry. Overlapping globs are rejected as a configuration error.

## Require index reachability

When `require_index_reachability = true`, docguard builds a document link graph and flags documents that cannot be reached from any configured `index_files` entry inside the scanned scope.

This catches documentation that exists in the repository but is likely to be missed during review because nothing links to it.

## Detailed rule guides

| Topic | Document |
|-------|----------|
| Phase 2 organization link rules | [docs/organization-rules.md](organization-rules.md) |
| Phase 3 structure rules | [docs/structure-rules.md](structure-rules.md) |
| Prose style rules | [docs/prose-style-rules.md](prose-style-rules.md) |
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

Severity can be tightened directly or relaxed with a reason:

```toml
[[tool.docguard.relaxations]]
parameter = "severity.DG-SIZE001"
value = "warning"
reason = "Legacy documents need a temporary migration window while pages are split."
```

Supported values are `error`, `warning`, and `experimental`. Only `error` fails a run.

## Add docguard to CI

Example GitHub Actions step after installing from PyPI:

```yaml
- uses: astral-sh/setup-uv@v5
- run: uv pip install docguard-structure
- run: uv run docguard --format json
```

For Git-based CI install, use the steps in [Install from Git](#install-from-git) instead of `uv pip install docguard-structure`.

Use exit code `1` for diagnostic failures and `2` for configuration failures. See [Use predictable CI exit codes](#use-predictable-ci-exit-codes).

## Unicode and UTF-8 support

Docguard reads Markdown as UTF-8 with optional BOM. Japanese headings, paths, and configuration values are supported; non-UTF-8 files fail during discovery with exit code `2`. Non-ASCII split suggestions fall back to `section-{line_number}` when a Latin slug cannot be generated. See [ADR 0004](adr/0004-utf-8-markdown-encoding.md); coverage lives in `tests/test_unicode_support.py`.

## Phase 1.5 UX and reliability

Reliability details: output flag combinations live in [Output modes](#output-modes), exit code meanings live in [Use predictable CI exit codes](#use-predictable-ci-exit-codes), `--docguard-only` runs only docguard pytest items, JSON includes `checked_document_count`, and `--verbose` takes precedence over `--summary`.

## Configuration

Run `docguard init` to print a strict-baseline starter snippet, then keep only project-specific scope and document type entries in `pyproject.toml`:

```toml
[tool.docguard]
paths = ["README.md", "CONTEXT.md", "docs"]
ignore_globs = ["docs/archive/**", "docs/generated/**"]
index_files = ["README.md"]

[[tool.docguard.document_types]]
name = "adr"
glob = "docs/adr/*.md"
required_headings = ["Status", "Context", "Decision", "Consequences"]
required_front_matter_keys = ["status", "date"]
max_document_lines = 160
max_section_lines = 60
```

Strict baseline defaults:

- `max_document_lines = 300`, `max_section_lines = 120`, `min_document_lines = 20`
- `require_index_reachability = true`, `require_duplicate_guidance_detection = true`
- `DG-SPLIT002`, `DG-STYLE001`, `DG-STYLE002`, `DG-STYLE003`, and `DG-SIZE003` are `error`
- Phase 2 orphan/hub checks and Phase 3 mixed-role/heading checks remain opt-in

Relaxations must be explicit and reasoned:

```toml
[[tool.docguard.relaxations]]
parameter = "max_document_lines"
value = 400
reason = "Legacy docs need a temporary migration window while pages are split."
```

Behavior notes:

- CLI paths override configured `paths`; include the configured index file when reachability is enabled
- ignored files are excluded from diagnostics and reachability graphs
- direct config values may keep or tighten the strict baseline; looser values require `[[tool.docguard.relaxations]]`
- missing or out-of-project CLI paths fail with exit code `2` — see [Use predictable CI exit codes](#use-predictable-ci-exit-codes)
- explicit CLI paths must point to Markdown files or directories containing Markdown
- configured paths that do not exist yet are skipped silently
- when `require_index_reachability = true`, at least one configured `index_files` entry must be inside the scanned scope
- orphan detection runs only when `require_orphan_detection = true`; index files in scope are excluded
- hub outgoing-link checks run only when `require_hub_outgoing_links = true`; hub documents are `index_files` plus optional `hub_globs`
- when `require_hub_outgoing_links = true` but no hub documents are in scope, docguard reports no diagnostics
- mixed-role detection runs only when `require_mixed_role_detection = true`; typed documents are excluded
- heading order checks run only when `require_heading_order_check = true`
- duplicate guidance detection is on by default; `duplicate_guidance_kinds` defaults to `code_block` and `list_item`. Add `heading` or `paragraph` to opt in.
- `allowed_duplicate_patterns`, `allowed_prose_phrases`, and `allowed_documentation_style_phrases` are relaxations because they suppress diagnostics
- prose and documentation style checks always run; typed documents are excluded from `DG-STYLE001`/`DG-STYLE002` and included in `DG-STYLE003`
- `extra_prohibited_prose_patterns` and `extra_prohibited_documentation_style_patterns` add case-insensitive regular expressions
- `experimental_rules_enabled = true` is reserved for future opt-in rules and currently has no effect

When documentation exceeds the configured budget, split files instead of raising `max_document_lines`. See [docs/dogfood.md](dogfood.md) and [docs/adr/0006-document-budget-dogfood-gate.md](adr/0006-document-budget-dogfood-gate.md).
