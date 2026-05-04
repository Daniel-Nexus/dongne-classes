"""송파구청 통합 강좌 신청 시스템.

URL 패턴:
- listing: /learn/youth/program/lecture_list.do?searchVal8={target}&page={N}
  - searchVal8: 27 = 유아, 28 = 어린이
  - page 파라미터는 form 의 hidden field 이름 ("pageIndex"가 아님). goPageNavigation(N) JS가 form submit.
- detail:  /learn/youth/program/lecture_view.do?lecture_idx={id}

listing은 한 강좌를 list/grid 두 뷰로 렌더해 anchor가 2배로 나오므로 external_id 기준 dedupe 필요.

렌더링: SSR. 익명 GET으로 listing/detail 모두 접근 가능.
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


BASE = "https://www.songpa.go.kr"
LIST_PATH = "/learn/youth/program/lecture_list.do"
DETAIL_PATH = "/learn/youth/program/lecture_view.do"

TARGET_KIDS = 28      # 어린이
TARGET_INFANT = 27    # 유아

# 우선순위 순서대로 substring 매칭. "온라인신청가능" 같은 합성 텍스트 처리.
# 외부홈페이지는 외부 사이트로 위임된 상태 — 우리 입장에선 미상.
_STATUS_RULES: list[tuple[str, Status]] = [
    ("신청가능", Status.RECRUITING),
    ("신청마감", Status.CLOSED),
    ("접수대기", Status.UPCOMING),
    ("대기신청", Status.WAITLIST),
    ("교육전", Status.UPCOMING),
    ("교육중", Status.IN_PROGRESS),
    ("교육종료", Status.ENDED),
]


def _map_reg_method(text: str) -> RegistrationMethod:
    has_online = "온라인" in text
    has_visit = "방문" in text
    has_phone = "전화" in text
    if sum([has_online, has_visit, has_phone]) >= 2:
        return RegistrationMethod.MIXED
    if has_online:
        return RegistrationMethod.ONLINE
    if has_visit:
        return RegistrationMethod.VISIT
    if has_phone:
        return RegistrationMethod.PHONE
    return RegistrationMethod.UNKNOWN


def _detail_url(lecture_idx: str) -> str:
    return f"{BASE}{DETAIL_PATH}?lecture_idx={lecture_idx}"


def _list_url(target_val: int, page: int) -> str:
    return f"{BASE}{LIST_PATH}?searchVal8={target_val}&page={page}"


class SongpaGuOfficeSource(Source):
    source_id = "songpa_gu_office"
    name = "송파구청 통합 강좌"
    base_url = BASE + LIST_PATH
    facility_type = FacilityType.GU_OFFICE
    notes = "동주민센터/구청/진학학습지원센터 강좌 통합. SSR + GET pagination."

    def __init__(self, *, request_delay: float = 0.5, max_pages_per_target: int = 100):
        self.request_delay = request_delay
        self.max_pages_per_target = max_pages_per_target

    def crawl(self) -> Iterator[ClassListing]:
        for target_val in (TARGET_INFANT, TARGET_KIDS):
            yield from self._crawl_target(target_val)

    def _crawl_target(self, target_val: int) -> Iterator[ClassListing]:
        page = 1
        total_pages: Optional[int] = None
        while page <= self.max_pages_per_target:
            items, tp = self._list_page(target_val, page)
            if not items:
                return
            if total_pages is None:
                total_pages = tp
            for item in items:
                detail = self._detail(item["external_id"])
                yield self._build(item, detail)
                time.sleep(self.request_delay)
            if total_pages and page >= total_pages:
                return
            page += 1

    def _list_page(self, target_val: int, page: int) -> tuple[list[dict], Optional[int]]:
        url = _list_url(target_val, page)
        r = fetch(url, FetchMode.HTTP)
        if r.status != 200:
            return [], None
        body = r.body.decode("utf-8", "ignore") if isinstance(r.body, bytes) else r.body
        tree = lxml_html.fromstring(body)

        # 같은 강좌가 list/grid 두 뷰로 렌더되어 anchor가 2배로 잡힘 → 첫 occurrence 유지.
        items: list[dict] = []
        seen_ids: set[str] = set()
        for a in tree.xpath('//a[contains(@class, "program_link")]'):
            href = a.get("href", "")
            m = re.search(r"lecture_idx=(\d+)", href)
            if not m:
                continue
            external_id = m.group(1)
            title_el = a.xpath('.//span[@class="lec_tit"]')
            title = title_el[0].text_content().strip() if title_el else ""
            loca_el = a.xpath('.//span[@class="loca"]')
            loca = loca_el[0].text_content().strip().rstrip("/").strip() if loca_el else ""
            # title이 빈 view variant는 skip (다른 view로 같은 idx가 들어옴).
            if external_id in seen_ids:
                continue
            seen_ids.add(external_id)
            if not title:
                # title 없는 variant가 먼저 잡혀도 다음 variant를 받도록 seen에서 제거.
                seen_ids.discard(external_id)
                continue

            items.append({
                "external_id": external_id,
                "source_url": urljoin(BASE, href),
                "title": title,
                "facility_name": loca,
            })

        # total pages: <span class="total">N</span>
        total_pages: Optional[int] = None
        m_total = re.search(r'class="total"[^>]*>(\d+)<', body)
        if m_total:
            total_pages = int(m_total.group(1))
        return items, total_pages

    def _detail(self, lecture_idx: str) -> dict:
        url = _detail_url(lecture_idx)
        r = fetch(url, FetchMode.HTTP)
        if r.status != 200:
            return {}
        body = r.body.decode("utf-8", "ignore") if isinstance(r.body, bytes) else r.body

        # status: <span class="...link_btn...">교육전|신청가능|...</span>
        m_status = re.search(
            r'<span[^>]*class="[^"]*link_btn[^"]*"[^>]*>\s*([^<\s][^<]*?)\s*</span>',
            body,
        )
        status_text = m_status.group(1).strip() if m_status else ""

        text = re.sub(r"<[^>]+>", " ", body)
        text = re.sub(r"\s+", " ", text)

        def grab(label: str) -> str:
            # `LABEL : VALUE` until next known label/marker. 짧게 끊어 노이즈 차단.
            stops = (
                r"교육기간|교육시간|교육대상|교육장소|수강료|접수기간|접수방법|문의|강사"
                r"|기본정보|강좌정보|메뉴|강의실|주소|지도보기|모집인원|연령제한|좋아요|교육기관|교육분야"
            )
            pat = rf"{label}\s*:?\s*((?:(?!{stops}).){{1,200}})"
            m = re.search(pat, text)
            return m.group(1).strip(" :|") if m else ""

        return {
            "edu_period": grab("교육기간"),
            "edu_time": grab("교육시간"),
            "target_desc": grab("교육대상"),
            "venue": grab("교육장소"),
            "fee": grab("수강료"),
            "reg_period": grab("접수기간"),
            "reg_method": grab("접수방법"),
            "contact": grab("문의"),
            "status_text": status_text,
        }

    def _build(self, item: dict, detail: dict) -> ClassListing:
        period_start, period_end = parse_period(detail.get("edu_period", ""))
        reg_start, reg_end = parse_period(detail.get("reg_period", ""))
        days, sched_time = parse_schedule(detail.get("edu_time", ""))
        fee_won = parse_fee(detail.get("fee", ""))
        target_desc = detail.get("target_desc") or None
        venue = detail.get("venue") or None
        reg_method = _map_reg_method(detail.get("reg_method", ""))
        status: Status = match_first(  # type: ignore[assignment]
            detail.get("status_text", ""), _STATUS_RULES, Status.UNKNOWN
        )
        age_min, age_max = normalize_target_age(target_desc or "")
        now = datetime.now()
        return ClassListing(
            source_id=self.source_id,
            external_id=item["external_id"],
            source_url=item["source_url"],
            title=item["title"],
            facility_name=item.get("facility_name") or "송파구청",
            facility_type=self.facility_type,
            venue_detail=venue,
            target_description=target_desc,
            target_age_min=age_min,
            target_age_max=age_max,
            schedule_days=days,
            schedule_time=sched_time,
            period_start=period_start,
            period_end=period_end,
            registration_start=reg_start,
            registration_end=reg_end,
            registration_method=reg_method,
            status=status,
            fee_won=fee_won,
            crawled_at=now,
            last_seen_at=now,
            raw={"detail": detail},
        )
