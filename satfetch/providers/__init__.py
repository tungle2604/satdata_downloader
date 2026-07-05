from __future__ import annotations

from .copernicus import CopernicusProvider
from .gee import GeeProvider
from .stac_provider import StacProvider
from .usgs_m2m import UsgsM2MProvider


EARTHSEARCH_COLLECTIONS = {
    "Sentinel-2 L2A": "sentinel-2-l2a",
    "Sentinel-2 L1C": "sentinel-2-l1c",
    "Landsat Collection 2 L2": "landsat-c2-l2",
}

PLANETARY_COLLECTIONS = {
    "Sentinel-2 L2A": "sentinel-2-l2a",
    "Landsat Collection 2 L2": "landsat-c2-l2",
}

COPERNICUS_COLLECTIONS = {
    "Sentinel-1": "SENTINEL-1",
    "Sentinel-2": "SENTINEL-2",
    "Sentinel-3": "SENTINEL-3",
    "Landsat-8": "LANDSAT-8",
    "Landsat-9": "LANDSAT-9",
}

USGS_COLLECTIONS = {
    "Landsat 8-9 OLI/TIRS C2 L2": "landsat_ot_c2_l2",
    "Landsat 8-9 OLI/TIRS C2 L1": "landsat_ot_c2_l1",
    "Landsat 4-5 TM C2 L2": "landsat_tm_c2_l2",
}

GEE_COLLECTIONS = {
    "Sentinel-2 SR Harmonized": "COPERNICUS/S2_SR_HARMONIZED",
    "Landsat 8 C2 L2": "LANDSAT/LC08/C02/T1_L2",
    "Landsat 9 C2 L2": "LANDSAT/LC09/C02/T1_L2",
}


PROVIDER_COLLECTIONS = {
    "earthsearch": EARTHSEARCH_COLLECTIONS,
    "planetary": PLANETARY_COLLECTIONS,
    "copernicus": COPERNICUS_COLLECTIONS,
    "usgs": USGS_COLLECTIONS,
    "gee": GEE_COLLECTIONS,
}


def get_provider(name: str):
    normalized = name.lower().strip()
    if normalized == "earthsearch":
        return StacProvider(
            name="earthsearch",
            endpoint="https://earth-search.aws.element84.com/v1",
            sign_planetary=False,
        )
    if normalized == "planetary":
        return StacProvider(
            name="planetary",
            endpoint="https://planetarycomputer.microsoft.com/api/stac/v1",
            sign_planetary=True,
        )
    if normalized == "copernicus":
        return CopernicusProvider()
    if normalized == "usgs":
        return UsgsM2MProvider()
    if normalized == "gee":
        return GeeProvider()
    raise ValueError(f"Unknown provider: {name}")

