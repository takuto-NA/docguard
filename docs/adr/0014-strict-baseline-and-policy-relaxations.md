---
status: accepted
date: 2026-05-28
---

# Strict baseline and policy relaxations

## Status

Accepted.

## Context

Docguard 0.2.0 let repositories start with a lenient fallback: scan `docs/`, allow 400-line documents, leave reachability and duplicate guidance off, and report prose style as warnings. That made adoption easy but also let teams believe docguard was active while important structure checks were not effective.

Maintainers also had an easy escape hatch: directly raising `max_document_lines` or downgrading severity in `pyproject.toml`. This repeated the same failure recorded in ADR 0006, where editing config bypassed the documentation split pressure docguard is supposed to create.

## Decision

Docguard 0.3.0 replaces zero-config with a strict baseline. The baseline scans `README.md`, `CONTEXT.md`, and `docs`; uses `README.md` as the index file; enforces 300-line documents, 120-line sections, and a 20-line floor for untyped non-index documents; enables index reachability and duplicate guidance; and treats duplicate guidance plus prose style diagnostics as errors.

Loosening that baseline is allowed only through `[[tool.docguard.relaxations]]` entries with `parameter`, `value`, and a concrete `reason`. Direct pyproject values may keep or tighten the baseline, but direct values that loosen it fail as configuration errors.

## Consequences

Existing 0.2.x users can be broken by upgrading to 0.3.0. That is acceptable while docguard is Alpha because earlier users were beta testers and the previous defaults were too weak to be a reliable guardrail.

Repositories that need migration time can still proceed, but every relaxation is visible in one table and carries a reason. This keeps temporary exceptions reviewable and avoids silent config drift.
