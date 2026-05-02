"""송파어린이문화회관 (epart.net 플랫폼)."""
from typing import Iterator

from src.models import ClassListing, FacilityType
from src.sources.base import Source


class SongpaKidsSource(Source):
    source_id = "songpa_kids"
    name = "송파어린이문화회관"
    base_url = "https://songpakids.epart.net"
    facility_type = FacilityType.KIDS_CULTURE
    # epart.net 플랫폼이 다른 자치구 시설에서도 쓰인다면 횡적 확장 후보.
    notes = "어린이 전용. epart.net 외부 신청 플랫폼."

    def crawl(self) -> Iterator[ClassListing]:
        raise NotImplementedError
