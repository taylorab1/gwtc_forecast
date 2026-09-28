from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import h5py

from .downloader import file_is_verified, md5sum
from .models import ResolvedFile
from .paths import ProjectPaths


class VerificationError(RuntimeError):
    """Raised when the pilot dataset is incomplete or corrupt."""


def _hdf5_signature_ok(path: Path) -> bool | None:
    if path.suffix.lower() not in {".hdf", ".h5", ".hdf5"}:
        return None
    try:
        with h5py.File(path, "r"):
            return True
    except OSError:
        return False


def verify_files(files: list[ResolvedFile], paths: ProjectPaths) -> Path:
    results: list[dict[str, object]] = []
    failures: list[str] = []

    for item in files:
        exists = item.destination.is_file()
        size_ok = exists and item.destination.stat().st_size == item.remote.size_bytes
        expected = item.spec.expected_md5 or item.remote.md5
        observed_md5 = md5sum(item.destination) if size_ok and expected else None
        md5_ok = expected is None or observed_md5 == expected
        hdf5_ok = _hdf5_signature_ok(item.destination) if exists else None
        verified = bool(
            exists
            and size_ok
            and md5_ok
            and hdf5_ok is not False
            and file_is_verified(item)
        )

        extraction_ok: bool | None = None
        extraction_path: str | None = None
        if item.spec.extract and item.spec.extract_subdir:
            extraction = paths.extracted / item.spec.extract_subdir
            extraction_path = str(extraction)
            extraction_ok = (extraction / ".extraction_complete.json").is_file()

        results.append(
            {
                "role": item.spec.role,
                "filename": item.remote.filename,
                "path": str(item.destination),
                "exists": exists,
                "size_ok": size_ok,
                "expected_md5": expected,
                "observed_md5": observed_md5,
                "md5_ok": md5_ok,
                "hdf5_signature_ok": hdf5_ok,
                "verified": verified,
                "extraction_path": extraction_path,
                "extraction_ok": extraction_ok,
            }
        )
        if not verified:
            failures.append(item.remote.filename)

    paths.manifests.mkdir(parents=True, exist_ok=True)
    report = paths.manifests / "pilot_verification_report.json"
    payload = {
        "schema": "gwtc_forecast.verification.v1",
        "status": "PASS" if not failures else "FAIL",
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "all_raw_files_verified": not failures,
        "failures": failures,
        "files": results,
    }
    tmp = report.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(report)

    if failures:
        raise VerificationError(
            f"{len(failures)} pilot file(s) failed verification. See {report}"
        )
    return report
