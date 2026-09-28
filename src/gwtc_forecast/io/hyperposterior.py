from __future__ import annotations

from pathlib import Path
from typing import Any

SAFE_SUFFIXES = {".json", ".h5", ".hdf", ".hdf5", ".csv", ".dat", ".txt"}
UNSAFE_SUFFIXES = {".pickle", ".pkl"}


def discover_hyperposterior_files(root: Path) -> dict[str, Any]:
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(root)
    safe: list[dict[str, Any]] = []
    unsafe: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name == ".extraction_complete.json":
            continue
        suffix = path.suffix.lower()
        if suffix in UNSAFE_SUFFIXES:
            unsafe.append(str(path))
            continue
        if suffix in SAFE_SUFFIXES:
            safe.append(
                {
                    "path": str(path),
                    "suffix": suffix,
                    "size_bytes": path.stat().st_size,
                    "name_hint": path.stem.lower(),
                }
            )
    return {
        "root": str(root),
        "safe_candidates": sorted(safe, key=lambda item: item["path"]),
        "unsafe_pickle_candidates_not_loaded": sorted(unsafe),
    }


def inspect_bilby_result(path: Path) -> dict[str, Any]:
    try:
        from bilby.core.result import read_in_result
    except ImportError as exc:
        raise RuntimeError("Bilby is not installed") from exc
    result = read_in_result(filename=str(path))
    posterior = getattr(result, "posterior", None)
    if posterior is None:
        raise RuntimeError(f"Bilby result has no posterior table: {path}")
    return {
        "path": str(path),
        "label": getattr(result, "label", None),
        "posterior_rows": int(len(posterior)),
        "posterior_columns": [str(column) for column in posterior.columns],
        "log_evidence": float(getattr(result, "log_evidence", float("nan"))),
    }
