"""SQLite 저장소 동작 테스트."""
from datetime import datetime

from src import storage
from src.models import ClassListing, FacilityType, RegistrationMethod, Status


def _make(
    source_id: str = "songpa_gu_office",
    external_id: str = "1",
    title: str = "테스트 강좌",
    age_min: int | None = 5,
    age_max: int | None = 6,
    crawled_at: datetime | None = None,
    last_seen_at: datetime | None = None,
    status: Status = Status.RECRUITING,
    registration_end: datetime | None = None,
) -> ClassListing:
    now = datetime(2026, 5, 1, 10, 0)
    return ClassListing(
        source_id=source_id,
        external_id=external_id,
        source_url="https://example.com/x",
        title=title,
        facility_name="잠실본동 자치회관",
        facility_type=FacilityType.GU_OFFICE,
        target_age_min=age_min,
        target_age_max=age_max,
        registration_method=RegistrationMethod.ONLINE,
        status=status,
        registration_end=registration_end,
        crawled_at=crawled_at or now,
        last_seen_at=last_seen_at or now,
    )


def test_upsert_then_get(tmp_path):
    conn = storage.connect(tmp_path / "t.db")
    listing = _make()
    storage.upsert(conn, listing)
    fetched = storage.get(conn, "songpa_gu_office", "1")
    assert fetched is not None
    assert fetched.title == "테스트 강좌"
    assert fetched.target_age_min == 5


def test_upsert_preserves_crawled_at(tmp_path):
    conn = storage.connect(tmp_path / "t.db")
    first = _make(
        crawled_at=datetime(2026, 1, 1),
        last_seen_at=datetime(2026, 1, 1),
        title="첫 버전",
    )
    storage.upsert(conn, first)
    later = _make(
        crawled_at=datetime(2026, 5, 1),  # 새 객체엔 새 시간이지만 DB는 보존해야 함
        last_seen_at=datetime(2026, 5, 1),
        title="갱신된 제목",
    )
    storage.upsert(conn, later)

    row = conn.execute(
        "SELECT title, crawled_at, last_seen_at FROM listings WHERE external_id=?",
        ("1",),
    ).fetchone()
    assert row["title"] == "갱신된 제목"
    assert row["crawled_at"].startswith("2026-01-01")
    assert row["last_seen_at"].startswith("2026-05-01")


def test_upsert_many_returns_count(tmp_path):
    conn = storage.connect(tmp_path / "t.db")
    items = [_make(external_id=str(i), title=f"강좌 {i}") for i in range(5)]
    n = storage.upsert_many(conn, items)
    assert n == 5
    count = conn.execute("SELECT COUNT(*) AS c FROM listings").fetchone()["c"]
    assert count == 5


def test_search_kids_age_overlap_default_4_7(tmp_path):
    conn = storage.connect(tmp_path / "t.db")
    storage.upsert_many(conn, [
        _make(external_id="a", age_min=0, age_max=3, title="영아"),       # 안 맞음
        _make(external_id="b", age_min=4, age_max=6, title="유치원"),     # 맞음
        _make(external_id="c", age_min=6, age_max=8, title="유치~초저"),  # 맞음 (6~7 겹침)
        _make(external_id="d", age_min=8, age_max=12, title="초등"),      # 안 맞음
        _make(external_id="e", age_min=None, age_max=None, title="대상미상"),  # 제외
    ])
    # 기본 4~7세.
    titles = sorted(c.title for c in storage.search_kids(conn))
    assert titles == ["유치~초저", "유치원"]


def test_search_kids_multi_status(tmp_path):
    conn = storage.connect(tmp_path / "t.db")
    storage.upsert_many(conn, [
        _make(external_id="a", status=Status.RECRUITING),
        _make(external_id="b", status=Status.UPCOMING),
        _make(external_id="c", status=Status.ENDED),
    ])
    ids = sorted(c.external_id for c in storage.search_kids(conn, statuses=["recruiting", "upcoming"]))
    assert ids == ["a", "b"]


def test_search_kids_orders_by_status_then_deadline(tmp_path):
    conn = storage.connect(tmp_path / "t.db")
    # registration_end 다른 두 recruiting + 한 upcoming + 한 ended.
    storage.upsert_many(conn, [
        _make(external_id="late", status=Status.RECRUITING,
              registration_end=datetime(2026, 8, 1)),
        _make(external_id="soon", status=Status.RECRUITING,
              registration_end=datetime(2026, 5, 10)),
        _make(external_id="upcoming", status=Status.UPCOMING,
              registration_end=datetime(2026, 5, 5)),
        _make(external_id="ended", status=Status.ENDED,
              registration_end=datetime(2026, 4, 1)),
    ])
    ids = [c.external_id for c in storage.search_kids(conn, limit=10)]
    # recruiting 먼저, 그 안에서 마감 가까운 순. ended는 맨 뒤.
    assert ids == ["soon", "late", "upcoming", "ended"]
