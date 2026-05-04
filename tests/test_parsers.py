"""공통 파서 헬퍼 테스트."""
from datetime import datetime

from src.models import Status
from src.parsers import (
    match_first,
    normalize_target_age,
    parse_date,
    parse_fee,
    parse_period,
    parse_schedule,
)


def test_parse_period_with_time():
    s, e = parse_period("26-04-28 11:00 ~ 26-04-29 17:00")
    assert s == datetime(2026, 4, 28, 11, 0)
    assert e == datetime(2026, 4, 29, 17, 0)


def test_parse_period_dates_only():
    s, e = parse_period("26-05-04 ~ 26-05-29")
    assert s == datetime(2026, 5, 4)
    assert e == datetime(2026, 5, 29)


def test_parse_period_full_year():
    s, e = parse_period("2026-05-04 ~ 2026-05-29")
    assert s == datetime(2026, 5, 4)


def test_parse_period_invalid():
    assert parse_period("미정") == (None, None)


def test_parse_schedule_multi_day():
    days, t = parse_schedule("매주 월, 수 09:30~12:00")
    assert days == ["월", "수"]
    assert t == "09:30~12:00"


def test_parse_schedule_single_day():
    days, t = parse_schedule("매주 토 10:00~11:30")
    assert days == ["토"]


def test_parse_schedule_excludes_요일_substring():
    # "(화요일)" 안의 "일"이 별도 day로 잘못 잡히면 안 됨.
    days, t = parse_schedule("매주 (화요일) 16:00-16:50")
    assert days == ["화"]
    assert t == "16:00-16:50"


def test_parse_fee():
    assert parse_fee("10,000원") == 10000
    assert parse_fee("무료") == 0
    assert parse_fee("0원") == 0
    assert parse_fee("") is None
    assert parse_fee("문의") is None


def test_match_first_priority():
    rules = [("AB", 1), ("A", 2)]
    assert match_first("ABC", rules, 0) == 1  # AB 먼저 매칭
    assert match_first("XAYZ", rules, 0) == 2
    assert match_first("none", rules, -1) == -1


def test_normalize_target_age_explicit_range():
    assert normalize_target_age("(유아) 6~7세 12명") == (6, 7)
    assert normalize_target_age("만 5~7세") == (5, 7)
    # `5세 ~ 6세` (세가 양쪽 모두) — songpakids 흔한 표기
    assert normalize_target_age("유아 5세 ~ 6세") == (5, 6)


def test_normalize_target_age_mixed_units():
    # `6세 ~ 초2` — songpakids 혼합 표기, 6세부터 초2(만 8세)까지.
    assert normalize_target_age("유아 6세 ~ 초2") == (6, 8)
    # 반대 방향 `초1 ~ 9세`
    assert normalize_target_age("초1 ~ 9세") == (7, 9)


def test_normalize_target_age_grade():
    assert normalize_target_age("초등 3~4학년 10명") == (9, 10)
    assert normalize_target_age("초등 1학년") == (7, 7)


def test_normalize_target_age_birth_year():
    # 2026년 기준 2019~2020년생 → 6~7세 (단순 연도 차).
    assert normalize_target_age("(아동) 2019~2020년생", today_year=2026) == (6, 7)
    # `(2020년 ~ 2021년)` — 생 생략된 생년 범위, songpakids 흔한 표기.
    assert normalize_target_age("(2020년 ~ 2021년)", today_year=2026) == (5, 6)


def test_normalize_target_age_keyword_fallback():
    # 명시 연령 없으면 키워드로 fallback.
    assert normalize_target_age("유아 어린이") == (0, 12)
    assert normalize_target_age("청소년") == (13, 18)
    # 다중 키워드 → union.
    assert normalize_target_age("유아 어린이 청소년") == (0, 18)


def test_normalize_target_age_no_signal():
    assert normalize_target_age("") == (None, None)
    assert normalize_target_age("누구나") == (None, None)


def test_parse_date_formats():
    assert parse_date("2026-05-04") == datetime(2026, 5, 4)
    assert parse_date("26-05-04") == datetime(2026, 5, 4)
    assert parse_date("2026-05-04 11:00") == datetime(2026, 5, 4, 11, 0)
    assert parse_date("2026.05.04") == datetime(2026, 5, 4)
    assert parse_date("invalid") is None
