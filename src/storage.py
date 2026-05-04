"""SQLite 저장소.

스키마: 검색에 필요한 컬럼만 native, 나머지는 `data` JSON 컬럼에 묶음.
PK는 (source_id, external_id). 재크롤 시 `crawled_at`는 보존,
`last_seen_at` + 가변 필드만 업데이트하는 upsert.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Optional

from src.models import ClassListing


SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    source_id           TEXT NOT NULL,
    external_id         TEXT NOT NULL,
    title               TEXT NOT NULL,
    facility_name       TEXT NOT NULL,
    facility_type       TEXT NOT NULL,
    target_age_min      INTEGER,
    target_age_max      INTEGER,
    period_start        TEXT,
    period_end          TEXT,
    registration_start  TEXT,
    registration_end    TEXT,
    status              TEXT NOT NULL,
    fee_won             INTEGER,
    source_url          TEXT NOT NULL,
    crawled_at          TEXT NOT NULL,
    last_seen_at        TEXT NOT NULL,
    data                TEXT NOT NULL,
    PRIMARY KEY (source_id, external_id)
);
CREATE INDEX IF NOT EXISTS idx_listings_age      ON listings(target_age_min, target_age_max);
CREATE INDEX IF NOT EXISTS idx_listings_period   ON listings(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_listings_facility ON listings(facility_name);
CREATE INDEX IF NOT EXISTS idx_listings_status   ON listings(status);
"""


def connect(db_path: str | Path, *, check_same_thread: bool = False) -> sqlite3.Connection:
    """SQLite 연결. FastAPI(스레드풀)에서 한 connection을 공유하기 위해 기본
    `check_same_thread=False`. 읽기 위주의 단일-프로세스 MVP 가정. 동시 쓰기가
    들어오면 별도 락이나 connection-per-request로 옮길 것.
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _row_from(listing: ClassListing) -> dict:
    """검색에 쓰일 native 컬럼 + JSON-encoded full payload."""
    payload = listing.model_dump(mode="json")
    return {
        "source_id": listing.source_id,
        "external_id": listing.external_id,
        "title": listing.title,
        "facility_name": listing.facility_name,
        "facility_type": listing.facility_type.value,
        "target_age_min": listing.target_age_min,
        "target_age_max": listing.target_age_max,
        "period_start": payload.get("period_start"),
        "period_end": payload.get("period_end"),
        "registration_start": payload.get("registration_start"),
        "registration_end": payload.get("registration_end"),
        "status": listing.status.value,
        "fee_won": listing.fee_won,
        "source_url": str(listing.source_url),
        "crawled_at": payload["crawled_at"],
        "last_seen_at": payload["last_seen_at"],
        "data": json.dumps(payload, ensure_ascii=False),
    }


# crawled_at은 첫 등장 시점을 보존하도록 upsert에서 갱신 제외.
_UPSERT_SQL = """
INSERT INTO listings (
    source_id, external_id, title, facility_name, facility_type,
    target_age_min, target_age_max, period_start, period_end,
    registration_start, registration_end, status, fee_won, source_url,
    crawled_at, last_seen_at, data
) VALUES (
    :source_id, :external_id, :title, :facility_name, :facility_type,
    :target_age_min, :target_age_max, :period_start, :period_end,
    :registration_start, :registration_end, :status, :fee_won, :source_url,
    :crawled_at, :last_seen_at, :data
)
ON CONFLICT(source_id, external_id) DO UPDATE SET
    title              = excluded.title,
    facility_name      = excluded.facility_name,
    facility_type      = excluded.facility_type,
    target_age_min     = excluded.target_age_min,
    target_age_max     = excluded.target_age_max,
    period_start       = excluded.period_start,
    period_end         = excluded.period_end,
    registration_start = excluded.registration_start,
    registration_end   = excluded.registration_end,
    status             = excluded.status,
    fee_won            = excluded.fee_won,
    source_url         = excluded.source_url,
    last_seen_at       = excluded.last_seen_at,
    data               = excluded.data
"""


def upsert(conn: sqlite3.Connection, listing: ClassListing) -> None:
    conn.execute(_UPSERT_SQL, _row_from(listing))


def upsert_many(conn: sqlite3.Connection, listings: Iterable[ClassListing]) -> int:
    rows = [_row_from(c) for c in listings]
    if not rows:
        return 0
    conn.executemany(_UPSERT_SQL, rows)
    return len(rows)


def get(conn: sqlite3.Connection, source_id: str, external_id: str) -> Optional[ClassListing]:
    row = conn.execute(
        "SELECT data FROM listings WHERE source_id=? AND external_id=?",
        (source_id, external_id),
    ).fetchone()
    if row is None:
        return None
    return ClassListing.model_validate(json.loads(row["data"]))


# 기본 검색은 유치원생(4~7세, 초등 입학 전) — 본 서비스의 1차 페르소나.
DEFAULT_AGE_MIN = 4
DEFAULT_AGE_MAX = 7

# 부모 입장에서 보고 싶은 우선순위. SQLite CASE로 정렬에 직접 박는다.
_STATUS_PRIORITY: dict[str, int] = {
    "recruiting": 0,   # 지금 신청 가능 — 1순위
    "waitlist": 1,     # 대기 — 곧 자리 날 수도
    "upcoming": 2,     # 모집 시작 예정
    "in_progress": 3,  # 진행중 (중도 합류 어려움)
    "ended": 4,
    "closed": 5,
    "unknown": 6,
}


def _status_priority_case(column: str = "status") -> str:
    parts = [f"WHEN '{k}' THEN {v}" for k, v in _STATUS_PRIORITY.items()]
    return f"CASE {column} " + " ".join(parts) + " ELSE 99 END"


def search_kids(
    conn: sqlite3.Connection,
    *,
    age_min: int = DEFAULT_AGE_MIN,
    age_max: int = DEFAULT_AGE_MAX,
    statuses: Optional[Iterable[str]] = None,
    limit: int = 100,
) -> list[ClassListing]:
    """`age_min..age_max` 와 겹치는 강좌.

    정렬: 상태 우선순위(recruiting → ended) 후 registration_end ASC (가까운 마감 먼저).
    age 컬럼이 NULL인 항목은 검색에서 제외 (raw text는 살아있음).

    statuses=None 이면 모든 상태 반환. ['recruiting', 'upcoming'] 처럼 묶어 받을 수 있음.
    """
    sql = (
        "SELECT data FROM listings "
        "WHERE target_age_min IS NOT NULL "
        "AND target_age_max IS NOT NULL "
        "AND target_age_min <= ? "
        "AND target_age_max >= ? "
    )
    args: list = [age_max, age_min]
    if statuses:
        statuses = list(statuses)
        placeholders = ",".join("?" * len(statuses))
        sql += f"AND status IN ({placeholders}) "
        args.extend(statuses)
    sql += (
        f"ORDER BY {_status_priority_case()}, "
        # 모집 마감이 가까운 순. NULL은 뒤로.
        "CASE WHEN registration_end IS NULL THEN 1 ELSE 0 END, "
        "registration_end ASC, "
        "period_start ASC "
        "LIMIT ?"
    )
    args.append(limit)
    rows = conn.execute(sql, args).fetchall()
    return [ClassListing.model_validate(json.loads(r["data"])) for r in rows]
