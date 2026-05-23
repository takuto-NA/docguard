# Dogfood and readiness

This repository uses docguard on its own documentation. This page records dogfood impact tables, self-test commands, and readiness checklists.

## What you can rely on in this repository

Two audiences, one dogfood setup:

| Audience | What is available now |
|----------|----------------------|
| **Tool users** | Nine structure diagnostics across core, Phase 2 (links between files), and Phase 3 (structure inside each file). Same CLI, JSON, and pytest entry points as any project. |
| **Maintainers of this documentation** | A fixed document budget, split pages by role, and automated gates that block config workarounds for size. |

### Tool capabilities

See [docs/usage.md](usage.md#what-you-can-do-today) for the phased capability table, configuration, and exit codes.

### Document budget and split documentation

During Phase 3 work, `docs/usage.md` outgrew the original 400-line dogfood budget. Tests were kept green by raising `max_document_lines` to 530. That defeated the rule docguard is meant to demonstrate: when documentation grows, **split it** instead of inflating configured limits.

The document budget gate restored the intended behavior:

| Before | After |
|--------|-------|
| One large `docs/usage.md` | `usage.md` is a concise entry point; Phase 2, Phase 3, and dogfood details live in focused pages |
| `max_document_lines = 530` | Global budget is **400 lines** again (ADRs: **160**) |
| Size pressure could be bypassed by editing config | `tests/test_document_budget.py` fails on config inflation or oversized in-scope files |

Correct response when docs grow: add or extend focused pages such as [docs/organization-rules.md](organization-rules.md), [docs/structure-rules.md](structure-rules.md), or this page — not a higher `max_document_lines`.

Phase 2 and Phase 3 opt-in rules can be enabled against the current documentation scope without mass failures; see the impact tables below.

**One-line summary:** docguard checks repository Markdown structure in three phases; this repository dogfoods those rules and enforces a fixed document budget in tests.

## Dogfood impact for Phase 2 rules

If Phase 2 rules were enabled in this repository today:

| Document | Incoming | Outgoing | Orphan candidate | Hub outgoing violation |
|----------|----------|----------|------------------|------------------------|
| `README.md` | none | 11 links | no (index excluded) | no |
| `CONTEXT.md` | `README.md`, `docs/organization-rules.md`, `docs/structure-rules.md` | `docs/adr/0004-utf-8-markdown-encoding.md`, `docs/adr/0006-document-budget-dogfood-gate.md` | no | no (leaf) |
| `docs/usage.md` | `README.md`, `docs/dogfood.md`, `docs/organization-rules.md`, `docs/structure-rules.md` | `docs/organization-rules.md`, `docs/structure-rules.md`, `docs/dogfood.md`, `docs/adr/0004-utf-8-markdown-encoding.md`, `docs/adr/0006-document-budget-dogfood-gate.md` | no | no (leaf) |
| `docs/organization-rules.md` | `README.md`, `docs/usage.md`, `docs/dogfood.md` | `CONTEXT.md`, `docs/adr/0003-organization-link-rules.md`, `docs/dogfood.md`, `docs/usage.md` | no | no (leaf) |
| `docs/structure-rules.md` | `README.md`, `docs/usage.md`, `docs/dogfood.md` | `CONTEXT.md`, `docs/adr/0005-phase3-structure-diagnostics.md`, `docs/dogfood.md`, `docs/usage.md` | no | no (leaf) |
| `docs/dogfood.md` | `README.md`, `docs/organization-rules.md`, `docs/structure-rules.md`, `docs/usage.md` | `docs/organization-rules.md`, `docs/structure-rules.md`, `docs/adr/0006-document-budget-dogfood-gate.md`, `docs/usage.md` | no | no (leaf) |
| `docs/adr/0001-cli-first-docguard.md` | `README.md` | none | no | no (leaf) |
| `docs/adr/0002-structured-diagnostics-and-strict-config.md` | `README.md`, `docs/adr/0004-utf-8-markdown-encoding.md` | none | no | no (leaf) |
| `docs/adr/0003-organization-link-rules.md` | `README.md`, `docs/organization-rules.md` | none | no | no (leaf) |
| `docs/adr/0004-utf-8-markdown-encoding.md` | `README.md`, `CONTEXT.md`, `docs/usage.md` | `docs/adr/0002-structured-diagnostics-and-strict-config.md` | no | no (leaf) |
| `docs/adr/0005-phase3-structure-diagnostics.md` | `README.md`, `docs/structure-rules.md` | none | no | no (leaf) |
| `docs/adr/0006-document-budget-dogfood-gate.md` | `README.md`, `CONTEXT.md`, `docs/dogfood.md`, `docs/usage.md` | none | no | no (leaf) |

Expected candidate counts: **0 orphan**, **0 hub outgoing violations**.

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
| `docs/adr/*.md` | no (typed; excluded from SPLIT001) | no |

Expected candidate counts: **0 mixed role**, **0 heading skip**.

Automated gate: `tests/test_phase3_readiness.py`.

## Document budget gate

This repository keeps a **400-line global document budget** for in-scope non-ADR Markdown. ADRs remain under the existing 160-line typed budget. When documentation grows, split files instead of raising `max_document_lines`.

Automated gate: `tests/test_document_budget.py`.

Full specification: [docs/adr/0006-document-budget-dogfood-gate.md](adr/0006-document-budget-dogfood-gate.md).

## Self-test in this repository

Configured scope in `pyproject.toml`:

- `README.md`
- `CONTEXT.md`
- everything under `docs/`

Configured checks:

- all scoped documents must be reachable from `README.md`
- global line limit is 400 lines (`max_document_lines` in `pyproject.toml`)
- ADRs must include `Status`, `Context`, `Decision`, and `Consequences`
- ADRs must include YAML front matter keys `status` and `date`

Run the self-check manually:

```bash
docguard README.md CONTEXT.md docs/ --summary
docguard README.md CONTEXT.md docs/ --quiet
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

See also: [docs/usage.md](usage.md).
