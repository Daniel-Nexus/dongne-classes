"""송파구청 통합 강좌 신청 시스템."""
from typing import Iterator

from src.models import ClassListing, FacilityType
from src.sources.base import Source


class SongpaGuOfficeSource(Source):
    source_id = "songpa_gu_office"
    name = "송파구청 통합 강좌"
    base_url = "https://www.songpa.go.kr/learn/youth/program/lecture_list.do"
    facility_type = FacilityType.GU_OFFICE
    notes = "동주민센터/구청/진학학습지원센터 강좌 통합"

    def crawl(self) -> Iterator[ClassListing]:
        raise NotImplementedError
