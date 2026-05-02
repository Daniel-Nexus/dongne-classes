"""Scrapling fetcher 래퍼 (API는 v0.4.x 설치 후 검증)."""
from enum import Enum


class FetchMode(str, Enum):
    HTTP = "http"
    STEALTH = "stealth"
    DYNAMIC = "dynamic"


def fetch(url: str, mode: FetchMode = FetchMode.HTTP):
    if mode is FetchMode.HTTP:
        from scrapling.fetchers import Fetcher
        return Fetcher.get(url)
    if mode is FetchMode.STEALTH:
        from scrapling.fetchers import StealthyFetcher
        return StealthyFetcher.fetch(url)
    if mode is FetchMode.DYNAMIC:
        from scrapling.fetchers import DynamicFetcher
        return DynamicFetcher.fetch(url)
    raise ValueError(f"Unknown fetch mode: {mode}")
