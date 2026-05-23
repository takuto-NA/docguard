---
status: accepted
date: 2026-05-24
---

# Document budget dogfood gate

## Status

Accepted.

## Context

During Phase 3 documentation work, `docs/usage.md` grew beyond the repository's original 400-line dogfood budget. To keep self-tests green, `max_document_lines` in `pyproject.toml` was raised to 530. That bypasses the very rule docguard is meant to enforce: when documentation grows too large, split it instead of inflating configured limits.

An agent or maintainer can repeat this workaround whenever documentation pressure appears, defeating dogfood as a guardrail.

## Decision

1. **Restore the global documentation budget to 400 lines** in this repository's `[tool.docguard]` configuration.
2. **Split oversized documentation by role** instead of raising limits. Phase-specific and dogfood material moves out of `docs/usage.md` into focused pages.
3. **Add `tests/test_document_budget.py`** as a dogfood gate that fails when:
   - repository `max_document_lines` exceeds 400
   - any in-scope document exceeds its configured budget (400 for normal docs, 160 for ADRs)
4. **No per-file exceptions** for normal Markdown documents. ADRs keep their existing typed budget through `document_types`.
5. **Do not rely on documentation-only warnings** for this invariant. The gate is automated in tests.

Alternatives rejected:

- per-file budget tables for normal docs
- silently increasing `max_document_lines` when usage grows
- trusting `tests/test_dogfood.py` alone, which only checks diagnostic output under the current inflated configuration

## Consequences

- `docs/usage.md` becomes a concise entry point with links to detailed pages.
- New documentation pages must remain reachable from `README.md`.
- Future documentation growth must split files or restructure content; raising the global budget requires changing both ADR policy and the budget gate test.
- Phase 2 and Phase 3 readiness snapshots may change when navigation links move.
