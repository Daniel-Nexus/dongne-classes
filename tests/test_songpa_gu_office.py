"""songpa_gu_office 소스 전용 헬퍼 테스트. 공통 헬퍼는 test_parsers.py 참고."""
from src.models import RegistrationMethod, Status
from src.parsers import match_first
from src.sources.songpa_gu_office import _STATUS_RULES, _map_reg_method


def test_status_rules_handle_compound_text():
    # 송파 시스템은 "온라인신청가능" 같이 합성 라벨을 씀.
    assert match_first("온라인신청가능", _STATUS_RULES, Status.UNKNOWN) is Status.RECRUITING
    assert match_first("온라인신청마감", _STATUS_RULES, Status.UNKNOWN) is Status.CLOSED
    assert match_first("교육중", _STATUS_RULES, Status.UNKNOWN) is Status.IN_PROGRESS
    assert match_first("외부홈페이지", _STATUS_RULES, Status.UNKNOWN) is Status.UNKNOWN


def test_map_reg_method_mixed():
    assert _map_reg_method("온라인, 방문") is RegistrationMethod.MIXED
    assert _map_reg_method("온라인") is RegistrationMethod.ONLINE
    assert _map_reg_method("방문") is RegistrationMethod.VISIT
    assert _map_reg_method("외부홈페이지") is RegistrationMethod.UNKNOWN
