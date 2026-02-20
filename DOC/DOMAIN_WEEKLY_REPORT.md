# 프로젝트: 주간보고 자동화 도메인 추가 (FastAPI + React)

## 1. 개요
사용자가 업로드한 4개의 ITS/어플리케이션 변경관리 엑셀 파일을 통합 및 분석하여, 정해진 구글 스프레드시트에 주간보고 양식을 복사하고 데이터를 자동 기입하는 기능을 추가한다. 
**이 기능은 프로젝트의 `ARCHITECTURE.md` 및 `DEVELOPMENT_GUIDE.md`를 엄격히 준수하는 새로운 도메인(예: `weekly_report`)으로 구현되어야 한다.**

## 2. 기술 스택 및 아키텍처 원칙
- **Backend**: Python 3.12, FastAPI, Pydantic (비동기 처리 원칙)
- **Frontend**: React 19, TypeScript, Zustand (기존 컨벤션 준수)
- **AI Integration**: `google-generativeai` (Gemini API)
- **디자인 패턴**: 계층화된 아키텍처 (`Router` -> `Service` -> `Calculator` / `Formatter` / `Repository`)
- **구현 규칙**: 모든 비즈니스 로직은 **클래스 기반**으로 작성하며 절차지향 함수 사용 금지. 의존성 주입(Dependency Injection) 적극 활용.

## 3. 백엔드 도메인 설계 (Layer별 역할)

### 3.1. Router Layer (`router.py`)
- **역할:** 프론트엔드로부터 주간 보고 날짜(예: `2026-02-18`)와 4개의 엑셀 파일(A, B, C, D)을 `UploadFile`로 수신. Pydantic 스키마 검증.

### 3.2. Calculator Layer (`calculator.py`)
- **역할:** 비즈니스 로직 계산, Pandas 데이터 전처리 및 필터링, Gemini API 텍스트 윤문.
- **로직 1 (통합):** A+B 병합(`AB 파일`), C+D 병합(`CD 파일`). Header는 3행(`header=2`).
- **로직 2 (필터링 기준 - 모든 기준은 SR 데이터):**
  - **추출 대상:** `AB 파일`의 F열 또는 W열(업무시스템2)이 '세아베스틸>기타>e-Procurement' 또는 '세아창원특수강>기타>e-Procurement'인 건.
  - **날짜 필터링:** - T열(변경 ID)이 없으면 P열(처리완료일) 기준, 있으면 Z열 기준.
    - 해당 날짜가 사용자가 입력한 날짜의 주(월~금)에 포함되면 추출. 빈 값이면(진행/대기) 무조건 추출.
- **로직 3 (데이터 매핑):**
  - 요청 ID: A열
  - 진행상태: B열 기준 ('종료/중단종료/취소종료' -> 완료, '요청 접수 및 분류' -> 대기, 그 외 -> 진행중)
  - 일정(~mm/dd): P열 추출(없으면 O열). `MM/DD` 포맷.
  - 구분: T열 없으면 C열, T열 있으면 `CD 파일`과 조인하여 D열 확인. '서비스요청 > 전산개발수정/신규 요청'이면 `개발/개선`, 그 외 `프로젝트/운영`.
- **로직 4 (Gemini 윤문):** - 원본 추출 (T열 유무에 따라 G, H, P/R 또는 Z/AB열 추출)
  - `google-generativeai` 비동기 호출: "주간보고서의 [제목], [개요], [내용] 항목에 맞게 각각 1~2줄 이내의 명확한 비즈니스 용어로 요약. 인사말, 이름 제거."

### 3.3. Formatter Layer (`formatter.py`)
- **역할:** Calculator에서 정제된 데이터를 구글 시트 출력 양식의 텍스트로 포맷팅.
- **포맷팅 규칙:** J열(요청회사)을 기준으로 창원/베스틸 분류하여 아래 텍스트 생성. (처리내용이 없으면 생략)

```text
◈EPRO 운영
[창원]
▣ ({구분}) ({요청 ID}) {제목} (~{mm/dd}, {진행상태})
  -. 개요 : {개요}
  -. 내용 : {내용}

[베스틸]
▣ ({구분}) ({요청 ID}) {제목} (~{mm/dd}, {진행상태})
  -. 개요 : {개요}
  -. 내용 : {내용}
```

### 3.4. Repository Layer (`repository.py` 또는 외부 API 클라이언트)
- **역할:** Google Sheets API 통신 전담.
- **로직:** - 환경변수 인증 정보(Service Account)를 사용하여 지정된 스프레드시트에 비동기로 접속.
  - '양식 sheet' 복사 후 사용자가 입력한 날짜 명칭으로 새 탭 생성.
  - 새 탭의 '금주 실적' 기간 업데이트 및 Formatter가 생성한 텍스트 데이터 Write.

### 3.5. Service Layer (`service.py`)
- **역할:** Facade Pattern으로 동작하며, Router의 요청을 받아 위 `Repository`, `Calculator`, `Formatter` 클래스들을 주입받아 워크플로우를 조율함.

## 4. 프론트엔드 설계
- **UI:** 날짜 선택(DatePicker) 및 다중 파일 업로드 영역 구현.
- **통신:** Zustand 스토어를 활용하여 상태를 관리하고, FastAPI 백엔드로 `multipart/form-data` 비동기 전송.

## 5. 에러 핸들링 및 유의사항
- Pandas에서 T열 결측치 처리 시 `NaN` 체크 유의.
- Gemini API Key 및 Google Sheets 접속 정보는 `.env` 파일로 관리.
- 코드는 반드시 `black`, `isort` 포맷팅을 준수할 것.