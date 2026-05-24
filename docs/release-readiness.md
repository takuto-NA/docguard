# Release readiness

This page records distribution milestones for docguard. It is separate from [docs/dogfood.md](dogfood.md), which covers self-application impact tables, self-test commands, and readiness checklists for this repository's own documentation. See [docs/adr/0007-document-responsibility-drift-guard.md](adr/0007-document-responsibility-drift-guard.md) for why release planning lives here.

## Distribution roadmap

Docguard is ready for Alpha source distribution from the repository. Users can clone the repository, install it locally, and evaluate the CLI and pytest plugin with the documented Alpha expectations.

The next distribution milestones are:

1. Alpha source distribution
   - Keep `Development Status :: 3 - Alpha`.
   - Use repository installation and source checkouts as the supported path.
   - Require the self-test commands in [docs/dogfood.md](dogfood.md#self-test-in-this-repository) to pass before sharing a release tag.
2. PyPI readiness
   - Decide whether PyPI users should rely on a self-contained README or bundled documentation.
   - Add release notes for user-facing changes.
   - Add CI that runs the full pytest suite and the docguard self-check.
   - Add a documentation language guard for user-facing pages, covering user-prohibited wording, pronoun overuse, Markdown strong emphasis, and unexplained slang.
   - Add a wheel smoke test that installs the built package and runs `docguard --help`.
3. Stable readiness
   - Freeze or explicitly version configuration keys and diagnostic JSON fields.
   - Document compatibility expectations for rule defaults and exit codes.
   - Keep dogfood gates green without raising document budgets or copying detailed reference content into README.

Do not present the project as a stable package until the PyPI and compatibility items are complete.

See also: [docs/dogfood.md](dogfood.md), [docs/usage.md](usage.md).
