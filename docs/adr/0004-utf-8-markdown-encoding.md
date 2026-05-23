---
status: accepted
date: 2026-05-23
---

# UTF-8 Markdown encoding

## Status

Accepted.

## Context

Docguard scans Markdown files from the CLI, pytest adapter, and library entry points such as `run_docguard_from_paths()`. Teams using Japanese or other non-ASCII content need a clear encoding contract and predictable failure behavior when a file cannot be decoded.

Today, `parse_markdown_document()` reads files with UTF-8 and lets `UnicodeDecodeError` escape as a traceback. That violates the strict failure model in [ADR 0002](0002-structured-diagnostics-and-strict-config.md), which reserves exit code 2 for configuration and pre-diagnostic failures instead of document diagnostics.

## Decision

1. **Markdown input encoding is UTF-8 only.** Files without a BOM are preferred. UTF-8 with BOM is also accepted through `utf-8-sig`.
2. **Non-UTF-8 files fail before diagnostics.** When discovery cannot decode a Markdown file, docguard raises `ConfigurationError` with a clear English message. CLI and pytest adapters exit with code `2` and must not print a traceback.
3. **Diagnostic language stays English.** Document paths, heading names, and configuration values may contain Unicode characters.
4. **Out of scope.** Docguard does not auto-detect Shift_JIS or other legacy encodings, and diagnostic messages are not localized.

This extends ADR 0002: although encoding validation happens during document discovery rather than initial configuration parsing, the failure is still treated as a pre-diagnostic configuration failure with exit code `2`.

## Consequences

- `MARKDOWN_FILE_ENCODING = "utf-8-sig"` becomes the single read contract in code.
- Tests must cover Japanese content, JSON output with CJK text, and non-UTF-8 failure paths across CLI, runner, and pytest.
- Documentation must state the UTF-8 requirement and show Japanese `required_headings` examples.
- Phase 2 organization rules assume UTF-8 Markdown input.
