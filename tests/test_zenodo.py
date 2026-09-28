from __future__ import annotations

from gwtc_forecast.zenodo import parse_record_files


def test_parse_classic_zenodo_metadata() -> None:
    payload = {
        "doi": "10.5281/zenodo.1",
        "metadata": {"version": "v1"},
        "files": [
            {
                "key": "data.hdf5",
                "size": 123,
                "checksum": "md5:0123456789abcdef0123456789abcdef",
                "links": {"self": "https://example.test/data"},
            }
        ],
    }
    files = parse_record_files(1, payload)
    item = files["data.hdf5"]
    assert item.size_bytes == 123
    assert item.md5 == "0123456789abcdef0123456789abcdef"
    assert item.record_doi == "10.5281/zenodo.1"
