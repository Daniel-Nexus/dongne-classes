"""잠실청소년센터 — DEPRECATED.

자체 사이트 `jamsilyouthcenter.or.kr`는 정보/공지 페이지 위주이고,
실제 강좌 신청은 `online538.youth.seoul.kr/center_index.php?center_id=538` 에서 이뤄짐.
seoul_youth 소스가 center_id=538을 포함하면 잠실 강좌가 자동으로 수집됨.

본 모듈은 인터페이스만 유지(레지스트리 호환). `crawl()` 은 빈 이터레이터.
"""
from typing import Iterator

from src.models import ClassListing, FacilityType
from src.sources.base import Source


class JamsilYouthSource(Source):
    source_id = "jamsil_youth"
    name = "잠실청소년센터 (deprecated, online538에 포함)"
    base_url = "https://jamsilyouthcenter.or.kr"
    facility_type = FacilityType.YOUTH_CENTER
    notes = "자체 사이트는 안내 페이지. 강좌는 seoul_youth (center_id=538)에서 수집."

    def crawl(self) -> Iterator[ClassListing]:
        return iter(())
