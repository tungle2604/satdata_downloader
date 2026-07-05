from satfetch.providers import PROVIDER_COLLECTIONS, get_provider


def test_provider_registry():
    assert {"earthsearch", "planetary", "copernicus", "usgs", "gee"} <= set(PROVIDER_COLLECTIONS)
    assert get_provider("earthsearch").name == "earthsearch"
    assert get_provider("planetary").name == "planetary"

