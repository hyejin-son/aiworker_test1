"""
주간보고 Formatter

Calculator에서 정제된 ReportItem 목록을 최종 텍스트로 포맷팅합니다.
"""

import logging
from typing import Optional

from server.app.shared.base.formatter import BaseFormatter
from server.app.domain.weekly_report.schemas import (
    ReportItem,
    WeeklyReportFormatterInput,
)

logger = logging.getLogger(__name__)

_COMPANY_CHANGWON = "창원"
_COMPANY_BESTEEL = "베스틸"


class WeeklyReportFormatter(BaseFormatter[WeeklyReportFormatterInput, str]):
    """
    주간보고 텍스트 Formatter

    요청회사(J열) 기준으로 창원/베스틸을 분류하고
    ◈EPRO 운영 형식의 최종 텍스트 문자열을 반환합니다.
    """

    async def format(self, input_data: WeeklyReportFormatterInput) -> str:
        """
        Args:
            input_data: 처리된 SR 목록

        Returns:
            str: 최종 포맷팅된 주간보고 텍스트
        """
        changwon_items = [i for i in input_data.items if _COMPANY_CHANGWON in i.company]
        besteel_items = [i for i in input_data.items if _COMPANY_BESTEEL in i.company]

        lines: list[str] = ["◈EPRO 운영"]

        lines.append("[창원]")
        if changwon_items:
            for item in changwon_items:
                lines.extend(self._format_item(item))
        else:
            lines.append("  (해당 없음)")

        lines.append("")  # 빈 줄 구분

        lines.append("[베스틸]")
        if besteel_items:
            for item in besteel_items:
                lines.extend(self._format_item(item))
        else:
            lines.append("  (해당 없음)")

        return "\n".join(lines)

    def _format_item(self, item: ReportItem) -> list[str]:
        """단일 SR 항목을 텍스트 줄 목록으로 변환합니다."""
        schedule_part = f"~{item.schedule}" if item.schedule else ""
        header = (
            f"▣ ({item.category}) ({item.request_id}) {item.title}"
            f" ({schedule_part}, {item.status})"
        )
        lines = [header, f"  -. 개요 : {item.summary}"]
        if item.content:
            lines.append(f"  -. 내용 : {item.content}")
        lines.append("")  # 아이템 간 빈 줄
        return lines
