from __future__ import annotations

from pathlib import Path

FORBIDDEN_SUFFIXES = {
    ".h5",
    ".hdf",
    ".hdf5",
    ".fits",
    ".npy",
    ".npz",
    ".parquet",
    ".pickle",
    ".pkl",
    ".part",
}
FORBIDDEN_NAMES = {"raw", "extracted", "processed", "results", "cache", "logs", "tmp"}
IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}


def audit_repository(root: Path, max_file_mib: int) -> list[str]:
    violations: list[str] = []
    limit = max_file_mib * 1024**2
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_dir():
            if path.name in FORBIDDEN_NAMES:
                violations.append(f"forbidden data/result directory: {relative}")
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            violations.append(f"forbidden scientific data artifact: {relative}")
        try:
            if path.stat().st_size > limit:
                violations.append(
                    f"file exceeds {max_file_mib} MiB repository limit: {relative}"
                )
        except FileNotFoundError:
            continue
    return sorted(set(violations))


def repository_code_size(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_file():
            total += path.stat().st_size
    return total
