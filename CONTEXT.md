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

**Reachable document**:
A document that can be reached from at least one index file by recursively following relative Markdown links.
_Avoid_: linked document, connected document

**Unreachable document**:
A scanned document that is not reachable from any configured index file.
_Avoid_: orphan, isolated document

**Orphan document**:
A document with no incoming Markdown links from other documents in scope.
_Avoid_: unreachable document, dead document

**Diagnostic**:
A structured finding with code, severity, location, message, why-it-matters text, and optional suggestion.
_Avoid_: error, violation, lint

**Severity**:
The impact level of a diagnostic: `error` fails the run, `warning` reports but passes, `experimental` is opt-in and initially non-failing.
_Avoid_: level, priority

## Example dialogue

**Developer**: This ADR is flagged as unreachable from index.
**Maintainer**: That means no configured index file can reach it through relative Markdown links. Add it to `docs/adr/README.md` or link it from another reachable document.
**Developer**: Is that the same as an orphan document?
**Maintainer**: No. Orphan means nothing links to it. Unreachable means it is not on a path from an index file. A document can be unreachable without being an orphan if it is part of a linked cluster that is not connected to any index.
