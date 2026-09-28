from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import requests

from .models import DownloadConfig, RemoteFile

ZENODO_API = "https://zenodo.org/api/records/{record_id}"
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")


class ZenodoError(RuntimeError):
    """Raised for Zenodo metadata or release-resolution failures."""


def _normalize_md5(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if ":" in text:
        algorithm, digest = text.split(":", 1)
        if algorithm.lower() != "md5":
            return None
        text = digest
    return text.lower() if MD5_RE.fullmatch(text) else None


def _iter_file_objects(record: dict[str, Any]) -> Iterable[dict[str, Any]]:
    raw = record.get("files", [])
    if isinstance(raw, list):
        yield from raw
        return
    if isinstance(raw, dict):
        entries = raw.get("entries")
        if isinstance(entries, dict):
            yield from entries.values()
            return
        if isinstance(entries, list):
            yield from entries
            return
        candidates = [value for value in raw.values() if isinstance(value, dict)]
        if candidates:
            yield from candidates
            return
    raise ZenodoError("Unrecognized Zenodo file metadata structure")


def _download_url(record_id: int, filename: str, links: dict[str, Any] | None) -> str:
    links = links or {}
    for key in ("content", "download", "self"):
        value = links.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    return (
        f"https://zenodo.org/records/{record_id}/files/"
        f"{quote(filename, safe='')}?download=1"
    )


def _record_version(record: dict[str, Any]) -> str | None:
    metadata = record.get("metadata", {})
    value = metadata.get("version") if isinstance(metadata, dict) else None
    return str(value) if value is not None else None


def _record_doi(record: dict[str, Any]) -> str | None:
    for location in (record, record.get("metadata", {})):
        if isinstance(location, dict) and location.get("doi"):
            return str(location["doi"])
    pids = record.get("pids", {})
    if isinstance(pids, dict):
        doi = pids.get("doi", {})
        if isinstance(doi, dict) and doi.get("identifier"):
            return str(doi["identifier"])
    return None


def make_session(download: DownloadConfig) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": download.user_agent})
    return session


def fetch_record_json(
    *,
    session: requests.Session,
    record_id: int,
    cache_dir: Path,
    download: DownloadConfig,
    refresh: bool,
    offline: bool,
) -> dict[str, Any]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"record_{record_id}.json"

    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text())
    if offline:
        raise ZenodoError(
            f"No cached metadata for Zenodo {record_id}: {cache_path}. "
            "Run once without --offline."
        )

    url = ZENODO_API.format(record_id=record_id)
    last_error: Exception | None = None
    for attempt in range(1, download.max_attempts + 1):
        try:
            response = session.get(
                url,
                timeout=(
                    download.connect_timeout_seconds,
                    download.read_timeout_seconds,
                ),
            )
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = (
                    int(retry_after)
                    if retry_after and retry_after.isdigit()
                    else min(60, 2**attempt)
                )
                time.sleep(delay)
                continue
            response.raise_for_status()
            payload = response.json()
            tmp = cache_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
            tmp.replace(cache_path)
            return payload
        except (requests.RequestException, ValueError, OSError) as exc:
            last_error = exc
            if attempt < download.max_attempts:
                time.sleep(min(60, 2**attempt))

    raise ZenodoError(
        f"Unable to retrieve Zenodo record {record_id} after "
        f"{download.max_attempts} attempts: {last_error}"
    )


def parse_record_files(record_id: int, record: dict[str, Any]) -> dict[str, RemoteFile]:
    version = _record_version(record)
    doi = _record_doi(record)
    parsed: dict[str, RemoteFile] = {}
    for obj in _iter_file_objects(record):
        filename = obj.get("key") or obj.get("filename")
        if not isinstance(filename, str):
            continue
        remote = RemoteFile(
            record_id=record_id,
            filename=filename,
            size_bytes=int(obj.get("size", 0)),
            md5=_normalize_md5(obj.get("checksum")),
            url=_download_url(record_id, filename, obj.get("links")),
            record_version=version,
            record_doi=doi,
        )
        parsed[filename] = remote
    if not parsed:
        raise ZenodoError(f"Zenodo record {record_id} exposes no files")
    return parsed
