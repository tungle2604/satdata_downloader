from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Iterable

import requests
from tqdm import tqdm

from .models import BBox, SearchResult


def parse_bbox(value: str | Iterable[float]) -> BBox:
    if isinstance(value, str):
        parts = [float(part.strip()) for part in value.split(",")]
    else:
        parts = [float(part) for part in value]
    if len(parts) != 4:
        raise ValueError("BBox must have 4 values: min_lon,min_lat,max_lon,max_lat")
    min_lon, min_lat, max_lon, max_lat = parts
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("BBox min values must be smaller than max values")
    return min_lon, min_lat, max_lon, max_lat


def bbox_to_geojson(bbox: BBox) -> dict[str, Any]:
    min_lon, min_lat, max_lon, max_lat = bbox
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]
        ],
    }


def bbox_to_wkt(bbox: BBox) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    return (
        "POLYGON(("
        f"{min_lon} {min_lat},"
        f"{max_lon} {min_lat},"
        f"{max_lon} {max_lat},"
        f"{min_lon} {max_lat},"
        f"{min_lon} {min_lat}"
        "))"
    )


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return value.strip("._") or "download"


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def stream_download(
    url: str,
    output_path: str | Path,
    headers: dict[str, str] | None = None,
    chunk_size: int = 1024 * 1024,
) -> Path:
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    with requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length") or 0)
        with output_path.open("wb") as handle:
            progress = tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                desc=output_path.name,
                disable=total == 0,
            )
            with progress:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        handle.write(chunk)
                        progress.update(len(chunk))
    return output_path


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def env_value(name: str) -> str | None:
    value = os.getenv(name)
    return value if value else None


def results_to_json(results: list[SearchResult], path: str | Path) -> Path:
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(
        json.dumps([result.to_jsonable() for result in results], indent=2),
        encoding="utf-8",
    )
    return path


def result_from_jsonable(data: dict[str, Any]) -> SearchResult:
    return SearchResult(
        provider=data["provider"],
        collection=data["collection"],
        item_id=data["item_id"],
        title=data.get("title") or data["item_id"],
        datetime=data.get("datetime"),
        cloud_cover=data.get("cloud_cover"),
        preview_href=data.get("preview_href"),
        assets=data.get("assets") or {},
        raw=data.get("raw") or {},
    )

