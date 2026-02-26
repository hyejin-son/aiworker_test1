import { apiClient } from '@/core/api';
import type { WeeklyReportFormData, WeeklyReportResponse } from './types';

export async function generateWeeklyReport(
  data: WeeklyReportFormData,
): Promise<WeeklyReportResponse> {
  const formData = new FormData();
  formData.append('report_date', data.report_date);
  formData.append('file_a', data.file_a as File);
  formData.append('file_b', data.file_b as File);
  formData.append('file_c', data.file_c as File);
  formData.append('file_d', data.file_d as File);

  const response = await apiClient.post<WeeklyReportResponse>(
    '/v1/weekly-report/generate',
    formData,
    { timeout: 120000 },
  );
  return response.data;
}
