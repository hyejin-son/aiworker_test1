"""
주간보고 Service

Router의 요청을 받아 Calculator → Formatter 워크플로우를 조율하고
최종 텍스트 문자열을 반환합니다.

Note: 본 도메인은 DB를 사용하지 않으므로 Repository 계층은 생략합니다.
      BaseService 상속 시 db=None으로 초기화합니다.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from google import genai

from server.app.core.config import settings
from server.app.shared.base.service import BaseService
from server.app.shared.types import ServiceResult
from server.app.domain.weekly_report.calculators import WeeklyReportCalculator
from server.app.domain.weekly_report.formatters import WeeklyReportFormatter
from server.app.domain.weekly_report.schemas import (
    WeeklyReportCalculatorInput,
    WeeklyReportFormatterInput,
    WeeklyReportResponse,
)

logger = logging.getLogger(__name__)


class WeeklyReportService(BaseService):  # type: ignore[type-arg]
    """
    주간보고 도메인 Service

    4개의 엑셀 파일과 보고 기준 날짜를 입력받아
    Gemini AI로 윤문된 주간보고 텍스트를 반환합니다.
    """

    def __init__(self) -> None:
        super().__init__(db=None)  # type: ignore[arg-type]

        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

        self._calculator = WeeklyReportCalculator(gemini_client=gemini_client)
        self._formatter = WeeklyReportFormatter()

    async def execute(  # type: ignore[override]
        self,
        file_a_bytes: bytes,
        file_b_bytes: bytes,
        file_c_bytes: bytes,
        file_d_bytes: bytes,
        report_date: str,
        **kwargs: Any,
    ) -> ServiceResult[WeeklyReportResponse]:
        """
        주간보고 생성 워크플로우 실행

        Args:
            file_a_bytes: ITS 엑셀 A 파일 bytes
            file_b_bytes: ITS 엑셀 B 파일 bytes
            file_c_bytes: 변경관리 엑셀 C 파일 bytes
            file_d_bytes: 변경관리 엑셀 D 파일 bytes
            report_date: 보고 기준 날짜 (YYYY-MM-DD)

        Returns:
            ServiceResult[WeeklyReportResponse]: 최종 포맷팅 텍스트 포함 응답
        """
        try:
            logger.info("주간보고 생성 시작: report_date=%s", report_date)

            # 1. Calculator: 전처리 + Gemini 윤문
            calc_input = WeeklyReportCalculatorInput(
                file_a_bytes=file_a_bytes,
                file_b_bytes=file_b_bytes,
                file_c_bytes=file_c_bytes,
                file_d_bytes=file_d_bytes,
                report_date=report_date,
            )
            calc_output = await self._calculator.calculate(calc_input)
            logger.info("Calculator 완료: 추출 SR 수=%d", len(calc_output.items))

            # 2. Formatter: 텍스트 포맷팅
            fmt_input = WeeklyReportFormatterInput(items=calc_output.items)
            result_text: str = await self._formatter.format(fmt_input)

            response = WeeklyReportResponse(
                result_text=result_text,
                generated_at=datetime.now(timezone.utc),
            )
            return ServiceResult.ok(response)

        except Exception as exc:
            logger.exception("주간보고 생성 실패: %s", exc)
            return ServiceResult.fail(str(exc))
