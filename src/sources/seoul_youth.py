"""서울시 청소년수련시설 통합신청 (online5XX.youth.seoul.kr).

URL 패턴:
- home (warm-up + 카테고리 발견): /center_index.php?center_id={N}
- listing (POST AJAX): /s_center/Lecture_Search_List7.ajax.php
  - data: item1=center_id, item2=category, page=N, search='', center_id=center_id
  - center_id 누락 시 500. 세션 cookie 필요(home 한 번 호출).

특징:
- 항목별 데이터가 `<tr>` 컬럼에 모두 inline + `goLink(...)` onclick에 metadata URL-encoded.
- 카테고리는 센터별 다름 (예: 507=008/009/029, 538=030/031). 홈 페이지의 `data-id`에서 발견.
- `goLink` arg7 = 강좌 제목 (요일/시간/호실/연령/메모 포함). arg10 = fee_won.

확장: center_ids 리스트로 여러 센터 동시 크롤. 25개 구 통합 가설은 부분 기각이라
실 라이브 ID는 별도 레지스트리. (현재 확인된 것: 507/508/510/538/540/545)
"""
from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Iterable, Iterator, Optional
from urllib.parse import unquote_plus

from lxml import html as lxml_html

from src.fetcher import FetchMode, fetch, post
from src.models import ClassListing, FacilityType, RegistrationMethod, Status
from src.parsers import (
    extract_explicit_age,
    keyword_age,
    match_first,
    parse_fee,
    parse_schedule,
)
from src.sources.base import Source


# 직접 확인된 라이브 센터 목록 (Phase 2: 자동 디렉터리 발굴).
KNOWN_CENTERS: dict[int, str] = {
    507: "송파청소년센터",
    508: "역삼청소년센터",
    510: "중구청소년센터",
    538: "잠실청소년센터",
    540: "천왕동청소년문화의집",
    545: "천호청소년문화의집",
}


def _home_url(center_id: int) -> str:
    return f"https://online{center_id}.youth.seoul.kr/center_index.php?center_id={center_id}"


def _ajax_url(center_id: int) -> str:
    return f"https://online{center_id}.youth.seoul.kr/s_center/Lecture_Search_List7.ajax.php"


_STATUS_RULES: list[tuple[str, Status]] = [
    ("수시접수", Status.RECRUITING),
    ("접수가능", Status.RECRUITING),
    ("접수예정", Status.UPCOMING),
    ("접수대기", Status.UPCOMING),
    ("접수마감", Status.CLOSED),
    ("접수불가", Status.CLOSED),
    ("대기", Status.WAITLIST),
    ("종료", Status.ENDED),
    ("교육중", Status.IN_PROGRESS),
]

# `category data-id` 가 3자리 숫자 + center_id 자체는 제외.
_DATA_ID_RE = re.compile(r'data-id="(\d{3})"')

# `goLink('id','cat_url','008','019','091','507','1','title_url','507','01','36000')` 패턴.
_GOLINK_RE = re.compile(r"goLink\(([^)]+)\)")


def _split_golink_args(arg_blob: str) -> list[str]:
    # `'a','b','c'` → ['a','b','c']. URL-encoded 안에 콤마는 없음 (안전).
    return [a.strip().strip("'\"") for a in arg_blob.split(",")]


def _discover_categories(center_id: int) -> list[str]:
    """홈 페이지에서 강습반 카테고리(item2) ID 추출."""
    r = fetch(_home_url(center_id), FetchMode.HTTP)
    if r.status != 200:
        return []
    body = r.body.decode("utf-8", "ignore") if isinstance(r.body, bytes) else r.body
    cid_str = str(center_id)
    cats = [m for m in _DATA_ID_RE.findall(body) if m != cid_str]
    # 순서 보존 dedupe.
    seen: set[str] = set()
    return [c for c in cats if not (c in seen or seen.add(c))]


def _normalize_time_text(text: str) -> str:
    # `토\n14:00~14:50` 등 줄바꿈 정리.
    return re.sub(r"\s+", " ", text or "").strip()


def _parse_capacity(text: str) -> tuple[Optional[int], Optional[int]]:
    """`9/16` → (9, 16). (current, total)."""
    m = re.match(r"\s*(\d+)\s*/\s*(\d+)", text or "")
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


class SeoulYouthSource(Source):
    source_id = "seoul_youth"
    name = "서울시 청소년수련시설 통합신청"
    base_url = "https://online507.youth.seoul.kr"
    facility_type = FacilityType.YOUTH_CENTER
    notes = "online{NNN}.youth.seoul.kr SaaS. 센터별 카테고리는 홈 페이지에서 발견."

    def __init__(
        self,
        *,
        center_ids: Iterable[int] = (507, 538),
        request_delay: float = 0.4,
        max_pages_per_category: int = 30,
    ):
        self.center_ids = list(center_ids)
        self.request_delay = request_delay
        self.max_pages_per_category = max_pages_per_category

    def crawl(self) -> Iterator[ClassListing]:
        for cid in self.center_ids:
            yield from self._crawl_center(cid)

    def _crawl_center(self, center_id: int) -> Iterator[ClassListing]:
        cats = _discover_categories(center_id)
        if not cats:
            return
        for cat in cats:
            page = 1
            seen_ids: set[str] = set()
            while page <= self.max_pages_per_category:
                items = self._list_page(center_id, cat, page)
                if not items:
                    break
                new = [c for c in items if c.external_id not in seen_ids]
                if not new:
                    break
                for c in new:
                    seen_ids.add(c.external_id)
                    yield c
                time.sleep(self.request_delay)
                page += 1

    def _list_page(self, center_id: int, item2: str, page: int) -> list[ClassListing]:
        r = post(
            _ajax_url(center_id),
            data={
                "item1": str(center_id),
                "item2": item2,
                "target": "",
                "page": str(page),
                "search": "",
                "center_id": str(center_id),
            },
            headers={
                "Referer": _home_url(center_id),
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        if r.status != 200:
            return []
        body = r.body.decode("utf-8", "ignore") if isinstance(r.body, bytes) else r.body
        if not body or "goLink" not in body:
            return []

        tree = lxml_html.fromstring(body)
        items: list[ClassListing] = []
        for tr in tree.xpath("//tr[.//a[contains(@onclick, 'goLink')]]"):
            listing = self._parse_row(tr, center_id, item2)
            if listing is not None:
                items.append(listing)
        return items

    def _parse_row(self, tr, center_id: int, item2: str) -> Optional[ClassListing]:
        a_nodes = tr.xpath(".//a[contains(@onclick, 'goLink')]")
        if not a_nodes:
            return None
        onclick = a_nodes[0].get("onclick", "")
        m = _GOLINK_RE.search(onclick)
        if not m:
            return None
        args = _split_golink_args(m.group(1))
        if len(args) < 11:
            return None
        external_id = args[0]
        title_raw = unquote_plus(args[7])
        category_raw = unquote_plus(args[1])
        fee_str = args[10]
        try:
            fee_won = int(fee_str) if fee_str else None
        except ValueError:
            fee_won = None

        # `<tr>` 컬럼 텍스트 — 인덱스 가변일 수 있어 위치 대신 시그널로 추출.
        tds = tr.xpath("./td")
        col_texts = [_normalize_time_text(td.text_content()) for td in tds]
        room = col_texts[0] if len(col_texts) > 0 else None

        # day + time: <span class="sm">토<br><span class="cc">14:00~14:50</span></span>
        sched_text = ""
        sm = tr.xpath('.//span[@class="sm"]')
        if sm:
            sched_text = _normalize_time_text(sm[0].text_content())
        days, sched_time = parse_schedule(sched_text)

        # target text (col 5 typically): "청소년(1개월)"
        target_text = col_texts[4] if len(col_texts) > 4 else ""
        # 제목엔 `11~16세` 같은 명시 연령이 박혀있지만 `초등`/`청소년` 같은 키워드도 자유롭게
        # 등장 → title까지 키워드 fallback에 넣으면 (7,18) 식으로 너무 넓어짐.
        # 명시 연령은 title+target 둘 다 보고, 키워드 fallback은 target만으로 좁힌다.
        age_min, age_max = extract_explicit_age(
            f"{target_text} {title_raw}", today_year=datetime.now().year
        )
        if age_min is None:
            age_min, age_max = keyword_age(target_text)

        # capacity: "9/16" → 16
        capacity: Optional[int] = None
        for txt in col_texts:
            cur, tot = _parse_capacity(txt)
            if tot is not None:
                capacity = tot
                break

        # status는 센터별로 클래스가 다양 (rbn/rbf/rbd/rbb…). class 접두사 `rb`로 통일 매칭.
        # 신청 버튼(rbb)이 아닌 첫 결과를 우선하기 위해 rbb는 제외.
        status_text = ""
        rb = tr.xpath(
            './/span[(starts-with(@class, "rb") or contains(@class, " rb"))'
            ' and not(contains(@class, "rbb"))]'
        )
        if rb:
            status_text = _normalize_time_text(rb[0].text_content())

        if fee_won is None:
            # fallback: 가격 컬럼 텍스트 파싱
            for td in tds:
                price_span = td.xpath('.//span[contains(@class, "price")]')
                if price_span:
                    fee_won = parse_fee(_normalize_time_text(price_span[0].text_content()) + "원")
                    break

        facility_name = KNOWN_CENTERS.get(center_id, f"청소년센터({center_id})")
        now = datetime.now()
        # source_url은 신청 페이지 (외부 진입은 불가하지만 사용자 추적용으로 home + lecture_id 표기).
        source_url = (
            f"{_home_url(center_id)}#lecture={external_id}"
        )
        return ClassListing(
            source_id=self.source_id,
            external_id=f"{center_id}:{external_id}",  # 센터 간 collision 방지
            source_url=source_url,
            title=title_raw,
            category=category_raw or None,
            facility_name=facility_name,
            facility_type=self.facility_type,
            venue_detail=room or None,
            target_description=target_text or None,
            target_age_min=age_min,
            target_age_max=age_max,
            schedule_days=days,
            schedule_time=sched_time,
            capacity=capacity,
            registration_method=RegistrationMethod.ONLINE,
            status=match_first(status_text, _STATUS_RULES, Status.UNKNOWN),  # type: ignore[arg-type]
            fee_won=fee_won,
            crawled_at=now,
            last_seen_at=now,
            raw={
                "center_id": center_id,
                "item2": item2,
                "status_text": status_text,
                "title_raw": title_raw,
            },
        )
