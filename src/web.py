"""FastAPI 검색 슬라이스.

단일 페이지 — GET 폼으로 필터(연령/상태/시설/시설타입/무료여부) → 서버 렌더 결과.
JS 프레임워크 없음, Tailwind CDN으로 스타일만. 추후 HTMX/SPA 도입 여지 보존.

실행:
    DONGNE_DB=data/dongne.db uvicorn src.web:app --reload
또는:
    python -m src.web
"""
from __future__ import annotations

import os
import sqlite3
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src import storage
from src.models import Status


DB_PATH = os.environ.get("DONGNE_DB", "data/dongne.db")
TEMPLATES_DIR = Path(__file__).parent / "templates"

# 검색 UI에 노출할 상태 (uknown 등 운영 노이즈 제외).
STATUS_OPTIONS: list[tuple[str, str]] = [
    ("recruiting", "모집중"),
    ("upcoming", "모집예정"),
    ("waitlist", "대기"),
    ("in_progress", "진행중"),
    ("closed", "마감"),
    ("ended", "종료"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    app.state.conn = storage.connect(DB_PATH)
    yield
    app.state.conn.close()


app = FastAPI(title="dongne-classes", lifespan=lifespan)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_conn(request: Request) -> sqlite3.Connection:
    return request.app.state.conn


def _facility_options(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT facility_name, COUNT(*) c FROM listings "
        "GROUP BY facility_name ORDER BY c DESC"
    ).fetchall()
    return [r["facility_name"] for r in rows]


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    age_min: int = Query(storage.DEFAULT_AGE_MIN, ge=0, le=99),
    age_max: int = Query(storage.DEFAULT_AGE_MAX, ge=0, le=99),
    status: list[str] = Query(default_factory=lambda: ["recruiting", "upcoming"]),
    facility: Optional[str] = Query(None),
    free_only: bool = Query(False),
    limit: int = Query(60, ge=1, le=300),
    conn: sqlite3.Connection = Depends(get_conn),
):
    # search_kids 결과를 받고 시설/무료 필터는 후처리 (저장소는 일반 검색만 노출).
    listings = storage.search_kids(
        conn,
        age_min=age_min,
        age_max=age_max,
        statuses=status or None,
        limit=limit * 3,  # 후처리 필터로 빠지는 분량 여유.
    )
    if facility:
        listings = [c for c in listings if c.facility_name == facility]
    if free_only:
        listings = [c for c in listings if c.fee_won == 0]
    listings = listings[:limit]

    status_counts = Counter(c.status.value for c in listings)
    total_in_db = conn.execute("SELECT COUNT(*) c FROM listings").fetchone()["c"]
    last_seen = conn.execute(
        "SELECT MAX(last_seen_at) m FROM listings"
    ).fetchone()["m"]

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "listings": listings,
            "age_min": age_min,
            "age_max": age_max,
            "selected_statuses": set(status),
            "facility": facility or "",
            "free_only": free_only,
            "limit": limit,
            "status_options": STATUS_OPTIONS,
            "facility_options": _facility_options(conn),
            "result_count": len(listings),
            "status_counts": status_counts,
            "total_in_db": total_in_db,
            "last_seen": last_seen,
        },
    )


@app.get("/api/search")
def api_search(
    age_min: int = Query(storage.DEFAULT_AGE_MIN, ge=0, le=99),
    age_max: int = Query(storage.DEFAULT_AGE_MAX, ge=0, le=99),
    status: list[str] = Query(default_factory=lambda: ["recruiting", "upcoming"]),
    facility: Optional[str] = Query(None),
    free_only: bool = Query(False),
    limit: int = Query(60, ge=1, le=300),
    conn: sqlite3.Connection = Depends(get_conn),
):
    listings = storage.search_kids(
        conn,
        age_min=age_min,
        age_max=age_max,
        statuses=status or None,
        limit=limit * 3,
    )
    if facility:
        listings = [c for c in listings if c.facility_name == facility]
    if free_only:
        listings = [c for c in listings if c.fee_won == 0]
    listings = listings[:limit]
    return {
        "count": len(listings),
        "results": [c.model_dump(mode="json") for c in listings],
    }


def main() -> None:
    import uvicorn
    uvicorn.run("src.web:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
