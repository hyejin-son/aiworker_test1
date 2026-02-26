import { create } from 'zustand';
import { generateWeeklyReport } from './api';
import type { WeeklyReportFormData, WeeklyReportResponse } from './types';

interface WeeklyReportState {
  formData: WeeklyReportFormData;
  result: WeeklyReportResponse | null;
  loading: boolean;
  error: string | null;

  setFormData: (patch: Partial<WeeklyReportFormData>) => void;
  generate: () => Promise<void>;
  reset: () => void;
}

const initialFormData: WeeklyReportFormData = {
  report_date: '',
  file_a: null,
  file_b: null,
  file_c: null,
  file_d: null,
};

export const useWeeklyReportStore = create<WeeklyReportState>((set, get) => ({
  formData: { ...initialFormData },
  result: null,
  loading: false,
  error: null,

  setFormData: (patch) =>
    set((state) => ({ formData: { ...state.formData, ...patch } })),

  generate: async () => {
    set({ loading: true, error: null, result: null });
    try {
      const result = await generateWeeklyReport(get().formData);
      set({ result, loading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '주간보고 생성 실패';
      set({ error: message, loading: false });
    }
  },

  reset: () =>
    set({ formData: { ...initialFormData }, result: null, error: null }),
}));
