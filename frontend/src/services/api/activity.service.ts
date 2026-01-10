import axiosInstance from '../axiosInstance';
import type { ApiResponse } from '@/types/api.types';
import type { DailySummaryResponse } from '@/types/activity.types';

export const activityService = {
  subPath: 'reports',

  async getDailySummary(date: string) {
    const response = await axiosInstance.get<ApiResponse<DailySummaryResponse>>(`/${this.subPath}/daily-summary`, {
      params: { date }
    });
    return response.data;
  },

  async getActivityStats() {
    const response = await axiosInstance.get<ApiResponse<any>>(`/${this.subPath}/stats`);
    return response.data;
  },

  async getMonthlyStats(month: number, year: number) {
    const response = await axiosInstance.get<ApiResponse<string[]>>(`/${this.subPath}/monthly-stats`, {
      params: { month, year }
    });
    return response.data;
  }
};
