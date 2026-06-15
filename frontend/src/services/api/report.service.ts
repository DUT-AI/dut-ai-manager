import axiosInstance from "../axiosInstance";
import type { ApiResponse } from "../../types/api.types";
import type { DashboardOverviewResponse, ReportResponse, TitleReportItem, ParticipationStats, ActivityTrendItem } from "../../types/report.types";

export const reportService = {
  getDashboardOverview: async (month: number, year: number): Promise<DashboardOverviewResponse> => {
    const response = await axiosInstance.get<ApiResponse<DashboardOverviewResponse>>('/reports/dashboard-overview', {
      params: { month, year }
    });
    return response.data.data as DashboardOverviewResponse;
  },

  getMonthlyActivityDates: async (month: number, year: number): Promise<string[]> => {
    const response = await axiosInstance.get<ApiResponse<string[]>>('/reports/monthly-stats', {
        params: { month, year }
    });
    return response.data.data as string[];
  },

  getDailySummary: async (date: string) => {
      const response = await axiosInstance.get('/reports/daily-summary', {
          params: { date }
      });
      return response.data.data;
  },

  getBonusPointReport: async (month?: number, year?: number, keyword?: string): Promise<ReportResponse> => {
    const response = await axiosInstance.get<ApiResponse<ReportResponse>>('/reports/bonus-points', {
        params: { month, year, keyword }
    });
    return response.data.data as ReportResponse;
  },

  getViolationReport: async (month?: number, year?: number, keyword?: string): Promise<ReportResponse> => {
    const response = await axiosInstance.get<ApiResponse<ReportResponse>>('/reports/violations', {
        params: { month, year, keyword }
    });
    return response.data.data as ReportResponse;
  },

  getTitlesReport: async (month: number, year: number): Promise<TitleReportItem[]> => {
    const response = await axiosInstance.get<ApiResponse<TitleReportItem[]>>('/reports/titles', {
        params: { month, year }
    });
    return response.data.data as TitleReportItem[];
  },

  getParticipationAnalysis: async (userId: number, month: number, year: number): Promise<ParticipationStats> => {
    const response = await axiosInstance.get<ApiResponse<ParticipationStats>>(`/reports/users/${userId}/participation`, {
        params: { month, year }
    });
    return response.data.data as ParticipationStats;
  },

  getParticipationLeaderboard: async (month: number, year: number): Promise<ParticipationStats[]> => {
    const response = await axiosInstance.get<ApiResponse<ParticipationStats[]>>('/reports/participation/leaderboard', {
        params: { month, year }
    });
    return response.data.data as ParticipationStats[];
  },

  getActivityTrend: async (month: number, year: number, mode: 'week' | 'month' = 'week'): Promise<ActivityTrendItem[]> => {
    const response = await axiosInstance.get<ApiResponse<ActivityTrendItem[]>>('/reports/activity-trend', {
        params: { month, year, mode }
    });
    return response.data.data as ActivityTrendItem[];
  }
};
