"""소스 공통 인터페이스."""
from abc import ABC, abstractmethod
from typing import Iterator

from src.models import ClassListing, FacilityType


class Source(ABC):
    source_id: str
    name: str
    base_url: str
    facility_type: FacilityType
    notes: str = ""

    @abstractmethod
    def crawl(self) -> Iterator[ClassListing]:
        ...
