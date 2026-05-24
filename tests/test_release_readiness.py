"""Release-readiness gate tests for PyPI Alpha distribution.

Verifies package metadata, README policy, changelog presence, prose style guard
through the docguard core, and uv-first documentation before a PyPI Alpha release.
"""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

from docguard.config import load_docguard_configuration
from docguard.markdown import parse_markdown_document
from docguard.models import DocumentInspectionContext
from docguard.rules import check_prose_style

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"
README_PATH = REPOSITORY_ROOT / "README.md"
CHANGELOG_PATH = REPOSITORY_ROOT / "CHANGELOG.md"

GITHUB_REPOSITORY_URL = "https://github.com/takuto-NA/docguard"

CI_WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
PUBLISH_WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "publish.yml"

REPOSITORY_NAVIGATION_HEADING = "## Repository navigation"

RELATIVE_DOCS_LINK_PATTERN = re.compile(r"\]\(docs/")
GITHUB_DOCS_LINK_PATTERN = re.compile(
    rf"\]\({re.escape(GITHUB_REPOSITORY_URL)}/blob/main/docs/"
)

REQUIRED_UV_CONSUMER_COMMANDS = (
    "uv add docguard",
    "uv run docguard",
)

REQUIRED_UV_CONTRIBUTOR_COMMANDS = (
    'uv pip install -e ".[dev]"',
    "uv run pytest",
)

REQUIRED_PIP_ALTERNATIVE_COMMAND = "pip install docguard"

REQUIRED_PRE_PYPI_INSTALL_GUIDE_URL = (
    f"{GITHUB_REPOSITORY_URL}/blob/main/docs/usage.md#before-pypi-publication"
)

REQUIRED_TOOL_DOCGUARD_MARKER = "[tool.docguard]"
REQUIRED_ALPHA_MARKER = "Alpha"


def extract_text_before_heading(document_text: str, heading: str) -> str:
    heading_start = document_text.find(heading)
    if heading_start == -1:
        return document_text
    return document_text[:heading_start]


def load_pyproject_data() -> dict:
    pyproject_text = PYPROJECT_PATH.read_text(encoding="utf-8")
    return tomllib.loads(pyproject_text)


def collect_missing_substrings(
    document_text: str,
    required_substrings: tuple[str, ...],
) -> list[str]:
    missing_substrings: list[str] = []
    for required_substring in required_substrings:
        if required_substring not in document_text:
            missing_substrings.append(required_substring)
    return missing_substrings


def collect_readme_prose_style_diagnostics():
    configuration = load_docguard_configuration(
        project_root=REPOSITORY_ROOT,
        config_path=PYPROJECT_PATH,
        cli_paths=tuple(),
    )
    parsed_document = parse_markdown_document(
        README_PATH,
        "README.md",
    )
    inspection_context = DocumentInspectionContext(
        parsed_document=parsed_document,
        document_type=None,
        max_document_lines=configuration.max_document_lines,
        max_section_lines=configuration.max_section_lines,
    )
    return check_prose_style(configuration, inspection_context)


def test_pyproject_includes_project_urls() -> None:
    pyproject_data = load_pyproject_data()
    project_urls = pyproject_data.get("project", {}).get("urls", {})

    assert project_urls.get("Homepage") == GITHUB_REPOSITORY_URL
    assert project_urls.get("Repository") == GITHUB_REPOSITORY_URL
    assert project_urls.get("Documentation") == f"{GITHUB_REPOSITORY_URL}#readme"
    assert project_urls.get("Changelog") == f"{GITHUB_REPOSITORY_URL}/blob/main/CHANGELOG.md"


def test_pyproject_includes_license_files_metadata() -> None:
    pyproject_data = load_pyproject_data()
    project_data = pyproject_data.get("project", {})

    license_files = project_data.get("license-files")
    assert license_files is not None
    assert "LICENSE" in license_files


def test_changelog_includes_initial_alpha_version() -> None:
    assert CHANGELOG_PATH.is_file(), "CHANGELOG.md must exist for PyPI Alpha release."

    changelog_text = CHANGELOG_PATH.read_text(encoding="utf-8")
    assert "## [0.1.0]" in changelog_text or "## 0.1.0" in changelog_text
    assert "Alpha" in changelog_text


def test_readme_has_no_relative_docs_links_outside_repository_navigation() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")
    readme_text_outside_repository_navigation = extract_text_before_heading(
        readme_text,
        REPOSITORY_NAVIGATION_HEADING,
    )
    relative_docs_links = RELATIVE_DOCS_LINK_PATTERN.findall(
        readme_text_outside_repository_navigation
    )

    assert relative_docs_links == [], (
        "README must use GitHub absolute links outside "
        f"'{REPOSITORY_NAVIGATION_HEADING}'."
    )
    assert REPOSITORY_NAVIGATION_HEADING in readme_text


def test_readme_documents_uv_first_workflow() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")

    missing_consumer_commands = collect_missing_substrings(
        readme_text,
        REQUIRED_UV_CONSUMER_COMMANDS,
    )
    missing_contributor_commands = collect_missing_substrings(
        readme_text,
        REQUIRED_UV_CONTRIBUTOR_COMMANDS,
    )

    assert missing_consumer_commands == [], (
        "README must document uv consumer commands. "
        f"Missing: {missing_consumer_commands}"
    )
    assert missing_contributor_commands == [], (
        "README must document uv contributor commands. "
        f"Missing: {missing_contributor_commands}"
    )
    assert REQUIRED_PIP_ALTERNATIVE_COMMAND in readme_text
    assert readme_text.index("uv add docguard") < readme_text.index(
        REQUIRED_PIP_ALTERNATIVE_COMMAND
    ), "README must show uv commands before pip alternatives."


def test_readme_links_to_pre_pypi_install_guide() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")

    assert REQUIRED_PRE_PYPI_INSTALL_GUIDE_URL in readme_text


def test_readme_includes_minimal_configuration_and_alpha_expectations() -> None:
    readme_text = README_PATH.read_text(encoding="utf-8")

    assert REQUIRED_TOOL_DOCGUARD_MARKER in readme_text
    assert REQUIRED_ALPHA_MARKER in readme_text
    assert GITHUB_DOCS_LINK_PATTERN.search(readme_text) is not None


def test_readme_passes_prose_style_guard() -> None:
    diagnostics = collect_readme_prose_style_diagnostics()
    diagnostic_messages = [
        f"{diagnostic.code} {diagnostic.message}" for diagnostic in diagnostics
    ]

    assert diagnostics == [], (
        "README failed prose style guard checks. "
        f"Violations: {diagnostic_messages}"
    )


def test_ci_workflow_exists_and_uses_uv() -> None:
    assert CI_WORKFLOW_PATH.is_file(), "CI workflow must exist for PyPI Alpha readiness."

    ci_workflow_text = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "astral-sh/setup-uv" in ci_workflow_text
    assert "python-version:" in ci_workflow_text or "matrix:" in ci_workflow_text
    assert "scripts/wheel_smoke.py" in ci_workflow_text
    assert "twine check" in ci_workflow_text


def test_publish_workflow_is_manual_dispatch_only() -> None:
    assert PUBLISH_WORKFLOW_PATH.is_file(), (
        "Publish workflow must exist for PyPI Alpha readiness."
    )

    publish_workflow_text = PUBLISH_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "workflow_dispatch" in publish_workflow_text
    assert "id-token: write" in publish_workflow_text
    assert "pypa/gh-action-pypi-publish" in publish_workflow_text
    assert "push:" not in publish_workflow_text.split("on:", maxsplit=1)[-1].split("jobs:", maxsplit=1)[0]
