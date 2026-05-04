# dongne-classes

송파구 **유치원생(4~7세, 초등 입학 전)** 부모 대상 공공 강좌 통합 검색 MVP. 자치구·도서관·문화시설에 흩어진 강좌를 한 곳에서 검색·필터링.

데이터 모델/저장은 0~18세 전체를 수용하지만, 본 서비스 1차 페르소나는 4~7세 유치원생 자녀를 둔 부모. 검색 기본값과 UX 우선순위가 이 범위에 맞춰져 있다 (`storage.DEFAULT_AGE_MIN/MAX`).

## 왜 송파구 + 유치원생부터

- 4~7세는 학원/유치원 외 **공공 인프라 활용 여력**이 가장 큰 구간 (초등 진학 후엔 학원 의존도 급증)
- 송파구는 0~12세 인구 서울 상위권 + 부모 구매력 높음
- 시설 인프라 풍부 (송파어린이문화회관, 구립도서관 13곳, 동주민센터 27개, 청소년시설 등)
- 송파구청이 동주민센터/평생학습 강좌를 **이미 통합 신청 시스템**으로 운영 → 크롤링 대상 폭발 방지
- 데이터 공개도 비교적 양호

## 데이터 소스 인벤토리 (1차)

| ID | 시설/시스템 | 범위 | URL | 상태 |
|---|---|---|---|---|
| `songpa_gu_office` | 송파구청 통합 강좌 신청 | 동주민센터 자치회관 + 구청 평생학습 + 진학학습지원센터 | `https://www.songpa.go.kr/learn/youth/program/lecture_list.do` | 200 OK |
| `splib` | 송파구통합도서관 | 송파/거마/글마루/가락몰 등 구립 분관 통합 | `https://www.splib.or.kr/` | 200 OK |
| `songpa_kids` | 송파어린이문화회관 | 어린이 전용 재능프로그램 | `https://www.songpakids.com/` | 200 OK |
| `seoul_youth_507` | 서울시 청소년수련시설 통합신청 | **센터별 서브도메인 + `center_id` 파라미터 패턴** — `online{NNN}.youth.seoul.kr/center_index.php?center_id={NNN}`. 송파=507, 잠실=538. 25개 구 동일 구조면 단일 크롤러로 전국 확장 가능 | `https://online507.youth.seoul.kr/center_index.php?center_id=507` | 200 OK |
| `jamsil_youth` | 잠실청소년센터 자체 사이트 | `seoul_youth_507`과 별개 자체 사이트. `online538`과의 중복 정도 확인 필요 | `https://jamsilyouthcenter.or.kr/` | 200 OK |

**보강 후보 (Phase 1 완료 후):** 체육시설(올림픽공원/방이동), 송파구민회관, 육아종합지원센터.

**참고:** `epart.net`은 송파어린이문화회관 SaaS 벤더 도메인 (`songpanew.epart.net` 등은 백엔드/관리자용 추정, `songpakids.epart.net`은 인증서 만료). 공식 외부 진입점은 `www.songpakids.com`.

## 사전 분석 결과

| 소스 | 어린이 필터 | 페이지네이션 | 상세 URL | 로그인 | 렌더링 | 구현 노트 |
|---|---|---|---|---|---|---|
| `songpa_gu_office` | `searchVal8=27\|28` (유아/어린이) | `?page=N` (GET, hidden form `page` — `pageIndex`로 잘못 추정한 적 있음) | `lecture_view.do?lecture_idx={id}` | 불필요 | **SSR** | listing list/grid 두 view 동시 렌더 → dedupe 필요 |
| `splib` | `eventTargetCd=CHL\|KID` | `?currentPageNo=N` (GET, form `method="get"`) | listing inline → detail 불필요 | 불필요 | **SSR** | `<span class="lib BD">` 분관 코드 매핑 |
| `songpa_kids` | UI 필터 (URL `eduTargets=...` 부분 동작) | `?cp=N&pageSize=12` (GET) | listing inline → detail 불필요 | 불필요 | **SSR** | dl/dt/dd 라벨-값, `5세 ~ 6세` / `6세 ~ 초2` 혼합 표기 |
| `seoul_youth` | item2 카테고리(센터별 자동 발견) | `page=N` POST | listing inline; goLink onclick에 URL-encoded 메타데이터 | 세션 쿠키만 필요 | **AJAX** | `center_id` 폼 필드 필수, status class `rb*` 다양 |
| `jamsil_youth` | n/a | n/a | n/a | n/a | n/a | online538(`seoul_youth` 538)이 커버 → deprecated |

**구현 함의**
- 4개는 `Fetcher.get` (HTTP)으로 충분. `seoul_youth_507`만 AJAX → `DynamicFetcher.fetch` 또는 직접 POST 시뮬레이션.
- `splib` 페이지네이션은 form POST. URL이 안 바뀜. 폼 필드 캡처 필요.
- `jamsil_youth` 자체 사이트는 정보/공지 위주. 강좌 신청은 `online538`. **PoC 단계에서 jamsil_youth 보류 권장** (정리는 PoC 끝나고).

## 청소년센터 SaaS 커버리지 (검증)

`online{NNN}.youth.seoul.kr` 패턴은 **연속 ID가 아님**. 직접 sweep으로 확인된 라이브 서브도메인:

| center_id | 센터 |
|---|---|
| 507 | 송파청소년센터 |
| 508 | 역삼청소년센터 |
| 510 | 중구청소년센터 |
| 538 | 잠실청소년센터 |
| 540 | 천왕동청소년문화의집 |
| 545 | 천호청소년문화의집 |

(나머지 시도한 ID 10개는 DNS 실패.) 결론: **단일 크롤러 다중 센터는 OK, 25개 구 자동 커버는 아님**. 확장하려면 **center_id 레지스트리**(공식 디렉터리 페이지에서 추출)가 필요. Phase 2 작업.

## 소스별 5개 분석 항목 (raw)

1. 어린이/유아 필터 존재 여부 — 위 표 "어린이 필터" 컬럼
2. 페이지네이션 URL 파라미터 — 위 표 "페이지네이션" 컬럼
3. 상세 페이지 URL 패턴 — 위 표 "상세 URL" 컬럼
4. 로그인 없이 상세까지 접근 가능 — 5개 모두 ✅ (전부 익명 GET 200)
5. SSR vs AJAX — 위 표 "렌더링" 컬럼

CAPTCHA, rate-limit 헤더, 차단 시그널은 사전 점검에서 발견되지 않음.

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
src/                     # 백엔드 (크롤러 + 모델)
  models.py              # ClassListing Pydantic 모델
  fetcher.py             # Scrapling 래퍼 (HTTP/STEALTH/DYNAMIC)
  parsers.py             # 공통 파서 (date/period/schedule/fee/target_age 정규화)
  storage.py             # SQLite (source_id, external_id) PK + upsert
  sources/
    base.py              # Source ABC
    songpa_gu_office.py  # ✅ listing→detail, GET pageparam
    splib.py             # ✅ listing-only (data inline)
    songpa_kids.py       # ✅ songpakids.com TALENT/list, listing-only
    seoul_youth.py       # ✅ AJAX POST + 카테고리 자동 발견, multi-center
    jamsil_youth.py      # 🚫 deprecated — online538에 포함
tests/
  test_models.py
  test_parsers.py
  test_storage.py
  test_songpa_gu_office.py

src/templates/index.html # FastAPI 검색 페이지 (Jinja2 + Tailwind CDN)
src/web.py               # FastAPI app: GET / + GET /api/search

web/                     # 별도 프런트엔드 (Vite + React + TS + Tailwind v4)
  src/
    App.tsx
    types.ts             # ClassListing TS 미러 (Pydantic 모델과 정합)
    data/mock.ts         # 합성 데이터 fixture (현재; 추후 /api/search 연결)
    components/          # Header, ClassCard, FilterPanel, ClassDetail, CategoryStrip

.github/workflows/
  pages.yml              # GitHub Pages 자동 배포 (web/ 변경 시 트리거)
```

**프런트엔드 두 갈래 병행**: `src/web.py` (FastAPI + Jinja, 실 DB 연결, 로컬 개발용)와 `web/` (React + Vite, 정적 배포, 현재 mock 데이터). 후자가 전자의 `/api/search`를 호출하도록 연결하는 게 다음 단계.

## 프런트엔드 라이브 미리보기

GitHub Pages 자동 배포: https://daniel-nexus.github.io/dongne-classes/

`Settings → Pages → Source: GitHub Actions` 한 번 활성화하면, 이후 `web/` 또는
워크플로우 파일에 push할 때마다 자동 빌드·배포.

## 개발

백엔드:
```bash
pip install -e ".[dev]"
pytest
```

프런트엔드:
```bash
cd web
npm install
npm run dev      # http://localhost:5173
npm run build    # 정적 산출 → web/dist
```

## 다음 액션

- [x] 프런트엔드 골격(`web/`) + mock 데이터 + 필터/검색/상세 + GitHub Pages 자동 배포
- [x] Scrapling 설치 후 `src/fetcher.py` API 검증 (v0.4.7, `[fetchers]` extras 필요)
- [x] 5개 소스 도달성 확인 (전부 200 OK)
- [x] 5개 소스 사전 분석 (어린이 필터/페이지네이션/상세 URL/로그인/렌더링) — `## 사전 분석 결과` 참조
- [x] `online5XX` SaaS 커버리지 — 연속 ID 아님, 단일 크롤러 다중 센터 OK 확인 (Phase 2: 공식 디렉터리에서 center_id 전체 추출)
- [x] **`songpa_gu_office` PoC 크롤러** — 31개 unique 강좌 추출, 16개 필드 100% 채움
- [x] **`splib` PoC 크롤러** — listing inline 데이터 (detail fetch 불필요). 600+ 강좌 (역사 포함)
- [x] 공통 파서 `src/parsers.py` 추출 — date/period/schedule/fee/match_first/target_age 정규화
- [x] `target_description` → `target_age_min/max` 정규화 (명시 연령/학년/생년 우선, 키워드 fallback)
- [x] **SQLite 저장소** `src/storage.py` — `(source_id, external_id)` PK, crawled_at 보존 upsert, age 인덱스 + `search_kids()` 헬퍼
- [x] **`songpa_kids` 크롤러** — songpakids.com TALENT 리스트, listing-only (181 강좌)
- [x] **`seoul_youth` 크롤러** — POST AJAX (Lecture_Search_List7.ajax.php + center_id), 카테고리 자동 발견, multi-center 지원 (507 송파 + 538 잠실 = 198 강좌)
- [x] `jamsil_youth` — deprecated 처리 (online538이 잠실 강좌를 모두 커버, 자체 사이트는 정보 페이지)
- [x] `Fetcher.post` 추가 (`src/fetcher.py`) — AJAX 엔드포인트용
- [ ] center_id 레지스트리 자동 발굴 (Phase 2 — 25개 구 확장 트리거)
- [x] **웹 프런트 + API** (FastAPI + Jinja 검색 UI, `search_kids` 노출, `GET /api/search` JSON)
- [x] CLI 진입점 (`python -m src.cli crawl --source=all --db=...`)
- [ ] **배포** (Railway/Vercel) + 스케줄 크롤 (매일 1~2회)
- [ ] `web/` (React) → FastAPI `/api/search` 연결 (현재 mock fixture 대체)
- [ ] 데이터 sanity check (제목 빈문자/이상치 탐지, 자동 중복 제거)

## PoC 결과

### `songpa_gu_office`

- 어린이/유아 필터: `searchVal8=27` (유아), `searchVal8=28` (어린이) — 합집합으로 0~12세 커버
- 페이지네이션은 **`page=N`** (사전 분석에서 `pageIndex`로 잘못 추정 → 검증 후 수정). hidden form field, `goPageNavigation(N)` JS submit.
- listing은 list/grid 두 view 동시 렌더 → external_id dedupe 필수.
- 상세 페이지에서 `교육기간/교육시간/교육대상/교육장소/수강료/접수기간/접수방법` 키워드 기반 추출. 상태는 `<span class="link_btn">` (`온라인신청가능`, `온라인신청마감` 같은 합성 라벨 — substring 매칭).
- 31 items × 1.5 페이지, request_delay=0.15s, 약 25초.

### `splib` (송파구통합도서관)

- 어린이/유아 필터: `eventTargetCd=CHL` (유아), `KID` (아동), `YNG` (청소년)
- 정식 listing URL: `/intro/menu/10052/program/30014/eventList.do?currentPageNo=N&eventTargetCd=...&manageCd=ALL`
- 페이지네이션은 **GET** `currentPageNo=N` (form `method="get"` — 사전 분석에서 POST로 잘못 추정 → 검증 후 수정).
- **핵심 차이**: listing item에 `분야/대상/수강료/교육기간/교육시간/장소/접수일정/상태` 가 모두 inline → **detail fetch 불필요**.
- `<span class="lib BD">` 같이 분관 코드(BD=소나무언덕4호)가 클래스에 포함됨 — `BRANCH_NAMES` 매핑으로 facility_name 추출.
- 상태: `<div class="statusBox">` 안에 `신청 : 9/10 (대기 : 0/10) 접수중` 형태 (정원/대기까지 inline — 추후 capacity 파서 후보).
- 빈 페이지가 종료 신호 (사이트의 "총N건" 표기는 capacity 텍스트와 충돌하므로 사용하지 않음).
- 600+ items, 약 25초 (페이지 단위 delay만).

### `songpa_kids` (송파어린이문화회관)

- listing URL: `/site/main/edu/TALENT/list?cp={N}&pageSize=12` — cp=20부터 빈 페이지 종료
- 항목 풍부: 제목/대상/기간/시간/정원/수강료/상태 모두 inline → detail 불필요
- `<dl><dt>강의대상</dt><dd>...</dd></dl>` 구조에서 라벨/값 추출 (`수 강 료` 같이 공백 라벨 정규화 매칭)
- 정원 정보(`12명 (정원 12명 / 신청 1명)`)에서 `capacity` 채움
- 181 강좌 (active+종료 통합), 약 39초

### `seoul_youth` (online5XX.youth.seoul.kr)

- **AJAX POST**: `/s_center/Lecture_Search_List7.ajax.php` (data: item1=center_id, item2=category, page=N, search='', `center_id=…`). `center_id` 폼 필드 누락 시 500 redirect (`../500_error.php?dtype=1&center_id=`)
- 세션 cookie 필요 — home(`/center_index.php?center_id={N}`) 한 번 호출로 PHPSESSID 발급
- 카테고리(item2)는 센터별 다름 (507: 008/009/029, 538: 030/031). 홈 페이지 `data-id`에서 자동 발견
- 항목당 `<tr>` + `goLink('id', 'cat_url', '008', ..., 'title_url', ..., 'fee')` onclick에 메타데이터 URL-encoded — 디코드해서 title/fee 추출. row 컬럼에서 venue/day+time/target/capacity/status
- 제목에 `11~16세` 같은 명시 연령이 박혀있는 경우 흔함 → title도 normalize_target_age 입력에 포함
- status class는 센터별 다양 (`rbn/rbf/rbd/...`). `class*=rb` (단 `rbb` 신청 버튼 제외) 통합 매칭
- 198 강좌 (507=87, 538=111), 약 7초
- 확장: `center_ids=(...)` 인자로 다중 센터. 확인된 라이브 6개: 507/508/510/538/540/545

### 통합 검색 (SQLite)

4개 소스 → 1,010 rows DB:

| 소스 | 강좌 수 |
|---|---|
| `splib` | 600 (대다수가 종료된 역사 데이터) |
| `seoul_youth` | 198 (송파 + 잠실) |
| `songpa_kids` | 181 |
| `songpa_gu_office` | 31 (2 페이지 샘플) |

`storage.search_kids(conn)` 기본값 = 4~7세 (`DEFAULT_AGE_MIN=4`, `DEFAULT_AGE_MAX=7`).
정렬은 **상태 우선순위(recruiting → ended) → registration_end ASC** (마감 가까운 모집중 강좌부터).
`statuses=['recruiting','upcoming']` 처럼 상태 묶어 받기 가능.

재크롤 시 `crawled_at` 보존 + `last_seen_at` 갱신, 같은 강좌 중복 INSERT 없음.

## CLI

```bash
# 4개 소스 모두 → SQLite
python -m src.cli crawl --source=all --db=data/dongne.db

# 일부만
python -m src.cli crawl --source=splib,songpa_kids --db=data/dongne.db

# 4~7세 모집중·예정 검색
python -m src.cli search --db=data/dongne.db --status=recruiting,upcoming
```

`crawl`은 한 소스가 실패해도 다른 소스로 전파되지 않게 격리(per-source try/except).
exit code: 모든 소스 성공 시 0, 하나라도 실패 시 1.

## 웹 (FastAPI)

```bash
# 1) DB 적재 (5분 정도)
python -m src.cli crawl --source=all --db=data/dongne.db

# 2) 서버 기동
DONGNE_DB=data/dongne.db uvicorn src.web:app --host 127.0.0.1 --port 8000

# 또는 entry script
python -m src.web
```

브라우저: http://127.0.0.1:8000

UI:
- 좌측 필터(아이 나이 / 접수 상태 / 시설 / 무료만)
- 우측 결과 카드 — 마감 가까운 모집중 강좌부터, 시설/연령/금액 칩, 외부 신청 페이지로 이동 링크
- `GET /api/search?...` JSON 엔드포인트 (같은 필터 파라미터)
