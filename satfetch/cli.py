from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from satfetch.models import SearchQuery
from satfetch.providers import PROVIDER_COLLECTIONS, get_provider
from satfetch.utils import (
    load_dotenv_if_available,
    parse_bbox,
    result_from_jsonable,
    results_to_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="satfetch",
        description="Search and download Landsat/Sentinel data from multiple providers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search scenes/products")
    search.add_argument("--provider", required=True, choices=sorted(PROVIDER_COLLECTIONS))
    search.add_argument("--collection", required=True)
    search.add_argument("--bbox", required=True, help="min_lon,min_lat,max_lon,max_lat")
    search.add_argument("--start", required=True, help="YYYY-MM-DD")
    search.add_argument("--end", required=True, help="YYYY-MM-DD")
    search.add_argument("--cloud", type=float, default=None)
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--out", default="data/results")

    download = subparsers.add_parser("download", help="Download assets from a saved search JSON")
    download.add_argument("--results-json", required=True)
    download.add_argument("--item-id", required=True)
    download.add_argument("--assets", default="", help="Comma-separated asset keys")
    download.add_argument("--out-dir", default="data/downloads")

    return parser


def run_search(args: argparse.Namespace) -> None:
    provider = get_provider(args.provider)
    query = SearchQuery(
        provider=args.provider,
        collection=args.collection,
        bbox=parse_bbox(args.bbox),
        start_date=args.start,
        end_date=args.end,
        limit=args.limit,
        cloud_cover=args.cloud,
    )
    results = provider.search(query)
    out_base = Path(args.out)
    json_path = results_to_json(results, out_base.with_suffix(".json"))
    csv_path = out_base.with_suffix(".csv")
    pd.DataFrame([result.to_record() for result in results]).to_csv(csv_path, index=False)
    print(f"Found {len(results)} result(s)")
    print(f"Saved JSON: {json_path}")
    print(f"Saved CSV: {csv_path}")
    if results:
        print(pd.DataFrame([result.to_record() for result in results]).head(10).to_string(index=False))


def run_download(args: argparse.Namespace) -> None:
    payload = json.loads(Path(args.results_json).read_text(encoding="utf-8"))
    results = [result_from_jsonable(item) for item in payload]
    selected = next((result for result in results if result.item_id == args.item_id), None)
    if selected is None:
        raise SystemExit(f"Item not found in saved results: {args.item_id}")

    provider = get_provider(selected.provider)
    asset_keys = [part.strip() for part in args.assets.split(",") if part.strip()]
    paths = provider.download_assets(selected, asset_keys, args.out_dir)
    print("Downloaded:")
    for path in paths:
        print(path)


def main() -> None:
    load_dotenv_if_available()
    args = build_parser().parse_args()
    if args.command == "search":
        run_search(args)
    elif args.command == "download":
        run_download(args)


if __name__ == "__main__":
    main()

