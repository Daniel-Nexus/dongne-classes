"""송파구 통합도서관 (splib).

URL 패턴:
- listing: /intro/menu/10052/program/30014/eventList.do?currentPageNo={N}&eventTargetCd={code}&manageCd=ALL
  - eventTargetCd: CHL 유아, KID 아동, YNG 청소년
- detail (참고): /intro/program/eventDetail.do?eventIdx={id}

특징: listing 자체가 풍부 (분야/대상/수강료/교육기간/시간/장소/접수일정/상태)
→ detail page 호출 불필요. 빠르고 부담 적음.

페이지당 article-list 컨테이너 단위로 순회하면 dedupe 자동 (fnDetail 콜은
list/grid 두 view에서 잡혀 더 많지만 article-list는 항목당 1개).
"""
from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Iterator, Optional

from lxml import html as lxml_html

from src.fetcher import FetchMode, fetch
from src.models import ClassListing, FacilityType, RegistrationMethod, Status
from src.parsers import (
    match_first,
    normalize_target_age,
    parse_date,
    parse_fee,
    parse_schedule,
)
from src.sources.base import Source


BASE = "https://www.splib.or.kr"
LIST_PATH = "/intro/menu/10052/program/30014/eventList.do"
DETAIL_PATH = "/intro/program/eventDetail.do"

TARGET_INFANT = "CHL"  # 유아
TARGET_KIDS = "KID"    # 아동

# manageCd 코드 → 분관 풀네임 (home 페이지 select 옵션에서 추출).
BRANCH_NAMES: dict[str, str] = {
    "ME": "송파글마루도서관",
    "MA": "송파어린이도서관",
    "MH": "송파위례도서관",
    "MB": "거마도서관",
    "MF": "돌마리도서관",
    "BA": "풍납도서관",
    "BB": "소나무언덕2호도서관",
    "BC": "소나무언덕3호도서관",
    "BD": "소나무언덕4호도서관",
    "MC": "소나무언덕잠실본동도서관",
    "MD": "송파어린이영어도서관",
    "MG": "가락몰도서관",
}

_STATUS_RULES: list[tuple[str, Status]] = [
    ("접수예정", Status.UPCOMING),
    ("접수중", Status.RECRUITING),
    ("대기접수", Status.WAITLIST),
    ("접수마감", Status.CLOSED),
    ("교육중", Status.IN_PROGRESS),
    # "종료" 단독 표기와 "교육종료" 둘 다 ENDED로 매핑.
    ("종료", Status.ENDED),
]


_TIME_RANGE = re.compile(r"\d{1,2}:\d{2}\s*[~\-]\s*\d{1,2}:\d{2}")


def _list_url(target_code: str, page: int) -> str:
    return (
        f"{BASE}{LIST_PATH}?currentPageNo={page}"
        f"&eventTargetCd={target_code}&manageCd=ALL"
    )


def _detail_url(event_idx: str) -> str:
    return f"{BASE}{DETAIL_PATH}?eventIdx={event_idx}"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _strip_label(span_text: str) -> str:
    """`분야 :자연과학` → `자연과학`. label 부분 제거."""
    return re.sub(r"^[^:]+:\s*", "", _norm(span_text))


class SplibSource(Source):
    source_id = "splib"
    name = "송파구통합도서관"
    base_url = BASE + LIST_PATH
    facility_type = FacilityType.LIBRARY
    notes = "송파구 13개 도서관 통합. listing inline data — detail fetch 불필요."

    def __init__(self, *, request_delay: float = 0.3, max_pages_per_target: int = 30):
        self.request_delay = request_delay
        self.max_pages_per_target = max_pages_per_target

    def crawl(self) -> Iterator[ClassListing]:
        for code in (TARGET_INFANT, TARGET_KIDS):
            yield from self._crawl_target(code)

    def _crawl_target(self, code: str) -> Iterator[ClassListing]:
        # 빈 페이지가 나오면 종료. "총건수" 표기는 (총N명) 같은 capacity 텍스트와 충돌 가능.
        page = 1
        seen_ids: set[str] = set()
        while page <= self.max_pages_per_target:
            items = self._list_page(code, page)
            if not items:
                return
            new = [c for c in items if c.external_id not in seen_ids]
            if not new:
                # 같은 페이지가 반복되면 (페이지 초과 시 마지막 페이지를 다시 주는 사이트도 있음) 종료.
                return
            for c in new:
                seen_ids.add(c.external_id)
                yield c
            time.sleep(self.request_delay)
            page += 1

    def _list_page(self, code: str, page: int) -> list[ClassListing]:
        url = _list_url(code, page)
        r = fetch(url, FetchMode.HTTP)
        if r.status != 200:
            return []
        body = r.body.decode("utf-8", "ignore") if isinstance(r.body, bytes) else r.body
        tree = lxml_html.fromstring(body)

        items: list[ClassListing] = []
        for art in tree.xpath('//div[@class="article-list"]'):
            listing = self._parse_article(art)
            if listing is not None:
                items.append(listing)
        return items

    def _parse_article(self, art) -> Optional[ClassListing]:
        title_a = art.xpath('.//div[@class="title"]/a')
        if not title_a:
            return None
        a = title_a[0]
        onclick = a.get("onclick", "")
        m_idx = re.search(r"fnDetail\('?(\d+)'?\)", onclick)
        if not m_idx:
            return None
        event_idx = m_idx.group(1)

        # 분관 코드: <span class="lib BD"> 같이 두 클래스 — 'lib' 외 하나가 코드.
        branch_code = ""
        lib_span = a.xpath('.//span[contains(@class, "lib")]')
        if lib_span:
            for c in lib_span[0].get("class", "").split():
                if c != "lib" and len(c) == 2 and c.isalpha():
                    branch_code = c.upper()
                    break

        # 제목: anchor 텍스트에서 분관 라벨 제거.
        full_text = a.text_content()
        if lib_span:
            full_text = full_text.replace(lib_span[0].text_content(), "", 1)
        title = _norm(full_text)

        info_rows = art.xpath('.//div[@class="info"]')

        category: Optional[str] = None
        target_desc: Optional[str] = None
        fee_won: Optional[int] = None
        period_start = period_end = None
        reg_start = reg_end = None
        sched_time: Optional[str] = None
        sched_days: list[str] = []
        venue: Optional[str] = None

        # row 1: 분야 / 대상 / 수강료
        if len(info_rows) >= 1:
            for sp in info_rows[0].xpath("./span"):
                text = _norm(sp.text_content())
                if text.startswith("분야"):
                    category = _strip_label(text) or None
                elif text.startswith("대상"):
                    target_desc = _strip_label(text) or None
                elif text.startswith("수강료"):
                    fee_won = parse_fee(_strip_label(text))

        # row 2: 교육기간 + 시간 + 장소
        if len(info_rows) >= 2:
            row = info_rows[1]
            row_text = _norm(row.text_content())
            m_period = re.search(
                r"교육기간\s*:\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})", row_text
            )
            if m_period:
                period_start = parse_date(m_period.group(1))
                period_end = parse_date(m_period.group(2))
            sched_days, sched_time = parse_schedule(row_text)
            # 라벨 없는 마지막 <span>이 장소.
            for sp in reversed(row.xpath("./span")):
                t = _norm(sp.text_content())
                if t and ":" not in t and not _TIME_RANGE.search(t):
                    venue = t
                    break

        # row 3: 접수일정
        if len(info_rows) >= 3:
            row_text = _norm(info_rows[2].text_content())
            m_reg = re.search(
                r"접수일정\s*:\s*(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2})\s*~\s*(\d{4}-\d{2}-\d{2}\s*\d{2}:\d{2})",
                row_text,
            )
            if m_reg:
                reg_start = parse_date(m_reg.group(1))
                reg_end = parse_date(m_reg.group(2))

        status_text = ""
        sb = art.xpath('.//div[contains(@class, "statusBox")]')
        if sb:
            status_text = _norm(sb[0].text_content())

        facility_name = BRANCH_NAMES.get(branch_code, "송파구통합도서관")
        age_min, age_max = normalize_target_age(
            target_desc or "", today_year=datetime.now().year
        )
        now = datetime.now()
        return ClassListing(
            source_id=self.source_id,
            external_id=event_idx,
            source_url=_detail_url(event_idx),
            title=title,
            category=category,
            facility_name=facility_name,
            facility_type=self.facility_type,
            venue_detail=venue,
            target_description=target_desc,
            target_age_min=age_min,
            target_age_max=age_max,
            schedule_days=sched_days,
            schedule_time=sched_time,
            period_start=period_start,
            period_end=period_end,
            registration_start=reg_start,
            registration_end=reg_end,
            registration_method=RegistrationMethod.ONLINE,
            status=match_first(status_text, _STATUS_RULES, Status.UNKNOWN),  # type: ignore[arg-type]
            fee_won=fee_won,
            crawled_at=now,
            last_seen_at=now,
            raw={"branch_code": branch_code, "status_text": status_text},
        )
