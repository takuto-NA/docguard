"""Shared pytest fixtures for docguard tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def temporary_project_directory(tmp_path: Path) -> Path:
    return tmp_path
