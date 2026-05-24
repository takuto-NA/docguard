# Structure rules (Phase 3)

Phase 3 adds two opt-in structure checks. They inspect heading patterns **inside each document** (not link structure like Phase 2).

Both rules default to **off** and to **`warning` severity**. Turn them on when you want early signals before documents grow large enough to fail `DG-SIZE001`.

## What you can do with Phase 3

| Capability | Diagnostic | Configuration |
|------------|------------|---------------|
| Detect mixed purposes in one untyped file | `DG-SPLIT001` | `require_mixed_role_detection = true` |
| Detect skipped heading levels | `DG-FORMAT002` | `require_heading_order_check = true` |
| Review warnings without failing CI | both | default severity `warning` |
| Fail CI on either rule | both | set severity to `"error"` |

**Entry points:** same as other rules — `docguard`, `--format json`, `pytest --docguard`.

```bash
docguard docs/
docguard docs/ --verbose       # review warnings
docguard docs/ --format json
pytest --docguard
```

## Role families for `DG-SPLIT001`

Docguard classifies **level-2 headings only** (`## ...`) into four built-in role families. English and representative Japanese keywords are supported.

| Role family | Example heading text |
|-------------|----------------------|
| `narrative` | Overview, Background, 概要, 背景 |
| `decision` | Decision, Alternatives, 決定, 代替 |
| `reference` | API, Configuration, 仕様, 設定 |
| `operations` | Deployment, Runbook, 運用, デプロイ |

When **two or more families** match across level-2 headings, docguard reports one `DG-SPLIT001` warning per document. Documents matching `document_types` (such as ADRs) are **never** checked for mixed roles.

## How Phase 3 differs from other checks

| Existing check | Phase 3 difference |
|----------------|-------------------|
| `DG-SIZE001` | SIZE fires after a file is already long; SPLIT001 signals mixed purpose earlier |
| `DG-FORMAT001` | FORMAT001 checks required headings on **typed** documents; SPLIT001 targets **untyped** mixed purpose |
| `DG-FORMAT002` | checks heading **level skips**, not missing required headings or required heading order |
| Phase 2 (`DG-ORG*`) | ORG checks **links between files**; Phase 3 checks **headings within a file** |

| Question | Diagnostic | When it runs |
|----------|------------|--------------|
| Does this untyped document mix multiple role families in level-2 headings? | `DG-SPLIT001` | `require_mixed_role_detection = true` |
| Does any heading skip a level (for example H2 then H4)? | `DG-FORMAT002` | `require_heading_order_check = true` |

Mixed roles and missing required headings are **not** the same. `DG-FORMAT001` checks typed documents for required sections. `DG-SPLIT001` warns when an **untyped** document's level-2 headings suggest multiple purposes such as overview plus operations. See [CONTEXT.md](../CONTEXT.md).

## Detect mixed document roles (`DG-SPLIT001`)

**What it finds:** untyped documents whose level-2 headings match two or more built-in role families (`narrative`, `decision`, `reference`, `operations`).

**Typical fix:** split the document by major topic so each file covers one concern.

**Example:** if `docs/guide.md` has `## Overview` and `## Deployment`, docguard reports `DG-SPLIT001` on `docs/guide.md`.

**Enable:**

```toml
[tool.docguard]
require_mixed_role_detection = true
```

Documents matching `document_types` are never flagged for mixed roles.

## Detect heading level skips (`DG-FORMAT002`)

**What it finds:** headings that jump more than one level deeper than the previous heading.

**Typical fix:** insert intermediate heading levels or restructure the section.

**Example:** if `## Section` is followed by `#### Deep`, docguard reports `DG-FORMAT002` at the deep heading line.

**Enable:**

```toml
[tool.docguard]
require_heading_order_check = true
```

## Enable both Phase 3 rules

Both rules are opt-in and default to `warning`:

```toml
[tool.docguard]
require_mixed_role_detection = true
require_heading_order_check = true

[tool.docguard.severity]
DG-SPLIT001 = "warning"
DG-FORMAT002 = "warning"
```

Full specification: [docs/adr/0005-phase3-structure-diagnostics.md](adr/0005-phase3-structure-diagnostics.md).

**In this repository:** both Phase 3 flags stay off in the default `pyproject.toml`. If you enable them against the current documentation scope, readiness tests expect **0** mixed-role candidates and **0** heading-level skips. See [docs/dogfood.md](dogfood.md).

## Detect duplicate guidance (`DG-SPLIT002`)

**What it finds:** repeated fenced code blocks, headings, or list items whose normalized text appears across the configured scan scope beyond rule thresholds.

**Typical fix:** keep one canonical install, CLI, configuration, or exit-code section and link to it elsewhere.

**Enable:**

```toml
[tool.docguard]
require_duplicate_guidance_detection = true
allowed_duplicate_patterns = ["^Status$"]
```

Use `allowed_duplicate_patterns` only for intentional repeated labels such as ADR section headings, not to hide accidental command duplication.

Full specification: [docs/adr/0009-duplicate-guidance-diagnostic.md](adr/0009-duplicate-guidance-diagnostic.md).

**In this repository:** duplicate guidance detection is enabled as `error`. Readiness tests expect **0** duplicate guidance groups after allowlisting ADR section headings. See [docs/dogfood.md](dogfood.md).

See also: [docs/usage.md](usage.md), [docs/dogfood.md](dogfood.md).
