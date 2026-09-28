from __future__ import annotations

from pathlib import Path, PurePath


class PathSafetyError(ValueError):
    """Raised when untrusted configuration would escape an approved root."""


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def require_within(path: Path, root: Path, *, label: str) -> Path:
    candidate = _resolved(path)
    approved = _resolved(root)
    try:
        candidate.relative_to(approved)
    except ValueError as exc:
        raise PathSafetyError(f"{label} escapes approved root {approved}: {candidate}") from exc
    return candidate


def validate_relative_path(value: str | Path, *, label: str) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        raise PathSafetyError(f"{label} must be relative, not absolute: {raw}")
    if not raw.parts or raw == Path("."):
        raise PathSafetyError(f"{label} must not be empty")
    if ".." in raw.parts:
        raise PathSafetyError(f"{label} contains parent traversal: {raw}")
    return raw


def safe_relative_child(root: Path, value: str | Path, *, label: str) -> Path:
    raw = validate_relative_path(value, label=label)
    return require_within(Path(root) / raw, Path(root), label=label)


def safe_filename(value: str, *, label: str = "filename") -> str:
    if not value or "\x00" in value:
        raise PathSafetyError(f"{label} must be a non-empty ordinary filename")
    raw = PurePath(value)
    if raw.is_absolute() or len(raw.parts) != 1 or raw.name in {".", ".."}:
        raise PathSafetyError(f"{label} must not contain a directory path: {value!r}")
    return raw.name
