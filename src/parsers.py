"""소스 간 공유 파서 헬퍼.

여기에 들어오는 함수의 기준: 2개 이상 소스에서 동일하게 쓰임. 1개 소스에서만
쓰는 파싱은 해당 소스 모듈에 둔다 (premature abstraction 방지).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


_DAY_TOKEN = re.compile(r"[월화수목금토일]")
_TIME_RANGE = re.compile(r"\d{1,2}:\d{2}\s*[~\-]\s*\d{1,2}:\d{2}")


def parse_schedule(text: str) -> tuple[list[str], Optional[str]]:
    """`매주 월, 수 09:30~12:00` → (['월','수'], '09:30~12:00').

    `(화요일)` 같이 `요일`이 붙으면 `요일` 안의 `일`이 별도 day로 잘못 잡히므로 먼저 제거.
    """
    cleaned = re.sub(r"요일", " ", text or "")
    days = _DAY_TOKEN.findall(cleaned)
    seen: set[str] = set()
    days = [d for d in days if not (d in seen or seen.add(d))]
    tm = _TIME_RANGE.search(cleaned)
    return days, (tm.group(0).replace(" ", "") if tm else None)


# 한국 공공 사이트는 2자리/4자리 연도, datetime/date를 섞어 씀. 흔한 포맷 모두 시도.
_DATE_FORMATS = (
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%y-%m-%d %H:%M",
    "%y-%m-%d",
    "%Y.%m.%d %H:%M",
    "%Y.%m.%d",
)


def parse_date(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def parse_period(text: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """`26-04-28 ~ 26-04-29` 형식. 시작/끝 datetime 튜플."""
    parts = re.split(r"\s*~\s*", (text or "").strip(), maxsplit=1)
    if len(parts) != 2:
        return None, None
    return parse_date(parts[0]), parse_date(parts[1])


def parse_fee(text: str) -> Optional[int]:
    """`10,000원` → 10000, `무료`/`0원` → 0, 빈 문자열/매치 실패 → None."""
    if not text:
        return None
    if "무료" in text:
        return 0
    m = re.search(r"([\d,]+)\s*원", text)
    if not m:
        return None
    return int(m.group(1).replace(",", ""))


def match_first(text: str, rules: list[tuple[str, object]], default: object) -> object:
    """`text`에 등장하는 첫 needle을 매칭해 매핑값 반환. rules 순서가 우선순위.

    상태 라벨이 합성('온라인신청가능') 또는 짧은 단독('종료')으로 둘 다 등장하므로
    exact dict lookup 대신 substring matching이 견고.
    """
    for needle, value in rules:
        if needle in text:
            return value
    return default


# --- target_description 정규화 -----------------------------------------------

# 대분류 키워드 → 추정 연령 범위. 명시 연령이 없을 때 fallback.
# (한국 공공 사이트는 일관성이 낮아 keyword 단독 매핑은 거칠지만, raw text와
#  병행 보관하므로 손실은 없음.)
TARGET_AGE_DEFAULT: dict[str, tuple[int, int]] = {
    "유아": (0, 6),
    "아동": (7, 12),
    "어린이": (7, 12),
    "초등": (7, 12),
    "청소년": (13, 18),
    "중등": (13, 15),
    "고등": (16, 18),
    "성인": (19, 64),
    "시니어": (65, 99),
    "어르신": (65, 99),
}


# 명시 연령 표현. `7~9세`, `만 5~7세`, `5세~7세`, `5세 ~ 6세`, `초등 3~4학년`,
# `2019~2018년생`, `(2020년~2021년)` (생 생략된 생년 범위) 등 한국 사이트별 표기 다양.
_AGE_RANGE = re.compile(
    r"(?:만\s*)?(\d{1,2})\s*세?\s*[~\-]\s*(?:만\s*)?(\d{1,2})\s*세"
)
_AGE_SINGLE = re.compile(r"(?:만\s*)?(\d{1,2})\s*세")
# `N세 ~ 초M` 같이 좌우가 다른 단위로 섞이는 케이스 (songpakids에 흔함).
_AGE_TO_GRADE = re.compile(r"(?:만\s*)?(\d{1,2})\s*세\s*[~\-]\s*초\s*(\d)")
_GRADE_TO_AGE = re.compile(r"초\s*(\d)\s*[~\-]\s*(?:만\s*)?(\d{1,2})\s*세")
_GRADE_RANGE = re.compile(r"초등?\s*(\d)\s*[~\-]\s*(\d)\s*학년")
_GRADE_SINGLE = re.compile(r"초등?\s*(\d)\s*학년")
# `2019~2018년생` (年생 묶임) / `2020년 ~ 2021년` (年 분리, 생 생략)
_BIRTHYEAR_RANGE = re.compile(
    r"(\d{4})\s*년?\s*[~\-]\s*(\d{4})\s*년\s*생?"
)


def _grade_to_age(grade: int) -> int:
    # 초등 1학년 ≈ 만 7세 기준.
    return 6 + grade


def extract_explicit_age(
    text: str, *, today_year: Optional[int] = None
) -> tuple[Optional[int], Optional[int]]:
    """숫자/학년/생년이 들어간 명시적 연령 표기만 추출. 키워드 fallback 없음.

    `유아` 같은 키워드 단독에는 (None, None) 반환 — 호출 측에서 키워드 fallback을
    어느 텍스트(target만? title 포함?)에서 받을지 결정할 수 있도록 분리.
    """
    if not text:
        return None, None
    text = re.sub(r"\s+", " ", text)

    # 1) 혼합 단위(세↔초등) 먼저 — `초1 ~ 9세`의 1이 일반 _AGE_RANGE 에 먼저 잡히면
    #    학년 정보가 사라지므로 우선순위 위로.
    m = _AGE_TO_GRADE.search(text)
    if m:
        lo, hi = int(m.group(1)), _grade_to_age(int(m.group(2)))
        return min(lo, hi), max(lo, hi)
    m = _GRADE_TO_AGE.search(text)
    if m:
        lo, hi = _grade_to_age(int(m.group(1))), int(m.group(2))
        return min(lo, hi), max(lo, hi)

    # 2) 명시 연령 범위 (세).
    m = _AGE_RANGE.search(text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return min(a, b), max(a, b)

    # 3) 학년 (초등).
    m = _GRADE_RANGE.search(text)
    if m:
        a, b = _grade_to_age(int(m.group(1))), _grade_to_age(int(m.group(2)))
        return min(a, b), max(a, b)
    m = _GRADE_SINGLE.search(text)
    if m:
        age = _grade_to_age(int(m.group(1)))
        return age, age

    # 4) 생년 범위 → 만나이 환산.
    m = _BIRTHYEAR_RANGE.search(text)
    if m and today_year is not None:
        ya, yb = int(m.group(1)), int(m.group(2))
        ages = sorted([today_year - ya, today_year - yb])
        return max(0, ages[0]), max(0, ages[1])

    # 5) 단일 연령.
    m = _AGE_SINGLE.search(text)
    if m:
        age = int(m.group(1))
        return age, age

    return None, None


def keyword_age(text: str) -> tuple[Optional[int], Optional[int]]:
    """`유아 어린이 청소년` 같은 키워드 fallback. 다중 매칭 시 union (min/max).

    명시 연령이 없을 때만 호출하는 게 안전. 제목처럼 잡담이 많은 텍스트에 그대로
    돌리면 광범위한 (0,18) 범위가 나와 검색 신호가 약해진다.
    """
    if not text:
        return None, None
    text = re.sub(r"\s+", " ", text)
    mins: list[int] = []
    maxs: list[int] = []
    for kw, (lo, hi) in TARGET_AGE_DEFAULT.items():
        if kw in text:
            mins.append(lo)
            maxs.append(hi)
    if mins:
        return min(mins), max(maxs)
    return None, None


def normalize_target_age(
    text: str, *, today_year: Optional[int] = None
) -> tuple[Optional[int], Optional[int]]:
    """단일 텍스트에서 명시 연령 우선, 없으면 키워드 fallback.

    텍스트 두 개(예: target + title)를 분리 처리하고 싶으면 `extract_explicit_age`,
    `keyword_age`를 직접 조합.
    """
    explicit = extract_explicit_age(text, today_year=today_year)
    if explicit != (None, None):
        return explicit
    return keyword_age(text)
