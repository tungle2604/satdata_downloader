from __future__ import annotations

import time
from pathlib import Path

import requests

from satfetch.models import SearchQuery, SearchResult
from satfetch.utils import ensure_dir, env_value, safe_filename, stream_download

from .base import Provider


class UsgsM2MProvider(Provider):
    name = "usgs"
    base_url = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    def _request(
        self,
        endpoint: str,
        payload: dict,
        api_key: str | None = None,
    ) -> dict:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-Auth-Token"] = api_key
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("errorCode"):
            raise RuntimeError(f"USGS M2M error: {body['errorCode']} - {body.get('errorMessage')}")
        return body["data"] if "data" in body else {}

    def _api_key(self) -> str:
        username = env_value("USGS_USERNAME")
        token = env_value("USGS_TOKEN")
        if not username or not token:
            raise RuntimeError(
                "Missing USGS_USERNAME/USGS_TOKEN. Create .env from .env.example and request M2M access."
            )
        data = self._request("login-token", {"username": username, "token": token})
        if not isinstance(data, str):
            raise RuntimeError("USGS login-token did not return an API key")
        return data

    def search(self, query: SearchQuery) -> list[SearchResult]:
        api_key = self._api_key()
        min_lon, min_lat, max_lon, max_lat = query.bbox
        scene_filter = {
            "acquisitionFilter": {
                "start": query.start_date,
                "end": query.end_date,
            },
            "spatialFilter": {
                "filterType": "mbr",
                "lowerLeft": {"latitude": min_lat, "longitude": min_lon},
                "upperRight": {"latitude": max_lat, "longitude": max_lon},
            },
        }
        if query.cloud_cover is not None:
            scene_filter["cloudCoverFilter"] = {
                "max": query.cloud_cover,
                "includeUnknown": True,
            }
        data = self._request(
            "scene-search",
            {
                "datasetName": query.collection,
                "sceneFilter": scene_filter,
                "maxResults": query.limit,
                "startingNumber": 1,
                "metadataType": "summary",
            },
            api_key=api_key,
        )
        results = data.get("results", [])
        return [self._result_from_scene(scene, query.collection) for scene in results]

    def _result_from_scene(self, scene: dict, collection: str) -> SearchResult:
        item_id = scene.get("entityId") or scene.get("displayId") or scene.get("entity_id")
        title = scene.get("displayId") or item_id
        return SearchResult(
            provider=self.name,
            collection=collection,
            item_id=item_id,
            title=title,
            datetime=scene.get("acquisitionDate"),
            cloud_cover=scene.get("cloudCover"),
            preview_href=(scene.get("browse") or [{}])[0].get("browsePath")
            if scene.get("browse")
            else None,
            assets={"usgs_entity": item_id},
            raw=scene,
        )

    def download_assets(
        self,
        result: SearchResult,
        asset_keys: list[str],
        output_dir: str | Path,
    ) -> list[Path]:
        output_dir = ensure_dir(output_dir)
        api_key = self._api_key()
        options = self._request(
            "download-options",
            {
                "datasetName": result.collection,
                "entityIds": [result.item_id],
            },
            api_key=api_key,
        )
        candidates = [item for item in options if item.get("available")]
        if not candidates:
            raise RuntimeError("No immediately available USGS downloads for this scene")

        product = self._choose_product(candidates)
        label = f"satfetch_{int(time.time())}"
        request_data = self._request(
            "download-request",
            {
                "downloads": [
                    {
                        "entityId": result.item_id,
                        "productId": product["id"],
                    }
                ],
                "label": label,
            },
            api_key=api_key,
        )
        downloads = request_data.get("availableDownloads") or []
        if not downloads:
            raise RuntimeError(
                "USGS accepted the request, but the file is still being prepared. Try again later in EarthExplorer/M2M."
            )

        paths: list[Path] = []
        for item in downloads:
            url = item["url"]
            suffix = Path(url.split("?")[0]).suffix or ".tar"
            filename = f"{safe_filename(result.title)}_{safe_filename(product['productName'])}{suffix}"
            paths.append(stream_download(url, output_dir / filename))
        return paths

    @staticmethod
    def _choose_product(candidates: list[dict]) -> dict:
        for keyword in ("bundle", "level-2", "landsat"):
            for item in candidates:
                name = (item.get("productName") or "").lower()
                if keyword in name:
                    return item
        return candidates[0]
