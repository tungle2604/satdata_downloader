from __future__ import annotations

from pathlib import Path

from satfetch.models import SearchQuery, SearchResult


class Provider:
    name: str

    def search(self, query: SearchQuery) -> list[SearchResult]:
        raise NotImplementedError

    def download_assets(
        self,
        result: SearchResult,
        asset_keys: list[str],
        output_dir: str | Path,
    ) -> list[Path]:
        raise NotImplementedError

