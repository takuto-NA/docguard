---
status: accepted
date: 2026-05-24
---

# Phase 3 structure diagnostics

## Status

Accepted.

## Context

Phase 1 and 2 cover document size, typed headings, front matter, and link organization. Teams still hit two structural gaps before SIZE001 fires:

- untyped documents that mix overview, reference, and operations content in one file
- heading hierarchies that skip levels (for example H2 then H4), which hurts navigation

Phase 3 adds two opt-in diagnostics without changing existing FORMAT001 required-heading checks or organization rules.

## Decision

Phase 3 adds two opt-in structure rules:

| Code | Name | Definition |
|------|------|------------|
| `DG-SPLIT001` | mixed document roles | An untyped document whose level-2 headings match two or more built-in role families |
| `DG-FORMAT002` | unexpected heading order | A heading more than one level deeper than the previous heading |

Rules and semantics:

1. **SPLIT001 vs FORMAT001.** FORMAT001 checks that typed documents include required headings. SPLIT001 signals that an untyped document may serve multiple purposes and should be split.
2. **Typed documents are excluded from SPLIT001.** Documents matching `document_types` are not checked for mixed roles, avoiding false positives on ADRs with Status, Context, Decision, and Consequences sections.
3. **SPLIT001 uses level-2 headings only.** H1 is the document title; deeper headings are subtopics.
4. **Four built-in role families.** `narrative`, `decision`, `reference`, and `operations`, matched by English and representative Japanese keywords in heading text. First matching family wins per heading.
5. **FORMAT002 is level-skip only.** Required-heading order for document types remains out of scope.
6. **Both rules are opt-in.** Configuration keys are `require_mixed_role_detection` and `require_heading_order_check`, both defaulting to `false`.
7. **Initial severity is warning.** Both diagnostics default to `warning` so teams can adopt Phase 3 without immediately failing CI.
8. **`experimental_rules_enabled` is unchanged.** Phase 3 uses dedicated flags, not the reserved experimental master switch.

Configuration shape:

```toml
[tool.docguard]
require_mixed_role_detection = false
require_heading_order_check = false

[tool.docguard.severity]
DG-SPLIT001 = "warning"
DG-FORMAT002 = "warning"
```

## Consequences

- Pure classification logic lives in `role_families.py` and `heading_order.py`; rule functions wire diagnostics in `rules/__init__.py`.
- Dogfood impact is measured with a probe before fixing readiness snapshot expectations.
- Documentation and tests preserve the distinction between mixed roles, missing required headings, and heading level skips in `CONTEXT.md`.
