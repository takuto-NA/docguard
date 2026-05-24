---
status: accepted
date: 2026-05-24
---

# Duplicate guidance diagnostic

## Status

Accepted.

## Context

During review of `docs/usage.md`, repeated install commands, CLI entry points, configuration examples, and exit-code explanations appeared across multiple reading paths. Existing docguard checks passed because they cover size, reachability, typed document shape, heading skips, mixed roles, and document responsibility drift, but not repeated guidance.

If docguard cannot detect this class of documentation failure in its own repository, the tool fails its dogfood promise.

## Decision

1. **Add product diagnostic `DG-SPLIT002` for duplicate guidance.**
2. **Detect repeated fenced code blocks, headings, and list items across the configured scan scope.**
3. **Use structural normalization rather than semantic prose similarity.**
4. **Make the rule opt-in with default `warning` severity.**
5. **Enable the rule as `error` in this repository's dogfood configuration.**
6. **Support `allowed_duplicate_patterns` for intentional repeated normalized text.**

Alternatives rejected:

- repository-only dogfood tests without a product diagnostic
- semantic prose similarity across documents
- same-document-only duplicate detection
- default-on error severity for all adopters

## Consequences

- Adopters can opt in with `require_duplicate_guidance_detection = true`.
- This repository treats duplicate guidance as a blocking documentation failure.
- Intentional repetition must be allowlisted explicitly rather than silently tolerated.
- Documentation refactors should consolidate canonical install, CLI, configuration, and exit-code guidance into one owner section.
- Default heading duplicate scope was narrowed in [docs/adr/0010-duplicate-guidance-kind-scope.md](0010-duplicate-guidance-kind-scope.md).
