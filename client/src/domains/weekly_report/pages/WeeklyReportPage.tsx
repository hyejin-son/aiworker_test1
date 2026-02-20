import React from 'react';
import { WeeklyReportForm } from '../components/WeeklyReportForm';
import { WeeklyReportResult } from '../components/WeeklyReportResult';

export const WeeklyReportPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-10">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">주간보고 자동 생성</h1>
          <p className="mt-1 text-sm text-gray-500">
            ITS/변경관리 엑셀 파일 4개를 업로드하면 Gemini AI가 EPRO 운영 주간보고를 생성합니다.
          </p>
        </div>

        <div className="flex flex-col gap-8">
          {/* 입력 폼 */}
          <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
            <h2 className="mb-5 text-base font-semibold text-gray-800">파일 업로드</h2>
            <WeeklyReportForm />
          </section>

          {/* 결과 출력 */}
          <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
            <WeeklyReportResult />
          </section>
        </div>
      </div>
    </div>
  );
};
