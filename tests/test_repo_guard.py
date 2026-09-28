from __future__ import annotations

from gwtc_forecast.repo_guard import audit_repository


def test_repository_guard_rejects_data_artifacts(tmp_path) -> None:
    (tmp_path / "result.hdf5").write_bytes(b"test")
    violations = audit_repository(tmp_path, max_file_mib=20)
    assert any("scientific data artifact" in item for item in violations)


def test_repository_guard_accepts_source_tree(tmp_path) -> None:
    (tmp_path / "module.py").write_text("x = 1\n")
    assert audit_repository(tmp_path, max_file_mib=20) == []
