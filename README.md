# docguard

CLI-first Markdown structure checker for repositories.

Docguard helps teams keep documentation from growing too large, becoming unreachable from index files, or drifting away from expected document types such as ADRs.

## Quick start

Install from PyPI as `docguard-structure` (CLI command remains `docguard`; this is not the unrelated [docguard-cli](https://pypi.org/project/docguard-cli/) package). Use `uv add docguard-structure`, then run `uv run docguard --summary`. Existing uv users can upgrade with `uv add --upgrade docguard-structure`; see [Update an existing uv install](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md#update-an-existing-uv-install). Equivalent with pip: `pip install docguard-structure`. Git-based install: [usage guide — Install from Git](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md#install-from-git).

Run `docguard init` for a starter `[tool.docguard]` snippet, or use the strict baseline without configuration. Full install commands, configuration, pytest integration, and exit codes: [usage guide](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md). To adopt docguard in another repository, see [Use in another repository](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md#use-in-another-repository).

```bash
docguard --summary
```

## What this tool checks

Docguard focuses on document structure and repository health. Prose style checks (`DG-STYLE001`, `DG-STYLE002`) flag decorative strong emphasis and conversational phrasing in body text; they are not a general Markdown formatter.

With no configuration, docguard applies the strict baseline: scan `README.md`, `CONTEXT.md`, and `docs`; require reachability from `README.md`; enforce 300-line documents, 120-line sections, and a 20-line floor for untyped non-index documents; and fail duplicate guidance plus prose style diagnostics as errors. Any relaxation from that baseline must be recorded in `[[tool.docguard.relaxations]]` with a reason.

| Phase | What you can check | Diagnostics | Typical default |
|-------|-------------------|-------------|-----------------|
| Core | Document and section size; stub detection; typed document shape; index reachability; prose style | `DG-SIZE001`, `DG-SIZE002`, `DG-SIZE003`, `DG-FORMAT001`, `DG-FORMAT003`, `DG-ORG003`, `DG-STYLE001`, `DG-STYLE002` | strict baseline, `error` |
| Phase 2 | Link structure between files: orphans and hub dead ends | `DG-ORG001`, `DG-ORG002` | opt-in, `warning` |
| Phase 3 | Structure inside each file: mixed roles and heading level skips | `DG-SPLIT001`, `DG-FORMAT002` | opt-in, `warning` |
| Duplicate guidance | Repeated commands, list guidance, or prose paragraphs across the scan scope; headings and paragraphs opt-in | `DG-SPLIT002` | strict baseline, `error` |

Phase 2 details: [organization rules](https://github.com/takuto-NA/docguard/blob/main/docs/organization-rules.md). Phase 3 and duplicate guidance details: [structure rules](https://github.com/takuto-NA/docguard/blob/main/docs/structure-rules.md). Prose style details: [prose style rules](https://github.com/takuto-NA/docguard/blob/main/docs/prose-style-rules.md). To adopt docguard in another repository, see [Use in another repository](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md#use-in-another-repository).

## Development

Requires Python 3.11+ and uv on PATH:

```bash
uv pip install -e ".[dev]"
uv run pytest
uv run docguard README.md CONTEXT.md docs/ --summary
```

## Documentation

- [Usage](https://github.com/takuto-NA/docguard/blob/main/docs/usage.md)
- [Organization rules (Phase 2)](https://github.com/takuto-NA/docguard/blob/main/docs/organization-rules.md)
- [Structure rules (Phase 3)](https://github.com/takuto-NA/docguard/blob/main/docs/structure-rules.md)
- [Prose style rules](https://github.com/takuto-NA/docguard/blob/main/docs/prose-style-rules.md)
- [Dogfood and self-test](https://github.com/takuto-NA/docguard/blob/main/docs/dogfood.md)
- [Release readiness](https://github.com/takuto-NA/docguard/blob/main/docs/release-readiness.md)
- [Domain glossary (CONTEXT.md)](https://github.com/takuto-NA/docguard/blob/main/CONTEXT.md)
- [Architecture decision records](https://github.com/takuto-NA/docguard/tree/main/docs/adr)

## Status

Alpha (`Development Status :: 3 - Alpha`). Configuration keys, diagnostic JSON fields, and rule defaults may change; breaking changes are recorded in [CHANGELOG.md](https://github.com/takuto-NA/docguard/blob/main/CHANGELOG.md). Exit codes and existing diagnostic meanings are preserved where practical.

Docguard 0.3.0 uses a strict baseline by default. Relaxations require `[[tool.docguard.relaxations]]` entries with reasons. Release readiness is documented in [docs/release-readiness.md](https://github.com/takuto-NA/docguard/blob/main/docs/release-readiness.md).

## Repository navigation

Relative links for clone checkouts and docguard reachability checks:

- [docs/usage.md](docs/usage.md)
- [docs/organization-rules.md](docs/organization-rules.md)
- [docs/structure-rules.md](docs/structure-rules.md)
- [docs/prose-style-rules.md](docs/prose-style-rules.md)
- [docs/dogfood.md](docs/dogfood.md)
- [docs/release-readiness.md](docs/release-readiness.md)
- [CONTEXT.md](CONTEXT.md)
- [docs/adr/0001-cli-first-docguard.md](docs/adr/0001-cli-first-docguard.md)
- [docs/adr/0002-structured-diagnostics-and-strict-config.md](docs/adr/0002-structured-diagnostics-and-strict-config.md)
- [docs/adr/0003-organization-link-rules.md](docs/adr/0003-organization-link-rules.md)
- [docs/adr/0004-utf-8-markdown-encoding.md](docs/adr/0004-utf-8-markdown-encoding.md)
- [docs/adr/0005-phase3-structure-diagnostics.md](docs/adr/0005-phase3-structure-diagnostics.md)
- [docs/adr/0006-document-budget-dogfood-gate.md](docs/adr/0006-document-budget-dogfood-gate.md)
- [docs/adr/0007-document-responsibility-drift-guard.md](docs/adr/0007-document-responsibility-drift-guard.md)
- [docs/adr/0008-pypi-alpha-distribution.md](docs/adr/0008-pypi-alpha-distribution.md)
- [docs/adr/0009-duplicate-guidance-diagnostic.md](docs/adr/0009-duplicate-guidance-diagnostic.md)
- [docs/adr/0010-duplicate-guidance-kind-scope.md](docs/adr/0010-duplicate-guidance-kind-scope.md)
- [docs/adr/0011-duplicate-prose-paragraph-guidance.md](docs/adr/0011-duplicate-prose-paragraph-guidance.md)
- [docs/adr/0012-prose-style-diagnostics.md](docs/adr/0012-prose-style-diagnostics.md)
- [docs/adr/0013-pypi-distribution-name-docguard-structure.md](docs/adr/0013-pypi-distribution-name-docguard-structure.md)
- [docs/adr/0014-strict-baseline-and-policy-relaxations.md](docs/adr/0014-strict-baseline-and-policy-relaxations.md)
