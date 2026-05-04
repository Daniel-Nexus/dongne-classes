"""송파어린이문화회관 (songpakids.com).

URL 패턴:
- listing: /site/main/edu/TALENT/list?cp={N}&pageSize=12 (cp=20부터 빈 페이지로 종료)
- detail:  /site/main/edu/{eduIdx}

특징: listing item 자체가 풍부 (대상/기간/시간/정원/수강료) → detail fetch 불필요.
어린이 시설이지만 대상은 유아/초등/부모/단체 섞여 있음 — 전부 받아 target_age 정규화로 분류.
"""
from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Iterator, Optional
from urllib.parse import urljoin

from lxml import html as lxml_html

from src.fetcher import FetchMode, fetch
from src.models import ClassListing, FacilityType, RegistrationMethod, Status
from src.parsers import (
    match_first,
    normalize_target_age,
    parse_fee,
    parse_period,
    parse_schedule,
)
from src.sources.base import Source


BASE = "https://www.songpakids.com"
LIST_PATH = "/site/main/edu/TALENT/list"
DETAIL_PATH_PREFIX = "/site/main/edu/"


_STATUS_RULES: list[tuple[str, Status]] = [
    ("모집중", Status.RECRUITING),
    ("모집마감", Status.CLOSED),
    ("모집 마감", Status.CLOSED),
    ("교육종료", Status.ENDED),
    ("교육 종료", Status.ENDED),
    ("교육중", Status.IN_PROGRESS),
    ("대기", Status.WAITLIST),
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _list_url(page: int, page_size: int = 12) -> str:
    return f"{BASE}{LIST_PATH}?cp={page}&pageSize={page_size}"


def _detail_url(edu_idx: str) -> str:
    return f"{BASE}{DETAIL_PATH_PREFIX}{edu_idx}"


_DD_BY_LABEL = {
    "강의대상": "target",
    "강의기간": "period",
    "강의시간": "schedule",
    "강의정원": "capacity",
    "수강료": "fee",
}


def _extract_dl_pairs(box) -> dict:
    """`<dl><dt>강의대상</dt><dd>...</dd></dl>` 묶음을 라벨→값 dict로.

    `수 강 료` 처럼 공백이 들어간 라벨도 정규화해 매칭.
    """
    result: dict = {}
    for dl in box.xpath('.//dl'):
        dt = dl.xpath('./dt')
        dd = dl.xpath('./dd')
        if not dt or not dd:
            continue
        label_raw = _norm(dt[0].text_content()).replace(" ", "")
        if label_raw not in _DD_BY_LABEL:
            continue
        result[_DD_BY_LABEL[label_raw]] = _norm(dd[0].text_content())
    return result


_CAPACITY_RE = re.compile(r"정원\s*(\d+)\s*명\s*/\s*신청\s*(\d+)\s*명")


def _parse_capacity(text: str) -> Optional[int]:
    """`12명 (정원 12명 / 신청 1명)` → 12. 정원 숫자만 반환."""
    if not text:
        return None
    m = _CAPACITY_RE.search(text)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*명", text)
    return int(m.group(1)) if m else None


class SongpaKidsSource(Source):
    source_id = "songpa_kids"
    name = "송파어린이문화회관"
    base_url = BASE + LIST_PATH
    facility_type = FacilityType.KIDS_CULTURE
    notes = "재능프로그램 (TALENT). listing inline data — detail 불필요."

    def __init__(self, *, request_delay: float = 0.3, max_pages: int = 30):
        self.request_delay = request_delay
        self.max_pages = max_pages

    def crawl(self) -> Iterator[ClassListing]:
        for page in range(1, self.max_pages + 1):
            items = self._list_page(page)
            if not items:
                return
            for c in items:
                yield c
            time.sleep(self.request_delay)

    def _list_page(self, page: int) -> list[ClassListing]:
        url = _list_url(page)
        r = fetch(url, FetchMode.HTTP)
        if r.status != 200:
            return []
        body = r.body.decode("utf-8", "ignore") if isinstance(r.body, bytes) else r.body
        tree = lxml_html.fromstring(body)

        items: list[ClassListing] = []
        for box in tree.xpath('//div[contains(@class, "content-box")]'):
            listing = self._parse_box(box)
            if listing is not None:
                items.append(listing)
        return items

    def _parse_box(self, box) -> Optional[ClassListing]:
        href_a = box.xpath('./a')
        if not href_a:
            return None
        href = href_a[0].get("href", "")
        m_idx = re.search(r"/site/main/edu/(\d+)", href)
        if not m_idx:
            return None
        edu_idx = m_idx.group(1)

        title_el = box.xpath('.//p[contains(@class, "title")]')
        title = _norm(title_el[0].text_content()) if title_el else ""
        if not title:
            return None

        # status badge: <span class="current ..."> 텍스트 </span>
        status_text = ""
        st = box.xpath('.//span[contains(@class, "current")]')
        if st:
            status_text = _norm(st[0].text_content())

        pairs = _extract_dl_pairs(box)
        target_text = pairs.get("target", "")
        period_start, period_end = parse_period(pairs.get("period", ""))
        sched_days, sched_time = parse_schedule(pairs.get("schedule", ""))
        capacity = _parse_capacity(pairs.get("capacity", ""))
        fee_won = parse_fee(pairs.get("fee", ""))
        age_min, age_max = normalize_target_age(
            target_text, today_year=datetime.now().year
        )

        now = datetime.now()
        return ClassListing(
            source_id=self.source_id,
            external_id=edu_idx,
            source_url=urljoin(BASE, href),
            title=title,
            facility_name="송파어린이문화회관",
            facility_type=self.facility_type,
            target_description=target_text or None,
            target_age_min=age_min,
            target_age_max=age_max,
            schedule_days=sched_days,
            schedule_time=sched_time,
            period_start=period_start,
            period_end=period_end,
            capacity=capacity,
            registration_method=RegistrationMethod.ONLINE,
            status=match_first(status_text, _STATUS_RULES, Status.UNKNOWN),  # type: ignore[arg-type]
            fee_won=fee_won,
            crawled_at=now,
            last_seen_at=now,
            raw={"status_text": status_text},
        )
