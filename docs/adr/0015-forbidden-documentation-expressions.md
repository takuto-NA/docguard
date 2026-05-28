---
status: accepted
date: 2026-05-28
---

# Forbidden documentation expressions

## Status

Accepted.

## Context

ADR 0012 added `DG-STYLE001` and `DG-STYLE002` for body prose only. Those checks intentionally skip headings, Markdown tables, and typed documents such as ADRs. The GhPyAnsys documentation cleanup work showed a separate class of problems: conversational Japanese headings, vague section titles, heading subtitles joined with ` — `, and informal table labels.

The raw cleanup ranking mixes high-confidence structural patterns with context-dependent Japanese phrases. Shipping all 27 items as universal hard errors would create false positives in general-purpose documentation.

## Decision

1. **Add product diagnostic `DG-STYLE003`.**
2. **Inspect headings, body prose, and Markdown table header cells.**
3. **Apply `DG-STYLE003` to typed documents such as ADRs.**
4. **Keep `DG-STYLE001` and `DG-STYLE002` unchanged and body-prose scoped.**
5. **Ship a ranked built-in manifest for the 27 source expressions plus general colloquial phrases with enforcement status:**
   - `active` and `scoped` entries are checked by default
   - `candidate` entries are documented only until a precise pattern is approved
6. **Use source-scoped matching.** Example: heading ` — ` subtitles are checked in headings only, not in body prose that legitimately uses em dashes.
7. **Treat rank as migration priority in diagnostics, not per-match severity.**
8. **Default and strict-baseline severity for `DG-STYLE003` is `error`.**
9. **Add configuration keys `allowed_documentation_style_phrases` and `extra_prohibited_documentation_style_patterns`.**

Alternatives rejected:

- extend `DG-STYLE002` with Japanese patterns, which would blur prose-only scope and typed-document exclusion
- enforce all 27 ranked expressions as built-in hard errors without classification
- tiered severity by rank, which would complicate the existing per-code severity model

## Consequences

- Repository documentation can enforce formal heading and table-label style without rewriting ADR decision lists under `DG-STYLE001`.
- External adopters may need `allowed_documentation_style_phrases` relaxations during migration.
- General colloquial phrases such as `ざっくり`, `とりあえず`, `ちょっと`, `いい感じ`, `便利`, `簡単`, and `おすすめ` are active built-ins because they are broad documentation voice issues and current dogfood docs have no matching usage.
- ChatGPT-style vague phrasing such as `筋が良い`, `結論から言うと`, `こうです。`, `本命`, `重い`, `非常に`, `核心`, and deictic words such as `ここ`, `この`, `それ`, `こう`, `その`, and `あの` are active built-ins for the same reason.
- Future expression additions should update the ranked manifest and its completeness test before changing enforcement status.
