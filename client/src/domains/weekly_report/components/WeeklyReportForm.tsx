import React, { useRef } from 'react';
import { useWeeklyReportStore } from '../store';

const FILE_LABELS: { key: 'file_a' | 'file_b' | 'file_c' | 'file_d'; label: string }[] = [
  { key: 'file_a', label: 'A 파일 (ITS)' },
  { key: 'file_b', label: 'B 파일 (ITS)' },
  { key: 'file_c', label: 'C 파일 (변경관리)' },
  { key: 'file_d', label: 'D 파일 (변경관리)' },
];

export const WeeklyReportForm: React.FC = () => {
  const { formData, loading, setFormData, generate } = useWeeklyReportStore();
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const isFormValid =
    formData.report_date &&
    formData.file_a &&
    formData.file_b &&
    formData.file_c &&
    formData.file_d;

  const handleFileChange =
    (key: 'file_a' | 'file_b' | 'file_c' | 'file_d') =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0] ?? null;
      setFormData({ [key]: file });
    };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isFormValid) generate();
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      {/* 날짜 선택 */}
      <div className="flex flex-col gap-1">
        <label htmlFor="report_date" className="text-sm font-semibold text-gray-700">
          보고 기준 날짜
        </label>
        <input
          id="report_date"
          type="date"
          value={formData.report_date}
          onChange={(e) => setFormData({ report_date: e.target.value })}
          className="w-48 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          required
        />
        <p className="text-xs text-gray-500">
          선택한 날짜가 속한 주(월~금)의 SR을 추출합니다.
        </p>
      </div>

      {/* 파일 업로드 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {FILE_LABELS.map(({ key, label }) => {
          const file = formData[key];
          return (
            <div key={key} className="flex flex-col gap-1">
              <label className="text-sm font-semibold text-gray-700">{label}</label>
              <div
                className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 px-4 py-5 transition hover:border-blue-400 hover:bg-blue-50"
                onClick={() => fileRefs.current[key]?.click()}
              >
                <input
                  ref={(el) => {
                    fileRefs.current[key] = el;
                  }}
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileChange(key)}
                  className="hidden"
                />
                {file ? (
                  <span className="text-center text-xs font-medium text-blue-600 break-all">
                    {file.name}
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">클릭하여 엑셀 파일 선택</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 제출 버튼 */}
      <button
        type="submit"
        disabled={!isFormValid || loading}
        className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <>
            <svg
              className="h-4 w-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v8H4z"
              />
            </svg>
            AI 분석 중…
          </>
        ) : (
          '주간보고 생성'
        )}
      </button>
    </form>
  );
};
