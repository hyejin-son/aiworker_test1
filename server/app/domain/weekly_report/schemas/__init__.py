"""
주간보고 도메인 스키마

요청/응답 및 내부 DTO를 정의합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from server.app.shared.types import CalculatorInput, CalculatorOutput, FormatterInput


# ====================
# 외부 응답 스키마
# ====================


class WeeklyReportResponse(BaseModel):
    """주간보고 생성 결과 응답"""

    result_text: str = Field(description="최종 포맷팅된 주간보고 텍스트")
    generated_at: datetime = Field(description="생성 일시")

    model_config = {
        "json_schema_extra": {
            "example": {
                "result_text": "◈EPRO 운영\n[창원]\n▣ ...",
                "generated_at": "2026-02-20T10:00:00",
            }
        }
    }


# ====================
# 내부 DTO
# ====================


class ReportItem(BaseModel):
    """개별 SR(서비스 요청) 항목"""

    request_id: str = Field(description="요청 ID (A열)")
    status: str = Field(description="진행상태 (완료/진행중/대기)")
    schedule: str = Field(description="일정 (MM/DD 포맷)")
    category: str = Field(description="구분 (개발/개선 or 프로젝트/운영)")
    title: str = Field(description="제목 (AI 윤문 결과)")
    summary: str = Field(description="개요 (AI 윤문 결과)")
    content: Optional[str] = Field(default=None, description="내용 (AI 윤문 결과, 없을 수 있음)")
    company: str = Field(description="요청회사 분류 (창원 or 베스틸)")


class WeeklyReportCalculatorInput(CalculatorInput):
    """Calculator 입력 DTO"""

    file_a_bytes: bytes = Field(description="A 파일 바이트 데이터")
    file_b_bytes: bytes = Field(description="B 파일 바이트 데이터")
    file_c_bytes: bytes = Field(description="C 파일 바이트 데이터")
    file_d_bytes: bytes = Field(description="D 파일 바이트 데이터")
    report_date: str = Field(description="보고 기준 날짜 (YYYY-MM-DD)")


class WeeklyReportCalculatorOutput(CalculatorOutput):
    """Calculator 출력 DTO"""

    items: list[ReportItem] = Field(default_factory=list, description="처리된 SR 목록")


class WeeklyReportFormatterInput(FormatterInput):
    """Formatter 입력 DTO"""

    items: list[ReportItem] = Field(default_factory=list, description="처리된 SR 목록")
