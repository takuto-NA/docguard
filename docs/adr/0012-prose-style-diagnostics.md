---
status: accepted
date: 2026-05-25
---

# Prose style diagnostics

## Status

Accepted.

## Context

LLM-assisted drafts often add Markdown strong emphasis and conversational phrasing to repository documentation. ADR 0008 recorded the PyPI README language guard as a release gate test only, not as a product diagnostic. Teams adopting docguard need the same checks in CLI, JSON, and pytest output.

Typed documents such as ADRs use bold numbered decision lists by convention. Prose style checks must not force ADR rewrites, consistent with Phase 3 mixed-role exclusion for typed documents.

## Decision

1. **Add product diagnostics `DG-STYLE001` and `DG-STYLE002`.**
2. **Run prose style checks on every scan** with default `warning` severity.
3. **`DG-STYLE001` counts closed strong emphasis pairs in prose lines** against `max_strong_emphasis_pairs` (default `0`).
4. **`DG-STYLE002` matches built-in prohibited pronoun and slang patterns** plus optional `extra_prohibited_prose_patterns`, with `allowed_prose_phrases` escape hatches.
5. **Exclude code fences, headings, YAML front matter, Markdown table rows, glossary term lines (`**Term**:`), and content under `## Example dialogue`.**
6. **Skip prose style checks for documents matching `document_types`.**
7. **Enable both diagnostics as `error` in this repository's dogfood configuration.**
8. **Replace the release gate emphasis and regex logic with the shared core** in `tests/test_release_readiness.py`.

Future prose-style rules (emoji density, list cadence, and similar) ship as separate `DG-STYLE*` codes.

Alternatives rejected:

- keep README-only release gate logic duplicated outside the product
- apply prose style checks to typed ADRs and rewrite decision lists
- opt-in flag for prose style (always-on warnings were chosen for discoverability)

## Consequences

- README and usage docs note that prose style complements structure checks; it is not a general Markdown formatter.
- ADR 0008 item 6 is superseded for emphasis and prohibited-pattern checks.
- External adopters may see warnings on first run when `max_strong_emphasis_pairs = 0`; severity and limits are configurable.
- Dogfood documentation removes decorative strong emphasis from prose outside tables and typed documents.
