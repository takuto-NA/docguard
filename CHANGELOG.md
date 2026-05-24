# Changelog

All notable user-facing changes to docguard are documented in this file.

## Alpha compatibility

Docguard is in Alpha. Configuration keys, diagnostic JSON fields, and rule defaults may change between releases. Breaking changes are listed under each version. Exit codes (`0` success, `1` diagnostic failure, `2` configuration failure) and existing diagnostic code meanings are preserved where practical.

## [Unreleased]

### Added

- Opt-in `paragraph` kind for `DG-SPLIT002` duplicate guidance detection.
- `duplicate_guidance_kinds` configuration key to choose which duplicate guidance atom kinds `DG-SPLIT002` checks.

### Changed

- `DG-SPLIT002` no longer detects repeated headings unless `duplicate_guidance_kinds` includes `heading`. Default kinds are `code_block` and `list_item`. Prose paragraph detection requires `paragraph` in `duplicate_guidance_kinds`.

## [0.1.0] - 2026-05-24

### Added

- CLI-first Markdown structure checker with nine diagnostics across Core, Phase 2, and Phase 3.
- Structured diagnostics with human and JSON output.
- Pytest plugin entry point (`pytest --docguard`, `pytest --docguard-only`).
- Typed document support via `[tool.docguard.document_types]` (ADR example included).
- UTF-8 Markdown encoding requirement with Japanese path and heading support.
- PyPI Alpha distribution as `docguard` with uv-first documentation and pip-compatible wheels.

[0.1.0]: https://github.com/takuto-NA/docguard/releases/tag/v0.1.0
