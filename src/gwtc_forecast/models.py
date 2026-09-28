from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StorageConfig:
    external_mount: Path
    root: Path
    require_mountpoint: bool
    require_separate_device: bool
    minimum_free_gib: float


@dataclass(frozen=True)
class LayoutConfig:
    raw: str
    extracted: str
    processed: str
    results: str
    cache: str
    manifests: str
    logs: str
    tmp: str


@dataclass(frozen=True)
class DownloadConfig:
    chunk_mib: int
    connect_timeout_seconds: int
    read_timeout_seconds: int
    max_attempts: int
    user_agent: str


@dataclass(frozen=True)
class GuardConfig:
    max_repository_file_mib: int


@dataclass(frozen=True)
class ProjectConfig:
    storage: StorageConfig
    layout: LayoutConfig
    download: DownloadConfig
    guards: GuardConfig


@dataclass(frozen=True)
class FileSpec:
    record_id: int
    filename: str
    role: str
    category: str
    extract: bool
    extract_subdir: str | None = None
    expected_md5: str | None = None
    run: str | None = None
    event_id: str | None = None


@dataclass(frozen=True)
class PilotManifest:
    name: str
    description: str
    files: tuple[FileSpec, ...]


@dataclass(frozen=True)
class NumericalGates:
    minimum_event_ess: float
    minimum_selection_ess: float
    maximum_joint_prequential_difference: float
    maximum_mc_sigma_delta_s: float
    maximum_fractional_mc_error: float


@dataclass(frozen=True)
class ProductionGates:
    pe_labels_frozen: bool
    pe_priors_validated: bool
    injection_mapping_validated: bool
    selection_reference_validated: bool
    released_models_validated: bool
    mock_calibration_passed: bool

    def all_real_data_gates_pass(self) -> bool:
        return all(
            (
                self.pe_labels_frozen,
                self.pe_priors_validated,
                self.injection_mapping_validated,
                self.selection_reference_validated,
                self.released_models_validated,
                self.mock_calibration_passed,
            )
        )


@dataclass(frozen=True)
class ScienceConfig:
    name: str
    primary_question: str
    real_data_scoring_enabled: bool
    events: tuple[str, ...]
    chronological_order: tuple[str, ...]
    models: tuple[str, ...]
    runs: tuple[str, ...]
    coordinates: dict[str, str]
    numerical_gates: NumericalGates
    production_gates: ProductionGates


@dataclass(frozen=True)
class RemoteFile:
    record_id: int
    filename: str
    size_bytes: int
    md5: str | None
    url: str
    record_version: str | None
    record_doi: str | None


@dataclass(frozen=True)
class ResolvedFile:
    spec: FileSpec
    remote: RemoteFile
    destination: Path
