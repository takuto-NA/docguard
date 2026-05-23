---
status: accepted
date: 2026-05-23
---

# Structured diagnostics and strict configuration

## Status

Accepted.

## Context

Docguard is a CI quality gate. Users need predictable failure behavior, machine-readable output, and confidence that invalid configuration is rejected before document scanning begins.

## Decision

Docguard returns structured diagnostics with human-readable and JSON output from the same model. Only `error` severity fails a run; `warning` reports but passes; `experimental` rules are opt-in and initially non-failing. Configuration errors exit with code 2 instead of being reported as document diagnostics.

## Consequences

CLI and pytest adapters must share one diagnostic model and one severity-to-exit-code mapping. Configuration validation happens before document scanning.
