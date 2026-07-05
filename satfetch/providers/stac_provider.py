from __future__ import annotations

from pathlib import Path

from satfetch.models import SearchQuery, SearchResult
from satfetch.utils import ensure_dir, safe_filename, stream_download

from .base import Provider


class StacProvider(Provider):
    def __init__(self, name: str, endpoint: str, sign_planetary: bool = False) -> None:
        self.name = name
        self.endpoint = endpoint
        self.sign_planetary = sign_planetary

    def _client(self):
        from pystac_client import Client

        if self.sign_planetary:
            import planetary_computer

            return Client.open(self.endpoint, modifier=planetary_computer.sign_inplace)
        return Client.open(self.endpoint)

    def search(self, query: SearchQuery) -> list[SearchResult]:
        client = self._client()
        stac_query = {}
        if query.cloud_cover is not None:
            stac_query = {"eo:cloud_cover": {"lt": query.cloud_cover}}

        search = client.search(
            collections=[query.collection],
            bbox=list(query.bbox),
            datetime=f"{query.start_date}/{query.end_date}",
            query=stac_query or None,
            max_items=query.limit,
        )
        items = list(search.items())
        return [self._result_from_item(item, query.collection) for item in items]

    def _result_from_item(self, item, collection: str) -> SearchResult:
        assets = {
            key: asset.href
            for key, asset in item.assets.items()
            if getattr(asset, "href", None)
        }
        preview_href = self._preview_href(item, assets)
        item_datetime = item.properties.get("datetime")
        if item_datetime is None and getattr(item, "datetime", None):
            item_datetime = item.datetime.isoformat()
        return SearchResult(
            provider=self.name,
            collection=collection,
            item_id=item.id,
            title=item.id,
            datetime=item_datetime,
            cloud_cover=item.properties.get("eo:cloud_cover"),
            preview_href=preview_href,
            assets=assets,
            raw={
                "bbox": item.bbox,
                "properties": item.properties,
                "links": [link.to_dict() for link in item.links],
            },
        )

    @staticmethod
    def _preview_href(item, assets: dict[str, str]) -> str | None:
        preferred_keys = [
            "rendered_preview",
            "thumbnail",
            "overview",
            "visual",
            "visual-jp2",
        ]
        for key in preferred_keys:
            if key in assets:
                return assets[key]
        for key, asset in item.assets.items():
            roles = getattr(asset, "roles", None) or []
            if "thumbnail" in roles:
                return asset.href
        return None

    def download_assets(
        self,
        result: SearchResult,
        asset_keys: list[str],
        output_dir: str | Path,
    ) -> list[Path]:
        output_dir = ensure_dir(output_dir)
        if not asset_keys:
            raise ValueError("Choose at least one asset key to download")

        downloaded: list[Path] = []
        for key in asset_keys:
            if key not in result.assets:
                raise KeyError(f"Asset '{key}' is not available for {result.item_id}")
            url = result.assets[key]
            suffix = Path(url.split("?")[0]).suffix or ".dat"
            filename = f"{safe_filename(result.item_id)}_{safe_filename(key)}{suffix}"
            downloaded.append(stream_download(url, output_dir / filename))
        return downloaded

