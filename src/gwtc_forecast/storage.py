from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from .models import ProjectConfig
from .paths import ProjectPaths


class StorageGuardError(RuntimeError):
    """Raised when the external data location is not demonstrably safe."""


def human_bytes(nbytes: int) -> str:
    value = float(nbytes)
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    raise AssertionError("unreachable")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def assert_external_storage(config: ProjectConfig, *, write_test: bool) -> None:
    mount = config.storage.external_mount
    root = config.storage.root

    if not mount.exists():
        raise StorageGuardError(
            f"Safety stop: external mount does not exist: {mount}. Connect the LaCie disk."
        )
    if config.storage.require_mountpoint and not os.path.ismount(mount):
        raise StorageGuardError(
            f"Safety stop: {mount} exists but is not a mounted filesystem. "
            "Writing now could fill the laptop."
        )
    if not _is_relative_to(root, mount):
        raise StorageGuardError(f"Data root {root} is not inside external mount {mount}")
    if config.storage.require_separate_device:
        if Path("/").stat().st_dev == mount.stat().st_dev:
            raise StorageGuardError(
                f"Safety stop: {mount} is on the same device as /. "
                "The external disk may not be mounted."
            )
    if not os.access(mount, os.W_OK | os.X_OK):
        raise StorageGuardError(f"External mount is not writable: {mount}")

    if write_test:
        root.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                prefix=".gwtc-write-test-",
                dir=root,
                delete=True,
            ) as stream:
                stream.write("external-storage-write-test\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as exc:
            raise StorageGuardError(f"Cannot write to external root {root}: {exc}") from exc


def free_bytes(config: ProjectConfig) -> int:
    target = config.storage.root if config.storage.root.exists() else config.storage.external_mount
    return shutil.disk_usage(target).free


def required_minimum_bytes(config: ProjectConfig) -> int:
    return int(config.storage.minimum_free_gib * 1024**3)


def bootstrap_storage(config: ProjectConfig) -> ProjectPaths:
    assert_external_storage(config, write_test=True)
    paths = ProjectPaths.from_config(config)
    paths.create()
    for path in paths.as_environment().values():
        candidate = Path(path)
        if candidate.suffix == "" and candidate != paths.root:
            candidate.mkdir(parents=True, exist_ok=True)
    marker = paths.root / ".gwtc_external_data_root"
    marker.write_text(
        "External data/results root for the GWTC catalog-to-catalog forecast.\n"
        "Large/generated files must not be placed in the Git repository.\n"
    )
    if free_bytes(config) < required_minimum_bytes(config):
        raise StorageGuardError(
            "External disk has less than the configured minimum free space "
            f"({config.storage.minimum_free_gib:.1f} GiB)."
        )
    return paths
