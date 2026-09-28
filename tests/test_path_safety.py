from __future__ import annotations

from dataclasses import replace

import pytest

from gwtc_forecast.config import load_project_config
from gwtc_forecast.path_safety import PathSafetyError, safe_filename
from gwtc_forecast.paths import ProjectPaths
from gwtc_forecast.planner import raw_destination


def test_layout_parent_traversal_is_rejected(tmp_path) -> None:
    project = load_project_config()
    project = replace(
        project,
        storage=replace(project.storage, root=tmp_path / "root"),
        layout=replace(project.layout, raw="../escape"),
    )
    with pytest.raises(PathSafetyError, match="parent traversal"):
        ProjectPaths.from_config(project)


def test_raw_destination_rejects_manifest_path_in_filename(tmp_path) -> None:
    project = load_project_config()
    project = replace(project, storage=replace(project.storage, root=tmp_path / "root"))
    paths = ProjectPaths.from_config(project)
    with pytest.raises(PathSafetyError, match="directory path"):
        raw_destination(paths, 123, "../outside.h5")


def test_safe_filename_accepts_ordinary_release_name() -> None:
    assert safe_filename("release-file.tar.gz") == "release-file.tar.gz"
