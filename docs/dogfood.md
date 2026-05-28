# Dogfood and readiness

This repository uses docguard on its own documentation. This page records dogfood impact tables, self-test commands, and readiness checklists.

## What you can rely on in this repository

Two audiences, one dogfood setup:

| Audience | What is available now |
|----------|----------------------|
| **Tool users** | Twelve diagnostics across core (including prose style), Phase 2 (links between files), Phase 3 (structure inside each file), and duplicate guidance. Same CLI, JSON, and pytest entry points as any project. |
| **Maintainers of this documentation** | A fixed document budget, split pages by role, document responsibility boundaries, and automated gates that block config workarounds for size or document responsibility drift. |

### Tool capabilities

See [docs/usage.md](usage.md#what-you-can-do-today) for the phased capability table, configuration, and exit codes.

### Document budget and split documentation

During Phase 3 work, `docs/usage.md` outgrew the original 400-line dogfood budget. Tests were kept green by raising `max_document_lines` to 530. That defeated the rule docguard is meant to demonstrate: when documentation grows, split it instead of inflating configured limits.

The document budget gate restored the intended behavior:

| Before | After |
|--------|-------|
| One large `docs/usage.md` | `usage.md` is a concise entry point; Phase 2, Phase 3, and dogfood details live in focused pages |
| `max_document_lines = 530` | Strict baseline budget is 300 lines (ADRs: 160) |
| Size pressure could be bypassed by editing config | `tests/test_document_budget.py` fails on config inflation or oversized in-scope files |

Correct response when docs grow: add or extend focused pages such as [docs/organization-rules.md](organization-rules.md), [docs/structure-rules.md](structure-rules.md), or this page — not a higher `max_document_lines`.

### Document responsibility boundaries

When `README.md` repeated diagnostic catalogs, Phase 2/3 detail tables, and configuration prose, first-time readers could not tell which page was canonical. When release planning landed in this page instead of a dedicated release page, dogfood absorbed material outside its declared responsibility. The document responsibility gate keeps each page in its lane and blocks responsibility drift in tests.

| Document | Responsibility |
|----------|----------------|
| `README.md` | Entry point: Quick start, one phase summary table, links to canonical pages |
| `docs/usage.md` | Diagnostic catalog, output modes, configuration, CI exit codes, pytest |
| `docs/organization-rules.md` | Phase 2 link-structure rules, examples, configuration |
| `docs/structure-rules.md` | Phase 3 in-document structure rules, role families, configuration |
| `docs/prose-style-rules.md` | Prose style diagnostics, thresholds, exclusions, configuration |
| `docs/dogfood.md` | This repository's dogfood gates, impact tables, readiness checklists |
| `docs/release-readiness.md` | Release and distribution milestones for Alpha, PyPI, and stable readiness |

### What the document responsibility gate gives you

This work did not add new docguard diagnostics. It added documentation structure and automated guards so maintainers can tell which page is canonical and CI can block responsibility drift.

| Before | After |
|--------|-------|
| `README.md` repeated diagnostic catalogs, Phase 2/3 detail, and configuration prose | `README.md` is an entry point: Quick start, one phase summary table, links to canonical pages |
| Release planning lived in `docs/dogfood.md` under a distribution heading | [docs/release-readiness.md](release-readiness.md) owns Alpha, PyPI, and stable milestones |
| Only README detail creep was tested | `tests/test_document_responsibilities.py` also fails when dogfood absorbs release planning |
| No shared term for the failure mode | [CONTEXT.md](../CONTEXT.md) defines Document responsibility and Document responsibility drift; [ADR 0007](adr/0007-document-responsibility-drift-guard.md) records the incident and rejected fixes |

What `tests/test_document_responsibilities.py` blocks today:

| Document | Drift class blocked |
|----------|---------------------|
| `README.md` | third-level detail headings under `## What this tool checks`; full diagnostic catalog tables; Phase 2/3 rule or configuration prose copied from canonical pages; `## Roadmap` instead of `## Status` or `## Current scope` |
| `docs/dogfood.md` | distribution-milestone headings; release markers such as PyPI milestone checklists, wheel smoke tests, CI requirements, or prose style rule specifications copied from [docs/prose-style-rules.md](prose-style-rules.md) |
| `docs/release-readiness.md` | must own the distribution roadmap section so release planning has a single canonical page |

Heading renames alone do not bypass these gates. If release content stays in dogfood, tests still fail.

Correct responses when documentation needs more detail:

- README needs diagnostic or configuration detail → link to [docs/usage.md](usage.md) or the phase rule page
- dogfood needs distribution milestones → link to [docs/release-readiness.md](release-readiness.md)
- release-readiness needs self-test commands → link to [Self-test in this repository](#self-test-in-this-repository) on this page

Prose style diagnostics run on every scan. The PyPI README gate reuses the same core through `tests/test_release_readiness.py`. Rule details live in [docs/prose-style-rules.md](prose-style-rules.md).

README must stay a summary. Under `## What this tool checks` it may keep one phase summary table aligned with [docs/usage.md](usage.md#what-you-can-do-today). It must not add:

- third-level detail headings such as `### ...`
- full diagnostic catalog tables such as `| Code | Check |` or `| Code | Check | Default |`
- Phase 2/3 rule explanations or configuration prose that belong in canonical pages
- a `## Roadmap` heading for current-scope status text; use `## Status` or `## Current scope` instead

Correct response when README needs more detail: link to the canonical page — do not copy tables or rule explanations back into README.

Automated gate: `tests/test_document_responsibilities.py`.

Phase 2 and Phase 3 opt-in rules can be enabled against the current documentation scope without mass failures; see the impact tables below.

One-line summary: docguard checks repository Markdown structure in three phases; this repository dogfoods those rules, enforces a fixed document budget, and blocks document responsibility drift in tests.

## Dogfood impact for Phase 2 rules

If Phase 2 rules were enabled in this repository today. Authoritative link counts live in `tests/test_phase2_readiness.py`; update that test when adding documents or links.

| Document | Incoming | Outgoing | Orphan candidate | Hub outgoing violation |
|----------|----------|----------|------------------|------------------------|
| `README.md` | none | 17 links | no (index excluded) | no |
| `CONTEXT.md` | `README.md`, `docs/dogfood.md`, `docs/organization-rules.md`, `docs/structure-rules.md` | `docs/adr/0004-utf-8-markdown-encoding.md`, `docs/adr/0006-document-budget-dogfood-gate.md`, `docs/adr/0007-document-responsibility-drift-guard.md`, `docs/adr/0009-duplicate-guidance-diagnostic.md`, `docs/adr/0010-duplicate-guidance-kind-scope.md`, `docs/adr/0011-duplicate-prose-paragraph-guidance.md` | no | no (leaf) |
| `docs/usage.md` | `README.md`, `docs/dogfood.md`, `docs/organization-rules.md`, `docs/release-readiness.md`, `docs/structure-rules.md` | `docs/organization-rules.md`, `docs/structure-rules.md`, `docs/dogfood.md`, `docs/adr/0004-utf-8-markdown-encoding.md`, `docs/adr/0006-document-budget-dogfood-gate.md` | no | no (leaf) |
| `docs/organization-rules.md` | `README.md`, `docs/usage.md`, `docs/dogfood.md` | `CONTEXT.md`, `docs/adr/0003-organization-link-rules.md`, `docs/dogfood.md`, `docs/usage.md` | no | no (leaf) |
| `docs/structure-rules.md` | `README.md`, `docs/adr/0010-duplicate-guidance-kind-scope.md`, `docs/adr/0011-duplicate-prose-paragraph-guidance.md`, `docs/dogfood.md`, `docs/usage.md` | `CONTEXT.md`, `docs/adr/0005-phase3-structure-diagnostics.md`, `docs/adr/0009-duplicate-guidance-diagnostic.md`, `docs/adr/0010-duplicate-guidance-kind-scope.md`, `docs/adr/0011-duplicate-prose-paragraph-guidance.md`, `docs/dogfood.md`, `docs/usage.md` | no | no (leaf) |
| `docs/dogfood.md` | `README.md`, `docs/adr/0007-document-responsibility-drift-guard.md`, `docs/organization-rules.md`, `docs/release-readiness.md`, `docs/structure-rules.md`, `docs/usage.md` | `CONTEXT.md`, `docs/organization-rules.md`, `docs/structure-rules.md`, `docs/adr/0006-document-budget-dogfood-gate.md`, `docs/adr/0007-document-responsibility-drift-guard.md`, `docs/adr/0011-duplicate-prose-paragraph-guidance.md`, `docs/release-readiness.md`, `docs/usage.md` | no | no (leaf) |
| `docs/release-readiness.md` | `README.md`, `docs/dogfood.md` | `docs/adr/0007-document-responsibility-drift-guard.md`, `docs/dogfood.md`, `docs/usage.md` | no | no (leaf) |
| `docs/adr/0001-cli-first-docguard.md` | `README.md` | none | no | no (leaf) |
| `docs/adr/0002-structured-diagnostics-and-strict-config.md` | `README.md`, `docs/adr/0004-utf-8-markdown-encoding.md` | none | no | no (leaf) |
| `docs/adr/0003-organization-link-rules.md` | `README.md`, `docs/organization-rules.md` | none | no | no (leaf) |
| `docs/adr/0004-utf-8-markdown-encoding.md` | `README.md`, `CONTEXT.md`, `docs/usage.md` | `docs/adr/0002-structured-diagnostics-and-strict-config.md` | no | no (leaf) |
| `docs/adr/0005-phase3-structure-diagnostics.md` | `README.md`, `docs/structure-rules.md` | none | no | no (leaf) |
| `docs/adr/0006-document-budget-dogfood-gate.md` | `README.md`, `CONTEXT.md`, `docs/dogfood.md`, `docs/usage.md` | none | no | no (leaf) |
| `docs/adr/0007-document-responsibility-drift-guard.md` | `README.md`, `CONTEXT.md`, `docs/dogfood.md`, `docs/release-readiness.md` | `docs/dogfood.md` | no | no (leaf) |
| `docs/adr/0011-duplicate-prose-paragraph-guidance.md` | `README.md`, `CONTEXT.md`, `docs/adr/0009-duplicate-guidance-diagnostic.md`, `docs/dogfood.md`, `docs/structure-rules.md` | `docs/adr/0009-duplicate-guidance-diagnostic.md`, `docs/adr/0010-duplicate-guidance-kind-scope.md`, `docs/structure-rules.md` | no | no (leaf) |

Expected candidate counts: 0 orphan, 0 hub outgoing violations.

Automated gate: `tests/test_phase2_readiness.py`.

## Dogfood impact for Phase 3 rules

If Phase 3 rules were enabled in this repository today:

| Document | Mixed role candidate (`DG-SPLIT001`) | Heading skip (`DG-FORMAT002`) |
|----------|--------------------------------------|-------------------------------|
| `README.md` | no (untyped; single-family H2 matches) | no |
| `CONTEXT.md` | no | no |
| `docs/usage.md` | no | no |
| `docs/organization-rules.md` | no | no |
| `docs/structure-rules.md` | no | no |
| `docs/dogfood.md` | no | no |
| `docs/release-readiness.md` | no | no |
| `docs/adr/*.md` | no (typed; excluded from SPLIT001) | no |

Expected candidate counts: 0 mixed role, 0 heading skip.

Automated gate: `tests/test_phase3_readiness.py`.

## Dogfood impact for duplicate guidance

With duplicate guidance detection enabled in this repository:

| Document | Duplicate guidance candidate (`DG-SPLIT002`) |
|----------|----------------------------------------------|
| `README.md` | no |
| `CONTEXT.md` | no |
| `docs/usage.md` | no |
| `docs/organization-rules.md` | no |
| `docs/structure-rules.md` | no |
| `docs/dogfood.md` | no |
| `docs/release-readiness.md` | no |
| `docs/adr/*.md` | no |

Expected candidate count: 0 duplicate guidance groups with default kinds `code_block` and `list_item`. Prose paragraph detection is opt-in through `duplicate_guidance_kinds = ["paragraph"]`; see [docs/adr/0011-duplicate-prose-paragraph-guidance.md](adr/0011-duplicate-prose-paragraph-guidance.md).

Automated gate: `tests/test_duplicate_guidance_readiness.py`.

## Dogfood impact for prose style

With prose style diagnostics enabled as `error` in this repository:

| Document | Strong emphasis candidate (`DG-STYLE001`) | Prohibited pattern candidate (`DG-STYLE002`) |
|----------|-------------------------------------------|-----------------------------------------------|
| `README.md` | no | no |
| `CONTEXT.md` | no (glossary and example dialogue excluded) | no |
| `docs/usage.md` | no | no |
| `docs/organization-rules.md` | no | no |
| `docs/structure-rules.md` | no | no |
| `docs/dogfood.md` | no | no |
| `docs/release-readiness.md` | no | no |
| `docs/adr/*.md` | no (typed; excluded) | no |

Expected candidate counts: 0 strong emphasis violations, 0 prohibited pattern violations.

Automated gate: `tests/test_prose_style_readiness.py`.

## Dogfood impact for documentation style

With `DG-STYLE003` enabled as `error`, expected forbidden-expression candidate count is 0 across `README.md`, `CONTEXT.md`, and `docs/**`, including typed ADRs.

Automated gate: `tests/test_documentation_style_readiness.py`.

## Document budget gate

This repository keeps a 300-line global document budget for in-scope non-ADR Markdown. Untyped non-index documents must also stay at or above the 20-line document floor so refactor leftovers do not linger as stub pages. ADRs remain under the existing 160-line typed budget. When documentation grows, split files instead of raising `max_document_lines`.

Automated gate: `tests/test_document_budget.py`.

Full specification: [docs/adr/0006-document-budget-dogfood-gate.md](adr/0006-document-budget-dogfood-gate.md).

## Document responsibility gate

`README.md` must stay an entry-point summary. `docs/dogfood.md` must not absorb release planning or distribution milestones. See [What the document responsibility gate gives you](#what-the-document-responsibility-gate-gives-you) and [Document responsibility boundaries](#document-responsibility-boundaries) above for outcomes, the responsibility table, and README rules.

Run the gate manually:

```bash
python -m pytest tests/test_document_responsibilities.py
```

Automated gate: `tests/test_document_responsibilities.py`.

## Self-test in this repository

Configured scope in `pyproject.toml`:

- `README.md`
- `CONTEXT.md`
- everything under `docs/`

Configured checks:

- all scoped documents must be reachable from `README.md`
- global line limit is 300 lines from the strict baseline
- prose style diagnostics `DG-STYLE001` and `DG-STYLE002` run as strict-baseline `error`
- documentation style diagnostic `DG-STYLE003` runs as strict-baseline `error`
- untyped non-index documents must have at least 20 lines
- ADRs must include `Status`, `Context`, `Decision`, and `Consequences`
- ADRs must include YAML front matter keys `status` and `date`

Run the self-check manually:

```bash
uv run docguard README.md CONTEXT.md docs/ --summary
uv run docguard README.md CONTEXT.md docs/ --quiet
uv run docguard README.md CONTEXT.md docs/ --verbose
uv run docguard README.md CONTEXT.md docs/ --format json
uv run pytest tests/test_dogfood.py tests/test_prose_style_readiness.py tests/test_prose_style.py tests/test_documentation_style_readiness.py tests/test_documentation_style.py tests/test_release_readiness.py::test_readme_passes_prose_style_guard tests/test_release_readiness.py::test_readme_passes_documentation_style_guard
uv run pytest --docguard
uv run pytest --docguard-only
uv run pytest
```

Equivalent pip development install:

```bash
pip install -e ".[dev]"
python -m pytest
```

Automated self-check tests live in `tests/test_dogfood.py`.

Release and distribution readiness requirements live in [docs/release-readiness.md](release-readiness.md).

## Phase 2 Readiness Checklist

- [x] ADR 0003 accepted
- [x] `test_graph_phase2_contract.py` green
- [x] `test_phase2_readiness.py` green
- [x] `--verbose` shipped and tested
- [x] Dogfood impact table documented
- [x] Phase 2 Execute plan approved
- [x] Phase 2 diagnostics and configuration keys shipped

## Phase 3 Readiness Checklist

- [x] ADR 0005 accepted
- [x] `test_phase3_contract.py` green
- [x] `test_phase3_readiness.py` green
- [x] Dogfood impact table documented
- [x] Phase 3 Execute plan approved
- [x] Phase 3 diagnostics and configuration keys shipped

## Document budget Readiness Checklist

- [x] ADR 0006 accepted
- [x] `test_document_budget.py` green
- [x] `docs/usage.md` split instead of raising global line limit
- [x] Dogfood impact tables moved to this page

## Document responsibility Readiness Checklist

- [x] ADR 0007 accepted
- [x] `README.md` trimmed to entry-point summary plus one phase table
- [x] `test_document_responsibilities.py` green
- [x] Document responsibility boundaries documented on this page
- [x] Release planning moved to [docs/release-readiness.md](release-readiness.md)

## Prose style Readiness Checklist

- [x] ADR 0012 accepted
- [x] `test_prose_style.py` green
- [x] `test_prose_style_readiness.py` green
- [x] Prose style impact table documented on this page
- [x] PyPI README gate reuses docguard core prose style checks

## Documentation style Readiness Checklist

- [x] ADR 0015 accepted
- [x] `test_documentation_style.py` and `test_documentation_style_readiness.py` green
- [x] PyPI README gate reuses docguard core documentation style checks

See also: [docs/usage.md](usage.md), [docs/release-readiness.md](release-readiness.md).
