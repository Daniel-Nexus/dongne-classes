"""Scrapling fetcher 래퍼 (v0.4.7 검증 완료)."""
from enum import Enum
from typing import Optional


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


def post(url: str, data: dict, headers: Optional[dict] = None):
    """form-encoded POST. AJAX 엔드포인트용 (Scrapling Fetcher.post 래핑)."""
    from scrapling.fetchers import Fetcher
    return Fetcher.post(url, data=data, headers=headers or {})
