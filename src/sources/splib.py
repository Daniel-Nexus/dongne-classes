"""송파구통합도서관."""
from typing import Iterator

from src.models import ClassListing, FacilityType
from src.sources.base import Source


class SplibSource(Source):
    source_id = "splib"
    name = "송파구통합도서관"
    base_url = "https://www.splib.or.kr"
    facility_type = FacilityType.LIBRARY
    notes = "구립 도서관 통합 — 어린이 강좌 비중 높음"

    def crawl(self) -> Iterator[ClassListing]:
        raise NotImplementedError
