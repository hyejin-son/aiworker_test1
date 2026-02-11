# CLAUDE.md - Vibe Web Starter AI 코딩 가이드

> 이 파일은 Claude Code(AI 어시스턴트)가 이 프로젝트에서 작업할 때 반드시 따라야 할 규칙과 컨텍스트를 정의합니다.

## 프로젝트 개요

FastAPI + SQLAlchemy 2.0 + React 19 + Tailwind CSS 4 기반의 풀스택 웹 애플리케이션 템플릿입니다.
**"유지보수성 최우선"** 및 **"모듈화"**를 핵심 가치로 하며, 도메인 플러그인 구조를 채택합니다.

- Python >= 3.12, Node.js (Vite 7)
- DB: PostgreSQL (asyncpg) + Supabase
- 인증: JWT (python-jose)
- 상태관리: Zustand

## 절대 금지 사항 (NEVER DO)

1. **아키텍처 파괴 금지**: `Router -> Service -> Repository` 계층 구조를 반드시 준수. 도메인 간 내부 구현 직접 참조 금지.
2. **절차지향 금지**: 비즈니스 로직은 반드시 클래스 기반으로 구현 (BaseService 상속). 절차지향 함수 사용 금지.
3. **직접 DB 쿼리 금지**: Service/Repository를 통해서만 DB 접근. Router에서 직접 쿼리 금지.
4. **타입 힌트 누락 금지**: Python 함수/메서드에 타입 힌트 필수. TypeScript에서 `any` 타입 사용 금지.
5. **직접 axios 호출 금지**: 프론트엔드에서 `apiClient`를 통해서만 API 호출.
6. **인라인 스타일 금지**: Tailwind CSS 클래스 사용 필수.
7. **마이그레이션 파일 수정 금지**: `alembic/versions/` 파일은 Append-only. 기존 파일 수정 금지.
8. **민감정보 로깅 금지**: 비밀번호, 토큰 등을 로그에 기록하지 않음. 모든 로그에 `request_id` 포함.

## 프로젝트 구조

```
├── server/                     # 백엔드 (FastAPI)
│   ├── main.py                 # 진입점
│   └── app/
│       ├── core/               # 설정, DB연결, 미들웨어, 로깅
│       ├── shared/             # 베이스 클래스, 예외, 유틸리티
│       │   └── base/           # BaseService, BaseRepository, BaseCalculator, BaseFormatter
│       ├── domain/             # 비즈니스 도메인 (플러그인 구조)
│       │   └── {domain}/       # 각 도메인 독립 모듈
│       │       ├── models/     # SQLAlchemy 모델
│       │       ├── schemas/    # Pydantic 스키마
│       │       ├── repositories/ # 데이터 접근 계층
│       │       ├── calculators/  # 순수 계산 로직
│       │       ├── formatters/   # 응답 변환 로직
│       │       └── service.py    # 비즈니스 오케스트레이션
│       ├── api/                # API 라우터
│       └── examples/           # 예제 코드
│
├── client/                     # 프론트엔드 (React 19 + Vite 7)
│   └── src/
│       ├── core/               # 공유 인프라 (api, ui, layout, errors, hooks, store, loading, utils)
│       └── domains/            # 도메인별 기능
│           └── {domain}/       # 각 도메인 독립 모듈
│               ├── components/ # UI 컴포넌트
│               ├── pages/      # 페이지 컴포넌트
│               ├── api.ts      # API 호출
│               ├── store.ts    # Zustand 상태
│               └── types.ts    # 타입 정의
│
├── alembic/                    # DB 마이그레이션 (Append-only)
├── tests/                      # 테스트
│   ├── unit/                   # 단위 테스트
│   └── integration/            # 통합 테스트
├── DOC/                        # 프로젝트 문서 (ARCHITECTURE.md 등)
├── pyproject.toml              # Python 프로젝트 설정 및 도구 구성
└── requirements.txt            # Python 의존성
```

## 계층별 책임 (Layer Responsibilities)

| 계층 | 책임 | 금지 사항 |
|------|------|-----------|
| **Router (API)** | HTTP 입출력 처리, Pydantic 검증, Service 호출 | 비즈니스 로직, 직접 DB 접근 |
| **Service** | 도메인 로직 오케스트레이션, 트랜잭션 관리. `BaseService` 상속 필수, `execute()` 구현 | 직접 DB 쿼리, HTTP 처리 |
| **Repository** | DB 조회/외부 데이터 소스 접근. `BaseRepository` 상속, `provide()` 구현 | 계산 로직, 비즈니스 로직 |
| **Calculator** | 순수 함수 기반 계산/분석. `BaseCalculator` 상속, `calculate()` 구현 | DB/API 접근, 부수 효과 |
| **Formatter** | 응답 데이터 변환/마스킹. `BaseFormatter` 상속, `format()` 구현 | 계산 로직, 비즈니스 로직 |

**데이터 흐름**: `Router → Service → Repository → Calculator → Formatter → Response`

**도메인 간 통신**: 한 도메인은 다른 도메인의 `Service`나 `Repository`를 통해서만 통신. 내부 구현 직접 참조 금지.

## 코드 스타일

### Python (백엔드)
- **라인 길이**: 100자 (`black` 기준)
- **포맷터**: `black` (line-length=100, target=py312)
- **Import 정렬**: `isort` (profile="black")
- **린터**: `ruff` (E, W, F, I, C, B, UP 규칙)
- **타입 체크**: `mypy` (python 3.12)
- **ORM**: SQLAlchemy 2.0 비동기 패턴 (`select()`, `await db.execute()`)
- **검증**: Pydantic v2 `BaseModel`

### TypeScript (프론트엔드)
- **프레임워크**: React 19
- **빌드**: Vite 7
- **스타일**: Tailwind CSS 4, `cn()` 유틸로 조건부 클래스 처리
- **상태관리**: Zustand (도메인별 스토어)
- **린터**: ESLint 9
- **API 호출**: `apiClient` (core/api/client.ts) 사용 필수. 직접 axios 금지.

## 주요 명령어

### 백엔드
```bash
# 서버 실행
python -m server.main

# 코드 포맷팅
black server/
isort server/

# 린팅
ruff check server/
ruff check server/ --fix    # 자동 수정

# 타입 체크
mypy server/

# 테스트
pytest                       # 전체 실행 (커버리지 포함)
pytest tests/unit/           # 단위 테스트만
pytest tests/integration/    # 통합 테스트만
pytest -m "not slow"         # 느린 테스트 제외
pytest -v --lf               # 실패한 테스트 재실행
```

### 프론트엔드
```bash
cd client
npm install                  # 의존성 설치
npm run dev                  # 개발 서버 (localhost:3000)
npm run build                # 프로덕션 빌드 (tsc + vite build)
npm run lint                 # ESLint 검사
npx tsc --noEmit             # TypeScript 타입 체크
```

### DB 마이그레이션 (Alembic)
```bash
# 마이그레이션 생성 (모델 변경 후)
alembic revision --autogenerate -m "설명"

# 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

**DB 변경 워크플로우**:
1. 변경 사항을 사용자에게 설명하고 승인 요청
2. `server/app/domain/{domain}/models/` 수정
3. `alembic revision --autogenerate` 로 마이그레이션 생성
4. 생성된 파일 검토 보고 후 `alembic upgrade head` 안내

## 새 도메인 추가 시 필수 절차

### 백엔드
1. `server/app/domain/{domain}/` 디렉토리 생성 (models, schemas, repositories, calculators, formatters 하위 디렉토리 포함)
2. SQLAlchemy 모델 정의 → Pydantic 스키마 정의
3. Repository → Calculator → Formatter → Service 순서로 구현 (각 Base 클래스 상속)
4. `server/app/api/v1/endpoints/{domain}.py` 라우터 작성
5. `server/app/api/v1/router.py`에 라우터 등록
6. Alembic 마이그레이션 생성 및 적용
7. 단위 테스트 + 통합 테스트 작성

### 프론트엔드
1. `client/src/domains/{domain}/` 디렉토리 생성 (components, pages 포함)
2. `types.ts` → `api.ts` → `store.ts` 순서로 작성
3. 컴포넌트 및 페이지 구현
4. `App.tsx` 라우팅 등록

## 테스트 규칙

- **파일명**: `test_*.py` 또는 `*_test.py`
- **클래스명**: `Test*`
- **함수명**: `test_*`
- **마커**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **비동기**: `@pytest.mark.asyncio` (asyncio_mode="auto")
- **패턴**: Given/When/Then 구조 권장
- **커버리지 대상**: `server/` 디렉토리

## 환경 변수

`.env.example` 참조. 주요 변수:
- `DATABASE_URL`: PostgreSQL 연결 문자열 (`postgresql+asyncpg://...`)
- `SECRET_KEY`: JWT 서명 키
- `API_V1_PREFIX`: API 경로 접두사 (기본값 `/api/v1`)
- `ALLOWED_ORIGINS`: CORS 허용 오리진
- `DEBUG`, `ENVIRONMENT`, `LOG_LEVEL`: 운영 환경 설정

## 변경 제안 시 형식

아키텍처나 스키마 변경을 제안할 때 반드시 다음 형식을 따릅니다:
1. **현재 상황**: 현재 구현 상태
2. **제안**: 변경 내용
3. **영향 범위**: 영향받는 파일/모듈
4. **리스크**: 잠재적 위험 요소

## 참조 문서

프로젝트 상세 문서는 `DOC/` 폴더 우선 참고:
- `DOC/ARCHITECTURE.md` - 시스템 아키텍처 및 설계 패턴
- `DOC/DEVELOPMENT_GUIDE.md` - 도메인 추가 체크리스트, 코드 품질 관리
- `DOC/BEGINNER_QUICK_START.md` - 환경 설정 및 첫 실행
- `DOC/PROJECT_HANDOVER.md` - 프로젝트 전체 개요
- `DOC/ALEMBIC_GUIDE.md` - DB 마이그레이션 가이드
- `server/README.md` - 백엔드 상세 가이드
- `client/README.md` - 프론트엔드 상세 가이드
