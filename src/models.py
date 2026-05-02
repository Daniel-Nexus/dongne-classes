"""강좌 데이터 모델."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class FacilityType(str, Enum):
    GU_OFFICE = "gu_office"
    LIBRARY = "library"
    DONG_CENTER = "dong_center"
    KIDS_CULTURE = "kids_culture"
    YOUTH_CENTER = "youth_center"
    SPORTS = "sports"
    PARENTING = "parenting"
    OTHER = "other"


class RegistrationMethod(str, Enum):
    ONLINE = "online"
    PHONE = "phone"
    VISIT = "visit"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class Status(str, Enum):
    UPCOMING = "upcoming"
    RECRUITING = "recruiting"
    WAITLIST = "waitlist"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"
    ENDED = "ended"
    UNKNOWN = "unknown"


class ClassListing(BaseModel):
    source_id: str
    external_id: str
    source_url: HttpUrl

    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    instructor: Optional[str] = None

    facility_name: str
    facility_type: FacilityType
    address: Optional[str] = None
    venue_detail: Optional[str] = None

    # raw 텍스트(target_description) + 정규화 값(min/max) 둘 다 보관 — 파싱 실패 대비.
    target_description: Optional[str] = None
    target_age_min: Optional[int] = None
    target_age_max: Optional[int] = None

    schedule_days: list[str] = Field(default_factory=list)
    schedule_time: Optional[str] = None
    session_count: Optional[int] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    capacity: Optional[int] = None
    registration_start: Optional[datetime] = None
    registration_end: Optional[datetime] = None
    registration_method: RegistrationMethod = RegistrationMethod.UNKNOWN
    status: Status = Status.UNKNOWN

    fee_won: Optional[int] = None
    materials_fee_won: Optional[int] = None

    crawled_at: datetime
    last_seen_at: datetime
    raw: dict = Field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.facility_name}] {self.title} ({self.source_id}:{self.external_id})"
