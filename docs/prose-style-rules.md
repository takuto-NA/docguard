# Prose style rules

Prose style checks run on every docguard scan. They complement structure diagnostics by flagging decorative strong emphasis and conversational phrasing in body prose.

Prose style is not a general Markdown formatter. It does not validate heading spelling, list markers, or link syntax.

## What you can do with prose style

| Capability | Diagnostic | Configuration |
|------------|------------|---------------|
| Limit strong emphasis in prose | `DG-STYLE001` | `max_strong_emphasis_pairs` (default `0`) |
| Flag prohibited pronoun and slang patterns | `DG-STYLE002` | built-in patterns; optional `extra_prohibited_prose_patterns` and `allowed_prose_phrases` |
| Fail CI on either rule | both | strict baseline severity is `"error"` |

Entry points: same as other rules — `docguard`, `--format json`, `pytest --docguard`.

## What counts as prose

Docguard inspects prose lines only. The following are excluded:

- fenced code blocks
- heading lines
- YAML front matter
- Markdown table rows
- glossary term definition lines such as `**Term**:`
- lines under `## Example dialogue`

Inline code segments do not contribute to strong emphasis pair counts.

Documents matching `document_types` (such as ADRs) skip prose style checks entirely.

## Detect excess strong emphasis (`DG-STYLE001`)

What it finds: more closed strong emphasis pairs in prose than `max_strong_emphasis_pairs` allows.

Typical fix: remove strong emphasis or rewrite the sentence in plain text.

Example configuration:

```toml
[[tool.docguard.relaxations]]
parameter = "max_strong_emphasis_pairs"
value = 2
reason = "Legacy prose cleanup needs a temporary emphasis allowance."
```

Raise the limit only as a reasoned relaxation when adopting docguard against legacy documentation, then remove it once prose is cleaned up.

## Detect prohibited prose patterns (`DG-STYLE002`)

What it finds: built-in matches for direct address (`you`, `your`, `we`, `our`) and casual filler (`easy`, `simple`, `just`) in prose lines after removing Markdown links and bare URLs.

Typical fix: rewrite in neutral documentation voice.

Allow intentional phrases:

```toml
[[tool.docguard.relaxations]]
parameter = "allowed_prose_phrases"
value = ["What you can check"]
reason = "Usage documentation keeps this exact heading during migration."
```

Add project-specific patterns:

```toml
[tool.docguard]
extra_prohibited_prose_patterns = ["\\bkindly\\b"]
```

Invalid regular expressions fail configuration loading.

## Example output

```text
WARNING docs/guide.md::docguard

DG-STYLE001 excess strong emphasis
  docs/guide.md has 2 strong emphasis pairs in prose. Limit: 0.

Why this matters:
  Heavy Markdown strong emphasis in prose often signals AI-generated drafts or decorative wording that makes documentation harder to scan.

Remove strong emphasis from prose or rewrite the sentence in plain text.

WARNING docs/guide.md::docguard

DG-STYLE002 prohibited prose pattern
  Prohibited prose pattern matched at line 12: \beasy\b

Why this matters:
  Direct address and casual filler words make repository documentation sound promotional or conversational instead of precise and maintainable.

Rewrite the sentence in neutral documentation voice, or add an allowed_prose_phrases entry when the wording is intentional.
```

## In this repository

Both diagnostics run as `error` in `pyproject.toml`. Readiness tests expect 0 prose style candidates across the dogfood scope. The PyPI README gate reuses the same core through `tests/test_release_readiness.py`.

Self-test commands for prose style:

```bash
uv run pytest tests/test_prose_style.py tests/test_prose_style_readiness.py tests/test_prose_style_baseline.py
uv run pytest tests/test_release_readiness.py::test_readme_passes_prose_style_guard
uv run docguard README.md CONTEXT.md docs/ --summary
```

Full specification: [docs/adr/0012-prose-style-diagnostics.md](adr/0012-prose-style-diagnostics.md).

See also: [docs/usage.md](usage.md), [docs/dogfood.md](dogfood.md).
