export interface WeeklyReportResponse {
  result_text: string;
  generated_at: string;
}

export interface WeeklyReportFormData {
  report_date: string;
  file_a: File | null;
  file_b: File | null;
  file_c: File | null;
  file_d: File | null;
}
