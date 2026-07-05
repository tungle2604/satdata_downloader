from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from satfetch.models import SearchQuery
from satfetch.providers import PROVIDER_COLLECTIONS, get_provider
from satfetch.utils import load_dotenv_if_available, parse_bbox, results_to_json


load_dotenv_if_available()

st.set_page_config(page_title="Satellite Data Downloader", layout="wide")

st.title("Satellite Data Downloader")

with st.sidebar:
    st.header("Truy vấn")
    provider_name = st.selectbox(
        "Nguồn dữ liệu",
        ["earthsearch", "planetary", "copernicus", "usgs", "gee"],
        index=0,
    )
    collections = PROVIDER_COLLECTIONS[provider_name]
    collection_label = st.selectbox("Bộ dữ liệu", list(collections.keys()))
    collection = collections[collection_label]

    bbox_text = st.text_input(
        "BBox",
        value="105.70,20.90,106.05,21.20",
        help="min_lon,min_lat,max_lon,max_lat",
    )
    today = date.today()
    start_date = st.date_input("Từ ngày", today - timedelta(days=60))
    end_date = st.date_input("Đến ngày", today)
    cloud_cover = st.slider("Mây tối đa (%)", 0, 100, 30)
    limit = st.slider("Số kết quả", 1, 50, 10)
    output_dir = st.text_input("Thư mục tải", value="data/downloads")
    search_clicked = st.button("Tìm dữ liệu", use_container_width=True)


def draw_bbox_map(bbox):
    min_lon, min_lat, max_lon, max_lat = bbox
    center = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]
    fmap = folium.Map(location=center, zoom_start=10, tiles="CartoDB positron")
    folium.Rectangle(
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        color="#2563eb",
        weight=2,
        fill=True,
        fill_opacity=0.08,
    ).add_to(fmap)
    return fmap


try:
    bbox = parse_bbox(bbox_text)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

left, right = st.columns([1.1, 1.6], gap="large")

with left:
    st.subheader("Vùng quan tâm")
    st_folium(draw_bbox_map(bbox), height=420, use_container_width=True)

with right:
    st.subheader("Kết quả")
    if search_clicked:
        try:
            provider = get_provider(provider_name)
            query = SearchQuery(
                provider=provider_name,
                collection=collection,
                bbox=bbox,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                cloud_cover=float(cloud_cover),
                limit=int(limit),
            )
            with st.spinner("Đang tìm dữ liệu..."):
                st.session_state["results"] = provider.search(query)
                st.session_state["provider_name"] = provider_name
                st.session_state["collection"] = collection
        except Exception as exc:
            st.error(f"Không tìm được dữ liệu: {exc}")

    results = st.session_state.get("results", [])
    if not results:
        st.info("Chưa có kết quả. Chọn nguồn dữ liệu rồi bấm Tìm dữ liệu.")
    else:
        frame = pd.DataFrame([result.to_record() for result in results])
        st.dataframe(frame, use_container_width=True, hide_index=True)

        csv_bytes = frame.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Tải metadata CSV",
            data=csv_bytes,
            file_name="satellite_search_results.csv",
            mime="text/csv",
        )

        saved_json = results_to_json(results, Path("data/results.json"))
        st.caption(f"Đã lưu metadata JSON: {saved_json}")

        labels = [f"{idx + 1}. {result.title}" for idx, result in enumerate(results)]
        chosen_label = st.selectbox("Chọn cảnh/sản phẩm", labels)
        chosen = results[labels.index(chosen_label)]

        if chosen.preview_href:
            st.image(chosen.preview_href, caption=chosen.title, use_container_width=True)

        asset_keys = sorted(chosen.assets.keys())
        selected_assets = st.multiselect(
            "Asset cần tải",
            asset_keys,
            default=asset_keys[:1],
        )
        if st.button("Tải asset đã chọn", use_container_width=True):
            try:
                provider = get_provider(chosen.provider)
                with st.spinner("Đang tải dữ liệu..."):
                    paths = provider.download_assets(chosen, selected_assets, output_dir)
                st.success("Tải xong")
                for path in paths:
                    st.write(str(path))
            except Exception as exc:
                st.error(f"Không tải được: {exc}")

