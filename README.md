# dongne-classes

송파구 어린이(0~12세) 대상 공공 강좌 통합 검색 MVP. 흩어진 자치구·도서관·문화시설 강좌를 한 곳에서 검색·필터링.

## 왜 송파구부터

- 0~12세 인구 서울 상위권 + 부모 구매력 높음
- 시설 인프라 풍부 (송파어린이문화회관, 구립도서관, 동주민센터 27개, 청소년시설 등)
- 송파구청이 동주민센터/평생학습 강좌를 **이미 통합 신청 시스템**으로 운영 → 크롤링 대상 폭발 방지
- 데이터 공개도 비교적 양호

## 데이터 소스 인벤토리 (1차)

| ID | 시설/시스템 | 범위 | 상태 |
|---|---|---|---|
| `songpa_gu_office` | 송파구청 통합 강좌 신청 | 동주민센터 자치회관 + 구청 평생학습 + 진학학습지원센터 | 미확인 |
| `splib` | 송파구통합도서관 | 송파/거마/글마루/가락몰 등 구립 분관 통합 | 미확인 |
| `songpa_kids` | 송파어린이문화회관 (epart.net) | 어린이 전용 재능프로그램 | 미확인 |
| `seoul_youth_507` | 서울시 청소년수련시설 통합신청 | 송파청소년센터 등. **25개 구 커버 여부 확인 시 확장 잠재력 큼** | 미확인 |
| `jamsil_youth` | 잠실청소년센터 | 별도 사이트 (online507 중복 가능성) | 미확인 |

**보강 후보 (Phase 1 완료 후):** 체육시설(올림픽공원/방이동), 송파구민회관, 육아종합지원센터.

**"미확인" 사유:** 빌드 환경에서 한국 공공기관 도메인 5개 모두 `HTTP 403` (egress 레벨 차단, 동일 21바이트 응답). 한국 IP 환경에서 사전 분석 필요. 확인 항목:

1. 어린이/유아 필터 존재 여부
2. 페이지네이션 URL 파라미터
3. 상세 페이지 URL 패턴
4. 로그인 없이 상세까지 접근 가능한지
5. SSR vs AJAX 렌더링

## 데이터 모델

`src/models.py` — `ClassListing` (Pydantic v2). 핵심 그룹:

- 식별자: `source_id`, `external_id`, `source_url`
- 본문: `title`, `description`, `category`, `instructor`
- 시설: `facility_name`, `facility_type`, `address`
- 대상: `target_description` (raw), `target_age_min/max` (정규화)
- 일정: `schedule_days`, `schedule_time`, `period_start/end`
- 모집: `capacity`, `registration_*`, `status`
- 비용: `fee_won`, `materials_fee_won`
- 메타: `crawled_at`, `last_seen_at`, `raw` (소스별 추가)

대상 연령은 raw 텍스트와 정규화 값 둘 다 보관 — 파싱 실패해도 raw는 살림.

## 스택 결정

| 영역 | 선택 | 사유 |
|---|---|---|
| 언어 | Python 3.10+ | 한국 공공 크롤링 생태계 표준, Pydantic 등 데이터 도구 풍부 |
| 크롤링 | [Scrapling](https://github.com/D4Vinci/Scrapling) | Auto-relocate 셀렉터, HTTP/스텔시/Playwright 통합, BSD-3, 활발 |
| 검증 | Pydantic v2 | 강좌 데이터 sanity check |

**Scrapling 의존도 제한:** fetcher로만 사용. 파싱은 명시적 셀렉터로 작성, auto-match는 fallback. v0.x API churn 대비.

**감안할 리스크:**

- Scrapling의 Cloudflare 우회는 우리 영역(한국 공공)에서 거의 안 쓰임 (한국 WAF는 WAPPLES/MONITORAPP 계열). auto-relocate 때문에 채택하는 것
- Auto-match가 잘못된 요소 잡으면 데이터 오염 → 검증 레이어로 막음
- v0.x API 변경 가능성 → 의존 표면 최소화

## 레포 구조

```
src/
  models.py              # ClassListing Pydantic 모델
  fetcher.py             # Scrapling 래퍼 (HTTP/STEALTH/DYNAMIC)
  sources/
    base.py              # Source ABC
    songpa_gu_office.py  # 5개 소스 stub
    splib.py
    songpa_kids.py
    seoul_youth.py
    jamsil_youth.py
tests/
  test_models.py
```

## 개발

```bash
pip install -e ".[dev]"
pytest
```

## 다음 액션

- [ ] 한국 IP 환경에서 5개 소스 사전 분석 (위 5개 확인 항목)
- [ ] `seoul_youth_507`의 25개 구 커버 여부 확인 (Phase 2 확장 결정)
- [ ] `jamsil_youth`가 `seoul_youth_507`에 포함되는지 확인 (중복 정리)
- [ ] 가장 단순한 소스 1개부터 실제 crawler 구현 → 데이터 모델 미세조정
- [ ] 데이터 sanity check 함수 (강좌명 유효성, 연령 파싱 등)
- [ ] Scrapling 실제 설치 후 `src/fetcher.py` API 검증
