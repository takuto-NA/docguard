# Changelog

All notable user-facing changes to docguard are documented in this file.

## Alpha compatibility

Docguard is in Alpha. Configuration keys, diagnostic JSON fields, and rule defaults may change between releases. Breaking changes are listed under each version. Exit codes (`0` success, `1` diagnostic failure, `2` configuration failure) and existing diagnostic code meanings are preserved where practical.

## [Unreleased]

### Added

- `DG-STYLE003` flags forbidden documentation expressions in headings, body prose, and Markdown table header cells. Typed documents such as ADRs are included.
- Configuration keys `allowed_documentation_style_phrases` and `extra_prohibited_documentation_style_patterns`.
- [docs/adr/0015-forbidden-documentation-expressions.md](docs/adr/0015-forbidden-documentation-expressions.md).

### Changed

- `DG-STYLE002` now flags parenthetical punctuation in body prose after masking Markdown links, image links, bare URLs, and inline code. Half-width `()` and full-width `（）` in remaining body text are prohibited.

## [0.3.0] - 2026-05-28

### Breaking

- Replaced the lenient zero-config fallback with a strict baseline that scans `README.md`, `CONTEXT.md`, and `docs`; requires index reachability from `README.md`; enables duplicate guidance detection; enforces 300-line documents; and treats duplicate guidance plus prose style diagnostics as errors.
- Direct config values that loosen the strict baseline now fail with exit code `2`. Use `[[tool.docguard.relaxations]]` with `parameter`, `value`, and `reason` instead.

### Added

- `DG-SIZE003` reports untyped non-index Markdown documents below the 20-line document floor.
- `docguard init` prints a strict-baseline starter snippet.
- `--summary` prints the active policy line on clean runs.

## [0.2.0] - 2026-05-25

### Added

- Prose style diagnostics `DG-STYLE001` (excess strong emphasis) and `DG-STYLE002` (prohibited prose patterns), always on with default `warning` severity.
- Configuration keys `max_strong_emphasis_pairs`, `allowed_prose_phrases`, and `extra_prohibited_prose_patterns`.
- [docs/prose-style-rules.md](docs/prose-style-rules.md) and [docs/adr/0012-prose-style-diagnostics.md](docs/adr/0012-prose-style-diagnostics.md).
- First PyPI release as **`docguard-structure`** (CLI and import remain `docguard`). See [docs/adr/0013-pypi-distribution-name-docguard-structure.md](docs/adr/0013-pypi-distribution-name-docguard-structure.md).

### Changed

- PyPI README prose checks reuse the docguard core instead of duplicated release-gate regex logic (supersedes ADR 0008 item 6 for emphasis and prohibited-pattern checks).
- Opt-in `paragraph` kind for `DG-SPLIT002` duplicate guidance detection.
- `duplicate_guidance_kinds` configuration key to choose which duplicate guidance atom kinds `DG-SPLIT002` checks.
- `DG-SPLIT002` no longer detects repeated headings unless `duplicate_guidance_kinds` includes `heading`. Default kinds are `code_block` and `list_item`. Prose paragraph detection requires `paragraph` in `duplicate_guidance_kinds`.

## [0.1.0] - 2026-05-24

### Added

- CLI-first Markdown structure checker with nine diagnostics across Core, Phase 2, and Phase 3.
- Structured diagnostics with human and JSON output.
- Pytest plugin entry point (`pytest --docguard`, `pytest --docguard-only`).
- Typed document support via `[tool.docguard.document_types]` (ADR example included).
- UTF-8 Markdown encoding requirement with Japanese path and heading support.
- PyPI Alpha distribution planning with uv-first documentation and pip-compatible wheels.

[0.3.0]: https://github.com/takuto-NA/docguard/releases/tag/v0.3.0
[0.2.0]: https://github.com/takuto-NA/docguard/releases/tag/v0.2.0
[0.1.0]: https://github.com/takuto-NA/docguard/releases/tag/v0.1.0
