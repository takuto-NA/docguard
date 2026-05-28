# Prose style rules

Prose style checks run on every docguard scan. They complement structure diagnostics by flagging decorative strong emphasis, conversational phrasing, and parenthetical asides in body prose.

Prose style is not a general Markdown formatter. It does not validate heading spelling, list markers, or link syntax.

## What you can do with prose style

| Capability | Diagnostic | Configuration |
|------------|------------|---------------|
| Limit strong emphasis in prose | `DG-STYLE001` | `max_strong_emphasis_pairs` (default `0`) |
| Flag prohibited pronoun, slang, and parenthetical punctuation patterns | `DG-STYLE002` | built-in patterns; optional `extra_prohibited_prose_patterns` and `allowed_prose_phrases` |
| Flag forbidden documentation expressions in headings, prose, and table headers | `DG-STYLE003` | built-in ranked manifest; optional `extra_prohibited_documentation_style_patterns` and `allowed_documentation_style_phrases` |
| Fail CI on any prose or documentation style rule | all three | strict baseline severity is `"error"` |

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

Documents matching `document_types`, such as ADRs, skip `DG-STYLE001` and `DG-STYLE002`. `DG-STYLE003` applies to typed documents. Lines under `## Example dialogue` are excluded from all three checks.

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

What it finds: built-in matches for direct address, namely `you`, `your`, `we`, and `our`, and casual filler, namely `easy`, `simple`, and `just`, in prose lines after masking Markdown links, image links, bare URLs, and inline code. Parenthetical punctuation in remaining body text is also prohibited.

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

## Detect forbidden documentation expressions (`DG-STYLE003`)

What it finds: ranked forbidden documentation expressions in headings, body prose, and Markdown table header cells. Built-in rules cover high-confidence patterns such as heading ` — ` subtitles, full-width heading subtitles `（…）`, conversational Japanese section titles, table headers such as `以前` or `現在`, prose lines starting with `責務:`, and general colloquial phrases such as `ざっくり`, `とりあえず`, `ちょっと`, `いい感じ`, `便利`, `簡単`, and `おすすめ`. They also cover ChatGPT-style vague phrasing such as `筋が良い`, `結論から言うと`, `こうです。`, `本命`, `重い`, `非常に`, `核心`, and deictic words such as `ここ`, `この`, `それ`, `こう`, `その`, and `あの`.

Typical fix: rewrite the heading, prose, or table label in neutral documentation voice using the recommended replacement shown in the diagnostic message.

Allow intentional phrases:

```toml
[[tool.docguard.relaxations]]
parameter = "allowed_documentation_style_phrases"
value = ["このリポジトリ"]
reason = "Legacy migration keeps this repository label temporarily."
```

Add project-specific patterns:

```toml
[tool.docguard]
extra_prohibited_documentation_style_patterns = ["\\\\blegacy\\\\b"]
```

Unlike `DG-STYLE001` and `DG-STYLE002`, `DG-STYLE003` applies to typed documents such as ADRs.

Full ranked manifest and enforcement status: [docs/adr/0015-forbidden-documentation-expressions.md](adr/0015-forbidden-documentation-expressions.md).

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
  Direct address, casual filler words, and parenthetical asides make repository documentation sound promotional or conversational instead of precise and maintainable.

Rewrite the sentence in neutral documentation voice without parenthetical asides, or add an allowed_prose_phrases entry when the wording is intentional.
```

## In this repository

All three style diagnostics run as `error` in `pyproject.toml`. Readiness tests expect 0 prose style and documentation style candidates across the dogfood scope. The PyPI README gate reuses the same core through `tests/test_release_readiness.py`.

Self-test commands for prose style and documentation style:

```bash
uv run pytest tests/test_prose_style.py tests/test_prose_style_readiness.py tests/test_prose_style_baseline.py
uv run pytest tests/test_documentation_style.py tests/test_documentation_style_readiness.py tests/test_documentation_style_baseline.py
uv run pytest tests/test_release_readiness.py::test_readme_passes_prose_style_guard
uv run pytest tests/test_release_readiness.py::test_readme_passes_documentation_style_guard
uv run docguard README.md CONTEXT.md docs/ --summary
```

Full specification: [docs/adr/0012-prose-style-diagnostics.md](adr/0012-prose-style-diagnostics.md) and [docs/adr/0015-forbidden-documentation-expressions.md](adr/0015-forbidden-documentation-expressions.md).

See also: [docs/usage.md](usage.md), [docs/dogfood.md](dogfood.md).
