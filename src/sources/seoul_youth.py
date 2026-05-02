"""서울시 청소년수련시설 통합신청 (online507)."""
from typing import Iterator

from src.models import ClassListing, FacilityType
from src.sources.base import Source


class SeoulYouthSource(Source):
    source_id = "seoul_youth_507"
    name = "서울시 청소년수련시설 통합신청"
    base_url = "https://online507.youth.seoul.kr"
    facility_type = FacilityType.YOUTH_CENTER
    # 25개 구 통합 시 Phase 2 확장 비용 폭락 — 커버리지 확인이 최우선 검증 항목.
    notes = "서울시 통합. 25개 구 커버 여부가 확장 잠재력 결정"

    def crawl(self) -> Iterator[ClassListing]:
        raise NotImplementedError
