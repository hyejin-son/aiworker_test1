"""
주간보고 API 엔드포인트

4개의 엑셀 파일과 날짜를 받아 AI 윤문 주간보고 텍스트를 반환합니다.
"""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from server.app.domain.weekly_report.schemas import WeeklyReportResponse
from server.app.domain.weekly_report.service import WeeklyReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weekly-report", tags=["weekly-report"])


@router.post(
    "/generate",
    response_model=WeeklyReportResponse,
    summary="주간보고 생성",
    description=(
        "4개의 ITS/변경관리 엑셀 파일과 보고 기준 날짜를 업로드하면 "
        "Gemini AI로 윤문된 주간보고 텍스트를 반환합니다."
    ),
)
async def generate_weekly_report(
    report_date: str = Form(..., description="보고 기준 날짜 (YYYY-MM-DD)"),
    file_a: UploadFile = File(..., description="ITS 엑셀 A 파일"),
    file_b: UploadFile = File(..., description="ITS 엑셀 B 파일"),
    file_c: UploadFile = File(..., description="변경관리 엑셀 C 파일"),
    file_d: UploadFile = File(..., description="변경관리 엑셀 D 파일"),
) -> WeeklyReportResponse:
    """
    주간보고 자동 생성

    - **report_date**: 보고 기준 날짜. 해당 날짜가 속한 주(월~금)의 SR을 추출합니다.
    - **file_a / file_b**: ITS 엑셀 파일 (병합하여 AB 파일로 처리)
    - **file_c / file_d**: 변경관리 엑셀 파일 (병합하여 CD 파일로 처리)
    """
    file_a_bytes = await file_a.read()
    file_b_bytes = await file_b.read()
    file_c_bytes = await file_c.read()
    file_d_bytes = await file_d.read()

    service = WeeklyReportService()
    result = await service.execute(
        file_a_bytes=file_a_bytes,
        file_b_bytes=file_b_bytes,
        file_c_bytes=file_c_bytes,
        file_d_bytes=file_d_bytes,
        report_date=report_date,
    )

    if result.success:
        return result.data  # type: ignore[return-value]

    logger.error("주간보고 생성 실패: %s", result.error)
    raise HTTPException(status_code=400, detail=result.error)
