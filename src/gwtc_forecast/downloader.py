from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import requests

from .models import DownloadConfig, ResolvedFile
from .storage import human_bytes
from .zenodo import make_session


class DownloadError(RuntimeError):
    """Raised when a file cannot be downloaded or verified."""


def md5sum(path: Path, chunk_bytes: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_is_verified(item: ResolvedFile) -> bool:
    path = item.destination
    if not path.is_file() or path.stat().st_size != item.remote.size_bytes:
        return False
    expected = item.spec.expected_md5 or item.remote.md5
    return expected is None or md5sum(path) == expected


def remaining_bytes(item: ResolvedFile) -> int:
    if file_is_verified(item):
        return 0
    partial = item.destination.with_name(item.destination.name + ".part")
    existing = partial.stat().st_size if partial.exists() else 0
    return max(0, item.remote.size_bytes - min(existing, item.remote.size_bytes))


def _verify_finished(item: ResolvedFile) -> None:
    path = item.destination
    observed_size = path.stat().st_size
    if observed_size != item.remote.size_bytes:
        raise DownloadError(
            f"Size mismatch for {path.name}: {observed_size} != {item.remote.size_bytes}"
        )
    expected = item.spec.expected_md5 or item.remote.md5
    if expected:
        observed = md5sum(path)
        if observed != expected:
            path.unlink(missing_ok=True)
            raise DownloadError(
                f"MD5 mismatch for {path.name}: {observed} != {expected}"
            )


def download_one(
    *, session: requests.Session, item: ResolvedFile, config: DownloadConfig
) -> None:
    path = item.destination
    path.parent.mkdir(parents=True, exist_ok=True)

    if file_is_verified(item):
        print(f"SKIP verified: {path}")
        return

    partial = path.with_name(path.name + ".part")
    if partial.exists() and partial.stat().st_size > item.remote.size_bytes:
        partial.unlink()

    last_error: Exception | None = None
    for attempt in range(1, config.max_attempts + 1):
        start = partial.stat().st_size if partial.exists() else 0
        headers = {"Range": f"bytes={start}-"} if start else {}
        try:
            with session.get(
                item.remote.url,
                headers=headers,
                stream=True,
                timeout=(config.connect_timeout_seconds, config.read_timeout_seconds),
                allow_redirects=True,
            ) as response:
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    delay = (
                        int(retry_after)
                        if retry_after and retry_after.isdigit()
                        else min(60, 2**attempt)
                    )
                    time.sleep(delay)
                    continue
                if response.status_code == 416 and start == item.remote.size_bytes:
                    partial.replace(path)
                    _verify_finished(item)
                    return
                response.raise_for_status()

                append = start > 0 and response.status_code == 206
                if start > 0 and not append:
                    start = 0
                mode = "ab" if append else "wb"
                written = start
                last_report = time.monotonic()

                with partial.open(mode) as output:
                    for chunk in response.iter_content(
                        chunk_size=config.chunk_mib * 1024 * 1024
                    ):
                        if not chunk:
                            continue
                        output.write(chunk)
                        written += len(chunk)
                        now = time.monotonic()
                        if now - last_report >= 10:
                            percent = (
                                100.0 * written / item.remote.size_bytes
                                if item.remote.size_bytes
                                else 0.0
                            )
                            print(
                                f"  {path.name}: {human_bytes(written)} / "
                                f"{human_bytes(item.remote.size_bytes)} ({percent:.1f}%)"
                            )
                            last_report = now
                    output.flush()
                    os.fsync(output.fileno())

            if partial.stat().st_size != item.remote.size_bytes:
                raise DownloadError(
                    f"Incomplete file {path.name}: {partial.stat().st_size} / "
                    f"{item.remote.size_bytes} bytes"
                )
            partial.replace(path)
            _verify_finished(item)
            print(f"DONE: {path} ({human_bytes(item.remote.size_bytes)})")
            return
        except (requests.RequestException, OSError, DownloadError) as exc:
            last_error = exc
            if attempt < config.max_attempts:
                delay = min(60, 2**attempt)
                print(f"Retry {attempt}/{config.max_attempts} for {path.name}: {exc}")
                time.sleep(delay)

    raise DownloadError(
        f"Failed to download {path.name} after {config.max_attempts} attempts: "
        f"{last_error}"
    )


def download_plan(files: list[ResolvedFile], config: DownloadConfig) -> None:
    session = make_session(config)
    for index, item in enumerate(files, start=1):
        print(
            f"\n[{index}/{len(files)}] {item.spec.role}: {item.remote.filename} "
            f"({human_bytes(item.remote.size_bytes)})"
        )
        download_one(session=session, item=item, config=config)
