# Satellite Data Downloader

Công cụ Python để tìm kiếm và tải dữ liệu Landsat/Sentinel từ nhiều nguồn:

- EarthSearch: STAC API, chạy được không cần tài khoản.
- Microsoft Planetary Computer: STAC API, có ký URL bằng `planetary-computer`.
- Copernicus Data Space Ecosystem / ESA: OData API, cần tài khoản CDSE khi tải file.
- USGS EarthExplorer / M2M: M2M API, cần USGS username và application token.
- Google Earth Engine: Earth Engine Python API, cần xác thực GEE và Google Cloud project.

## Kết luận nhanh về mức độ hoàn chỉnh

Nếu chỉ có thư mục gốc ban đầu thì chưa thể gọi là công cụ hoàn chỉnh, vì chưa có mã nguồn, giao diện, hướng dẫn chạy, file cấu hình, kiểm thử, hay Git repo.

Bộ dự án này là phiên bản MVP có thể demo:

- Có giao diện Streamlit để chọn nguồn, bbox, ngày, độ mây, xem metadata và tải asset.
- Có CLI để tìm/tải dữ liệu bằng lệnh Python.
- Có cấu trúc provider riêng cho từng nguồn.
- Có file `.env.example` để cấu hình tài khoản an toàn.
- Có `.gitignore` để không đẩy file ảnh vệ tinh dung lượng lớn lên Git.
- Có test nhỏ cho phần xử lý bbox và registry provider.

Để gọi là hoàn chỉnh theo mức độ bảo vệ/báo cáo, bạn nên chạy và chụp minh chứng cho ít nhất:

- EarthSearch search + tải 1 asset nhỏ/preview.
- Planetary Computer search + tải 1 asset.
- Copernicus search + tải 1 product sau khi điền tài khoản.
- USGS search + tải 1 product sau khi có M2M token.
- GEE search + export 1 vùng nhỏ sau khi authenticate.

## Cài đặt

Khuyến nghị dùng Python 3.11 hoặc 3.12.

```powershell
cd C:\Users\PC\Documents\Codex\2026-07-02\t-i\outputs\satdata_downloader
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu là Python 3.13:

```powershell
python -m pip install -r requirements.txt
```

## Cấu hình tài khoản

Tạo file `.env` từ file mẫu:

```powershell
copy .env.example .env
notepad .env
```

Chỉ điền nguồn nào bạn cần dùng.

Copernicus / ESA:

```text
CDSE_USERNAME=email_cua_ban
CDSE_PASSWORD=mat_khau_cua_ban
```

USGS EarthExplorer:

```text
USGS_USERNAME=username_cua_ban
USGS_TOKEN=application_token_cua_ban
```

Google Earth Engine:

```powershell
earthengine authenticate
```

Sau đó điền:

```text
GEE_PROJECT=ten_google_cloud_project
```

## Chạy giao diện trực quan

```powershell
streamlit run app.py
```

Mở trình duyệt tại địa chỉ Streamlit hiện ra, thường là:

```text
http://localhost:8501
```

Demo nhanh nên chọn:

- Nguồn dữ liệu: `earthsearch`
- Bộ dữ liệu: `Sentinel-2 L2A`
- BBox mẫu: `105.70,20.90,106.05,21.20`
- Số kết quả: `5`
- Bấm `Tìm dữ liệu`

Nếu có kết quả, chọn một cảnh, xem preview nếu có, rồi tải asset nhỏ như `thumbnail`, `overview`, `visual` nếu asset đó tồn tại. Không nên tải tất cả bands trong lần demo đầu vì file có thể rất lớn.

## Chạy bằng CLI

Tìm dữ liệu EarthSearch:

```powershell
python -m satfetch.cli search `
  --provider earthsearch `
  --collection sentinel-2-l2a `
  --bbox 105.70,20.90,106.05,21.20 `
  --start 2025-01-01 `
  --end 2025-02-01 `
  --cloud 30 `
  --limit 5 `
  --out data\earthsearch_demo
```

Lệnh trên tạo:

```text
data\earthsearch_demo.json
data\earthsearch_demo.csv
```

Tải asset sau khi có `item_id` và `asset_keys` trong file CSV/JSON:

```powershell
python -m satfetch.cli download `
  --results-json data\earthsearch_demo.json `
  --item-id ID_CANH_CAN_TAI `
  --assets thumbnail `
  --out-dir data\downloads
```



## Nguồn tài liệu chính thức

- Copernicus Data Space Ecosystem APIs/OData: https://documentation.dataspace.copernicus.eu/APIs/OData.html
- Copernicus token: https://documentation.dataspace.copernicus.eu/APIs/Token.html
- USGS M2M API: https://m2m.cr.usgs.gov/
- USGS M2M application token: https://www.usgs.gov/media/files/m2m-application-token-documentation
- Google Earth Engine Python API: https://developers.google.com/earth-engine/guides/python_install
- Planetary Computer SDK for Python: https://github.com/microsoft/planetary-computer-sdk-for-python
- EarthSearch API: https://element84.com/earth-search/examples/
