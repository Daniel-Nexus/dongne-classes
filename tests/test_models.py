from datetime import datetime

from src.models import ClassListing, FacilityType, RegistrationMethod, Status


def test_minimal():
    now = datetime.now()
    c = ClassListing(
        source_id="songpa_gu_office",
        external_id="12345",
        source_url="https://www.songpa.go.kr/learn/youth/program/lecture_view.do?seq=12345",
        title="어린이 미술 교실",
        facility_name="송파구청 평생학습관",
        facility_type=FacilityType.GU_OFFICE,
        crawled_at=now,
        last_seen_at=now,
    )
    assert c.status is Status.UNKNOWN
    assert c.registration_method is RegistrationMethod.UNKNOWN
    assert c.schedule_days == []
    assert c.fee_won is None


def test_full():
    now = datetime.now()
    c = ClassListing(
        source_id="splib",
        external_id="course-789",
        source_url="https://www.splib.or.kr/course/view/789",
        title="초등 독서 토론",
        facility_name="거마도서관",
        facility_type=FacilityType.LIBRARY,
        target_description="초등 3~4학년",
        target_age_min=9,
        target_age_max=10,
        schedule_days=["수"],
        schedule_time="15:00~16:30",
        capacity=15,
        fee_won=0,
        registration_method=RegistrationMethod.ONLINE,
        status=Status.RECRUITING,
        crawled_at=now,
        last_seen_at=now,
    )
    assert c.fee_won == 0
    assert c.target_age_max == 10
    assert "거마" in c.facility_name
