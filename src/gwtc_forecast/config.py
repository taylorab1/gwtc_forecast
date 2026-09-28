from __future__ import annotations

import os
import tomllib
from importlib.resources import files
from pathlib import Path
from typing import Any

from .path_safety import safe_filename, validate_relative_path
from .models import (
    DownloadConfig,
    FileSpec,
    GuardConfig,
    LayoutConfig,
    NumericalGates,
    PilotManifest,
    ProductionGates,
    ProjectConfig,
    ScienceConfig,
    StorageConfig,
)


def _read_path(path: Path) -> tuple[dict[str, Any], str]:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream), str(path)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Configuration file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise RuntimeError(f"Invalid TOML in {path}: {exc}") from exc


def _read_selected_toml(
    *,
    explicit: Path | None,
    environment_name: str,
    local_name: str,
    packaged_name: str,
) -> tuple[dict[str, Any], str]:
    if explicit is not None:
        return _read_path(explicit.expanduser().resolve())
    environment_value = os.environ.get(environment_name)
    if environment_value:
        return _read_path(Path(environment_value).expanduser().resolve())
    local = Path.cwd() / "config" / local_name
    if local.exists():
        return _read_path(local.resolve())

    resource = files("gwtc_forecast").joinpath("defaults", packaged_name)
    label = f"package:gwtc_forecast/defaults/{packaged_name}"
    try:
        return tomllib.loads(resource.read_text()), label
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError(f"Unable to read {label}: {exc}") from exc


def load_project_config(path: Path | None = None) -> ProjectConfig:
    data, source = _read_selected_toml(
        explicit=path,
        environment_name="GWTC_PROJECT_CONFIG",
        local_name="project.toml",
        packaged_name="project.toml",
    )
    if int(data.get("schema_version", -1)) != 1:
        raise RuntimeError(f"Unsupported project config schema in {source}")

    storage = data["storage"]
    layout = data["layout"]
    download = data["download"]
    guards = data["guards"]
    return ProjectConfig(
        storage=StorageConfig(
            external_mount=Path(storage["external_mount"]).expanduser(),
            root=Path(storage["root"]).expanduser(),
            require_mountpoint=bool(storage["require_mountpoint"]),
            require_separate_device=bool(storage["require_separate_device"]),
            minimum_free_gib=float(storage["minimum_free_gib"]),
        ),
        layout=LayoutConfig(**{key: str(value) for key, value in layout.items()}),
        download=DownloadConfig(
            chunk_mib=int(download["chunk_mib"]),
            connect_timeout_seconds=int(download["connect_timeout_seconds"]),
            read_timeout_seconds=int(download["read_timeout_seconds"]),
            max_attempts=int(download["max_attempts"]),
            user_agent=str(download["user_agent"]),
        ),
        guards=GuardConfig(
            max_repository_file_mib=int(guards["max_repository_file_mib"])
        ),
    )


def load_pilot_manifest(path: Path | None = None) -> PilotManifest:
    data, source = _read_selected_toml(
        explicit=path,
        environment_name="GWTC_PILOT_MANIFEST",
        local_name="pilot_manifest.toml",
        packaged_name="pilot_manifest.toml",
    )
    if int(data.get("schema_version", -1)) != 1:
        raise RuntimeError(f"Unsupported pilot manifest schema in {source}")

    specs: list[FileSpec] = []
    for raw in data.get("files", []):
        filename = safe_filename(str(raw["filename"]), label="manifest filename")
        extract_subdir = None
        if raw.get("extract_subdir") is not None:
            extract_subdir = str(
                validate_relative_path(
                    str(raw["extract_subdir"]), label="manifest extract_subdir"
                )
            )
        extract = bool(raw["extract"])
        if extract and extract_subdir is None:
            raise RuntimeError(
                f"Manifest entry {filename} requests extraction without extract_subdir"
            )
        if not extract and extract_subdir is not None:
            raise RuntimeError(
                f"Manifest entry {filename} sets extract_subdir but extract=false"
            )
        specs.append(
            FileSpec(
                record_id=int(raw["record_id"]),
                filename=filename,
                role=str(raw["role"]),
                category=str(raw["category"]),
                extract=extract,
                extract_subdir=extract_subdir,
                expected_md5=(
                    str(raw["expected_md5"]).lower()
                    if raw.get("expected_md5")
                    else None
                ),
                run=str(raw["run"]) if raw.get("run") is not None else None,
                event_id=(
                    str(raw["event_id"]) if raw.get("event_id") is not None else None
                ),
            )
        )
    if not specs:
        raise RuntimeError(f"Pilot manifest contains no files: {source}")
    return PilotManifest(
        name=str(data["name"]),
        description=str(data["description"]),
        files=tuple(specs),
    )


def load_science_config(path: Path | None = None) -> ScienceConfig:
    data, source = _read_selected_toml(
        explicit=path,
        environment_name="GWTC_SCIENCE_CONFIG",
        local_name="science.toml",
        packaged_name="science.toml",
    )
    if int(data.get("schema_version", -1)) != 1:
        raise RuntimeError(f"Unsupported science config schema in {source}")
    pilot = data["pilot"]
    ng = data["numerical_gates"]
    pg = data["production_gates"]
    return ScienceConfig(
        name=str(data["name"]),
        primary_question=str(data["primary_question"]),
        real_data_scoring_enabled=bool(data["real_data_scoring_enabled"]),
        events=tuple(str(x) for x in pilot["events"]),
        chronological_order=tuple(str(x) for x in pilot["chronological_order"]),
        models=tuple(str(x) for x in pilot["models"]),
        runs=tuple(str(x) for x in pilot["runs"]),
        coordinates={str(k): str(v) for k, v in data["coordinates"].items()},
        numerical_gates=NumericalGates(
            minimum_event_ess=float(ng["minimum_event_ess"]),
            minimum_selection_ess=float(ng["minimum_selection_ess"]),
            maximum_joint_prequential_difference=float(
                ng["maximum_joint_prequential_difference"]
            ),
            maximum_mc_sigma_delta_s=float(ng["maximum_mc_sigma_delta_s"]),
            maximum_fractional_mc_error=float(ng["maximum_fractional_mc_error"]),
        ),
        production_gates=ProductionGates(
            pe_labels_frozen=bool(pg["pe_labels_frozen"]),
            pe_priors_validated=bool(pg["pe_priors_validated"]),
            injection_mapping_validated=bool(pg["injection_mapping_validated"]),
            selection_reference_validated=bool(pg["selection_reference_validated"]),
            released_models_validated=bool(pg["released_models_validated"]),
            mock_calibration_passed=bool(pg["mock_calibration_passed"]),
        ),
    )
