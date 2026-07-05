import pytest

from satfetch.utils import bbox_to_geojson, bbox_to_wkt, parse_bbox, safe_filename


def test_parse_bbox_valid():
    assert parse_bbox("105.7,20.9,106.0,21.2") == (105.7, 20.9, 106.0, 21.2)


def test_parse_bbox_rejects_bad_order():
    with pytest.raises(ValueError):
        parse_bbox("106,20,105,21")


def test_bbox_formats():
    bbox = (105.7, 20.9, 106.0, 21.2)
    assert bbox_to_geojson(bbox)["type"] == "Polygon"
    assert bbox_to_wkt(bbox).startswith("POLYGON((")


def test_safe_filename():
    assert safe_filename("S2A scene / product.zip") == "S2A_scene_product.zip"

