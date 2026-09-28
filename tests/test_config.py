from __future__ import annotations

from pathlib import Path

from gwtc_forecast.config import (
    load_pilot_manifest,
    load_project_config,
    load_science_config,
)
from gwtc_forecast.paths import ProjectPaths


def test_packaged_configuration_is_self_consistent() -> None:
    project = load_project_config()
    manifest = load_pilot_manifest()
    science = load_science_config()
    paths = ProjectPaths.from_config(project)

    assert project.storage.root == Path("/media/oamacias/LaCie/GW_Project_Data")
    assert paths.raw.parent == paths.root
    assert len(science.events) == 5
    assert set(science.events) == {
        spec.event_id for spec in manifest.files if spec.event_id is not None
    }
    assert not science.real_data_scoring_enabled
    assert not science.production_gates.all_real_data_gates_pass()


def test_manifest_excludes_known_large_unneeded_archive() -> None:
    manifest = load_pilot_manifest()
    filenames = {spec.filename for spec in manifest.files}
    assert "popsummary_files.tar.gz" not in filenames
    assert "samples-rpo4ab-1366933504-55469568-clipped.hdf" in filenames
