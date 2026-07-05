from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class SearchQuery:
    provider: str
    collection: str
    bbox: BBox
    start_date: str
    end_date: str
    limit: int = 10
    cloud_cover: float | None = None


@dataclass
class SearchResult:
    provider: str
    collection: str
    item_id: str
    title: str
    datetime: str | None = None
    cloud_cover: float | None = None
    preview_href: str | None = None
    assets: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "collection": self.collection,
            "item_id": self.item_id,
            "title": self.title,
            "datetime": self.datetime,
            "cloud_cover": self.cloud_cover,
            "preview_href": self.preview_href,
            "asset_keys": ", ".join(sorted(self.assets.keys())),
        }

    def to_jsonable(self) -> dict[str, Any]:
        record = self.to_record()
        record["assets"] = self.assets
        record["raw"] = self.raw
        return record

