from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import ProjectConfig
from .path_safety import safe_relative_child


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    raw: Path
    extracted: Path
    processed: Path
    results: Path
    cache: Path
    manifests: Path
    logs: Path
    tmp: Path

    @classmethod
    def from_config(cls, config: ProjectConfig) -> "ProjectPaths":
        root = config.storage.root.expanduser().resolve(strict=False)
        layout = config.layout
        paths = cls(
            root=root,
            raw=safe_relative_child(root, layout.raw, label="layout.raw"),
            extracted=safe_relative_child(
                root, layout.extracted, label="layout.extracted"
            ),
            processed=safe_relative_child(
                root, layout.processed, label="layout.processed"
            ),
            results=safe_relative_child(root, layout.results, label="layout.results"),
            cache=safe_relative_child(root, layout.cache, label="layout.cache"),
            manifests=safe_relative_child(
                root, layout.manifests, label="layout.manifests"
            ),
            logs=safe_relative_child(root, layout.logs, label="layout.logs"),
            tmp=safe_relative_child(root, layout.tmp, label="layout.tmp"),
        )
        managed = (
            paths.raw,
            paths.extracted,
            paths.processed,
            paths.results,
            paths.cache,
            paths.manifests,
            paths.logs,
            paths.tmp,
        )
        if len(set(managed)) != len(managed):
            raise ValueError("configured project layout paths must be distinct")
        return paths

    def create(self) -> None:
        for path in (
            self.root,
            self.raw,
            self.extracted,
            self.processed,
            self.results,
            self.cache,
            self.manifests,
            self.logs,
            self.tmp,
            self.tmp / "runtime",
            self.tmp / "jupyter-runtime",
            self.tmp / "joblib",
            self.cache / "xdg",
            self.cache / "matplotlib",
            self.cache / "numba",
        ):
            path.mkdir(parents=True, exist_ok=True)

    def as_environment(self) -> dict[str, str]:
        return {
            "GWTC_DATA_ROOT": str(self.root),
            "GWTC_RAW_ROOT": str(self.raw),
            "GWTC_EXTRACTED_ROOT": str(self.extracted),
            "GWTC_PROCESSED_ROOT": str(self.processed),
            "GWTC_RESULTS_ROOT": str(self.results),
            "GWTC_CACHE_ROOT": str(self.cache),
            "GWTC_MANIFESTS_ROOT": str(self.manifests),
            "GWTC_LOGS_ROOT": str(self.logs),
            "GWTC_TMP_ROOT": str(self.tmp),
            "TMPDIR": str(self.tmp / "runtime"),
            "XDG_CACHE_HOME": str(self.cache / "xdg"),
            "MPLCONFIGDIR": str(self.cache / "matplotlib"),
            "JUPYTER_RUNTIME_DIR": str(self.tmp / "jupyter-runtime"),
            "NUMBA_CACHE_DIR": str(self.cache / "numba"),
            "JOBLIB_TEMP_FOLDER": str(self.tmp / "joblib"),
        }
