import React, { useState } from 'react';
import { useWeeklyReportStore } from '../store';

export const WeeklyReportResult: React.FC = () => {
  const { result, error, loading } = useWeeklyReportStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!result?.result_text) return;
    try {
      await navigator.clipboard.writeText(result.result_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback for environments without clipboard API
      const textarea = document.createElement('textarea');
      textarea.value = result.result_text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-gray-200 bg-gray-50 p-10">
        <svg className="h-8 w-8 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        <p className="text-sm text-gray-500">Gemini AI가 주간보고를 생성하고 있습니다…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6">
        <p className="text-sm font-semibold text-red-600">오류 발생</p>
        <p className="mt-1 text-sm text-red-500">{error}</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 p-10">
        <p className="text-sm text-gray-400">
          파일과 날짜를 선택한 후 생성 버튼을 눌러 주세요.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">생성 결과</h2>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 active:scale-95"
        >
          {copied ? (
            <>
              <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              복사됨!
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              복사하기
            </>
          )}
        </button>
      </div>

      <textarea
        readOnly
        value={result.result_text}
        className="min-h-[400px] w-full resize-y rounded-xl border border-gray-200 bg-white p-4 font-mono text-sm leading-relaxed text-gray-800 focus:outline-none"
      />

      <p className="text-right text-xs text-gray-400">
        생성일시: {new Date(result.generated_at).toLocaleString('ko-KR')}
      </p>
    </div>
  );
};
