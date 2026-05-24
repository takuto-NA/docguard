---
status: accepted
date: 2026-05-24
---

# Duplicate guidance kind scope

## Status

Accepted.

## Context

ADR 0009 introduced `DG-SPLIT002` for repeated fenced code blocks, headings, and list items across the scan scope. In practice, heading duplicates conflict with template-based documentation structure. Teams that standardize headings such as `Purpose` or `Document responsibility` across many files were forced to rename headings just to stay green when `DG-SPLIT002` was enabled as `error`.

The original rule treated structural template headings and repeated maintenance guidance the same way. That pushed teams toward heading variation instead of format consistency.

## Decision

1. **Add `duplicate_guidance_kinds` to `[tool.docguard]`.**
2. **Default duplicate guidance detection to `code_block` and `list_item` only.**
3. **Make heading duplicate detection opt-in by adding `heading` to `duplicate_guidance_kinds`.**
4. **Keep `allowed_duplicate_patterns` as a string-level escape hatch for enabled kinds.**
5. **Use heading-specific diagnostic suggestions that recommend kind configuration or allowlisting instead of renaming template headings.**

Alternatives rejected:

- repository-only guidance without a product configuration change
- `template_headings` as the primary configuration path
- keeping heading detection on by default and relying on growing allowlists

## Consequences

- Adopters can unify template headings without disabling duplicate guidance entirely.
- Teams that still want heading duplicate detection can opt in explicitly.
- ADR 0009 remains valid for the diagnostic itself; this ADR narrows the default scope.
- Alpha adopters who relied on default heading detection must add `heading` to `duplicate_guidance_kinds` or remove those diagnostics from CI gates.

See also: [docs/adr/0009-duplicate-guidance-diagnostic.md](0009-duplicate-guidance-diagnostic.md), [docs/structure-rules.md](../structure-rules.md).
