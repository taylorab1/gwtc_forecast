from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import PilotManifest, ProjectConfig, ResolvedFile
from .paths import ProjectPaths
from .path_safety import safe_filename, safe_relative_child
from .storage import human_bytes
from .zenodo import fetch_record_json, make_session, parse_record_files


class PlanError(RuntimeError):
    """Raised when a pinned pilot file cannot be resolved safely."""


def raw_destination(paths: ProjectPaths, record_id: int, filename: str) -> Path:
    safe_name = safe_filename(filename, label="Zenodo filename")
    record_root = safe_relative_child(
        paths.raw, f"zenodo_{int(record_id)}", label="Zenodo record directory"
    )
    return safe_relative_child(record_root, safe_name, label="raw download destination")


def resolve_plan(
    *,
    config: ProjectConfig,
    manifest: PilotManifest,
    paths: ProjectPaths,
    refresh: bool,
    offline: bool,
) -> list[ResolvedFile]:
    session = make_session(config.download)
    record_ids = sorted({spec.record_id for spec in manifest.files})
    records: dict[int, dict[str, object]] = {}

    for record_id in record_ids:
        payload = fetch_record_json(
            session=session,
            record_id=record_id,
            cache_dir=paths.cache / "zenodo",
            download=config.download,
            refresh=refresh,
            offline=offline,
        )
        records[record_id] = parse_record_files(record_id, payload)

    resolved: list[ResolvedFile] = []
    for spec in manifest.files:
        available = records[spec.record_id]
        remote = available.get(spec.filename)
        if remote is None:
            raise PlanError(
                f"Pinned file is absent from Zenodo {spec.record_id}: {spec.filename}"
            )
        if spec.expected_md5:
            if not remote.md5:
                raise PlanError(f"Zenodo exposed no MD5 for {spec.filename}")
            if remote.md5 != spec.expected_md5:
                raise PlanError(
                    f"Release drift for {spec.filename}: Zenodo MD5 {remote.md5}, "
                    f"pinned MD5 {spec.expected_md5}. Audit before proceeding."
                )
        resolved.append(
            ResolvedFile(
                spec=spec,
                remote=remote,
                destination=raw_destination(paths, spec.record_id, spec.filename),
            )
        )
    return resolved


def plan_total_bytes(files: list[ResolvedFile]) -> int:
    return sum(item.remote.size_bytes for item in files)


def write_resolved_plan(
    *, manifest: PilotManifest, files: list[ResolvedFile], paths: ProjectPaths
) -> Path:
    paths.manifests.mkdir(parents=True, exist_ok=True)
    output = paths.manifests / f"{manifest.name}.resolved.json"
    payload = {
        "schema_version": 1,
        "name": manifest.name,
        "description": manifest.description,
        "resolved_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_bytes": plan_total_bytes(files),
        "total_human": human_bytes(plan_total_bytes(files)),
        "files": [
            {
                "spec": asdict(item.spec),
                "remote": asdict(item.remote),
                "destination": str(item.destination),
            }
            for item in files
        ],
    }
    tmp = output.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
    tmp.replace(output)
    return output
