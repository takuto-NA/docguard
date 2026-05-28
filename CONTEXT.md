# Docguard

Docguard is a CLI-first Markdown structure checker that keeps repository documentation from growing too large, becoming unreachable, or drifting away from expected document types.

## Language

**Docguard**:
A CLI-first tool that checks Markdown document structure in a repository.
_Avoid_: pytest-docguard, doc linter

**Document**:
A Markdown file inside the active scan scope.
_Avoid_: file, page, note

**Document type**:
A named set of structural expectations matched by glob; a document must match at most one type.
_Avoid_: template, schema, category

**Index file**:
A configured Markdown root used as a navigation entry point for reachability checks.
_Avoid_: root doc, landing page, hub

**Outgoing link**:
A relative Markdown link from one in-scope document to another in-scope Markdown file.
_Avoid_: backlink, reference, href

**Hub document**:
A configured navigation document expected to link onward to other in-scope Markdown files. Index files are always hub documents; additional paths may match optional `hub_globs`.
_Avoid_: index file, landing page, root doc

**Leaf document**:
An in-scope document that is not a hub document.
_Avoid_: terminal page, detail page

**Reachable document**:
A document that can be reached from at least one index file by recursively following relative Markdown links.
_Avoid_: linked document, connected document

**Unreachable document**:
A scanned document that is not reachable from any configured index file.
_Avoid_: orphan, isolated document

**Orphan document**:
A document with no incoming Markdown links from other documents in scope. Index files are excluded from orphan detection.
_Avoid_: unreachable document, dead document

**Diagnostic**:
A structured finding with code, severity, location, message, why-it-matters text, and optional suggestion.
_Avoid_: error, violation, lint

**Severity**:
The impact level of a diagnostic: `error` fails the run, `warning` reports but passes, `experimental` is opt-in and initially non-failing.
_Avoid_: level, priority

**Document encoding**:
Markdown files must be UTF-8. UTF-8 with BOM is accepted. Non-UTF-8 files fail with exit code 2. See [docs/adr/0004-utf-8-markdown-encoding.md](docs/adr/0004-utf-8-markdown-encoding.md).
_Avoid_: charset, code page, Shift_JIS

**Document role family**:
A built-in category, namely `narrative`, `decision`, `reference`, or `operations`, inferred from level-2 section heading text.
_Avoid_: document type, template section

**Mixed document roles**:
An untyped document whose level-2 headings match two or more document role families.
_Avoid_: missing required heading, document too long

**Heading level skip**:
A heading more than one level deeper than the previous heading in document order, for example H2 followed by H4.
_Avoid_: missing required heading, wrong section order

**Document budget**:
A repository-owned size limit that keeps documentation maintainable; exceeding it should trigger splitting or restructuring instead of raising the configured line limit.
_Avoid_: max lines bump, configuration workaround
See [docs/adr/0006-document-budget-dogfood-gate.md](docs/adr/0006-document-budget-dogfood-gate.md).

**Strict baseline**:
The built-in default policy applied when no `[tool.docguard]` table exists or when it is empty. It replaces the former lenient zero-config defaults and is not relaxable except through documented policy relaxations.
_Avoid_: zero-config, default config, implicit settings

**Policy relaxation**:
An explicit, reasoned exception that makes docguard less strict than the strict baseline for one parameter. Relaxations are recorded only in `[[tool.docguard.relaxations]]`; direct pyproject keys that loosen policy are rejected.
_Avoid_: override, config tweak, limit bump

**Document floor**:
The minimum line count for an untyped in-scope document. Documents below the floor are treated as refactor leftovers or stub pages that should be merged into a canonical document instead of kept as separate files.
_Avoid_: min lines, tiny doc rule, stub threshold

**Stub document**:
An untyped Markdown file that is too short to stand alone as maintainable documentation, often left behind after a split or refactor.
_Avoid_: orphan page, placeholder, empty doc

**Document responsibility**:
A declared ownership boundary for what a document is allowed to explain in detail.
_Avoid_: page role, doc type, content area

**Document responsibility drift**:
A documentation failure mode where a document absorbs topics outside its declared responsibility because the material is nearby or convenient to edit.
_Avoid_: doc bloat, scope creep, content overlap
See [docs/adr/0007-document-responsibility-drift-guard.md](docs/adr/0007-document-responsibility-drift-guard.md).

**Duplicate guidance**:
Repeated commands, list items, or prose paragraphs that make the same maintenance instruction appear in multiple places without a clear canonical owner. Heading and paragraph duplicates are opt-in through `duplicate_guidance_kinds`.
_Avoid_: copy-paste docs, repeated examples, duplicate setup blocks
See [docs/adr/0009-duplicate-guidance-diagnostic.md](docs/adr/0009-duplicate-guidance-diagnostic.md), [docs/adr/0010-duplicate-guidance-kind-scope.md](docs/adr/0010-duplicate-guidance-kind-scope.md), [docs/adr/0011-duplicate-prose-paragraph-guidance.md](docs/adr/0011-duplicate-prose-paragraph-guidance.md).

**Prose style violation**:
Excess Markdown strong emphasis or prohibited conversational phrasing in body prose, including parenthetical asides that are not part of Markdown syntax. Checked by `DG-STYLE001` and `DG-STYLE002`; typed documents are excluded.
_Avoid_: AI-like text, formatting error, lint, parenthetical aside
See [docs/adr/0012-prose-style-diagnostics.md](docs/adr/0012-prose-style-diagnostics.md).

**Prohibited parenthetical punctuation**:
Half-width `()` or full-width `（）` used as a non-Markdown aside in body prose.
_Avoid_: parenthesis, bracket aside, supplementary note
See [docs/adr/0012-prose-style-diagnostics.md](docs/adr/0012-prose-style-diagnostics.md).

**Strong emphasis pair**:
One closed strong emphasis span in a prose line after inline code segments are removed.
_Avoid_: bold marker count, asterisk count

**Prose line**:
A non-empty line that is not a code fence, heading, front matter line, table row, glossary term definition line, or part of the example dialogue section.
_Avoid_: body text, paragraph

## Example dialogue

**Developer**: This ADR is flagged as unreachable from index.
**Maintainer**: That means no configured index file can reach it through relative Markdown links. Add it to `docs/adr/README.md` or link it from another reachable document.
**Developer**: Is that the same as an orphan document?
**Maintainer**: No. Orphan means nothing links to it. Unreachable means it is not on a path from an index file. A document can be unreachable without being an orphan if it is part of a linked cluster that is not connected to any index.
**Developer**: Why would a hub document fail a check?
**Maintainer**: Docguard warns when a hub document has no outgoing links to other in-scope Markdown files. That usually means the navigation entry point is a dead end.
**Developer**: A page in `docs/` is only twelve lines after we moved content elsewhere. Why is that an error?
**Maintainer**: Untyped documents below the document floor are stub documents. Merge them into the canonical page they point at or delete them. Index files listed in `index_files` and typed documents such as ADRs are excluded because short entry points and decision records are expected there.
**Developer**: Can we lower the floor for one legacy folder?
**Maintainer**: Only through a policy relaxation with a written reason in `[[tool.docguard.relaxations]]`. Direct `min_document_lines` in `[tool.docguard]` is rejected.