"""잠실청소년센터."""
from typing import Iterator

from src.models import ClassListing, FacilityType
from src.sources.base import Source


class JamsilYouthSource(Source):
    source_id = "jamsil_youth"
    name = "잠실청소년센터"
    base_url = "https://jamsilyouthcenter.or.kr"
    facility_type = FacilityType.YOUTH_CENTER
    # online507에 포함되면 이 소스는 제거.
    notes = "online507 중복 가능성 — 확인 후 정리"

    def crawl(self) -> Iterator[ClassListing]:
        raise NotImplementedError
