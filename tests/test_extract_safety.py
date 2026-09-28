from __future__ import annotations

import io
import tarfile

import pytest

from gwtc_forecast.extract import ExtractionError, _preflight_archive, _safe_member


def test_archive_member_safety() -> None:
    safe = tarfile.TarInfo("directory/file.txt")
    safe.type = tarfile.REGTYPE
    unsafe_parent = tarfile.TarInfo("../escape.txt")
    unsafe_parent.type = tarfile.REGTYPE
    unsafe_link = tarfile.TarInfo("link")
    unsafe_link.type = tarfile.SYMTYPE
    assert _safe_member(safe)
    assert not _safe_member(unsafe_parent)
    assert not _safe_member(unsafe_link)


def test_archive_preflight_rejects_excessive_expansion(tmp_path) -> None:
    archive_path = tmp_path / "large-ratio.tar"
    content = b"x" * 128
    with tarfile.open(archive_path, "w") as archive:
        member = tarfile.TarInfo("file.bin")
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))
    with tarfile.open(archive_path, "r") as archive:
        with pytest.raises(ExtractionError, match="expansion ratio"):
            _preflight_archive(
                archive,
                compressed_bytes=1,
                max_members=10,
                max_unpacked_bytes=1024,
                max_expansion_ratio=2.0,
            )


def test_archive_preflight_rejects_duplicate_names(tmp_path) -> None:
    archive_path = tmp_path / "duplicate.tar"
    with tarfile.open(archive_path, "w") as archive:
        for payload in (b"one", b"two"):
            member = tarfile.TarInfo("same.txt")
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    with tarfile.open(archive_path, "r") as archive:
        with pytest.raises(ExtractionError, match="duplicate"):
            _preflight_archive(archive, compressed_bytes=archive_path.stat().st_size)
