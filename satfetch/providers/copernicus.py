from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

import requests

from satfetch.models import SearchQuery, SearchResult
from satfetch.utils import (
    bbox_to_wkt,
    ensure_dir,
    env_value,
    safe_filename,
    stream_download,
)

from .base import Provider


class CopernicusProvider(Provider):
    name = "copernicus"
    catalog_url = "https://catalogue.dataspace.copernicus.eu/odata/v1"
    download_url = "https://download.dataspace.copernicus.eu/odata/v1"
    token_url = (
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
        "protocol/openid-connect/token"
    )

    def search(self, query: SearchQuery) -> list[SearchResult]:
        wkt = bbox_to_wkt(query.bbox)
        filters = [
            f"Collection/Name eq '{query.collection}'",
            f"ContentDate/Start ge {query.start_date}T00:00:00.000Z",
            f"ContentDate/Start le {query.end_date}T23:59:59.999Z",
            f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}')",
        ]
        params = {
            "$filter": " and ".join(filters),
            "$top": str(query.limit),
            "$orderby": "ContentDate/Start desc",
            "$select": "Id,Name,ContentLength,Online,ContentDate,GeoFootprint",
        }
        response = requests.get(
            f"{self.catalog_url}/Products",
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        products = response.json().get("value", [])
        return [self._result_from_product(product, query.collection) for product in products]

    def _result_from_product(self, product: dict, collection: str) -> SearchResult:
        product_id = product["Id"]
        title = product.get("Name") or product_id
        download_href = f"{self.download_url}/Products({product_id})/$value"
        return SearchResult(
            provider=self.name,
            collection=collection,
            item_id=product_id,
            title=title,
            datetime=(product.get("ContentDate") or {}).get("Start"),
            preview_href=None,
            assets={"product_zip": download_href},
            raw=product,
        )

    def _token(self) -> str:
        username = env_value("CDSE_USERNAME")
        password = env_value("CDSE_PASSWORD")
        if not username or not password:
            raise RuntimeError(
                "Missing CDSE_USERNAME/CDSE_PASSWORD. Create .env from .env.example."
            )
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "client_id": "cdse-public",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def download_assets(
        self,
        result: SearchResult,
        asset_keys: list[str],
        output_dir: str | Path,
    ) -> list[Path]:
        output_dir = ensure_dir(output_dir)
        token = self._token()
        keys = asset_keys or ["product_zip"]
        downloaded: list[Path] = []
        for key in keys:
            if key not in result.assets:
                raise KeyError(f"Asset '{key}' is not available for {result.item_id}")
            filename = f"{safe_filename(result.title)}.zip"
            downloaded.append(
                stream_download(
                    quote(result.assets[key], safe="/:?=&()$"),
                    output_dir / filename,
                    headers={"Authorization": f"Bearer {token}"},
                )
            )
        return downloaded

