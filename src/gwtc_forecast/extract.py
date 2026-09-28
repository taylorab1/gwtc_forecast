from __future__ import annotations

import json
import shutil
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from .downloader import file_is_verified, md5sum
from .models import ResolvedFile
from .path_safety import safe_filename, safe_relative_child
from .paths import ProjectPaths


class ExtractionError(RuntimeError):
    """Raised for unsafe or failed archive extraction."""


@dataclass(frozen=True)
class ArchivePreflight:
    member_count: int
    file_count: int
    unpacked_bytes: int
    expansion_ratio: float


DEFAULT_MAX_MEMBERS = 250_000
DEFAULT_MAX_UNPACKED_BYTES = 500 * 1024**3
DEFAULT_MAX_EXPANSION_RATIO = 200.0
EXTRA_FREE_SPACE_BYTES = 2 * 1024**3


def _safe_member(member: tarfile.TarInfo) -> bool:
    if member.name in {".", "./"}:
        return member.isdir()
    name = PurePosixPath(member.name)
    if name.is_absolute() or ".." in name.parts or not name.parts:
        return False
    # Reject links, devices, fifos, sparse special members, and any type that
    # could obtain semantics outside ordinary data-file extraction.
    return member.isfile() or member.isdir()


def _preflight_archive(
    archive: tarfile.TarFile,
    *,
    compressed_bytes: int,
    max_members: int = DEFAULT_MAX_MEMBERS,
    max_unpacked_bytes: int = DEFAULT_MAX_UNPACKED_BYTES,
    max_expansion_ratio: float = DEFAULT_MAX_EXPANSION_RATIO,
) -> tuple[list[tarfile.TarInfo], ArchivePreflight]:
    if max_members <= 0 or max_unpacked_bytes <= 0 or max_expansion_ratio <= 0.0:
        raise ValueError("archive limits must be positive")
    members = archive.getmembers()
    if len(members) > max_members:
        raise ExtractionError(
            f"Archive contains {len(members)} members; limit is {max_members}"
        )

    unsafe = [member.name for member in members if not _safe_member(member)]
    if unsafe:
        raise ExtractionError(f"Unsafe archive members: {unsafe[:5]}")

    normalized_names: set[str] = set()
    duplicate_names: list[str] = []
    unpacked_bytes = 0
    file_count = 0
    for member in members:
        normalized = PurePosixPath(member.name).as_posix().rstrip("/")
        if normalized in normalized_names:
            duplicate_names.append(normalized)
        normalized_names.add(normalized)
        if member.isfile():
            file_count += 1
            if member.size < 0:
                raise ExtractionError(f"Archive member has negative size: {member.name}")
            unpacked_bytes += int(member.size)
            if unpacked_bytes > max_unpacked_bytes:
                raise ExtractionError(
                    f"Archive expands beyond configured limit of {max_unpacked_bytes} bytes"
                )
    if duplicate_names:
        raise ExtractionError(
            f"Archive contains duplicate normalized member names: {duplicate_names[:5]}"
        )

    expansion_ratio = unpacked_bytes / max(int(compressed_bytes), 1)
    if expansion_ratio > max_expansion_ratio:
        raise ExtractionError(
            f"Archive expansion ratio {expansion_ratio:.1f} exceeds "
            f"configured limit {max_expansion_ratio:.1f}"
        )
    return members, ArchivePreflight(
        member_count=len(members),
        file_count=file_count,
        unpacked_bytes=unpacked_bytes,
        expansion_ratio=float(expansion_ratio),
    )


def _completion_marker(target: Path) -> Path:
    return target / ".extraction_complete.json"


def _already_complete(item: ResolvedFile, target: Path) -> bool:
    marker = _completion_marker(target)
    if not marker.is_file():
        return False
    try:
        payload = json.loads(marker.read_text())
    except (OSError, ValueError):
        return False
    expected = item.spec.expected_md5 or item.remote.md5
    return payload.get("archive") == str(item.destination) and payload.get(
        "archive_md5"
    ) == expected


def extract_one(item: ResolvedFile, paths: ProjectPaths) -> None:
    if not item.spec.extract or not item.spec.extract_subdir:
        return
    if not item.destination.is_file():
        raise ExtractionError(f"Archive is missing: {item.destination}")
    if not file_is_verified(item):
        raise ExtractionError(
            f"Archive has not passed size/checksum verification: {item.destination}"
        )

    target = safe_relative_child(
        paths.extracted,
        item.spec.extract_subdir,
        label=f"extraction target for {item.spec.role}",
    )
    if _already_complete(item, target):
        print(f"SKIP extracted: {target}")
        return

    role = safe_filename(item.spec.role, label="manifest role")
    temp = safe_relative_child(
        paths.tmp / "extract", f"{role}.partial", label="temporary extraction path"
    )
    if temp.exists():
        shutil.rmtree(temp)
    temp.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(item.destination, "r:*") as archive:
            members, preflight = _preflight_archive(
                archive, compressed_bytes=item.destination.stat().st_size
            )
            existing_target_bytes = 0
            if target.exists():
                existing_target_bytes = sum(
                    path.stat().st_size
                    for path in target.rglob("*")
                    if path.is_file() and not path.is_symlink()
                )
            free = shutil.disk_usage(paths.root).free
            required = (
                preflight.unpacked_bytes
                + existing_target_bytes
                + EXTRA_FREE_SPACE_BYTES
            )
            if free < required:
                raise ExtractionError(
                    f"Not enough free space to extract {item.destination.name}: "
                    f"{free} bytes free, {required} required from archive preflight"
                )
            try:
                archive.extractall(temp, members=members, filter="data")
            except TypeError:
                # Python <3.12 compatibility; member-type and path checks above
                # remain the enforced extraction policy.
                archive.extractall(temp, members=members)

        expected = item.spec.expected_md5 or item.remote.md5 or md5sum(item.destination)
        marker_payload = {
            "archive": str(item.destination),
            "archive_md5": expected,
            "archive_member_count": preflight.member_count,
            "archive_file_count": preflight.file_count,
            "archive_unpacked_bytes": preflight.unpacked_bytes,
            "archive_expansion_ratio": preflight.expansion_ratio,
            "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        (temp / ".extraction_complete.json").write_text(
            json.dumps(marker_payload, indent=2, sort_keys=True)
        )

        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = target.with_name(target.name + ".old")
            if backup.exists():
                shutil.rmtree(backup)
            target.rename(backup)
            try:
                temp.rename(target)
            except Exception:
                backup.rename(target)
                raise
            shutil.rmtree(backup)
        else:
            temp.rename(target)
        print(f"EXTRACTED: {item.destination.name} -> {target}")
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def extract_plan(files: list[ResolvedFile], paths: ProjectPaths) -> None:
    for item in files:
        if item.spec.extract:
            extract_one(item, paths)
