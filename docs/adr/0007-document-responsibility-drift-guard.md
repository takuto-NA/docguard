---
status: accepted
date: 2026-05-24
---

# Document responsibility drift guard

## Status

Accepted.

## Context

During documentation work, release and distribution planning was added to `docs/dogfood.md` under `## Distribution roadmap`. That page is declared as the place for self-application impact tables, self-test commands, and readiness checklists. Release planning is related but not the same responsibility.

The existing document budget gate catches oversized files. The existing README-only responsibility gate catches detail creep in the entry point. Neither gate catches responsibility drift when an agent adds reasonable-looking material to a nearby document, renames a heading, and still passes line, link, and README-only checks.

This is a hostile-change class for documentation because agents tend to append to the nearest file instead of splitting by responsibility.

## Decision

1. **Treat document responsibility drift as a major documentation risk** and record it in the glossary and tests.
2. **Split release planning into `docs/release-readiness.md`.** Dogfood/self-test material stays in `docs/dogfood.md`.
3. **Extend `tests/test_document_responsibilities.py`** so `docs/dogfood.md` fails when it contains release-roadmap material, even if the heading is renamed.
4. **Require `docs/release-readiness.md` to own distribution milestones** including Alpha source distribution, PyPI readiness, stable readiness, CI, wheel checks, and the future language guard requirement.
5. **Do not rely on heading-only fixes, manual review, or documentation-only warnings** for this invariant.

Alternatives rejected:

- rename `## Distribution roadmap` to `## Distribution readiness` and keep the content in `docs/dogfood.md`
- keep release planning in dogfood because it is "related to readiness"
- rely on the 400-line document budget alone
- rely on manual review after agent edits
- keep README-only responsibility tests

## Consequences

- New release planning must go to `docs/release-readiness.md`, not `docs/dogfood.md`.
- `docs/dogfood.md` links to the release-readiness page instead of duplicating milestones.
- Phase 2 readiness snapshots must include the new page and updated link graph.
- Future agent edits that reintroduce release planning into dogfood fail in CI.
- The PyPI language guard remains a release-readiness requirement, not a dogfood topic.
- Maintainers can rely on the outcomes documented in [docs/dogfood.md](../dogfood.md#what-the-document-responsibility-gate-gives-you): clear page ownership, a trimmed README, dogfood drift tests, and glossary terms for the failure mode.
