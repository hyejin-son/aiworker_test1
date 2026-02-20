"""
주간보고 Calculator

엑셀 파일 전처리(Pandas), 필터링, 데이터 매핑, Gemini AI 윤문을 담당합니다.
"""

import asyncio
import io
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from server.app.shared.base.calculator import BaseCalculator
from server.app.domain.weekly_report.schemas import (
    ReportItem,
    WeeklyReportCalculatorInput,
    WeeklyReportCalculatorOutput,
)

logger = logging.getLogger(__name__)

# 필터링 대상 업무시스템 값
_TARGET_SYSTEMS = {
    "세아베스틸>기타>e-Procurement",
    "세아창원특수강>기타>e-Procurement",
}

# 진행상태 종료 키워드
_CLOSED_STATUSES = {"종료", "중단종료", "취소종료"}

# 구분 매핑
_DEV_CATEGORY_KEYWORD = "서비스요청 > 전산개발수정/신규 요청"
_CATEGORY_DEV = "개발/개선"
_CATEGORY_OPS = "프로젝트/운영"

# 회사 분류 키워드
_COMPANY_CHANGWON = "창원"
_COMPANY_BESTEEL = "베스틸"

# 엑셀 열 인덱스 (0-based, header=2 기준)
_COL_A = 0   # 요청 ID
_COL_B = 1   # 진행상태
_COL_C = 2   # 구분 (T열 없을 때)
_COL_D = 3   # 구분 타입 (CD 파일 조인용)
_COL_F = 5   # 업무시스템
_COL_G = 6   # 제목
_COL_H = 7   # 요구사항(개요)
_COL_J = 9   # 요청회사
_COL_O = 14  # 일정 (백업)
_COL_P = 15  # 처리완료일 (T 없을 때)
_COL_R = 17  # 처리내용 (T 없고 P 있을 때)
_COL_T = 19  # 변경 ID (CR ID)
_COL_W = 22  # 업무시스템2
_COL_Z = 25  # 처리완료일 (T 있을 때)
_COL_AB = 27 # 처리내용 (T 있고 Z 있을 때)


class WeeklyReportCalculator(BaseCalculator[WeeklyReportCalculatorInput, WeeklyReportCalculatorOutput]):
    """
    주간보고 데이터 처리 Calculator

    엑셀 4개 파일을 병합·필터링하고 Gemini API로 텍스트를 윤문합니다.
    Gemini 클라이언트는 생성자 주입을 통해 받아 아키텍처 결합도를 최소화합니다.
    """

    def __init__(self, gemini_client: object) -> None:
        """
        Args:
            gemini_client: google.generativeai.GenerativeModel 인스턴스
        """
        self._gemini = gemini_client

    async def calculate(
        self, input_data: WeeklyReportCalculatorInput
    ) -> WeeklyReportCalculatorOutput:
        """
        전체 파이프라인 실행: 병합 → 필터 → 매핑 → AI 윤문

        Args:
            input_data: 4개 엑셀 bytes + 보고 기준 날짜

        Returns:
            WeeklyReportCalculatorOutput: 처리된 SR 목록
        """
        # 1. 엑셀 읽기 & 병합
        ab_df = self._merge_files(input_data.file_a_bytes, input_data.file_b_bytes)
        cd_df = self._merge_files(input_data.file_c_bytes, input_data.file_d_bytes)

        # 2. 시스템 필터
        ab_df = self._filter_by_system(ab_df)
        if ab_df.empty:
            logger.info("필터링 결과 추출된 SR 없음")
            return WeeklyReportCalculatorOutput(items=[])

        # 3. 날짜 필터
        week_start, week_end = self._get_week_range(input_data.report_date)
        ab_df = self._filter_by_date(ab_df, week_start, week_end)
        if ab_df.empty:
            logger.info("날짜 필터링 결과 추출된 SR 없음")
            return WeeklyReportCalculatorOutput(items=[])

        # 4. 데이터 매핑 (raw 아이템 리스트)
        raw_items = self._map_rows(ab_df, cd_df)

        # 5. Gemini 윤문 (병렬)
        polished_items = await self._polish_with_gemini(raw_items)

        return WeeklyReportCalculatorOutput(items=polished_items)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _merge_files(self, bytes_a: bytes, bytes_b: bytes) -> pd.DataFrame:
        """두 엑셀 파일을 읽어 세로 방향으로 병합합니다. header=2(3행)."""
        df_a = pd.read_excel(io.BytesIO(bytes_a), header=2, dtype=str)
        df_b = pd.read_excel(io.BytesIO(bytes_b), header=2, dtype=str)
        merged = pd.concat([df_a, df_b], ignore_index=True)
        return merged

    def _get_cell(self, row: pd.Series, col_idx: int) -> str:
        """열 인덱스로 값을 안전하게 가져옵니다. NaN이면 빈 문자열 반환."""
        try:
            val = row.iloc[col_idx]
            if pd.isna(val):
                return ""
            return str(val).strip()
        except (IndexError, TypeError):
            return ""

    def _filter_by_system(self, df: pd.DataFrame) -> pd.DataFrame:
        """F열 또는 W열이 대상 업무시스템에 해당하는 행만 추출합니다."""
        def _is_target(row: pd.Series) -> bool:
            f_val = self._get_cell(row, _COL_F)
            w_val = self._get_cell(row, _COL_W)
            return f_val in _TARGET_SYSTEMS or w_val in _TARGET_SYSTEMS

        mask = df.apply(_is_target, axis=1)
        return df[mask].copy()

    def _get_week_range(self, report_date: str) -> tuple[datetime, datetime]:
        """보고 기준 날짜가 속한 주의 월요일~금요일 범위를 반환합니다."""
        dt = datetime.strptime(report_date, "%Y-%m-%d")
        week_start = dt - timedelta(days=dt.weekday())       # 월요일
        week_end = week_start + timedelta(days=4)             # 금요일
        return week_start.replace(hour=0, minute=0, second=0), week_end.replace(
            hour=23, minute=59, second=59
        )

    def _parse_date(self, value: str) -> Optional[datetime]:
        """다양한 날짜 형식을 파싱합니다. 실패 시 None 반환."""
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(value[:10], fmt)
            except ValueError:
                continue
        return None

    def _filter_by_date(
        self, df: pd.DataFrame, week_start: datetime, week_end: datetime
    ) -> pd.DataFrame:
        """
        날짜 기준 필터링:
        - T열(변경 ID) 없음 → P열 기준
        - T열 있음 → Z열 기준
        - 날짜가 빈 값이면 무조건 포함 (진행중/대기)
        """
        def _include(row: pd.Series) -> bool:
            t_val = self._get_cell(row, _COL_T)
            date_val = self._get_cell(row, _COL_Z if t_val else _COL_P)

            if not date_val:
                return True  # 날짜 없음 → 진행/대기 → 포함

            dt = self._parse_date(date_val)
            if dt is None:
                return True  # 파싱 실패도 안전하게 포함

            return week_start <= dt <= week_end

        mask = df.apply(_include, axis=1)
        return df[mask].copy()

    def _map_status(self, b_val: str) -> str:
        """B열 진행상태를 3단계로 정규화합니다."""
        for keyword in _CLOSED_STATUSES:
            if keyword in b_val:
                return "완료"
        if "요청 접수 및 분류" in b_val:
            return "대기"
        return "진행중"

    def _map_schedule(self, row: pd.Series) -> str:
        """P열 처리완료일(없으면 O열)을 MM/DD 포맷으로 반환합니다."""
        p_val = self._get_cell(row, _COL_P)
        date_str = p_val if p_val else self._get_cell(row, _COL_O)
        dt = self._parse_date(date_str)
        if dt:
            return dt.strftime("%m/%d")
        return date_str[:5] if date_str else ""

    def _map_category(self, row: pd.Series, cd_df: pd.DataFrame) -> str:
        """
        구분 매핑:
        - T열 없음 → C열 그대로 사용
        - T열 있음 → cd_df에서 T열(변경 ID)로 조인, D열 확인
        """
        t_val = self._get_cell(row, _COL_T)
        if not t_val:
            return self._get_cell(row, _COL_C)

        # CD 파일에서 T열(변경 ID)로 매핑하여 D열 확인
        # cd_df의 A열(0)이 변경 ID(T열)와 매핑된다고 가정
        matched = cd_df[cd_df.iloc[:, 0].astype(str).str.strip() == t_val]
        if matched.empty:
            return _CATEGORY_OPS

        d_val = self._get_cell(matched.iloc[0], _COL_D)
        return _CATEGORY_DEV if d_val == _DEV_CATEGORY_KEYWORD else _CATEGORY_OPS

    def _map_company(self, j_val: str) -> str:
        """J열 요청회사를 창원/베스틸로 분류합니다."""
        if _COMPANY_CHANGWON in j_val:
            return _COMPANY_CHANGWON
        if _COMPANY_BESTEEL in j_val or "베스틸" in j_val:
            return _COMPANY_BESTEEL
        return j_val  # 분류 불가 시 원본 유지

    def _map_rows(self, ab_df: pd.DataFrame, cd_df: pd.DataFrame) -> list[dict]:
        """
        필터링된 ab_df 행들을 raw dict 목록으로 매핑합니다.
        Gemini 윤문 전 원본 텍스트를 추출합니다.
        """
        raw_items: list[dict] = []

        for _, row in ab_df.iterrows():
            t_val = self._get_cell(row, _COL_T)
            p_val = self._get_cell(row, _COL_P)
            z_val = self._get_cell(row, _COL_Z)

            # 원본 텍스트 추출
            raw_title = self._get_cell(row, _COL_G)
            raw_summary = self._get_cell(row, _COL_H)
            raw_content: Optional[str] = None

            if not t_val:
                # T열 없음: P열에 데이터 있으면 R열도 추출
                if p_val:
                    raw_content = self._get_cell(row, _COL_R) or None
            else:
                # T열 있음: Z열에 데이터 있으면 AB열도 추출
                if z_val:
                    raw_content = self._get_cell(row, _COL_AB) or None

            raw_items.append(
                {
                    "request_id": self._get_cell(row, _COL_A),
                    "status": self._map_status(self._get_cell(row, _COL_B)),
                    "schedule": self._map_schedule(row),
                    "category": self._map_category(row, cd_df),
                    "company": self._map_company(self._get_cell(row, _COL_J)),
                    "raw_title": raw_title,
                    "raw_summary": raw_summary,
                    "raw_content": raw_content,
                }
            )

        return raw_items

    async def _polish_single(self, raw: dict) -> ReportItem:
        """단일 SR 항목을 Gemini로 윤문합니다."""
        prompt = self._build_prompt(raw["raw_title"], raw["raw_summary"], raw["raw_content"])
        try:
            response = await asyncio.to_thread(
                self._gemini.generate_content, prompt
            )
            title, summary, content = self._parse_gemini_response(
                response.text, raw["raw_title"], raw["raw_summary"], raw["raw_content"]
            )
        except Exception as exc:
            logger.warning("Gemini 윤문 실패, 원본 사용: %s", exc)
            title = raw["raw_title"]
            summary = raw["raw_summary"]
            content = raw["raw_content"]

        return ReportItem(
            request_id=raw["request_id"],
            status=raw["status"],
            schedule=raw["schedule"],
            category=raw["category"],
            company=raw["company"],
            title=title,
            summary=summary,
            content=content,
        )

    async def _polish_with_gemini(self, raw_items: list[dict]) -> list[ReportItem]:
        """모든 SR 항목을 병렬로 Gemini 윤문합니다."""
        tasks = [self._polish_single(raw) for raw in raw_items]
        return list(await asyncio.gather(*tasks))

    def _build_prompt(
        self, title: str, summary: str, content: Optional[str]
    ) -> str:
        """Gemini 윤문 프롬프트를 생성합니다."""
        content_line = f"\n처리내용(원본): {content}" if content else ""
        return (
            "다음은 IT 서비스 요청 데이터입니다.\n"
            "주간보고서의 [제목], [개요], [내용] 항목에 맞게 "
            "각각 1~2줄 이내의 명확한 비즈니스 용어로 요약해 주세요.\n"
            "인사말, 이름, 서명은 제거하고 핵심 내용만 작성하세요.\n"
            "반드시 아래 형식으로만 응답하세요:\n"
            "[제목]: <내용>\n"
            "[개요]: <내용>\n"
            "[내용]: <내용 없으면 '없음' 으로>\n\n"
            f"제목(원본): {title}\n"
            f"요구사항(원본): {summary}"
            f"{content_line}"
        )

    def _parse_gemini_response(
        self,
        text: str,
        fallback_title: str,
        fallback_summary: str,
        fallback_content: Optional[str],
    ) -> tuple[str, str, Optional[str]]:
        """
        Gemini 응답 텍스트를 [제목]/[개요]/[내용] 형식으로 파싱합니다.
        파싱 실패 시 원본 값을 반환합니다.
        """
        title = fallback_title
        summary = fallback_summary
        content = fallback_content

        for line in text.splitlines():
            line = line.strip()
            if line.startswith("[제목]:"):
                title = line.removeprefix("[제목]:").strip() or fallback_title
            elif line.startswith("[개요]:"):
                summary = line.removeprefix("[개요]:").strip() or fallback_summary
            elif line.startswith("[내용]:"):
                parsed = line.removeprefix("[내용]:").strip()
                content = None if parsed in ("없음", "") else parsed

        return title, summary, content
