"""Pytest adapter for docguard."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.config import ConfigurationError, find_project_root, load_docguard_configuration
from docguard.constants import EXIT_CODE_CONFIGURATION_FAILURE
from docguard.diagnostics import Diagnostic
from docguard.formatters import format_document_diagnostics_human
from docguard.runner import DocguardConfigurationFailure, run_docguard_checks

DOCGUARD_COLLECTOR_NAME = "docguard"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--docguard",
        action="store_true",
        default=False,
        help="Run docguard checks against configured Markdown documents.",
    )
    parser.addoption(
        "--docguard-only",
        action="store_true",
        default=False,
        help="Run only docguard document checks without normal Python tests.",
    )


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--docguard") or config.getoption("--docguard-only"):
        config.addinivalue_line(
            "markers",
            "docguard: docguard document structure check",
        )


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    docguard_only_enabled = config.getoption("--docguard-only")
    docguard_enabled = config.getoption("--docguard")
    if not docguard_enabled and not docguard_only_enabled:
        return

    if docguard_only_enabled:
        items.clear()

    docguard_collector = DocguardRootCollector.from_parent(
        session,
        name=DOCGUARD_COLLECTOR_NAME,
    )
    items.extend(docguard_collector.collect())


class DocguardRootCollector(pytest.Collector):
    def collect(self) -> list[pytest.Item]:
        project_root = find_project_root(self.config.rootpath)
        if project_root is None:
            project_root = self.config.rootpath.resolve()

        try:
            configuration = load_docguard_configuration(
                project_root=project_root,
                config_path=None,
                cli_paths=tuple(),
            )
            run_result = run_docguard_checks(configuration)
        except (ConfigurationError, DocguardConfigurationFailure) as error:
            pytest.exit(str(error), returncode=EXIT_CODE_CONFIGURATION_FAILURE)

        diagnostics_by_document: dict[str, list[Diagnostic]] = {}
        for diagnostic in run_result.diagnostics:
            diagnostics_by_document.setdefault(diagnostic.document_path, []).append(
                diagnostic
            )

        collected_items: list[pytest.Item] = []
        for document_path in run_result.checked_document_paths:
            collected_items.append(
                DocguardMarkdownItem.from_parent(
                    self,
                    name=f"{document_path}::docguard",
                    document_path=document_path,
                    diagnostics=tuple(diagnostics_by_document.get(document_path, [])),
                )
            )
        return collected_items


class DocguardMarkdownItem(pytest.Item):
    def __init__(
        self,
        name: str,
        parent: pytest.Collector,
        document_path: str,
        diagnostics: tuple[Diagnostic, ...],
        **kwargs: object,
    ) -> None:
        super().__init__(name, parent, **kwargs)
        self.document_path = document_path
        self.diagnostics = diagnostics

    def runtest(self) -> None:
        if not self.diagnostics:
            return
        failure_message = format_document_diagnostics_human(
            self.document_path,
            self.diagnostics,
        )
        pytest.fail(failure_message)

    def reportinfo(self) -> tuple[Path, int | None, str]:
        return self.config.rootpath / self.document_path, None, "docguard"
