from __future__ import annotations

from pathlib import Path

from satfetch.models import SearchQuery, SearchResult
from satfetch.utils import bbox_to_geojson, ensure_dir, env_value, safe_filename, stream_download

from .base import Provider


class GeeProvider(Provider):
    name = "gee"

    cloud_properties = {
        "COPERNICUS/S2_SR_HARMONIZED": "CLOUDY_PIXEL_PERCENTAGE",
        "LANDSAT/LC08/C02/T1_L2": "CLOUD_COVER",
        "LANDSAT/LC09/C02/T1_L2": "CLOUD_COVER",
    }

    true_color_bands = {
        "COPERNICUS/S2_SR_HARMONIZED": ["B4", "B3", "B2"],
        "LANDSAT/LC08/C02/T1_L2": ["SR_B4", "SR_B3", "SR_B2"],
        "LANDSAT/LC09/C02/T1_L2": ["SR_B4", "SR_B3", "SR_B2"],
    }

    vis_params = {
        "COPERNICUS/S2_SR_HARMONIZED": {"min": 0, "max": 3000},
        "LANDSAT/LC08/C02/T1_L2": {"min": 7000, "max": 18000},
        "LANDSAT/LC09/C02/T1_L2": {"min": 7000, "max": 18000},
    }

    def _ee(self):
        import ee

        project = env_value("GEE_PROJECT")
        try:
            if project:
                ee.Initialize(project=project)
            else:
                ee.Initialize()
        except Exception as exc:
            raise RuntimeError(
                "Google Earth Engine is not initialized. Run 'earthengine authenticate' "
                "and set GEE_PROJECT in .env."
            ) from exc
        return ee

    def search(self, query: SearchQuery) -> list[SearchResult]:
        ee = self._ee()
        geometry = ee.Geometry(bbox_to_geojson(query.bbox))
        cloud_property = self.cloud_properties.get(query.collection)
        collection = (
            ee.ImageCollection(query.collection)
            .filterBounds(geometry)
            .filterDate(query.start_date, query.end_date)
        )
        if query.cloud_cover is not None and cloud_property:
            collection = collection.filter(ee.Filter.lte(cloud_property, query.cloud_cover))

        image_list = collection.limit(query.limit).toList(query.limit)
        count = image_list.size().getInfo()
        results: list[SearchResult] = []
        for index in range(count):
            image = ee.Image(image_list.get(index))
            info = image.getInfo()
            image_id = info.get("id") or info["properties"].get("system:index")
            properties = info.get("properties", {})
            preview_href = self._preview_url(ee, image, query)
            results.append(
                SearchResult(
                    provider=self.name,
                    collection=query.collection,
                    item_id=image_id,
                    title=image_id,
                    datetime=str(properties.get("DATE_ACQUIRED") or properties.get("system:time_start")),
                    cloud_cover=properties.get(cloud_property) if cloud_property else None,
                    preview_href=preview_href,
                    assets={"gee_image_zip": image_id},
                    raw={
                        "bbox": query.bbox,
                        "collection": query.collection,
                        "properties": properties,
                    },
                )
            )
        return results

    def _preview_url(self, ee, image, query: SearchQuery) -> str | None:
        bands = self.true_color_bands.get(query.collection)
        if not bands:
            return None
        geometry = ee.Geometry(bbox_to_geojson(query.bbox))
        vis = {"bands": bands, **self.vis_params.get(query.collection, {})}
        return image.visualize(**vis).getThumbURL(
            {
                "region": geometry,
                "dimensions": 768,
                "format": "png",
            }
        )

    def download_assets(
        self,
        result: SearchResult,
        asset_keys: list[str],
        output_dir: str | Path,
    ) -> list[Path]:
        ee = self._ee()
        output_dir = ensure_dir(output_dir)
        bbox = tuple(result.raw["bbox"])
        geometry = ee.Geometry(bbox_to_geojson(bbox))
        bands = self.true_color_bands.get(result.collection)
        if not bands:
            raise RuntimeError(f"No default bands are configured for {result.collection}")
        image = ee.Image(result.item_id).select(bands)
        url = image.getDownloadURL(
            {
                "region": geometry,
                "scale": 30,
                "filePerBand": False,
                "format": "ZIPPED_GEO_TIFF",
            }
        )
        filename = f"{safe_filename(result.title)}_gee_true_color.zip"
        return [stream_download(url, output_dir / filename)]
