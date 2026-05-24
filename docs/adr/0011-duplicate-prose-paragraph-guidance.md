---
status: accepted
date: 2026-05-24
---

# Duplicate prose paragraph guidance

## Status

Accepted.

## Context

During dogfood on an external project, docguard reported GREEN while the same decisions, numeric thresholds, and roadmap prose appeared across multiple Pico/runtime documents. Existing `DG-SPLIT002` duplicate guidance covered fenced code blocks and list items, but not repeated body paragraphs.

ADR 0009 rejected semantic prose similarity. Teams still need a deterministic way to catch copy-pasted narrative guidance that should live in one canonical document.

## Decision

1. **Extend `DG-SPLIT002` with an opt-in `paragraph` atom kind.**
2. **Detect repeated prose paragraphs using structural extraction and normalized exact text equality.**
3. **Keep `paragraph` out of default `duplicate_guidance_kinds`.** Default kinds remain `code_block` and `list_item`.
4. **Require at least three occurrences** across the scan scope before reporting a duplicate paragraph group.
5. **Ignore paragraphs shorter than 80 normalized characters** to reduce boilerplate noise.
6. **Exclude fenced code, headings, list items, Markdown table rows, and YAML front matter** from paragraph extraction.
7. **Reuse `allowed_duplicate_patterns`** for intentional repeated paragraph text.

Alternatives rejected:

- semantic prose similarity or embedding-based near-duplicate detection
- default-on paragraph detection for all adopters
- a new diagnostic code separate from `DG-SPLIT002`
- section-level hashing across entire `##` sections in this phase

## Consequences

- Adopters can opt in with `duplicate_guidance_kinds = ["paragraph"]` (alone or combined with other kinds).
- Exact-copy narrative redundancy is detectable without introducing nondeterministic similarity scoring.
- Paraphrased redundancy, table-only numeric duplication, and meaning-level overlap remain out of scope.
- Documentation refactors should consolidate repeated prose into one canonical owner and link elsewhere.

See also: [docs/adr/0009-duplicate-guidance-diagnostic.md](0009-duplicate-guidance-diagnostic.md), [docs/adr/0010-duplicate-guidance-kind-scope.md](0010-duplicate-guidance-kind-scope.md), [docs/structure-rules.md](../structure-rules.md).
