"""크롤 파이프라인 — 다중 소스를 격리하여 실행 + DB upsert.

한 소스의 예외가 다른 소스로 전파되지 않게 try/except per source. 결과는
`SourceResult`로 모아서 호출 측이 상태 보고/알림에 쓸 수 있게.
"""
from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass
from typing import Iterable, Optional

from src import storage
from src.sources.base import Source

logger = logging.getLogger(__name__)


@dataclass
class SourceResult:
    source_id: str
    rows: int
    elapsed_sec: float
    error: Optional[str] = None  # 예외 클래스명 + 메시지 요약. None이면 성공.

    @property
    def ok(self) -> bool:
        return self.error is None


def configure_logging(level: int = logging.INFO) -> None:
    """기본 로깅 + Scrapling INFO 소음 제거.

    멱등하게 동작 — 여러 번 불러도 핸들러/Scrapling logger 교체 중복 없음.
    Scrapling은 자체 LoggerProxy(loguru 기반)로 stdout에 직접 INFO를 찍음.
    `set_logger()`로 stdlib logging.Logger를 주입해야 우리 레벨이 먹힘.
    """
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        root.addHandler(handler)
    root.setLevel(level)

    try:
        from scrapling.core.utils import set_logger
        scrapling_logger = logging.getLogger("scrapling")
        scrapling_logger.setLevel(logging.WARNING)
        set_logger(scrapling_logger)
    except Exception:
        # 버전 달라져 set_logger가 없거나 시그니처 바뀌어도 우리 코드 죽지 않게.
        logging.getLogger("scrapling").setLevel(logging.WARNING)


def crawl_source(source: Source, conn: sqlite3.Connection) -> SourceResult:
    sid = source.source_id
    t0 = time.time()
    try:
        rows = storage.upsert_many(conn, source.crawl())
        conn.commit()
    except Exception as exc:
        conn.rollback()
        elapsed = time.time() - t0
        logger.exception("source %s failed after %.1fs", sid, elapsed)
        return SourceResult(
            source_id=sid,
            rows=0,
            elapsed_sec=elapsed,
            error=f"{type(exc).__name__}: {exc}",
        )
    elapsed = time.time() - t0
    logger.info("source %s: %d rows in %.1fs", sid, rows, elapsed)
    return SourceResult(source_id=sid, rows=rows, elapsed_sec=elapsed)


def crawl_all(sources: Iterable[Source], conn: sqlite3.Connection) -> list[SourceResult]:
    return [crawl_source(s, conn) for s in sources]
