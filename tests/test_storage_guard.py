from __future__ import annotations

from dataclasses import replace

import pytest

from gwtc_forecast.config import load_project_config
from gwtc_forecast.storage import StorageGuardError, assert_external_storage


def test_mount_guard_rejects_plain_directory(tmp_path) -> None:
    project = load_project_config()
    storage = replace(
        project.storage,
        external_mount=tmp_path,
        root=tmp_path / "data",
        require_mountpoint=True,
        require_separate_device=False,
        minimum_free_gib=0.0,
    )
    guarded = replace(project, storage=storage)
    with pytest.raises(StorageGuardError, match="not a mounted filesystem"):
        assert_external_storage(guarded, write_test=False)
